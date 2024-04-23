from django.urls import path

from chat.views import answer_view, field_view, form_view, determine_language

app_name = "chat"

urlpatterns = [
    path('detect-language/', determine_language, name="detect-language"),
    path("<slug:slug>/", answer_view, name="answer"),
    path("<slug:slug>/fields/", field_view, name="fields"),
    path("", form_view, name="form"),
]
