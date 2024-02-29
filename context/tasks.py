from celery import shared_task

from context.embeddings import index_documents, reindex_documents
from context.models import Collection


@shared_task
def index_documents_task(pk):
    index_documents(Collection.objects.get(pk=pk))


@shared_task
def reindex_documents_task(pk):
    reindex_documents(Collection.objects.get(pk=pk))
