from typing import List, Optional

import openai
from django.conf import settings

from chat.models import ChatBot, Message, Thread
from context.models import Document

from chat.guards import create_guard


def format_doc(doc: Document):
    if doc.page and doc.page.published_at:
        date = doc.page.published_at.strftime(", (%Y-%m-%d)")
    else:
        date = ""
    return f"[{doc.content}]\n({doc.page.url if doc.page else doc.pk}{date})\n"


def get_system_prompt(question, bot, docs, **kwargs):
    system_prompt = bot.system_prompt_template.format(
        context="\n".join([format_doc(doc) for doc in docs]),
        question=question,
        **kwargs,
    )
    return system_prompt


def get_user_prompt(question, bot, docs, **kwargs):
    user_prompt = bot.user_prompt_template.format(question=question, **kwargs)
    return user_prompt


def get_messages(question, bot, docs, **kwargs):

    guard = create_guard()

    messages = kwargs.pop("messages", [])
    user_prompt = get_user_prompt(question, bot, docs, **kwargs, guard=guard)
    system_prompt = get_system_prompt(question, bot, docs, **kwargs, guard=guard)

    messages = (
        [{"role": "system", "content": system_prompt}]
        + messages[-10:]
        + [{"role": "user", "content": user_prompt}]
    )

    return messages


def get_completion(messages, bot, use_functions=False, **kwargs):
    if bot.base_url:
        client = openai.Client(api_key=settings.INFOMANIAK_KEY, base_url=bot.base_url)
    else:
        client = openai.Client(api_key=settings.OPENAI_KEY)

    if "tool_choice" in kwargs and kwargs["tool_choice"] != "none":
        tools = bot.functions
    else:
        tools = None
        
    messages = [{"role": message["role"], "content": message["content"]} for message in messages]

    completion = client.chat.completions.create(
        messages=messages,
        model=bot.model,
        tools=tools,
        **kwargs,
    )
    return completion


def generate_answer(question: str, bot: ChatBot, docs: List[Document], **kwargs):
    messages = kwargs.pop("messages", [])
    fields = [field.slug for field in bot.field_set.all()]

    for field in fields:
        kwargs[field] = kwargs.get(field, "")

    new_messages = get_messages(question, bot, docs, **kwargs)
    messages += new_messages

    for field in fields:
        kwargs.pop(field, "")

    return get_completion(messages, bot, **kwargs), new_messages


def generate_function_call(
    question: str, bot: ChatBot, docs: List[Document], function: Optional[str], **kwargs
):
    messages = get_messages(question, bot, docs, **kwargs)

    completion = get_completion(messages, bot, use_functions=True, **kwargs)

    return completion, messages


def query_tool():
    return {
        "type": "function",
        "function": {
            "name": "search",
            "description": (
                "Query semantic knowledge base with context for a question"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "search queries",
                    },
                },
                "required": ["query"],
            },
        },
    }


def init_thread(bot: ChatBot, question: str, docs, **kwargs):
    messages = get_messages(bot, question, docs, **kwargs)
    thread = Thread.objects.create(bot=bot)

    thread.message_set.create(
        content=messages[0]["content"],
        role="system",
    )

    thread.message_set.create(content=question, role="user")

    completion = get_completion(messages, bot)
    answer = completion.choices[0].message.content.replace("ß", "ss")

    Message.objects.bulk_create(
        [
            Message(content=messages[0]["content"], role="system", thread=thread),
            Message(content=question, role="user", thread=thread),
            Message(content=answer, role="assistant", thread=thread),
        ]
    )


def threaded_answer(thread: Thread, user_input):
    thread.message_set.create(content=user_input, role="user")
    messages = thread.messages()

    completion = get_completion(messages, thread.bot, tools=[query_tool()])

    # TODO: If tool => Query, append and recall (without tool)
    # else => add message, return to user
