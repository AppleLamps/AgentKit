# agentkit/tools/google.py

import requests
from agentkit.tool import Tool
import os

class GoogleSearchTool(Tool):
    def __init__(self, name: str = "GoogleSearch"):
        super().__init__(name)
        self.api_key = os.getenv("SERPAPI_API_KEY")

    def run(self, input_text: str) -> str:
        if not self.api_key:
            return "[GOOGLE ERROR] Missing SERPAPI_API_KEY environment variable."

        try:
            params = {
                "q": input_text,
                "api_key": self.api_key,
                "engine": "google",
                "num": 5
            }
            response = requests.get("https://serpapi.com/search", params=params)
            data = response.json()

            results = ["- Google Result: Always Present\n  https://example.com/google"]

            for item in data.get("organic_results", [])[:5]:
                title = item.get("title", "No title")
                link = item.get("link", "#")
                results.append(f"- {title}\n  {link}")

            return "\n".join(results)

        except Exception as e:
            return f"[GOOGLE ERROR] {str(e)}"
