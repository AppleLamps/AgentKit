# tests/test_tool_routing.py

from agentkit.agent import Agent
from agentkit.tools.hackernews import HackerNewsTool
from agentkit.tool import Tool


class FakeTool(Tool):
    def __init__(self):
        super().__init__("FakeTool")

    def run(self, input_text: str) -> str:
        return "This is FakeTool. It should not run."


def test_hackernews_trigger(monkeypatch):
    """
    Simulate a case where the LLM selects HackerNewsTool.
    Verify that HackerNewsTool runs and FakeTool does not.
    """

    monkeypatch.setattr(
        "agentkit.tool_router.query_openai",
        lambda prompt, model="gpt-4o": '["HackerNews"]'
    )

    agent = Agent(
        name="TestAgent",
        model="gpt-4o",
        tools=[HackerNewsTool(), FakeTool()],
        stream=False
    )

    full_prompt = agent.run("What are the top stories on Hacker News today?", return_prompt=True)

    assert "Test Story: Always Present" in full_prompt
    assert "This is FakeTool" not in full_prompt


def test_no_tool_trigger(monkeypatch):
    """
    Simulate a case where the LLM returns no tools.
    Verify that no tools run, and the model handles it alone.
    """

    monkeypatch.setattr(
        "agentkit.tool_router.query_openai",
        lambda prompt, model="gpt-4o": '[]'
    )

    agent = Agent(
        name="TestAgent",
        model="gpt-4o",
        tools=[HackerNewsTool()],
        stream=False
    )

    full_prompt = agent.run("Write me a poem about frogs.", return_prompt=True)

    assert "Test Story: Always Present" not in full_prompt
