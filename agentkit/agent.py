# agentkit/agent.py

from typing import List, Optional, Any, Callable, Generator, Union
from agentkit.tool import Tool
from agentkit.memory import Memory
from agentkit.models import load_model


class Agent:
    def __init__(self, name: str, model: str,
                 tools: Optional[List[Tool]] = None,
                 memory: Optional[Memory] = None,
                 behavior: Optional[str] = None,
                 stream: bool = False):
        """
        :param name: Name of the agent
        :param model: Model name (e.g., 'gpt-4o')
        :param tools: Optional list of tools (e.g., search, calculator)
        :param memory: Optional memory backend
        :param behavior: Optional behavior instruction (system prompt)
        :param stream: If True, returns streaming generator of response tokens
        """
        self.name = name
        self.model = load_model(model, stream=stream)
        self.tools = tools or []
        self.memory = memory
        self.behavior = behavior or "You are a helpful assistant."
        self.stream = stream

    def run(self, prompt: str, context: Optional[Any] = None) -> Union[str, Generator[str, None, None]]:
        """
        Runs the agent with the given user prompt.

        If `stream=True`, returns a generator yielding tokens.
        Otherwise, returns the full string response.
        """
        tool_outputs = self._run_tools(prompt)
        full_prompt = self._build_prompt(prompt, context, tool_outputs)

        if self.stream:
            return self.model(full_prompt)  # Generator
        else:
            response = self.model(full_prompt)
            if self.memory:
                self.memory.save(prompt, response)
            return response

    def _run_tools(self, prompt: str) -> str:
        """
        Runs all attached tools on the prompt and returns concatenated results.
        """
        results = []
        for tool in self.tools:
            try:
                tool_output = tool.run(prompt)
                results.append(f"Tool [{tool.name}] result:\n{tool_output}")
            except Exception as e:
                results.append(f"Tool [{tool.name}] error: {str(e)}")
        return "\n\n".join(results)

    def _build_prompt(self, prompt: str, context: Optional[Any], tool_outputs: Optional[str]) -> str:
        """
        Combines behavior, context, and tool outputs into a full model prompt.
        """
        context_str = f"\nContext:\n{context}" if context else ""
        tool_str = f"\nTools:\n{tool_outputs}" if tool_outputs else ""
        return f"{self.behavior}{context_str}{tool_str}\n\nUser: {prompt}"