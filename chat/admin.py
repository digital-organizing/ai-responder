from typing import Any
from django.contrib import admin
from django.db.models import Q
from django.db.models import JSONField
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest
from django_json_widget.widgets import JSONEditorWidget
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from django.contrib.auth.models import User, Group

from chat.message import store_question
from chat.models import ChatBot, Field, Message, Thread


class FieldInline(admin.TabularInline):
    model = Field


@admin.register(ChatBot)
class ChatBotAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_public"]
    inlines = [FieldInline]

    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget},
    }

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(group__in=request.user.groups.all())

    def get_form(self, request, obj=None, **kwargs):
        # Get the default form
        form = super().get_form(request, obj, **kwargs)
        # Exclude 'is_superuser' for non-superusers
        if not request.user.is_superuser:
            form.base_fields["group"].queryset = request.user.groups.all()
        return form


class MessageInline(admin.TabularInline):
    model = Message


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    inlines = [MessageInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(bot__group__in=request.user.groups.all())

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields["bot"].queryset = form.base_fields["bot"].queryset.filter(
                group__in=request.user.groups.all()
            )

        return form


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(thread__bot__group__in=request.user.groups.all())

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields["thread"].queryset = form.base_fields[
                "thread"
            ].queryset.filter(bot__group__in=request.user.groups.all())
        return form

    list_display = ["content", "role", "created_at", "thread_id"]
    list_filter = ["role", "thread__bot"]
    date_hierarchy = "created_at"

    actions = ["index_questions"]

    def index_questions(self, request, queryset):
        for message in queryset.filter(role="user"):
            store_question(message, message.thread.bot)


class CustomUserAdmin(UserAdmin):
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(
            Q(groups__in=request.user.groups.all()) | Q(groups__isnull=True)
        ).distinct()

    def get_readonly_fields(self, request, obj=None):
        # If the user is not a superuser, make 'is_superuser' read-only
        if not request.user.is_superuser:
            return self.readonly_fields + ("is_superuser", "user_permissions")
        return self.readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        # Get the default form
        form = super().get_form(request, obj, **kwargs)
        # Exclude 'is_superuser' for non-superusers
        if not request.user.is_superuser:
            pass
        return form

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "groups" and not request.user.is_superuser:
            # Restrict group selection to groups the user is part of
            kwargs["queryset"] = request.user.groups.all()
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class CustomGroupAdmin(GroupAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        return qs.filter(pk__in=request.user.groups.all().values_list("pk"))

    def get_readonly_fields(self, request, obj=None):
        # If the user is not a superuser, make 'is_superuser' read-only
        if not request.user.is_superuser:
            return self.readonly_fields + ("permissions",)

        return self.readonly_fields


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
