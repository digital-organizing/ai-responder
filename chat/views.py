# Create your views here.
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from langdetect import detect

from chat.completion import generate_answer, generate_function_call
from chat.models import ChatBot
from context.search import get_documents, search
from context.serializers import DocumentSerializer

import requests
import openai


def index_view(request: HttpRequest):
    requests.get("https://google.com", timeout=10)
    return render(request, "index.html")


@csrf_exempt
def answer_view(request: HttpRequest, slug):

    data = request.POST.dict()
    q = str(data.pop("question"))[-10_000:]

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


@csrf_exempt
def function_call(request: HttpRequest, slug):
    bot = ChatBot.objects.get(slug=slug)
    data = request.POST.dict()
    q = str(data.pop("question"))[-10_000:]
    function = data.pop("function", None)
    
    data.pop("csrfmiddlewaretoken", '')

    docs = []
    
    if bot.context_provider:
        results = search(bot.context_provider.slug, q, limit=10)
        docs = get_documents(results)
        
    answer = generate_function_call(q, bot, docs, function, **data)
    message : openai = answer.choices[0].message
    content = message.content or ''
    tools = message.tool_calls or []
    if len(tools) > 0:
        try:
            tools = json.loads(tools[0].function.arguments)
        except json.JSONDecodeError as er:
            tools = []    
    
    return JsonResponse({
        "tools": tools,
        "content": content.replace("ß", "ss"),
        "docs": docs
    })

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


@login_required
def manage_view(request):
    groups = request.user.groups.all()
    return render(request, "manage.html", {"groups": groups, "title": "Manage"})


@login_required
def manage_chatbot(request, slug):
    bot = ChatBot.objects.get(slug=slug)
    if not bot.group in request.user.groups.all():
        raise PermissionError("You are not allowed to manage this bot")

    return render(request, "chat/manage_bot.html", {"bot": bot})


def thread_init(request, slug):
    # TODO: create a new thread with init message and question
    # Important: 
    # - 
    pass


def thread_continue(request, slug):
    # TODO: add sent message to thread, get copmletion
    # Important
    # - 
    pass