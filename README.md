# AgentKit

**AgentKit** is a lightweight, modular Python library for building AI agents that are composable, debuggable, and developer-friendly. Inspired by the simplicity of Flask and the power of LangChain—without the bloat.

## Why AgentKit?

LLMs are powerful, but current frameworks for building agents are often:
- Overengineered
- Difficult to debug
- Poorly documented
- Full of “magic” abstraction

**AgentKit** solves this by giving developers explicit control over models, tools, memory, and workflows—with clean syntax, plug-and-play components, and no hidden behavior.
>>>>>>> 0cc24b3d959100e9d2466f3137bce706e7136999

---

# 🧠 AgentKit: Multi-Tool AI Agent Orchestrator

This project is a modular, prompt-to-plan-to-tools-to-summary pipeline built using OpenAI models, SerpAPI, and Streamlit. It enables users to input a goal and receive AI-curated multi-source insights using real tools like Google Search, Reddit, and Hacker News.

> This README is designed to help AI tools or developers deeply understand the logic, components, and extensibility of the app.

---

## ✅ What This App Does

1. Accepts a natural language prompt from the user.
2. Uses a language model (LLM) like GPT-4o to:
   - Analyze the prompt.
   - Generate a list of tools and inputs to execute (as a plan).
3. Executes those tool steps dynamically using real-time APIs.
4. Sends the combined results back to the LLM to produce a human-readable summary.
5. Displays everything clearly via a Streamlit UI.

---

## 🧩 Project Components

### `app.py` (Streamlit frontend)

- Entry point for the app.
- Contains sidebar controls to:
  - Enable/disable tools
  - Select LLM model
  - Show raw plan JSON
- Handles:
  - Goal submission
  - Planning
  - Tool execution
  - Summary generation

---

### `agentkit/agent.py`

- Core wrapper class for interacting with LLMs.
- Handles streaming or non-streaming output.
- Supports optional memory and custom behavior instructions.

---

### `agentkit/workflow.py`

- Contains `PlannerAgent`, which:
  - Accepts a user goal and list of tool names.
  - Uses an LLM to return a structured JSON plan like:

    ```json
    [
      {"tool": "GoogleSearch", "input": "Gemini AI"},
      {"tool": "RedditSearch", "input": "Gemini AI discussions"}
    ]
    ```

- Also contains `run_plan()`, which executes the list of steps and returns combined tool output.

---

### `agentkit/tools/` (Tool Registry)

Each tool inherits from `Tool` and implements a `.run()` method.

#### Available tools:
- `HackerNewsTool`: Pulls top HN stories using Firebase API
- `RedditSearchTool`: Pulls recent Reddit threads using Pushshift API
- `GoogleSearchTool`: Uses SerpAPI to search Google


> Tools return markdown-friendly string outputs and include a static marker (for testing).

---

### `.env`

Contains private API keys (e.g. for SerpAPI):

```env
SERPAPI_API_KEY=your_serpapi_key
```

This is loaded using `python-dotenv`.

---

## 🧠 How the Pipeline Works

1. **Prompt Input**
   - User enters a natural language prompt in the UI (e.g., “What are people saying about GPT-4o?”)

2. **Planner Agent**
   - `PlannerAgent.plan()` sends a system prompt and user goal to GPT-4o.
   - LLM returns a structured JSON array of tool invocations.
   - Tools are selected from the sidebar-enabled options only.

3. **Tool Execution**
   - Each step in the plan is routed to the corresponding `Tool.run()` method.
   - Tool responses are collected into a single string.

4. **Summary Agent**
   - Final output is passed to the LLM again.
   - It generates a structured, readable explanation of what was learned.

5. **Output**
   - Streamlit shows:
     - Planned steps
     - Raw tool output
     - Final LLM summary

---

## 🧪 Example Prompts to Try

- “What are people saying about open-source LLMs?”
- “Find news and discussion about Gemini AI.”
- “How are Reddit and Hacker News reacting to Apple’s AI announcements?”

---

## 🛠️ Tool Extensibility

