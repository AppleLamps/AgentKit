import streamlit as st
import json
import os
from agentkit.workflow import PlannerAgent, run_plan
from agentkit.agent import Agent
from agentkit.tools.hackernews import HackerNewsTool
from agentkit.tools.reddit import RedditSearchTool
from agentkit.tools.google import GoogleSearchTool 
from agentkit.tools.wikipedia import WikipediaSearchTool

from dotenv import load_dotenv
load_dotenv()

# Streamlit config
st.set_page_config(page_title="AgentKit Planner", layout="wide")
st.title("AgentKit Planner Dashboard")
st.write("Enter a goal and let AgentKit plan and run tool-based steps to fetch multi-source insights.")

# Sidebar: Tool selection
st.sidebar.header("Tool Selection")
use_hackernews = st.sidebar.checkbox("Enable HackerNews Tool", value=True)
use_reddit = st.sidebar.checkbox("Enable Reddit Search Tool", value=True)
use_google = st.sidebar.checkbox("Enable Google Search Tool", value=True)  # New option
use_wikipedia = st.sidebar.checkbox("Enable Wikipedia Search Tool", value=True)
# Sidebar: Planner settings
st.sidebar.header("Settings")
model_choice = st.sidebar.selectbox("Select LLM model", options=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], index=0)
show_raw_plan = st.sidebar.checkbox("Show Raw Plan", value=False)

# User input
user_goal = st.text_area("Enter your objective:", 
                         "Find out what people are saying about GPT-4o on Reddit and Hacker News.")
run_button = st.button("Run Planner + Execute Tools")

# Run pipeline
if run_button:
    st.subheader("Planned Steps:")
    planner = PlannerAgent(model=model_choice)

    tools = []
    if use_hackernews:
        tools.append(HackerNewsTool())
    if use_reddit:
        tools.append(RedditSearchTool())
    if use_google:
        tools.append(GoogleSearchTool())
    if use_wikipedia:
            tools.append(WikipediaSearchTool())

    tool_names = [t.name for t in tools]

    try:
        with st.spinner("Generating plan..."):
            raw_plan = planner.plan(user_goal, tool_names)

        if not raw_plan:
            st.error("Planner returned no steps. Try rephrasing your request.")
            st.stop()

        if show_raw_plan:
            st.code(json.dumps(raw_plan, indent=2), language="json")

        for i, step in enumerate(raw_plan):
            st.markdown(f"**Step {i+1}:** `{step['tool']}` → *{step['input']}*")

        with st.spinner("Running tools..."):
            final_output = run_plan(raw_plan, tools)

        st.divider()
        st.subheader("Final Output")
        st.code(final_output, language="markdown")

        with st.spinner("Generating summary..."):
            summarizer = Agent(name="Summarizer", model=model_choice)
            summary = summarizer.run(f"Summarize the findings below for a human:\n\n{final_output}")

        st.subheader("Final Summary")
        st.write(summary)

    except Exception as e:
        st.error(f"Error: {str(e)}")
