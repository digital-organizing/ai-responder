# Generated by Django 5.0.7 on 2024-07-10 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crawler", "0011_crawlconfig_timeout"),
    ]

    operations = [
        migrations.AddField(
            model_name="crawlconfig",
            name="stale",
            field=models.BooleanField(default=False),
        ),
    ]
