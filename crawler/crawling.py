import time
from contextlib import contextmanager
from hashlib import sha1
from typing import List, Optional, Set
from urllib.parse import ParseResult

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone
from selenium import webdriver
from tika import parser

from context.models import Document
from crawler.models import CrawlConfig, Page
from crawler.url_tools import sanitize_url


def body_text_length(content):
    document = BeautifulSoup(content, "lxml")
    if document.body is None:
        return 0

    text = document.body.get_text()
    return len(text)


def get_next_url(config: CrawlConfig):
    q = Page.objects.filter(domain__in=config.domains()).exclude(
        last_fetched__gte=config.last_fetched
    )
    for url in config.excludes():
        q = q.exclude(url__startswith=url)

    return q.first()


def crawl(config: CrawlConfig):
    print("Starting crawl...")
    config.last_fetched = timezone.now()
    config.save()

    url = sanitize_url(config.start_url)
    Page.objects.update_or_create(
        url=url.geturl(),
        domain=url.netloc,
    )

    if config.method == "selenium":
        _crawl_selenium(config)
    else:
        _crawl_requests(config)


def crawl_page(page: Page):
    domain = sanitize_url(page.url).netloc
    config = CrawlConfig.objects.filter(allowed_domains__contains=domain).first()
    if config is None:
        raise ValueError("No config found for domain: " + domain)
    config.last_fetched = timezone.now()
    config.refresh_from_db()
    if config.method == "selenium":
        crawl_page_selenium(page, config)
    else:
        crawl_page_requests(page, config)


def crawl_page_selenium(page: Page, config: CrawlConfig):
    try:
        title, content = fetch_url(page.url, config, None)
        _create_doc(title, content, page, config)
    except:
        pass


def crawl_page_requests(page: Page, config: CrawlConfig):
    print("Crawling pages")
    with requests.session() as session:
        try:
            title, content = fetch_url_requests(page.url, session)
            print("Fetched: " + title)
            _create_doc(title, content, page, config)
        except:
            print("Fetched: ")
            pass


def _crawl_selenium(config: CrawlConfig):
    page = get_next_url(config)
    with load_driver(config) as driver:
        while page is not None:
            try:
                title, content = fetch_url(page.url, config, driver)
                page = _create_doc(title, content, page, config)
            except Exception as ex:
                page.last_fetched = timezone.now()
                page.error = str(ex)
                page.save()
                page = get_next_url(config)


def _create_doc(title, content, page, config):
    print("Creating docs")
    doc = BeautifulSoup(content, "lxml")

    docs = []

    for paragraph in doc.find_all("p"):
        docs.append(paragraph.get_text())

    for i, d in enumerate(docs):
        if len(d) < 100 or len(d) > 2000:
            continue

        sha = sha1()
        sha.update(d.encode())
        hash = sha.hexdigest()

        Document.objects.update_or_create(
            content_hash=hash,
            collection=config.target_collection,
            defaults={"content": d, "title": title, "page": page, "number": i},
        )

    print("Creating links")
    urls = create_links_for_website(content, config.start_url)

    print("Creating pages")
    print(urls)
    Page.objects.bulk_create(
        [Page(url=url.geturl(), domain=url.netloc) for url in urls],
        ignore_conflicts=True,
    )

    page.last_fetched = timezone.now()
    page.save()

    print("Next page..")
    return get_next_url(config)


def _crawl_requests(config: CrawlConfig):
    page = get_next_url(config)
    with requests.Session() as s:
        while page is not None:
            try:
                title, content = fetch_url_requests(page.url, s)
                print("Fetched:", title)
                page = _create_doc(title, content, page, config)
            except Exception as ex:
                page.last_fetched = timezone.now()
                page.error = str(ex)
                page.save()
                page = get_next_url(config)


def create_links_for_website(content, source_url):
    links = extract_links(content)

    targets: List[ParseResult] = []
    for url in links:
        print(url)
        try:
            parsed = sanitize_url(url, source_url)
            targets.append(parsed)
        except ValueError:
            continue
    return targets


@contextmanager
def load_driver(c: CrawlConfig):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    for argument in c.arguments.split("\n"):
        if argument:
            options.add_argument(argument.strip())

    driver = webdriver.Remote(settings.SELENIUM_URL, options=options)

    try:
        yield driver
    finally:
        driver.quit()


def fetch_url(url: str, c: CrawlConfig, driver: Optional[webdriver.Remote] = None):
    if driver is None:
        with load_driver(c) as driver:
            return fetch_url(url, c, driver)

    driver.get(url)

    time.sleep(0.1)
    content = driver.page_source

    counter = 0
    while body_text_length(content) < 200 and counter < 15:
        time.sleep(0.2)

        content = driver.page_source
        counter += 1

    title = driver.title

    return title, content


def fetch_url_requests(url: str, session: requests.Session):
    print("Fetch")
    response = session.get(url, timeout=10)
    print("Fetched")

    if url.endswith(".pdf"):
        parsed = parser.from_buffer(response.content, xmlContent=True)
        text = parsed["content"]
        doc = BeautifulSoup(text, "lxml")
        pages = doc.find_all("div", {"class": "page"})

        paragraphs = ""
        for page in pages:
            paragraphs += "<p>" + page.get_text().replace("\n\n", "<br/>)") + "</p>"
        title = doc.find("title")
        return title if title else "", "<body>" + paragraphs + "</body>"

    content = response.text
    doc = BeautifulSoup(content, "lxml")
    title = doc.find("title")

    print("Parsed")
    return title.string if title else "", content


def skip_link(link) -> bool:
    extension = link.split(".")[-1]
    if extension.lower() in [
        "zip",
        "tar",
        "gz",
        "iso",
        "7z",
        "jpg",
        "jpeg",
        "png",
        "gif",
    ]:
        return True

    return False


def extract_links(content: str) -> List[str]:
    document = BeautifulSoup(content, "lxml")
    urls: Set[str] = set()

    for url in document.find_all("a", href=True):
        link: str = url.get("href")

        if skip_link(link):
            continue

        if link:
            urls.add(link)

    return list(urls)
