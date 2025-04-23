Steps needed to add the "coder" agent feature to your AgentKit library. This plan assumes you'll be handling the actual coding, but outlines the necessary components and integrations based on the provided AgentKit structure.

**Phase 1: Setup & Configuration**

1.  **Install Dependencies:** Add necessary Python libraries to your environment and potentially update your `pyproject.toml` [cite: 51] or a `requirements.txt` file. You'll likely need:
    * `supabase-py`: For interacting with Supabase.
    * `GitPython`: For cloning or interacting with GitHub repositories.
    * A library for generating embeddings (e.g., `openai` if using their embeddings API, or `sentence-transformers`).
2.  **Environment Variables:** Set up new environment variables (e.g., in your `.env` file [cite: 70, 78]) for:
    * `SUPABASE_URL`: Your Supabase project URL.
    * `SUPABASE_KEY`: Your Supabase service role key (or anon key, depending on your security model).
    * (Optional) `GITHUB_TOKEN`: If needed for accessing private repositories or avoiding rate limits.
3.  **Supabase Setup:**
    * Create a new table in your Supabase project designed to store code chunks and their corresponding vector embeddings. This typically involves columns for content, metadata (file path, repo URL), and the vector itself (using the `vector` type).
    * Ensure you have the `pgvector` extension enabled in Supabase.
    * Create a database function for similarity search if needed.

**Phase 2: Tool Implementation (`agentkit/tools/`)**

Create new Python files within the `agentkit/tools/` directory for the required tools. Each class should inherit from `agentkit.tool.Tool`[cite: 25].

1.  **`GitHubFetcherTool` (`agentkit/tools/github_fetcher.py`):**
    * `__init__`: Initialize with a name (e.g., "GitHubFetcher").
    * `run(self, repo_url: str) -> dict`:
        * Takes a GitHub repository URL as input.
        * Uses `GitPython` to clone the repository to a temporary location.
        * Reads the content of relevant code files (e.g., `.py`, `.js`, `.md` - you might need configuration for this).
        * Returns a dictionary mapping file paths to their content (or just a list of contents/files).
        * Include error handling for invalid URLs or cloning issues.
2.  **`CodeVectorStoreTool` (`agentkit/tools/code_vector_store.py`):**
    * `__init__`: Initialize with name (e.g., "CodeVectorStore"), Supabase client, and an embedding model/client. Load Supabase URL/Key from environment variables here.
    * `run(self, code_data: dict) -> str`:
        * Takes the code data (output from `GitHubFetcherTool`) as input.
        * Implement logic to chunk the code from files into manageable pieces suitable for embedding.
        * For each chunk:
            * Generate a vector embedding using your chosen embedding model (e.g., calling OpenAI's API via the existing `agentkit/models.py` structure [cite: 21, 81] if adapted, or directly using another library).
            * Store the chunk's text, its vector, and relevant metadata (file path, repo URL) in your Supabase table using the `supabase-py` client.
        * Return a status message (e.g., "Successfully processed and stored code from X files").
        * Handle potential errors during embedding or database insertion.
3.  **`CodeQueryTool` (`agentkit/tools/code_query.py`):**
    * `__init__`: Initialize with name (e.g., "CodeQuery"), Supabase client, and embedding model/client.
    * `run(self, user_query: str) -> str`:
        * Takes the user's natural language question about the codebase as input.
        * Generate an embedding for the user's query using the same embedding model used for storing.
        * Use the `supabase-py` client to perform a vector similarity search in your Supabase table against the query vector.
        * Retrieve the top N most relevant code chunks.
        * Format the retrieved code chunks (e.g., including file path) into a string suitable for context stuffing into an LLM prompt.
        * Return the formatted string of relevant code snippets. Handle cases where no relevant results are found.

**Phase 3: Agent Definition & Integration**

1.  **Register Tools:** Import and add your new tools to the list in `agentkit/tools/__init__.py`[cite: 1].
2.  **Define `CoderAgent`:**
    * You can either create a new script in `examples/` or integrate it into `app.py`.
    * Instantiate `agentkit.agent.Agent`[cite: 12, 64]:
        * `name="CoderAgent"`
        * `model="gpt-4o"` (or another suitable model)
        * `behavior`: A detailed prompt instructing the agent to act as a coding assistant, explaining that it should use the retrieved code context (provided by `CodeQueryTool`) to answer user questions about the specified codebase.
        * `tools`: Include an instance of `CodeQueryTool`. The `GitHubFetcherTool` and `CodeVectorStoreTool` might be called separately as part of an initial "indexing" step rather than during every query.
3.  **Workflow Integration (`agentkit/workflow.py` or `app.py`):**
    * **Indexing Flow:** Decide how the code fetching and vectorization/storage process is triggered. It could be:
        * A separate button/function in `app.py` that takes a GitHub URL and runs `GitHubFetcherTool` followed by `CodeVectorStoreTool`.
        * Potentially integrated into the `PlannerAgent` if you want the LLM to decide when to index a repo based on the user's goal (more complex).
    * **Querying Flow:** When the user asks a question:
        * The `CoderAgent` receives the question.
        * The agent (or the `tool_router` [cite: 23, 24]) determines the `CodeQueryTool` should run.
        * `CodeQueryTool` runs, retrieves context from Supabase.
        * The retrieved context is added to the prompt sent to the `CoderAgent`'s LLM.
        * The `CoderAgent` generates the answer based on the user's question and the retrieved code context.

**Phase 4: Testing & Refinement**

1.  **Unit Tests:** Create tests (similar to those in the `tests/` directory) for each new tool to ensure they handle inputs and errors correctly. Mock external dependencies (Git, Supabase API, Embedding API).
2.  **Integration Tests:** Test the end-to-end flow: indexing a small repo, asking questions, and verifying the answers are relevant and use the retrieved context.
3.  **Example Script:** Create a script in `examples/` demonstrating how to use the `CoderAgent` (similar to `examples/hackerbot.py` or `gpt4o_buzz.py` [cite: 32, 33]).

**(Optional) Phase 5: UI Integration (`app.py`)**

1.  Add UI elements to `app.py` to:
    * Input a GitHub repository URL for indexing.
    * Trigger the indexing process (running `GitHubFetcherTool` and `CodeVectorStoreTool`).
    * Provide feedback on the indexing status.
    * Allow users to select the "CoderAgent" or a dedicated "Ask the Codebase" mode.
    * Input questions for the `CoderAgent` and display the results.

This plan provides a detailed roadmap. Remember to handle API keys and sensitive data securely using environment variables.