To add a new tool:
1. Create a new file in `agentkit/tools/mytool.py`
2. Inherit from `Tool` and implement `.run(input_text: str) -> str`
3. Register it in `__init__.py`
4. Add a checkbox in `app.py` to enable it

---

## 🔐 Security & API Keys

- Keys are never hardcoded.
- `.env` is used to store secrets like:
  - `SERPAPI_API_KEY`
- All tools validate for key presence before executing.

---

## 🧠 Summary Agent Behavior

The summarization step uses an LLM to:
- Read the combined markdown output from tools
- Identify major themes and comparisons
- Generate concise insight for the end-user

This closes the loop from prompt → plan → action → synthesis.

---

## 🧩 Technologies Used

- **Streamlit**: UI frontend
- **OpenAI GPT Models**: LLM for planning and summarization
- **Python + Requests**: HTTP APIs for tools
- **SerpAPI**: Google search backend
- **dotenv**: Secure environment variable loading

---

## 📁 File Structure

```
agentkit/
│
├── agent.py           # LLM wrapper class
├── tool.py            # Base class for tools
├── tools/
│   ├── google.py
│   ├── reddit.py
│   ├── hackernews.py
│
├── workflow.py        # PlannerAgent and run_plan()
├── models.py          # Model loading logic
├── memory.py          # (optional) memory support
└── utils.py           # (optional) helpers

app.py                 # Main Streamlit app
.env                   # Secret API keys (not committed)
```

---

## 💬 Suggested Extensions

- Streaming GPT output using `st.empty()`
- Nested planning (multi-layer agent chains)
- Tool retries or refinement
- Auto-plan visualization with Graphviz
- Memory-aware summarization

---
<<<<<<< HEAD
=======

## TL;DR

- Modular: Agents, tools, memory, models—each is a standalone unit.
- Explicit: No hidden flows. What you code is what runs.
- Extensible: Add tools, swap models, plug in memory—all in plain Python.
- Streamable: GPT-4o streaming support built in.
- Composable: One-liner agent chaining is coming.

---

## Quick Start

```python
from agentkit import Agent

agent = Agent(
    name="Writer",
    model="gpt-4o",
    behavior="You are a helpful and concise assistant.",
    stream=True
)

for token in agent.run("Write a tweet about AGI breakthroughs"):
    print(token, end="")



⸻

Components

Component	File	Description
Agent	agent.py	Central class that handles prompt assembly, model calls, tools, memory
Tool	tool.py	Abstract base for any tool (e.g., web search, math)
Memory	memory.py	Tracks past prompts/responses (in-memory for now)
Model Loader	models.py	Supports GPT-4o, GPT-3.5, and streaming via OpenAI
(Coming soon)	workflow.py	Agent chaining and logic graphs
(Planned)	config.py	Load agents/pipelines from JSON or YAML



⸻

What You Can Build Right Now
	•	Single-agent pipelines with OpenAI models
	•	Real-time token streaming from GPT-4o
	•	Tool-augmented agents (base class ready)
	•	Save & replay agent memory
	•	CLI- or app-ready interface
	•	Tool registry + shared context
	•	Multi-agent workflows (Planner → Researcher → Writer)
	•	Drop-in GUI (Streamlit playground)

⸻

Dev Setup

git clone https://github.com/AppleLamps/AgentKit
cd AgentKit
pip install -r requirements.txt

# Set your OpenAI key
export OPENAI_API_KEY=sk-...



⸻

File Tree

agentkit/
├── agentkit/
│   ├── agent.py          # Main agent logic
│   ├── tool.py           # Tool interface
│   ├── memory.py         # Memory backend (in-memory for now)
│   ├── models.py         # GPT-4o model loading + streaming
│   └── config.py         # (Planned) config loading
│
├── examples/             # Sample agents & usage
├── tests/                # Unit tests (WIP)
├── README.md
└── pyproject.toml



⸻

Contributing
	•	Fork, branch, build, PR.
	•	Prefer single-purpose PRs.
	•	Include usage examples in /examples if adding new functionality.

⸻

License

MIT

---

Want this version as a separate `CONTRIBUTING.md` or merged into the bottom half of the full README?
>>>>>>> 0cc24b3d959100e9d2466f3137bce706e7136999
