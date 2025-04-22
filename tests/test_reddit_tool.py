# tests/test_reddit_tool.py

from agentkit.agent import Agent
from agentkit.tool import Tool
from agentkit.tools.reddit import RedditSearchTool


class FakeTool(Tool):
    def __init__(self):
        super().__init__("FakeTool")

    def run(self, input_text: str) -> str:
        return "This is FakeTool. It should not run."


def test_reddit_tool_output_contains_marker():
    """
    Directly test RedditSearchTool to verify static marker is present.
    """
    tool = RedditSearchTool()
    output = tool.run("GPT-4o")
    assert "Reddit Result: Always Present" in output


def test_reddit_tool_trigger(monkeypatch):
    """
    Simulate LLM choosing RedditSearchTool and verify it is triggered
    while FakeTool is skipped.
    """
    monkeypatch.setattr(
        "agentkit.tool_router.query_openai",
        lambda prompt, model="gpt-4o": '["RedditSearch"]'
    )

    agent = Agent(
        name="TestAgent",
        model="gpt-4o",
        tools=[RedditSearchTool(), FakeTool()],
        stream=False
    )

    full_prompt = agent.run("What are people saying about LLMs on Reddit?", return_prompt=True)

    assert "Reddit Result: Always Present" in full_prompt
    assert "This is FakeTool" not in full_prompt
