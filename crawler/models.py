from django.db import models

# Create your models here.


class CrawlConfig(models.Model):
    method = models.CharField(max_length=100)

    start_url = models.CharField(max_length=500)
    allowed_domains = models.TextField(blank=True)

    target_collection = models.ForeignKey("context.Collection", models.CASCADE)

    last_fetched = models.DateTimeField(blank=True, null=True)

    group = models.ForeignKey("auth.Group", models.CASCADE)

    exclude_paths = models.TextField(blank=True)
    include_paths = models.TextField(blank=True)

    arguments = models.TextField(blank=True)

    def excludes(self):
        return [line.strip() for line in self.exclude_paths.split("\n") if line.strip()]

    def has_includes(self):
        return self.include_paths != ""

    def includes(self):
        return [line.strip() for line in self.include_paths.split("\n")]

    def domains(self):
        return [domain.strip() for domain in self.allowed_domains.split()]


class Page(models.Model):
    url = models.CharField(max_length=2000, unique=True)
    domain = models.CharField(max_length=500)

    last_fetched = models.DateTimeField(blank=True, null=True)

    error = models.TextField(blank=True)

    stale = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["url"])]
