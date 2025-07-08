import time
from celery import shared_task
from django.conf import settings
from openai import OpenAI
import openai
import json

from context.embeddings import index_documents, reindex_documents
from context.models import Collection, Document


@shared_task
def index_documents_task(pk):
    index_documents(Collection.objects.get(pk=pk))


@shared_task
def reindex_documents_task(pk):
    reindex_documents(Collection.objects.get(pk=pk))


@shared_task
def create_document_titles(pks):
    documents = Document.objects.filter(pk__in=pks)

    batch = []

    for doc in documents:
        batch.append(
            json.dumps(
                {
                    "custom_id": f"{doc.pk}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "gpt-4o-mini-2024-07-18",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Generiere einen Titel basierend auf dem Inhalt des Dokumentes, der kurz und prägnant ist. Der Titel sollte den Inhalt des Dokuments zusammenfassen und ansprechend sein. Schreibe alles auf Deutsch.",
                            },
                            {
                                "role": "user",
                                "content": doc.content,
                            },
                        ],
                        "max_tokens": 50,
                        "temperature": 0.3,
                    },
                }
            )
        )

    jsonl_text = "\n".join(batch)

    client = openai.OpenAI(api_key=settings.OPENAI_KEY)

    batch_input_file = client.files.create(
        file=jsonl_text.encode("utf-8"),
        purpose="batch",
    )
    request = client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "nightly eval job"},
    )

    print(f"Batch request created with ID: {request.id}")
    status = client.batches.retrieve(request.id)

    while status.status not in ["completed", "failed"]:
        status = client.batches.retrieve(request.id)
        time.sleep(5)

    if status.status == "failed":
        raise Exception("Batch processing failed")

    assert status.output_file_id is not None, "No output file generated"

    file_result = client.files.content(status.output_file_id)

    for line in file_result.text.splitlines():
        result = json.loads(line)
        if result.get("error"):
            print(f"Error processing document: {result['error']}")
            continue

        custom_id = int(result.get("custom_id"))

        title = result["response"]["body"]["choices"][0]["message"]["content"]
        
        title = title.replace("\n", " ").strip().replace('"', "").replace("**", "")

        if custom_id and title:
            doc = documents.get(pk=custom_id)
            doc.title = title
            doc.save()
