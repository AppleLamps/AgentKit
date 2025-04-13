# agentkit/tools/hackernews.py

import requests
from agentkit.tool import Tool


class HackerNewsTool(Tool):
    def __init__(self, name: str = "HackerNews"):
        super().__init__(name)

    def run(self, input_text: str) -> str:
        """
        Ignores input_text for now — just fetches top stories from Hacker News API.
        In the future, we can parse intent and filter based on topic.
        """
        try:
            top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[:5]
            stories = []

            for story_id in top_ids:
                story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json").json()
                if story:
                    title = story.get("title", "No title")
                    url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                    stories.append(f"- {title}\n  {url}")

            return "Top Hacker News Stories:\n" + "\n".join(stories)

        except Exception as e:
            return f"Failed to fetch Hacker News stories: {str(e)}"