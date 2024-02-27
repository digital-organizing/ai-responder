# Generated by Django 4.2.9 on 2024-01-31 15:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('context', '0001_initial'),
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatbot',
            name='context_provider',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='context.collection'),
        ),
        migrations.AddField(
            model_name='chatbot',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group'),
        ),
    ]
