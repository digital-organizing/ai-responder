# Create your views here.
from django.http import JsonResponse
from django.shortcuts import render

from context.search import get_documents, search
from context.serializers import DocumentSerializer


def query_context(request):
    q = request.GET.get("question")
    slug = request.GET.get("collection")
    limit = int(request.GET.get("limit", 5))
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
