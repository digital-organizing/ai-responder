from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from crawler.crawling import crawl_page
from crawler.models import CrawlConfig, Page


@admin.register(CrawlConfig)
class CrawlConfigAdmin(admin.ModelAdmin):
    list_display = ["start_url", "last_fetched"]

    def get_queryset(self, request: Any) -> QuerySet[Any]:
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(group__in=request.user.groups)

    def has_add_permission(self, request: Any) -> bool:
        return request.user.is_superuser


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
