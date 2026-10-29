from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0010_alter_chatbot_options_chatbot_context_limit_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatbot',
            name='disable_reasoning_with_tools',
            field=models.BooleanField(default=True, help_text="Send reasoning_effort='none' when tools are used. Newer OpenAI models (GPT-5.4+) reject tools combined with reasoning on /v1/chat/completions."),
        ),
    ]
