from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from crawler.crawling import crawl_page
from crawler.models import CrawlConfig, Page
from crawler.tasks import run_crawler


@admin.register(CrawlConfig)
class CrawlConfigAdmin(admin.ModelAdmin):
    list_display = ["start_url", "last_fetched"]

    actions = ["run_crawler_action"]

    @admin.action(description="start crawler")
    def run_crawler_action(self, request, queryset):
        for config in queryset:
            run_crawler.delay(pk=config.pk)

    def get_queryset(self, request: Any) -> QuerySet[Any]:
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(group__in=request.user.groups.all())

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not request.user.is_superuser:
            form.base_fields["target_collection"].queryset = form.base_fields[
                "target_collection"
            ].queryset.filter(group__in=request.user.groups.all())
            form.base_fields["group"].queryset = request.user.groups.all()

        return form


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["url", "last_fetched"]
    list_filter = ["domain"]
    search_fields = ["url"]

    actions = ["crawl_page"]

    def has_change_permission(self, request: HttpRequest, *args, **kwargs) -> bool:
        return False

    @admin.action(description="Crawl page")
    def crawl_page(self, request, queryset):
        for page in queryset:
            crawl_page(page)
