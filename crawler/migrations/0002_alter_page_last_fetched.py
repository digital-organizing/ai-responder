# Generated by Django 4.2.9 on 2024-01-31 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='last_fetched',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
