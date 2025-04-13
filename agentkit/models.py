# agentkit/models.py

import openai
import os

# Automatically pull from environment variable or allow override
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def load_model(name: str):
    if name == "gpt-4o":
        return lambda prompt: query_openai(prompt, model="gpt-4o")
    elif name == "gpt-4":
        return lambda prompt: query_openai(prompt, model="gpt-4")
    elif name == "gpt-3.5-turbo":
        return lambda prompt: query_openai(prompt, model="gpt-3.5-turbo")
    else:
        raise ValueError(f"Unknown model: {name}")

def query_openai(prompt: str, model: str = "gpt-4o") -> str:
    if not OPENAI_API_KEY:
        raise EnvironmentError("OPENAI_API_KEY not set in environment.")
    
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message["content"].strip()