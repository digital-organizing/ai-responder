from django.http import HttpResponse, JsonResponse
import pandas as pd
from django.db.models import F, Count, Func
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.db.models import Count
from django.db.models import F
import numpy as np
from django.shortcuts import render
from django.db.models import Min
from django.contrib.auth.decorators import login_required

from chat.models import ChatBot, Message, Thread
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request

from chat.message import retrieve_questions

from context.embeddings import generate_embeddings_openai
from insights.forms import StatsForm
from datetime import timedelta
# Create your views here.


@login_required
def overview(request):
    context = {}

    if request.user.is_superuser:
        available_bots = ChatBot.objects.all()
    else:
        available_bots = ChatBot.objects.filter(group__in=request.user.groups.all())

    messages = Message.objects.filter(
        thread__bot__in=available_bots, role="user"
    ).order_by("-created_at")

    paginator = LimitOffsetPagination()
    paginator.default_limit = 100

    context["page"] = paginator.paginate_queryset(messages, Request(request))
    context["pager"] = paginator
    context["title"] = "Nachrichten"

    return render(request, "insights/overview.html", context)

@login_required
def export_messages(request):
    """Export messages as xlsx"""
    if request.user.is_superuser:
        available_bots = ChatBot.objects.all()
    else:
        available_bots = ChatBot.objects.filter(group__in=request.user.groups.all())

    messages = Message.objects.filter(
        thread__bot__in=available_bots, role="user"
    ).order_by("-created_at")[:50_000].select_related("thread__bot").values_list("created_at", "content", "thread__bot__name")
    
    df = pd.DataFrame(messages, columns=["created_at", "content", "bot"])
    df["created_at"] = df["created_at"].dt.tz_localize(None) 
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=messages.xlsx'
    df.to_excel(response, index=False)
    return response


@login_required
def threads_view(request):
    context = {}
    if request.user.is_superuser:
        available_bots = ChatBot.objects.all()
    else:
        available_bots = ChatBot.objects.filter(group__in=request.user.groups.all())
    threads = (
        Thread.objects.annotate(first_message_date=Min("message__created_at"))
        .filter(bot__in=available_bots)
        .order_by("-first_message_date")
    )

    paginator = LimitOffsetPagination()
    paginator.default_limit = 100

    context["page"] = paginator.paginate_queryset(threads, Request(request))
    context["pager"] = paginator
    context["title"] = "Threads"

    return render(request, "insights/threads.html", context)


@login_required
def thread_detail(request, pk):
    context = {}
    if request.user.is_superuser:
        available_bots = ChatBot.objects.all()
    else:
        available_bots = ChatBot.objects.filter(group__in=request.user.groups.all())
    thread = Thread.objects.get(pk=pk)
    if thread.bot not in available_bots:
        raise PermissionError("You do not have access to this thread.")
    context["thread"] = thread
    context["title"] = "Thread"
    return render(request, "insights/thread_detail.html", context)


@login_required
def message_detail(request, pk):

    message = Message.objects.get(pk=pk)

    if request.user.is_superuser:
        available_bots = ChatBot.objects.all()
    else:
        available_bots = ChatBot.objects.filter(group__in=request.user.groups.all())
    if message.thread.bot not in available_bots:
        raise PermissionError("You do not have access to this message.")

    messages = retrieve_questions(message, message.thread.bot)

    return render(
        request,
        "insights/message_detail.html",
        {
            "rows": messages,
            "current": message,
            "title": "Nachricht",
        },
    )
    
@login_required
def entry_view(request):
    return render(request, "insights/entry.html", {'title': 'Insights'})


@login_required
def stats_view(request):

    if not request.GET:
        form = StatsForm(user=request.user)
        return render(request, "insights/stats.html", {"form": form, "title": "Statistiken"})

    form = StatsForm(request.GET, user=request.user)

    if not form.is_valid():
        return render(request, "insights/stats.html", {"form": form , "title": "Statistiken"})

    bots = form.cleaned_data["bots"]
    start_date = form.cleaned_data["start_date"]
    end_date = form.cleaned_data["end_date"]
    group_by = form.cleaned_data["group_by"]

    messages = Message.objects.filter(thread__bot__in=bots, role="user")
    if start_date:
        messages = messages.filter(created_at__gte=start_date)
    if end_date:
        messages = messages.filter(created_at__lte=end_date)

    if group_by == "day":
        messages = (
            messages.annotate(
                range_start=TruncDay('created_at'),
            )
            .values("range_start")
            .annotate(
                count=Count("id"),
                # We need to use a raw SQL approach for the end date calculation
                range_end=Func(
                    F('range_start'), 
                    function='',
                    template="%(expressions)s + INTERVAL '1 day'"
                )
            )
        )
    elif group_by == "week":
        messages = (
            messages.annotate(
                range_start=TruncWeek('created_at'),
            )
            .values("range_start")
            .annotate(
                count=Count("id"),
                range_end=Func(
                    F('range_start'), 
                    function='',
                    template="%(expressions)s + INTERVAL '1 week'"
                )
            )
        )
    elif group_by == "month":
        messages = (
            messages.annotate(
                range_start=TruncMonth('created_at'),
            )
            .values("range_start")
            .annotate(
                count=Count("id"),
                range_end=Func(
                    F('range_start'), 
                    function='',
                    template="%(expressions)s + INTERVAL '1 month'"
                )
            )
        )
    elif group_by == "year":
        messages = (
            messages.annotate(
                range_start=TruncYear('created_at'),
            )
            .values("range_start")
            .annotate(
                count=Count("id"),
                range_end=Func(
                    F('range_start'), 
                    function='',
                    template="%(expressions)s + INTERVAL '1 year'"
                )
            )
        )
    else:
        raise ValueError("Invalid group_by value")
    messages = messages.order_by("range_start")
    total_messages = messages.aggregate(total=Count("id"))["total"]
    units = {
        "day": "Tag",
        "week": "Woche",
        "month": "Monat",
        "year": "Jahr",
    }
    return render(
        request,
        "insights/stats.html",
        {
            "form": form,
            "messages": messages,
            "total_messages": total_messages,
            "unit": units[group_by],
            "title": "Statistiken",
        },
    )

