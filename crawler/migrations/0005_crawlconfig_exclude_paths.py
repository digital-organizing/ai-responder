# Generated by Django 4.2.9 on 2024-02-12 12:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("crawler", "0004_page_error"),
    ]

    operations = [
        migrations.AddField(
            model_name="crawlconfig",
            name="exclude_paths",
            field=models.TextField(blank=True),
        ),
    ]
