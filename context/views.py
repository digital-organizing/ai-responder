# Create your views here.
from bs4 import BeautifulSoup
from tika import parser
from hashlib import sha1

from django.urls import reverse
from context.embeddings import (
    delete_documents,
    insert_document,
    update_document as update_document_qd,
    update_documents,
)
from context.models import Document, File, Collection
from django.http import JsonResponse
from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.core.exceptions import PermissionDenied


from context.search import get_documents, search
from context.serializers import DocumentSerializer


def _check_access(slug: str, user: User):
    c = Collection.objects.get(slug=slug)
    if c.group not in user.groups.all():
        raise PermissionDenied()
    return c


def query_context(request):
    q = request.GET.get("question")
    slug = request.GET.get("collection")
    limit = int(request.GET.get("n", 5))
    results = search(slug, q, limit)
    docs = get_documents(results)

    serializer = DocumentSerializer(docs, many=True)

    return JsonResponse(serializer.data, safe=False)


def search_view(request):
    return render(
        request,
        "context/search.html",
        {"groups": request.user.groups.all(), "title": "Suche"},
    )


@login_required
def manage_collection(request, slug):
    collection = _check_access(slug, request.user)

    return render(
        request,
        "context/manage_collection.html",
        {"collection": collection, "title": collection.slug},
    )


@login_required
def list_files(request, slug):
    collection = _check_access(slug, request.user)

    files = File.objects.filter(collection=collection)

    return render(
        request,
        "context/file_list.html",
        {
            "files": files,
            "collection": collection,
            "title": f"Dateien: {collection.slug}",
        },
    )


@login_required
def delete_file(request, slug):
    collection = _check_access(slug, request.user)

    pk = request.POST["pk"]

    f = File.objects.get(pk=pk, collection=collection)

    delete_documents(f.document_set.all())

    f.delete()

    return redirect("context:file-list", slug=slug)


@login_required
def upload_file(request, slug):
    collection = _check_access(slug, request.user)

    f = File.objects.create(
        content=request.FILES["content"],
        collection=collection,
    )

    parsed = parser.from_buffer(f.content.open().read(), xmlContent=True)

    text = parsed["content"]
    doc = BeautifulSoup(text, "lxml")
    if f.content.name.endswith(".pdf"):
        pages = doc.find_all("div", {"class": "page"})
        paragraphs = [p.get_text() for p in pages]
    else:
        paragraphs = [p.get_text() for p in doc.find_all("p")]

    paragraphs = list(filter(lambda x: len(x.strip()) > 100, paragraphs))
    title = request.POST["name"]

    documents = [
        Document(
            content=paragraph,
            title=title,
            number=i,
            collection=collection,
            file=f,
            content_hash=get_hash(paragraph),
        )
        for i, paragraph in enumerate(paragraphs)
    ]

    documents = Document.objects.bulk_create(documents)

    update_documents(f.document_set.all(), collection)

    return redirect("context:file-list", slug=slug)


@login_required
def list_documents(request, slug):
    collection = _check_access(slug, request.user)

    return render(
        request,
        "context/document_list.html",
        {
            "documents": collection.document_set.filter(page__isnull=True),
            "collection": collection,
            "title": f"Dokumente: {collection.slug}",
        },
    )


def get_hash(content):
    sha = sha1()

    sha.update(content.encode())
    return sha.hexdigest()


@login_required
def create_document(request, slug):
    collection = _check_access(slug, request.user)
    content = request.POST["content"]

    hash = get_hash(content)
    doc, created = Document.objects.update_or_create(
        content_hash=hash,
        collection=collection,
        defaults=dict(
            content=content,
            title=request.POST["title"],
            is_indexed=False,
            fetched_at=request.POST["date"],
            number=0,
        ),
    )

    if created:
        insert_document(doc)

    return redirect("context:document-list", slug=slug)


@login_required
def update_document(request, slug, pk):
    collection = _check_access(slug, request.user)
    doc = collection.document_set.get(pk=pk)

    if request.method != "POST":
        return render(
            request,
            "context/update_document.html",
            {"document": doc, "collection": collection, "title": "Dokument bearbeiten"},
        )

    doc.content = request.POST["content"]
    doc.hash = get_hash(doc.content)

    doc.save()

    update_document_qd(doc)

    return redirect("context:document-list", slug=slug)


@login_required
def delete_document(request, slug):
    collection = _check_access(slug, request.user)
    pk = request.POST["pk"]

    delete_documents(collection.document_set.filter(pk=pk))
    collection.document_set.filter(pk=pk).delete()

    return redirect("context:document-list", slug=slug)
