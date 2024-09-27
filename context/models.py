from django.db import models
from django.utils import timezone

# Create your models here.


class Collection(models.Model):
    slug = models.SlugField(unique=True, primary_key=True)
    language = models.CharField(max_length=100)
    name = models.CharField(max_length=100, blank=True)

    group = models.ForeignKey("auth.Group", models.CASCADE)

    use_openai = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.slug


def get_upload_name(obj: "File", name: str):
    return f"{obj.collection.slug}/{name}"


class File(models.Model):
    content = models.FileField(upload_to=get_upload_name)
    collection = models.ForeignKey(Collection, models.CASCADE)


class Document(models.Model):
    content = models.TextField(blank=True)
    title = models.TextField(blank=True)

    number = models.IntegerField()

    is_indexed = models.BooleanField(default=False)
    indexed_at = models.DateTimeField(blank=True, null=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    collection = models.ForeignKey(Collection, models.CASCADE)

    page = models.ForeignKey("crawler.Page", models.CASCADE, blank=True, null=True)
    content_hash = models.CharField(max_length=60, blank=True)

    file = models.ForeignKey(File, models.CASCADE, blank=True, null=True)

    stale = models.BooleanField(default=False)

    def __str__(self) -> str:
        return super().__str__()


class DocumentMeta(models.Model):
    date = models.DateTimeField(default=timezone.now)
