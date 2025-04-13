# agentkit/agent.py

from typing import List, Optional, Any, Callable
from agentkit.tool import Tool
from agentkit.memory import Memory
from agentkit.models import load_model


class Agent:
    def __init__(self, name: str, model: str, tools: Optional[List[Tool]] = None,
                 memory: Optional[Memory] = None, behavior: Optional[str] = None,
                 stream: bool = False):
        self.name = name
        self.model = load_model(model, stream=stream)
        self.tools = tools or []
        self.memory = memory
        self.behavior = behavior or "You are a helpful assistant."
        self.stream = stream

    def run(self, prompt: str, context: Optional[Any] = None) -> str:
        # Run tools first if they apply
        tool_outputs = self._run_tools(prompt)

        # Build full prompt
        full_prompt = self._build_prompt(prompt, context, tool_outputs)
        
        # Query the model
        response = self.model(full_prompt)

        if self.memory:
            self.memory.save(prompt, response)

        return response

    def _run_tools(self, prompt: str) -> str:
        results = []
        for tool in self.tools:
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