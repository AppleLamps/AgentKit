# examples/gpt4o_buzz.py

from agentkit.agent import Agent
from agentkit.tools.hackernews import HackerNewsTool
from agentkit.tools.reddit import RedditSearchTool

agent = Agent(
    name="BuzzBot",
    model="gpt-4o",
    tools=[HackerNewsTool(), RedditSearchTool()],
    behavior="You are a cross-platform trend analyst summarizing what's being said across Reddit and Hacker News.",
    stream=False
)

response = agent.run("What's the buzz around GPT-4o on Reddit and Hacker News?")
print(response)
