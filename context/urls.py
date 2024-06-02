from django.urls import path

from context.views import (
    query_context,
    search_view,
    upload_file,
    list_files,
    manage_collection,
    list_documents,
    delete_file,
    create_document,
    delete_document,
    update_document,
)

app_name = "context"

urlpatterns = [
    path("search/", query_context, name="search-api"),
    path("<slug:slug>/manage/", manage_collection, name="manage-collection"),
    path("<slug:slug>/files/", list_files, name="file-list"),
    path("<slug:slug>/documents/", list_documents, name="document-list"),
    path("<slug:slug>/documents/create/", create_document, name="create-document"),
    path("<slug:slug>/documents/delete/", delete_document, name="delete-document"),
    path(
        "<slug:slug>/<int:pk>/documents/update/",
        update_document,
        name="update-document",
    ),
    path("<slug:slug>/files/upload/", upload_file, name="upload-file"),
    path("<slug:slug>/files/delete/", delete_file, name="delete-file"),
    path("", search_view, name="search"),
]
