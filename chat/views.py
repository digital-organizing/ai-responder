# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from langdetect import detect

from chat.completion import generate_answer
from chat.models import ChatBot
from context.search import get_documents, search
from context.serializers import DocumentSerializer


def index_view(request: HttpRequest):
    return render(request, "index.html")


@csrf_exempt
def answer_view(request: HttpRequest, slug):
    data = request.POST.dict()
    q = str(data.pop("question"))[:10_000]

    bot = ChatBot.objects.get(slug=slug)
    docs = []

    if bot.context_provider:
        results = search(bot.context_provider.slug, q, limit=10)
        docs = get_documents(results)

    answer = generate_answer(q, bot, docs, **data)
    serializer = DocumentSerializer(docs, many=True)

    return JsonResponse(
        {
            "answer": answer.choices[0].message.content.replace("ß", "ss"),
            "docs": serializer.data,
        }
    )


@login_required
def form_view(request):
    groups = request.user.groups.all()

    return render(
        request, "chat/form.html", {"groups": groups, "title": "Simple-Answers"}
    )


@login_required
def field_view(request, slug):
    return render(
        request, "chat/bot_form.html", {"bot": ChatBot.objects.get(slug=slug)}
    )


@csrf_exempt
def determine_language(request):
    data = request.POST.dict()
    q = str(data.pop("question"))

    return JsonResponse({"lang": detect(q)})
