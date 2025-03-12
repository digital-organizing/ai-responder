from context.embeddings import (
    get_embedding,
    load_encoder,
    qdrant_client,
    generate_embeddings,
    generate_embeddings_openai,
    collection_exists,
)

from chat.models import ChatBot, Message
from context.models import Collection
from qdrant_client.http.models import models


def store_question(msg: Message, bot: ChatBot):
    store_name = bot.slug + "_questions"

    if bot.context_provider:
        use_openai = bot.context_provider.use_openai
    else:
        use_openai = True

    with qdrant_client() as client:
        if (
            collection_exists(client, store_name)
            and len(client.retrieve(collection_name=store_name, ids=[msg.pk])) > 0
        ):
            return

        if use_openai:
            embeddings = generate_embeddings_openai([msg.content])
        else:
            assert bot.context_provider is not None
            embeddings = generate_embeddings(
                [msg.content], load_encoder(bot.context_provider.language)
            )

        embedding_dim = embeddings.shape[-1]

        if not collection_exists(client, store_name):
            client.create_collection(
                store_name,
                models.VectorParams(
                    size=embedding_dim, distance=models.Distance.COSINE
                ),
            )
        client.upload_records(
            collection_name=store_name,
            records=[models.Record(id=msg.pk, vector=embeddings[0])],
        )
        print("Stored point", msg.pk)


def retrieve_questions(msg: Message, bot: ChatBot, n=50, offset=0):
    store_name = bot.slug + "_questions"

    with qdrant_client() as client:
        vector = client.retrieve(
            collection_name=store_name, ids=[msg.pk], with_vectors=True
        )[0].vector
        assert vector is not None
        msgs = client.search(store_name, vector, limit=n, offset=offset)

    pks = [r.id for r in msgs]
    scores = [r.score for r in msgs]

    messages = list(Message.objects.filter(pk__in=pks))
    messages = {m.pk: m for m in messages}

    messages = [(score, messages[pk]) for score, pk in zip(scores, pks)]

    return messages
