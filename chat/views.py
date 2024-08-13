# Create your views here.
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from langdetect import detect

from chat.completion import generate_answer
from chat.models import ChatBot, Thread, Message
from context.search import get_documents, search
from context.serializers import DocumentSerializer

import requests
import openai


def index_view(request: HttpRequest):
    return render(request, "index.html")


@csrf_exempt
def answer_view(request: HttpRequest, slug):

    data = request.POST.dict()
    q = str(data.pop("question"))[-10_000:]

    bot = ChatBot.objects.get(slug=slug)
    docs = []

    data.pop("csrfmiddlewaretoken", '')
    if bot.context_provider:
        results = search(bot.context_provider.slug, q, limit=10)
        docs = get_documents(results)

    answer, _ = generate_answer(q, bot, docs, **data)

    message : openai = answer.choices[0].message
    content = message.content or ''
    tools = message.tool_calls or []
    if len(tools) > 0:
        try:
            tools = json.loads(tools[0].function.arguments)
        except json.JSONDecodeError as er:
            tools = []    

    serializer = DocumentSerializer(docs, many=True)

    return JsonResponse({
        "tools": tools,
        "answer": content.replace("ß", "ss"),
        "docs": serializer.data
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


@csrf_exempt
def thread_init(request, slug):
    data = request.POST.dict()
    q = str(data.pop("question"))[-10_000:]

    bot = ChatBot.objects.get(slug=slug)
    docs = []

    data.pop("csrfmiddlewaretoken", '')

    if bot.context_provider:
        results = search(bot.context_provider.slug, q, limit=10)
        docs = get_documents(results)

    answer, messages = generate_answer(q, bot, docs, **data)
    
    # Init the thread
    thread = Thread.objects.create(bot=bot)

    for message in messages:
        thread.message_set.create(
            content=message['content'],
            role=message['role'],
        )

    message = answer.choices[0].message
    content = message.content or ''
    content = content.replace("ß", "ss")
    tools = message.tool_calls or []

    if len(tools) > 0:
        try:
            tools = json.loads(tools[0].function.arguments)
        except json.JSONDecodeError as er:
            tools = []    
    

    thread.message_set.create(
        content=content,
        tools=tools,
        role='assistant'
    )

    serializer = DocumentSerializer(docs, many=True)

    return JsonResponse(
        {
            "tools": tools,
            "answer": content,
            "docs": serializer.data,
            "threadId": thread.pk,
        }
    )

@csrf_exempt
def thread_continue(request, slug):
    
    if request.method == 'GET':
        thread_id = request.GET.get('pk')
        thread = Thread.objects.get(pk=thread_id)
        return JsonResponse({'messages': thread.messages()[1:]})

    data = request.POST.dict()

    data.pop("csrfmiddlewaretoken", '')

    q = str(data.pop("question"))[-10_000:]

    bot = ChatBot.objects.get(slug=slug)
    docs = []

    if bot.context_provider:
        results = search(bot.context_provider.slug, q, limit=10)
        docs = get_documents(results)

    thread = Thread.objects.get(pk=data.pop('threadId'))
    messages = thread.messages()

    answer, messages = generate_answer(q, bot, docs, messages=messages, **data)

    message = answer.choices[0].message
    content = message.content or ''

    content = content.replace("ß", "ss")
    tools = message.tool_calls or []

    if len(tools) > 0:
        try:
            tools = json.loads(tools[0].function.arguments)
        except json.JSONDecodeError as er:
            tools = []    

    msg = messages[-1]
    
    thread.message_set.create(role=msg['role'], content=msg['content'])
    thread.message_set.create(role='assistant', content=content, tools=tools)

    serializer = DocumentSerializer(docs, many=True)
    
    return JsonResponse({
        "tools": tools,
        "answer": content,
        "docs": serializer.data,
        "threadId": thread.pk,
    })