# Generated by Django 4.2.10 on 2024-02-29 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crawler", "0008_remove_page_crawler_pag_url_243307_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="crawlconfig",
            name="include_paths",
            field=models.TextField(blank=True),
        ),
    ]
