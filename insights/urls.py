from django.urls import path
from . import views

app_name = "insights"
urlpatterns = [
    path("", views.entry_view, name="entry"),
    path("messages/", views.overview, name="overview"),
    path("messages/export/", views.export_messages, name="export"),
    path("threads/", views.threads_view, name="thread-list"),
    path("threads/<uuid:pk>/", views.thread_detail, name="thread-detail"),
    path("messages/<int:pk>/", views.message_detail, name="message-detail"),
    path("stats/", views.stats_view, name="stats"),
]
