# Generated by Django 4.2.9 on 2024-02-12 14:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("crawler", "0007_page_crawler_pag_url_243307_idx"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="page",
            name="crawler_pag_url_243307_idx",
        ),
        migrations.AddIndex(
            model_name="page",
            index=models.Index(fields=["url"], name="crawler_pag_url_ef3d4b_idx"),
        ),
    ]
