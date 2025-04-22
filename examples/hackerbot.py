# examples/hackerbot.py

from agentkit.agent import Agent
from agentkit.tools.hackernews import HackerNewsTool

agent = Agent(
    name="HackerBot",
    model="gpt-4o",
    behavior="You're a tech researcher using Hacker News to stay informed.",
    tools=[HackerNewsTool()],
    stream=False
)

response = agent.run("Give me a quick tech news roundup")
print(response)