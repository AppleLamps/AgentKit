# agentkit/tools/wikipedia.py

import requests
from agentkit.tool import Tool

class WikipediaSearchTool(Tool):
    def __init__(self, name="WikipediaSearch"):
        super().__init__(name)

    def run(self, input_text: str) -> str:
        try:
            # Step 1: Try direct page lookup
            summary = self._get_summary(input_text)
            if summary:
                return summary

            # Step 2: Fallback to open search
            fallback_title = self._get_fallback_title(input_text)
            if fallback_title and fallback_title.lower() != input_text.lower():
                summary = self._get_summary(fallback_title)
                if summary:
                    return f"(Fallback to '{fallback_title}')\n\n{summary}"

            return f"No Wikipedia summary found for '{input_text}'."

        except Exception as e:
            return f"[WIKIPEDIA ERROR] {str(e)}"

    def _get_summary(self, title: str) -> str:
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "redirects": 1,
            "titles": title
        }
        res = requests.get("https://en.wikipedia.org/w/api.php", params=params).json()
        pages = res.get("query", {}).get("pages", {})
        if not pages:
            return None
        page = next(iter(pages.values()))
        return page.get("extract")

    def _get_fallback_title(self, query: str) -> str:
        params = {
            "action": "opensearch",
            "format": "json",
            "search": query,
            "limit": 1,
            "namespace": 0
        }
        res = requests.get("https://en.wikipedia.org/w/api.php", params=params).json()
        if res and len(res) >= 2 and res[1]:
            return res[1][0]
        return None
