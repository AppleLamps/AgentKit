# agentkit/models.py

import os
from dotenv import load_dotenv
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)


def load_model(name: str, stream: bool = False):
    def wrapper(prompt: str):
        return query_openai(prompt, model=name, stream=stream)
    return wrapper


def query_openai(prompt: str, model: str = "gpt-4o", stream: bool = False):
    messages = [{"role": "user", "content": prompt}]

    if stream:
        return stream_openai_response(messages, model)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()


def stream_openai_response(messages, model):
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        stream=True
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
