# Generated by Django 5.0.6 on 2024-09-13 09:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("context", "0007_document_stale"),
    ]

    operations = [
        migrations.AddField(
            model_name="collection",
            name="name",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
