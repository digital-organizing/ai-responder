from context.embeddings import (
    generate_embeddings,
    generate_embeddings_openai,
    load_encoder,
    qdrant_client,
)
from context.models import Collection, Document


def search(slug, query, limit=5):
    collection = Collection.objects.get(slug=slug)
    if collection.use_openai:
        embedding = generate_embeddings_openai([query])
    else:
        embedding = generate_embeddings([query], load_encoder(collection.language))

    with qdrant_client() as client:
        result = client.search(collection.slug, embedding[0], limit=limit)
    return result


def get_documents(result):
    pks = [r.id for r in result]
    scores = [r.score for r in result]
    docs = list(Document.objects.filter(pk__in=pks).prefetch_related("page"))

    docs = [x for _, x in sorted(zip(scores, docs))]
    print(docs)
    return docs
