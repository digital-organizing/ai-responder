# Register your models here.


from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest

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

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__in=request.user.groups.all())

    def get_form(self, request: HttpRequest, obj=None, **kwargs) -> type[ModelForm]:
        form = super().get_form(request, obj, **kwargs)

        if not request.user.is_superuser:
            form.base_fields["group"].queryset = request.user.groups.all()
        return form


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "collection"]

    actions = ["delete_documents_action"]

    autocomplete_fields = ["page"]

    @admin.action(description="Delete Documents")
    def delete_documents_action(self, request, queryset):
        delete_documents(queryset)
