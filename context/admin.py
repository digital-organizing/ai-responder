# Register your models here.


from django.contrib import admin

from context.embeddings import delete_documents
from context.models import Collection, Document
from context.tasks import index_documents_task, reindex_documents_task


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ["slug"]

    actions = ["index_collection_action", "reindex_collection_action"]

    @admin.action(description="Index collection")
    def index_collection_action(self, request, queryset):
        for q in queryset:
            index_documents_task.delay(pk=q.pk)

    @admin.action(description="Reindex collection")
    def reindex_collection_action(self, request, queryset):
        for q in queryset:
            reindex_documents_task.delay(pk=q.pk)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "collection"]

    actions = ["delete_documents_action"]

    @admin.action(description="Delete Documents")
    def delete_documents_action(self, request, queryset):
        delete_documents(queryset)
