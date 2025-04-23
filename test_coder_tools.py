import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentkit.tools.github_fetcher import GitHubFetcherTool
from agentkit.tools.code_vector_store import CodeVectorStoreTool
from agentkit.tools.code_query import CodeQueryTool
from dotenv import load_dotenv

def test_coder_tools():
    # Load environment variables
    load_dotenv()
    
    # Initialize tools
    github_tool = GitHubFetcherTool()
    vector_store_tool = CodeVectorStoreTool()
    query_tool = CodeQueryTool()
    
    try:
        # Test 1: Fetch repository
        print("🔄 Fetching repository...")
        repo_url = "https://github.com/AppleLamps/POPE"  # Testing with GrokRecipeSnap
        code_files = github_tool.run(repo_url)
        print(f"✅ Successfully fetched {len(code_files)} files")
        
        # Test 2: Store code with embeddings
        print("\n🔄 Storing code chunks...")
        result = vector_store_tool.run(code_files)
        print(f"✅ {result}")
        
        # Test 3: Query the code
        print("\n🔄 Testing code query...")
        test_query = "How does the tool system work?"
        results = query_tool.run(test_query)
        print("\n✅ Query results:")
        print(results)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_coder_tools()
