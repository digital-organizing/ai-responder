import time
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from selenium.webdriver.common.proxy import Proxy as SeleniumProxy, ProxyType

from django.utils.timezone import make_aware, is_aware
from dateutil.parser import parse
from datetime import datetime
import json
import traceback
from contextlib import contextmanager
from hashlib import sha1
from typing import List, Optional, Set
from urllib.parse import ParseResult

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from selenium import webdriver
from tika import parser
import tiktoken

from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer
from io import BytesIO
from docling.backend.html_backend import HTMLDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument

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

    f = Q()

    for include in config.includes():
        f = f | Q(url__startswith=include)

    q = q.filter(f)

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
    proxies = None
    if config.proxy:
        proxies = {"http": config.proxy.url, "https": config.proxy.url}

    with requests.session() as session:
        try:
            title, content = fetch_url_requests(page.url, session)
            print("Fetched: " + title)
            _create_doc(title, content, page, config)
        except Exception as ex:
            traceback.print_exc()
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
                traceback.print_exc()
                page.last_fetched = timezone.now()
                page.error = str(ex)
                page.save()
                page = get_next_url(config)

            time.sleep(config.timeout)


def get_published_date(soup) -> Optional[datetime]:

    print(soup)
    # Check common meta tags for publication date
    meta_tags = [
        {"property": "article:published_time"},
        {"property": "og:published_time"},
        {"name": "DC.date.issued"},
        {"name": "date"},
        {"itemprop": "datePublished"},
    ]

    for tag_attrs in meta_tags:
        tag = soup.find("meta", attrs=tag_attrs)
        if tag and tag.get("content"):
            return parse(tag["content"])

    # Check JSON-LD structured data
    json_ld_script = soup.find("script", type="application/ld+json")
    if json_ld_script:
        try:
            data = json.loads(json_ld_script.string)
            if isinstance(data, dict) and "datePublished" in data:
                return parse(data["datePublished"])
        except (json.JSONDecodeError, KeyError):
            pass

    # If no date is found, return None
    return None

def create_chunks(content: str, chunker: HybridChunker):
    in_doc = InputDocument(
        path_or_stream=BytesIO(content.encode()),
        format=InputFormat.HTML,
        backend=HTMLDocumentBackend,
        filename="duck.html",
    )
    backend = HTMLDocumentBackend(in_doc=in_doc, path_or_stream=BytesIO(content.encode()))
    dl_doc = backend.convert()

    chunks = list(chunker.chunk(dl_doc=dl_doc))
    
    return chunks
    

def _create_doc(title, content, page, config, chunker=None):
    print("Create docs")
    if chunker is None:
        tokenizer = OpenAITokenizer(
            tokenizer=tiktoken.encoding_for_model("gpt-4o"),
            max_tokens=5*1024,
        )
        chunker = HybridChunker(
            tokenizer=tokenizer,
            merge_peers=True
        )
        print("Loaded chunker")
        return _create_doc(title, content, page, config, chunker)
    
    print("Called with chunker")

    docs = create_chunks(content, chunker)
    print(docs)

    page.document_set.all().update(stale=True)

    for i, doc in enumerate(docs):
        sha = sha1()
        d = doc.text
        
        sha.update(d.encode())
        hash = sha.hexdigest()

        doc, created = Document.objects.update_or_create(
            content_hash=hash,
            page=page,
            collection=config.target_collection,
            defaults={
                "content": d,
                "title": title,
                "number": i,
            },
        )

        if created:
            doc.is_indexed = False
            doc.save()

    print("Creating links")
    urls = create_links_for_website(content, config.start_url)

    print("Creating pages")
    print(urls)
    Page.objects.bulk_create(
        [Page(url=url.geturl(), domain=url.netloc) for url in urls],
        ignore_conflicts=True,
    )

    page.last_fetched = timezone.now()
    published_at = None

    if published_at and not is_aware(published_at):
        published_at = make_aware(published_at)
    page.published_at = published_at
    page.save()

    print("Next page..")
    return get_next_url(config)


def _crawl_requests(config: CrawlConfig):
    page = get_next_url(config)
    with requests.Session() as s:
        if config.proxy:
            s.proxies = {"http": config.proxy.url, "https": config.proxy.url}
            s.verify = False
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
            time.sleep(config.timeout)


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

    if c.proxy:
        options.proxy = SeleniumProxy(
            {
                "proxyType": ProxyType.MANUAL,
                "httpProxy": c.proxy.url,
                "sslProxy": c.proxy.url,
            }
        )
        options.accept_insecure_certs = True
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

    if url.endswith(".pdf") or url.endswith(".docx"):
        pipeline_options = PdfPipelineOptions(do_table_structure=False)
        pipeline_options.table_structure_options.mode = TableFormerMode.FAST  # use more accurate TableFormer model
        converter = DocumentConverter(
            format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
        )

        result = converter.convert(url)
        return result.document.name, result.document.export_to_html()

    response = session.get(url, timeout=10)

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
