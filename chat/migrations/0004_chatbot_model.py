# Generated by Django 4.2.9 on 2024-02-12 16:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0003_thread_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatbot",
            name="model",
            field=models.CharField(default="gpt-3.5-turbo", max_length=200),
            preserve_default=False,
        ),
    ]
