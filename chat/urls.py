from django.urls import path

from chat.views import answer_view, field_view, form_view, determine_language, function_call, manage_view, manage_chatbot

app_name = "chat"

urlpatterns = [
    path('detect-language/', determine_language, name="detect-language"),
    path('manage/', manage_view, name="manage"),
    path("<slug:slug>/", answer_view, name="answer"),
    path("<slug:slug>/function/", function_call, name="function-call"),
    path("<slug:slug>/fields/", field_view, name="fields"),
    path("<slug:slug>/manage/", manage_chatbot, name="manage-chatbot"),
    path("", form_view, name="form"),
]
