# agentkit/workflow.py

from agentkit.agent import Agent
from agentkit.tool import Tool
from typing import List, Dict


class PlannerAgent:
    def __init__(self, model: str = "gpt-4o"):
        self.model = Agent(
            name="Planner",
            model=model,
            behavior=(
                "You are a planning agent. Your job is to read a user goal and return a list of steps "
                "that should be executed to fulfill it. Each step must reference a known tool and an input."
            )
        )

    def plan(self, goal: str, available_tools: List[str]) -> List[Dict[str, str]]:
        prompt = (
            f"You are a planning agent that receives a user goal and selects tools to execute it.\n"
            f"Your task is to return a list of JSON steps, where each step has two fields:\n"
            f"  - tool: one of {available_tools}\n"
            f"  - input: what to feed into the tool\n\n"
            f"Goal: {goal}\n\n"
            f"EXAMPLE OUTPUT:\n"
            f"[{{\"tool\": \"RedditSearch\", \"input\": \"open-source AI\"}}, {{\"tool\": \"HackerNews\", \"input\": \"open-source AI\"}}]\n\n"
            f"ONLY return a valid JSON list of steps — no commentary, no explanation.\n"
        )

        plan_json = self.model.run(prompt)

        try:
            return eval(plan_json)
        except Exception as e:
            print("[Planner Error] Failed to parse plan:", e)
            print("[Raw Response]:", plan_json)
            return []


def run_plan(plan: List[Dict[str, str]], tools: List[Tool]) -> str:
    tool_map = {tool.name: tool for tool in tools}
    results = []

    for step in plan:
        tool_name = step.get("tool")
        input_text = step.get("input", "")
        tool = tool_map.get(tool_name)

        if tool:
            output = tool.run(input_text)
            results.append(f"Step: {tool_name} — Input: {input_text}\n{output}")
        else:
            results.append(f"[ERROR] Unknown tool: {tool_name}")

    return "\n\n".join(results)
