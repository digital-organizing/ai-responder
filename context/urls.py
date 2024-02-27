from django.urls import path

from context.views import query_context, search_view

app_name = "context"

urlpatterns = [
    path("search/", query_context, name="search-api"),
    path("", search_view, name="search"),
]
