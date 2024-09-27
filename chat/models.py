from uuid import uuid4
import json

from django.db import models

# Create your models here.


class ChatBot(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    description = models.TextField(blank=True)

    system_prompt_template = models.TextField(blank=True)
    user_prompt_template = models.TextField(blank=True)

    model = models.CharField(max_length=200)

    context_provider = models.ForeignKey(
        "context.Collection",
        models.CASCADE,
        blank=True,
        null=True,
    )

    model_max_length = models.IntegerField()
    output_max_length = models.IntegerField()

    is_public = models.BooleanField()

    group = models.ForeignKey("auth.Group", models.CASCADE)

    base_url = models.CharField(blank=True, max_length=200)

    functions = models.JSONField(blank=True)

    def __str__(self):
        return self.name


class Field(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100)

    choices = models.TextField(blank=True)

    bot = models.ForeignKey(ChatBot, models.CASCADE)

    def iter_choices(self):
        return (choice.strip() for choice in self.choices.split("\n"))


class Thread(models.Model):
    bot = models.ForeignKey(ChatBot, models.CASCADE)
    uid = models.UUIDField(primary_key=True, default=uuid4)

    message_set: models.QuerySet["Message"]

    def messages(self):
        return [
            {
                "role": message.role,
                "content": message.content,
                "tools": json.dumps(message.tools),
            }
            for message in self.message_set.all()
        ]


class Message(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    role = models.CharField(max_length=100)
    thread = models.ForeignKey(Thread, models.CASCADE)

    tools = models.JSONField(default=dict)
