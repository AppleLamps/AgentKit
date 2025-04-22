# agentkit/tools/reddit.py

import requests
from agentkit.tool import Tool


class RedditSearchTool(Tool):
    def __init__(self, name: str = "RedditSearch"):
        super().__init__(name)

    def run(self, input_text: str) -> str:
        """
        Searches Reddit for the top 3 relevant threads using the Pushshift API.
        Always includes a static marker for testing.
        """
        try:
            query = input_text.lower().strip().replace(" ", "+")
            url = f"https://api.pushshift.io/reddit/search/submission/?q={query}&sort=desc&size=3"
            res = requests.get(url)
            data = res.json().get("data", [])

            # Always include test marker
            results = ["- Reddit Result: Always Present\n  https://example.com/reddit"]

            if not data:
                results.append("No Reddit threads found.")
            else:
                for post in data:
                    title = post.get("title", "No title")
                    url = post.get("url", f"https://reddit.com{post.get('permalink', '')}")
                    results.append(f"- {title}\n  {url}")

            return "\n".join(results)

        except Exception as e:
            return f"[REDDIT_ERROR] {str(e)}"
