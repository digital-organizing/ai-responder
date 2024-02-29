from celery import shared_task

from crawler.crawling import crawl
from crawler.models import CrawlConfig


@shared_task
def run_crawler(pk):
    crawl(CrawlConfig.objects.get(pk=pk))
