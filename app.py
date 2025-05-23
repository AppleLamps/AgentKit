import streamlit as st
import json
import os
import time
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Any, Optional
from agentkit.workflow import PlannerAgent, run_plan
from agentkit.agent import Agent
from agentkit.tools.hackernews import HackerNewsTool
from agentkit.tools.reddit import RedditSearchTool
from agentkit.tools.google import GoogleSearchTool
from agentkit.tools.github_fetcher import GitHubFetcherTool
from agentkit.tools.code_vector_store import CodeVectorStoreTool
from agentkit.tools.code_query import CodeQueryTool

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agentkit-dashboard")

# Streamlit config
st.set_page_config(
    page_title="AgentKit Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add global CSS
st.markdown("""
<style>
/* Global styling */
.stApp {
    font-family: 'Inter', sans-serif;
}
.container-border {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    background-color: #ffffff;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.section-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: #1E88E5;
}
.info-box {
    background-color: #e3f2fd;
    border-left: 4px solid #1E88E5;
    padding: 10px 15px;
    margin-bottom: 15px;
    border-radius: 0 5px 5px 0;
}
.warning-box {
    background-color: #fff8e1;
    border-left: 4px solid #ffc107;
    padding: 10px 15px;
    margin-bottom: 15px;
    border-radius: 0 5px 5px 0;
}
.step-indicator {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}
.step-number {
    background-color: #1E88E5;
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin-right: 10px;
    font-size: 0.9rem;
}
.step-text {
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# Create tabs for different functionalities
tab1, tab2 = st.tabs(["Planner", "Code Search"])

# Sidebar: Tool selection
st.sidebar.header("Tool Selection")
use_hackernews = st.sidebar.checkbox("Enable HackerNews Tool", value=True)
use_reddit = st.sidebar.checkbox("Enable Reddit Search Tool", value=True)
use_google = st.sidebar.checkbox("Enable Google Search Tool", value=True)

# Planner Tab
with tab1:
    st.title("AgentKit Planner Dashboard")
    st.write("Enter a goal and let AgentKit plan and run tool-based steps to fetch multi-source insights.")
    
    # User input
    with st.container():
        user_goal = st.text_area(
            "Enter your objective:", 
            "Find out what people are saying about GPT-4o on Reddit and Hacker News.",
            height=100
        )
        
        # Move settings from sidebar to an expander in the main area
        with st.expander("Advanced Settings", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                model_choice = st.selectbox(
                    "Select LLM model", 
                    options=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], 
                    index=0
                )
            with col2:
                show_raw_plan = st.checkbox("Show Raw Plan", value=False)
                
            st.info("Selected tools: " + 
                    ("HackerNews, " if use_hackernews else "") + 
                    ("Reddit, " if use_reddit else "") + 
                    ("Google" if use_google else ""),
                    icon="ℹ️")
        
        run_button = st.button("Run Planner + Execute Tools", use_container_width=True)

    # Run pipeline
    if run_button:
        logger.info(f"Starting planner with goal: {user_goal}")
        
        # Initialize tools
        tools = []
        if use_hackernews:
            tools.append(HackerNewsTool())
            logger.info("Added HackerNews tool")
        if use_reddit:
            tools.append(RedditSearchTool())
            logger.info("Added Reddit tool")
        if use_google:
            tools.append(GoogleSearchTool())
            logger.info("Added Google tool")
        
        tool_names = [t.name for t in tools]
        logger.info(f"Using tools: {tool_names}")
        
        # Create a status container for the execution process
        status_container = st.empty()
        
        # Create containers for each output section
        plan_container = st.container()
        with plan_container:
            st.markdown('<div class="container-border">', unsafe_allow_html=True)
            st.subheader("Planned Steps:")
            plan_content = st.empty()
            st.markdown('</div>', unsafe_allow_html=True)
        
        output_container = st.container()
        with output_container:
            st.markdown('<div class="container-border">', unsafe_allow_html=True)
            st.subheader("Final Output")
            output_content = st.empty()
            st.markdown('</div>', unsafe_allow_html=True)
        
        summary_container = st.container()
        with summary_container:
            st.markdown('<div class="container-border">', unsafe_allow_html=True)
            st.subheader("Final Summary")
            summary_content = st.empty()
            st.markdown('</div>', unsafe_allow_html=True)
        
        try:
            # Step 1: Generate plan
            status_container.info("🧠 Generating plan based on your objective...")
            planner = PlannerAgent(model=model_choice)
            
            try:
                raw_plan = planner.plan(user_goal, tool_names)
                logger.info(f"Plan generated with {len(raw_plan) if raw_plan else 0} steps")
                
                if not raw_plan:
                    status_container.error("⚠️ Planner returned no steps. Try rephrasing your request.")
                    st.stop()
            except Exception as plan_error:
                logger.error(f"Plan generation failed: {str(plan_error)}")
                status_container.error(f"⚠️ Failed to generate plan: {str(plan_error)}")
                st.stop()
            
            # Display the plan
            plan_markdown = ""
            if show_raw_plan:
                plan_markdown += f"```json\n{json.dumps(raw_plan, indent=2)}\n```\n\n"
            
            for i, step in enumerate(raw_plan):
                plan_markdown += f"**Step {i+1}:** `{step['tool']}` → *{step['input']}*\n\n"
            
            plan_content.markdown(plan_markdown)
            
            # Step 2: Execute tools
            total_steps = len(raw_plan)
            status_container.info(f"🔧 Executing {total_steps} tool steps...")
            
            try:
                # Create a progress bar
                progress_bar = st.progress(0)
                step_status = st.empty()
                
                # Custom run_plan function to track progress
                def run_plan_with_progress(plan, tools):
                    results = []
                    for i, step in enumerate(plan):
                        step_status.markdown(f"Running step {i+1}/{total_steps}: **{step['tool']}**")
                        progress_bar.progress((i) / total_steps)
                        # Execute the step
                        result = run_plan([step], tools)[0]
                        results.append(result)
                        progress_bar.progress((i + 1) / total_steps)
                    return "\n\n".join(results)
                
                # Run the plan with progress tracking
                final_output = run_plan_with_progress(raw_plan, tools)
                logger.info("Tool execution completed successfully")
                
            except Exception as tool_error:
                logger.error(f"Tool execution failed: {str(tool_error)}")
                status_container.error(f"⚠️ Error during tool execution: {str(tool_error)}")
                st.stop()
            
            # Display the output
            output_content.code(final_output, language="markdown")
            
            # Step 3: Generate summary
            status_container.info("📝 Generating summary of findings...")
            
            try:
                summarizer = Agent(name="Summarizer", model=model_choice)
                summary = summarizer.run(f"Summarize the findings below for a human:\n\n{final_output}")
                logger.info("Summary generated successfully")
            except Exception as summary_error:
                logger.error(f"Summary generation failed: {str(summary_error)}")
                status_container.warning(f"⚠️ Failed to generate summary: {str(summary_error)}")
                summary = "Summary generation failed. Please review the raw output above."
            
            # Display the summary
            summary_content.write(summary)
            
            # Update status to complete
            status_container.success("✅ Process completed successfully!")
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            status_container.error(f"⚠️ Error: {str(e)}")

# Code Search Tab
with tab2:
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {color: #1E88E5; font-size: 2.5rem; font-weight: 600; margin-bottom: 0.5rem;}
    .sub-header {color: #424242; font-size: 1.1rem; margin-bottom: 2rem;}
    .section-header {color: #1E88E5; font-size: 1.3rem; font-weight: 500; margin-top: 1.5rem; margin-bottom: 1rem;}
    .card {background-color: #f9f9f9; border-radius: 10px; padding: 20px; margin-bottom: 20px; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);}
    .highlight {background-color: #f0f7ff; padding: 2px 5px; border-radius: 3px; font-weight: 500;}
    .step-number {background-color: #1E88E5; color: white; padding: 3px 10px; border-radius: 50%; margin-right: 10px; font-weight: bold;}
    .code-block {background-color: #f5f5f5; border-left: 3px solid #1E88E5; padding: 10px; margin: 10px 0; border-radius: 0 5px 5px 0;}
    .file-path {font-family: monospace; color: #555; font-size: 0.9rem;}
    
    /* Chat styling */
    .chat-message {padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; flex-direction: row; align-items: flex-start; gap: 0.75rem;}
    .chat-message.user {background-color: #f0f7ff; border: 1px solid #e3f2fd;}
    .chat-message.assistant {background-color: #f5f5f5; border: 1px solid #eeeeee;}
    .chat-message .avatar {width: 2.5rem; height: 2.5rem; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;}
    .chat-message .avatar.user {background-color: #1E88E5; color: white;}
    .chat-message .avatar.assistant {background-color: #43a047; color: white;}
    .chat-message .message {flex-grow: 1;}
    .thinking {font-style: italic; color: #666;}
    
    /* Improved button styling */
    .example-button {
        transition: all 0.2s ease;
    }
    .example-button:hover {
        background-color: #f0f7ff !important;
        border-color: #1E88E5 !important;
    }
    
    /* Status indicator */
    .status-indicator {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        padding: 8px 12px;
        border-radius: 4px;
        background-color: #f5f5f5;
        border-left: 4px solid #1E88E5;
    }
    .status-indicator.success {
        background-color: #e8f5e9;
        border-left-color: #43a047;
    }
    .status-indicator.warning {
        background-color: #fff8e1;
        border-left-color: #ffc107;
    }
    .status-indicator.error {
        background-color: #ffebee;
        border-left-color: #e53935;
    }
    .status-icon {
        margin-right: 10px;
        font-size: 1.2rem;
    }
    .status-text {
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with improved styling
    st.markdown('<div class="main-header">Code Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Chat with an AI assistant about your codebase</div>', unsafe_allow_html=True)
    
    # Initialize tools for code search
    @st.cache_resource
    def load_code_tools():
        try:
            github_tool = GitHubFetcherTool()
            vector_store_tool = CodeVectorStoreTool()
            query_tool = CodeQueryTool()
            return github_tool, vector_store_tool, query_tool, None
        except Exception as e:
            return None, None, None, str(e)
    
    github_tool, vector_store_tool, query_tool, tool_error = load_code_tools()
    
    if tool_error:
        st.error(f"Error initializing tools: {tool_error}")
        
        # More specific guidance based on the error
        error_msg = str(tool_error).lower()
        if "supabase" in error_msg:
            st.info("⚠️ Supabase connection issue: Check that SUPABASE_URL and SUPABASE_KEY are correctly set in your .env file.")
        elif "google" in error_msg or "embedding" in error_msg:
            st.info("⚠️ Google API issue: Verify that GOOGLE_API_KEY is correctly set in your .env file.")
        elif "github" in error_msg or "token" in error_msg:
            st.info("⚠️ GitHub API issue: Ensure GITHUB_TOKEN is correctly set in your .env file for accessing repositories.")
        else:
            st.info("⚠️ Make sure all required environment variables are set in your .env file: SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY, and GITHUB_TOKEN.")
    else:
        # Initialize session state for chat history and repository info
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'repo_indexed' not in st.session_state:
            st.session_state.repo_indexed = False
            st.session_state.repo_name = ""
            st.session_state.repo_files_count = 0
            st.session_state.repo_url = ""
            st.session_state.file_hashes = {}
            st.session_state.last_indexed = None
        
        # Add confirmation state for clearing index
        if 'confirm_clear' not in st.session_state:
            st.session_state.confirm_clear = False
        
        # Two columns layout - repository setup and chat interface
        col1, col2 = st.columns([1, 3])
        
        # Repository setup column
        with col1:
            st.markdown('<div class="section-header">Repository Setup</div>', unsafe_allow_html=True)
            
            # Input card
            st.markdown('<div class="card">', unsafe_allow_html=True)
            repo_url = st.text_input(
                "GitHub Repository URL", 
                "https://github.com/AppleLamps/POPE",
                help="Enter the full URL of a public GitHub repository"
            )
            
            # Repository info display
            if repo_url and "/" in repo_url:
                try:
                    owner, repo = repo_url.split("/")[-2:]
                    st.markdown(f"<div class='highlight'>Repository: <b>{owner}/{repo}</b></div>", unsafe_allow_html=True)
                except:
                    pass
                
            fetch_button = st.button("🚀 Index Repository", use_container_width=True)
            
            # Show repository status
            if st.session_state.repo_indexed:
                st.success(f"✅ Repository indexed: {st.session_state.repo_name}")
                st.text(f"Files: {st.session_state.repo_files_count}")
                if st.session_state.last_indexed:
                    st.text(f"Last indexed: {st.session_state.last_indexed}")
                
                # Option to clear index with confirmation
                if not st.session_state.confirm_clear:
                    if st.button("Clear Index", use_container_width=True, key="clear_index_button"):
                        st.session_state.confirm_clear = True
                        st.rerun()
                else:
                    st.warning("⚠️ This will remove the index and clear chat history. Are you sure?")
                    col1a, col2a = st.columns(2)
                    with col1a:
                        if st.button("Yes, Clear", use_container_width=True, key="confirm_clear"):
                            st.session_state.repo_indexed = False
                            st.session_state.repo_name = ""
                            st.session_state.repo_files_count = 0
                            st.session_state.repo_url = ""
                            st.session_state.file_hashes = {}
                            st.session_state.last_indexed = None
                            st.session_state.chat_history = []
                            st.session_state.confirm_clear = False
                            logger.info(f"Index cleared for repository: {repo_url}")
                            st.rerun()
                    with col2a:
                        if st.button("Cancel", use_container_width=True, key="cancel_clear"):
                            st.session_state.confirm_clear = False
                            st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Example questions
            if st.session_state.repo_indexed:
                st.markdown('<div class="section-header">Example Questions</div>', unsafe_allow_html=True)
                st.markdown('<div class="card">', unsafe_allow_html=True)
                
                examples = [
                    "Explain the main functionality of this codebase",
                    "How is the data structured?",
                    "What are the key components?",
                    "Show me how to use this code",
                    "What does the initialization process do?",
                    "Are there any security concerns?"
                ]
                
                for example in examples:
                    if st.button(example, key=f"example_{example}", use_container_width=True):
                        st.session_state.chat_history.append({"role": "user", "content": example})
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat interface column
        with col2:
            # Results area for indexing
            if fetch_button:
                with st.spinner("Connecting to GitHub..."):
                    try:
                        # Step indicator
                        st.markdown('<div class="step-number">1</div> <b>Fetching repository files...</b>', unsafe_allow_html=True)
                        
                        # Fetch all files from the repository
                        code_files = github_tool.run(repo_url)
                        
                        # Try to get repository metadata from Supabase
                        repo_metadata = vector_store_tool.get_repo_metadata(repo_url)
                        is_repo_indexed = repo_metadata is not None
                        
                        # Extract repository name from URL
                        try:
                            repo_name = f"{repo_url.split('/')[-2]}/{repo_url.split('/')[-1]}"
                        except:
                            repo_name = repo_url
                        
                        # File list with collapsible section
                        with st.expander(f"✅ Successfully fetched {len(code_files)} files", expanded=False):
                            for file_path in code_files.keys():
                                st.markdown(f"<div class='file-path'>{file_path}</div>", unsafe_allow_html=True)
                        
                        # Detect changes if the repository is already indexed
                        if is_repo_indexed:
                            st.markdown('<div class="step-number">2</div> <b>Checking for changes in repository...</b>', unsafe_allow_html=True)
                            
                            # Get stored file hashes from metadata
                            stored_hashes = json.loads(repo_metadata['file_hashes'])
                            
                            # Detect file changes
                            new_files, modified_files, unchanged_files, deleted_files = vector_store_tool.detect_file_changes(
                                code_files, stored_hashes
                            )
                            
                            # Show summary of changes
                            if len(new_files) == 0 and len(modified_files) == 0 and len(deleted_files) == 0:
                                st.info(f"No changes detected since last indexing ({len(unchanged_files)} files unchanged)")
                                st.success(f"✅ Repository is up to date. Last indexed: {repo_metadata['last_indexed']}")
                                
                                # Update session state
                                st.session_state.repo_indexed = True
                                st.session_state.repo_name = repo_name
                                st.session_state.repo_url = repo_url
                                st.session_state.repo_files_count = len(code_files)
                                st.session_state.last_indexed = repo_metadata['last_indexed']
                                
                                st.rerun()
                            else:
                                st.write(f"Changes detected: {len(new_files)} new, {len(modified_files)} modified, {len(deleted_files)} deleted")
                                
                                # Only process files that have changed
                                files_to_process = {**new_files, **modified_files}
                                
                                # Show changes in expandable sections
                                if new_files:
                                    with st.expander(f"New files ({len(new_files)})", expanded=False):
                                        for file_path in new_files.keys():
                                            st.markdown(f"<div class='file-path'>{file_path}</div>", unsafe_allow_html=True)
                                
                                if modified_files:
                                    with st.expander(f"Modified files ({len(modified_files)})", expanded=False):
                                        for file_path in modified_files.keys():
                                            st.markdown(f"<div class='file-path'>{file_path}</div>", unsafe_allow_html=True)
                                
                                if deleted_files:
                                    with st.expander(f"Deleted files ({len(deleted_files)})", expanded=False):
                                        for file_path in deleted_files:
                                            st.markdown(f"<div class='file-path'>{file_path}</div>", unsafe_allow_html=True)
                        else:
                            # For new repositories, process all files
                            files_to_process = code_files
                            st.info(f"Repository not previously indexed. Processing all {len(code_files)} files.")
                        
                        # Processing steps - Modified for Batching
                        if len(files_to_process) > 0:
                            step_number = 3 if is_repo_indexed else 2
                            st.markdown(f'<div class="step-number">{step_number}</div> <b>Processing and indexing code in batches...</b>', unsafe_allow_html=True)
                            
                            # Progress tracking
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            total_files_to_process = len(files_to_process)
                            files_processed_count = 0
                            batch_size = 10 # Process 10 files per batch
                            
                            # Convert file dictionary to list for easier batching
                            file_items = list(files_to_process.items())
                            
                            logger.info(f"Starting batch processing for {total_files_to_process} files with batch size {batch_size}")
                            
                            overall_success = True
                            error_messages = []

                            for i in range(0, total_files_to_process, batch_size):
                                batch_files_list = file_items[i:min(i + batch_size, total_files_to_process)]
                                batch_files_dict = dict(batch_files_list)
                                current_batch_size = len(batch_files_dict)
                                
                                status_text.text(f"Processing batch {i//batch_size + 1}/{(total_files_to_process + batch_size - 1)//batch_size} ({current_batch_size} files)...")
                                
                                try:
                                    # Store chunks and metadata for the current batch
                                    with st.spinner(f"Generating embeddings and storing batch {i//batch_size + 1}..."):
                                        batch_result = vector_store_tool.run(batch_files_dict, repo_url=repo_url, repo_name=repo_name)
                                        logger.info(f"Batch {i//batch_size + 1} processed. Result: {batch_result}")
                                    
                                    files_processed_count += current_batch_size
                                    progress = files_processed_count / total_files_to_process
                                    progress_bar.progress(progress)
                                    status_text.text(f"Processed {files_processed_count} of {total_files_to_process} files ({int(progress*100)}%)")
                                    
                                    # Add a small delay to respect potential rate limits (e.g., 150 calls/min)
                                    # Adjust sleep time if needed based on typical batch processing time and rate limits
                                    time.sleep(1) 
                                    
                                except Exception as batch_error:
                                    logger.error(f"Error processing batch {i//batch_size + 1}: {str(batch_error)}")
                                    error_messages.append(f"Batch {i//batch_size + 1} failed: {str(batch_error)}")
                                    overall_success = False
                                    # Optionally break or continue processing other batches
                                    # For now, let's continue to process remaining batches
                                    status_text.warning(f"⚠️ Error in batch {i//batch_size + 1}. Continuing...")
                                    time.sleep(2) # Longer sleep after error

                            # Final status message
                            if overall_success:
                                status_text.success("✅ All batches processed successfully!")
                                if is_repo_indexed:
                                    st.success(f"✅ Successfully updated index for {total_files_to_process} files.")
                                else:
                                    st.success(f"✅ Successfully indexed {total_files_to_process} files.")
                            else:
                                status_text.error("❌ Indexing completed with errors.")
                                for err in error_messages:
                                    st.error(err)
                        
                        # Get updated repository metadata
                        repo_metadata = vector_store_tool.get_repo_metadata(repo_url)
                        
                        # Update session state
                        st.session_state.repo_indexed = True
                        st.session_state.repo_url = repo_url
                        st.session_state.repo_name = repo_name
                        st.session_state.repo_files_count = len(code_files)
                        
                        if repo_metadata:
                            st.session_state.last_indexed = repo_metadata['last_indexed']
                        
                        # Add system message to chat history if it's a new repository
                        if not is_repo_indexed:
                            welcome_msg = f"I've indexed your repository '{st.session_state.repo_name}' with {len(code_files)} files. How can I help you understand this codebase?"
                            st.session_state.chat_history.append({"role": "assistant", "content": welcome_msg})
                        else:
                            # Add update message if there were changes
                            if len(files_to_process) > 0:
                                update_msg = f"I've updated the index with the latest changes ({len(files_to_process)} files updated). How can I help you?"
                                st.session_state.chat_history.append({"role": "assistant", "content": update_msg})
                        
                        # Rerun to update UI
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            # Chat interface
            st.markdown('<div class="section-header">Chat with Code Assistant</div>', unsafe_allow_html=True)
            
            # Display chat history
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.chat_history:
                    if message["role"] == "user":
                        st.markdown(f"""
                        <div class="chat-message user">
                            <div class="avatar user">👤</div>
                            <div class="message">{message["content"]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="chat-message assistant">
                            <div class="avatar assistant">🤖</div>
                            <div class="message">{message["content"]}</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Input for new message
            st.markdown('<div class="card">', unsafe_allow_html=True)
            with st.form(key="chat_form", clear_on_submit=True):
                user_input = st.text_area(
                    "Ask about the code",
                    placeholder="Type your question here...",
                    height=100,
                    max_chars=500,
                    key="user_input"
                )
                
                submit_button = st.form_submit_button("Send Message", use_container_width=True)
                
                if submit_button and user_input.strip():
                    # Add user message to chat history
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    
                    # Check if repository is indexed
                    if not st.session_state.repo_indexed:
                        st.session_state.chat_history.append({
                            "role": "assistant", 
                            "content": "Please index a repository first by entering a GitHub URL and clicking 'Index Repository' in the sidebar."
                        })
                        st.rerun()
                    
                    # Rerun to update UI with the new message
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Process the latest user message if it hasn't been responded to
            if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user" and st.session_state.repo_indexed:
                user_question = st.session_state.chat_history[-1]["content"]
                
                # Show thinking indicator
                thinking_placeholder = st.empty()
                thinking_placeholder.markdown('<div class="thinking">Thinking...</div>', unsafe_allow_html=True)
                
                try:
                    # First, search for relevant code using the vector store
                    with st.spinner("Searching codebase..."):
                        code_results = query_tool.run(user_question)
                    
                    # Prepare prompt for the AI
                    if "No relevant code found" in code_results:
                        context = "I couldn't find specific code related to your question."
                    else:
                        context = f"Here are some relevant code snippets I found:\n\n{code_results}"
                    
                    prompt = f"""
                    You are an AI assistant helping a user understand a codebase. 
                    The user's question is: "{user_question}"
                    
                    Based on the following code context, provide a helpful, accurate, and concise response:
                    
                    {context}
                    
                    If the context doesn't contain enough information to answer the question fully, 
                    acknowledge that and provide the best explanation you can based on the available information.
                    Format your response using markdown for code blocks and explanations.
                    """
                    
                    # Generate response using the Agent
                    with st.spinner("Generating response..."):
                        code_assistant = Agent(name="CodeAssistant", model=model_choice)
                        response = code_assistant.run(prompt)
                    
                    # Clear thinking indicator
                    thinking_placeholder.empty()
                    
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                    # Rerun to update UI with the response
                    st.rerun()
                    
                except Exception as e:
                    thinking_placeholder.empty()
                    st.session_state.chat_history.append({"role": "assistant", "content": f"I encountered an error: {str(e)}. Please try again or rephrase your question."})
                    st.rerun()
