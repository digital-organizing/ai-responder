# Generated by Django 5.0.7 on 2024-07-10 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('context', '0006_documentmeta_file_document_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='stale',
            field=models.BooleanField(default=False),
        ),
    ]
