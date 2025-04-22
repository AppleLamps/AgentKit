# agentkit/agent.py

from typing import List, Optional, Any, Callable, Generator, Union
from agentkit.tool import Tool
from agentkit.memory import Memory
from agentkit.models import load_model
from agentkit.tool_router import choose_tools


class Agent:
    def __init__(self, name: str, model: str,
                 tools: Optional[List[Tool]] = None,
                 memory: Optional[Memory] = None,
                 behavior: Optional[str] = None,
                 stream: bool = False):
        self.name = name
        self.model = load_model(model, stream=stream)
        self.tools = tools or []
        self.memory = memory
        self.behavior = behavior or "You are a helpful assistant."
        self.stream = stream

    def run(self, prompt: str, context: Optional[Any] = None, return_prompt: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        Runs the agent with the given user prompt.

        If return_prompt=True, returns the raw prompt sent to the model (for testing/debug).
        If stream=True, returns a generator of streamed response tokens.
        """
        tool_outputs = self._run_tools(prompt)
        full_prompt = self._build_prompt(prompt, context, tool_outputs)

        if return_prompt:
            return full_prompt

        if self.stream:
            return self.model(full_prompt)
        else:
            response = self.model(full_prompt)
            if self.memory:
                self.memory.save(prompt, response)
            return response

    def _run_tools(self, prompt: str) -> str:
        if not self.tools:
            return ""

        tool_names = [tool.name for tool in self.tools]
        selected = choose_tools(prompt, tool_names)

        results = []
        for tool in self.tools:
            if tool.name in selected:
                try:
                    tool_output = tool.run(prompt)
                    results.append(f"Tool [{tool.name}] result:\n{tool_output}")
                except Exception as e:
                    results.append(f"Tool [{tool.name}] error: {str(e)}")

        return "\n\n".join(results)

    def _build_prompt(self, prompt: str, context: Optional[Any], tool_outputs: Optional[str]) -> str:
        context_str = f"\nContext:\n{context}" if context else ""
        tool_str = f"\nTools:\n{tool_outputs}" if tool_outputs else ""
        return f"{self.behavior}{context_str}{tool_str}\n\nUser: {prompt}"
