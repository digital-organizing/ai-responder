from django.db import models

# Create your models here.


class Collection(models.Model):
    slug = models.SlugField(unique=True, primary_key=True)
    language = models.CharField(max_length=100)

    group = models.ForeignKey("auth.Group", models.CASCADE)

    use_openai = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.slug


class Document(models.Model):
    content = models.TextField(blank=True)
    title = models.TextField(blank=True)

    number = models.IntegerField()

    is_indexed = models.BooleanField(default=False)
    indexed_at = models.DateTimeField(blank=True, null=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    collection = models.ForeignKey(Collection, models.CASCADE)

    page = models.ForeignKey("crawler.Page", models.CASCADE)
    content_hash = models.CharField(max_length=60, blank=True)

    def __str__(self) -> str:
        return super().__str__()
