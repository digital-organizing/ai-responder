from django.urls import path

from chat.views import answer_view, field_view, form_view

app_name = "chat"

urlpatterns = [
    path("<slug:slug>/", answer_view, name="answer"),
    path("<slug:slug>/fields/", field_view, name="fields"),
    path("", form_view, name="form"),
]
