# Generated by Django 4.2.9 on 2024-02-12 12:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("crawler", "0005_crawlconfig_exclude_paths"),
    ]

    operations = [
        migrations.AddField(
            model_name="crawlconfig",
            name="arguments",
            field=models.TextField(blank=True),
        ),
    ]
