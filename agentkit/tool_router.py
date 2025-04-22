# agentkit/tool_router.py

from typing import List
from agentkit.models import query_openai
import json


def choose_tools(user_prompt: str, tool_names: List[str], model: str = "gpt-4o") -> List[str]:
    """
    Uses an LLM to choose the most relevant tools for a given user prompt.
    Returns a list of tool names to execute.
    """
    instruction = (
        "You are a smart assistant deciding which tools should be used based on the user's request.\n"
        f"Available tools: {tool_names}\n"
        f"User request: \"{user_prompt}\"\n\n"
        "Respond with a JSON list of tool names that best apply, e.g.:\n"
        "[\"HackerNews\"]\n\n"
        "If none are relevant, respond with: []"
    )

    try:
        response = query_openai(prompt=instruction, model=model)
        return json.loads(response)
    except Exception as e:
        print(f"[ToolRouter] Failed to parse LLM response: {e}")
        return []

