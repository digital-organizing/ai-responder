from contextlib import contextmanager
from typing import List, TYPE_CHECKING

import numpy as np
import openai
from django.conf import settings
from django.db.models import QuerySet
from qdrant_client import QdrantClient, models

if TYPE_CHECKING:
    from laser_encoders import LaserEncoderPipeline

from context.models import Collection, Document


@contextmanager
def qdrant_client():
    client = QdrantClient(settings.QDRANT_HOST, port=settings.QDRANT_PORT)

    try:
        yield client
    finally:
        client.close()


def load_encoder(language):
    from laser_encoders import LaserEncoderPipeline

    encoder = LaserEncoderPipeline(language)
    return encoder


EMBEDDING_DIMENSION = 1024


def generate_embeddings(texts: List[str], encoder):
    return np.array(encoder.encode_sentences(texts, normalize_embeddings=True))


def generate_embeddings_openai(texts: List[str]):
    client = openai.Client(api_key=settings.OPENAI_KEY)
    response = client.embeddings.create(input=texts, model="text-embedding-3-large")
    results = [data.embedding for data in response.data]
    client.close()
    return np.array(results)


def get_embedding(document: Document):
    if document.collection.use_openai:
        return generate_embeddings_openai([document.content])

    return generate_embeddings(
        [document.content], load_encoder(document.collection.language)
    )


def batch_qs(qs, batch_size=1000):
    """
    Returns a (start, end, total, queryset) tuple for each batch in the given
    queryset.

    Usage:
        # Make sure to order your querset
        article_qs = Article.objects.order_by('id')
        for start, end, total, qs in batch_qs(article_qs):
            print "Now processing %s - %s of %s" % (start + 1, end, total)
            for article in qs:
                print article.body
    """
    total = qs.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield qs[start:end]


def names(response):
    return [collection.name for collection in response.collections]


def collection_exists(qdrant, slug):
    return slug in names(qdrant.get_collections())


def _batch_insert(collection, query, encoder, use_openai):
    records = list(query)
    print(f"Creating embeddings for {len(records)} texts")

    if use_openai:
        embeddings = generate_embeddings_openai([r[1] for r in records])
    else:
        embeddings = generate_embeddings([r[1] for r in records], encoder)

    embedding_dim = embeddings.shape[-1]

    with qdrant_client() as qdrant:
        if not collection_exists(qdrant, collection.slug):
            qdrant.create_collection(
                collection.slug,
                models.VectorParams(
                    size=embedding_dim, distance=models.Distance.COSINE
                ),
            )

        qdrant.upload_records(
            collection_name=collection.slug,
            records=[
                models.Record(id=r[0], vector=embedding)
                for r, embedding in zip(records, embeddings)
            ],
        )


def index_documents(collection: Collection):

    query = Document.objects.filter(collection=collection).filter(is_indexed=False)

    update_documents(query, collection)


def insert_document(doc: Document):
    with qdrant_client() as client:
        client.upsert(
            doc.collection.slug,
            [models.PointStruct(id=doc.pk, vector=get_embedding(doc)[0])],
        )


def update_document(doc: Document):
    with qdrant_client() as client:
        client.update_vectors(
            doc.collection.slug,
            [models.PointVectors(id=doc.pk, vector=get_embedding(doc)[0])],
        )


def update_documents(docs: QuerySet[Document], collection: Collection):
    if not collection.use_openai:
        encoder = load_encoder(collection.language)
    else:
        encoder = None

    for batch in batch_qs(docs.values_list("pk", "content").order_by("pk")):
        _batch_insert(collection, batch, encoder, collection.use_openai)

    docs.update(is_indexed=True)


def reindex_documents(collection: Collection):
    with qdrant_client() as qdrant:
        if collection_exists(qdrant, collection.slug):
            qdrant.delete_collection(collection.slug)

    Document.objects.filter(collection=collection, stale=True).delete()
    Document.objects.filter(collection=collection).update(is_indexed=False)
    index_documents(collection)


def delete_documents(queryset: QuerySet[Document]):
    indexed = queryset.filter(is_indexed=True)
    if not indexed.exists():
        return
    pks = list(indexed.values_list("pk", flat=True))
    collection = indexed[0].collection

    with qdrant_client() as client:
        client.delete(
            collection_name=collection.slug,
            points_selector=models.PointIdsList(
                points=pks,
            ),
        )

    queryset.delete()
