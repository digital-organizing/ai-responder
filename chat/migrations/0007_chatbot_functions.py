# Generated by Django 5.0.6 on 2024-07-09 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_chatbot_base_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatbot',
            name='functions',
            field=models.JSONField(blank=True, default={}),
            preserve_default=False,
        ),
    ]
