from django.urls import path

from context.views import query_context, search_view, upload_file, list_files

app_name = "context"

urlpatterns = [
    path("search/", query_context, name="search-api"),
    path("<slug:slug>/files/", list_files, name="upload"),
    path("<slug:slug>/files/upload/", upload_file, name="upload"),
    path("", search_view, name="search"),
]
