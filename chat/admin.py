from django.contrib import admin

from chat.models import ChatBot, Field, Message, Thread


class FieldInline(admin.TabularInline):
    model = Field


@admin.register(ChatBot)
class ChatBotAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_public"]
    inlines = [FieldInline]


class MessageInline(admin.TabularInline):
    model = Message


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    inlines = [MessageInline]
