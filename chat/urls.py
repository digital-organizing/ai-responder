from django.urls import path

from chat.views import (
    answer_view,
    field_view,
    form_view,
    determine_language,
    manage_view,
    manage_chatbot,
    thread_continue,
    thread_init,
)

app_name = "chat"

urlpatterns = [
    path("detect-language/", determine_language, name="detect-language"),
    path("manage/", manage_view, name="manage"),
    path("<slug:slug>/", answer_view, name="answer"),
    path("<slug:slug>/fields/", field_view, name="fields"),
    path("<slug:slug>/manage/", manage_chatbot, name="manage-chatbot"),
    path("<slug:slug>/thread/init/", thread_init, name="thread-init"),
    path("<slug:slug>/thread/", thread_continue, name="thread-continue"),
    path("", form_view, name="form"),
]
