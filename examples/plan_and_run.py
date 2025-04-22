# examples/plan_and_run.py

from agentkit.tools.hackernews import HackerNewsTool
from agentkit.tools.reddit import RedditSearchTool
from agentkit.workflow import PlannerAgent, run_plan

# Step 1: Initialize planner
planner = PlannerAgent()

# Step 2: Define tools
tools = [HackerNewsTool(), RedditSearchTool()]
tool_names = [t.name for t in tools]

# Step 3: Provide user goal
goal = "Find out what people are saying about open-source AI tools on Reddit and Hacker News."

# Step 4: Get plan
steps = planner.plan(goal=goal, available_tools=tool_names)
print("Plan:", steps)

# Step 5: Run plan
output = run_plan(steps, tools)
print("\n\nFinal Output:\n")
print(output)
