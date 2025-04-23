import os
from typing import List, Dict
from supabase import create_client
from google import genai
from google.genai import types
from ..tool import Tool

class CodeQueryTool(Tool):
    """Tool for querying code chunks using natural language."""
    
    def __init__(self, name: str = "CodeQuery"):
        super().__init__(name)
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
            
        self.supabase = create_client(supabase_url, supabase_key)
        # Initialize the embedding model (same as CodeVectorStoreTool)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY must be set in environment variables")
        self.client = genai.Client(api_key=google_api_key)
        
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for the query text using Google's text-embedding-004 model."""
        result = self.client.models.embed_content(
            model="models/text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        # Convert embeddings to list for JSON serialization
        embedding_values = result.embeddings[0].values
        return [float(x) for x in embedding_values]
        
    def _format_results(self, results: List[Dict]) -> str:
        """Format the search results into a readable string."""
        if not results:
            return "No relevant code found for your query."
            
        formatted_chunks = []
        for result in results:
            content = result['content']
            metadata = result['metadata']
            similarity = result['similarity']
            
            # Format the chunk with its metadata
            chunk_header = f"\nFile: {metadata['file_path']} (Chunk {metadata['chunk_index'] + 1}/{metadata['total_chunks']}, Relevance: {similarity:.2f})"
            chunk_content = f"```\n{content}\n```"
            formatted_chunks.append(f"{chunk_header}\n{chunk_content}")
            
        return "\n".join(formatted_chunks)
        
    def run(self, query: str, match_count: int = 5, match_threshold: float = 0.5) -> str:
        """
        Search for relevant code chunks based on a natural language query.
        
        Args:
            query (str): Natural language query about the code
            match_count (int): Number of matches to return
            match_threshold (float): Minimum similarity threshold (0-1)
            
        Returns:
            str: Formatted string containing relevant code chunks
        """
        try:
            # Generate embedding for the query
            query_embedding = self._generate_embedding(query)
            
            # Search for similar code chunks
            results = self.supabase.rpc(
                'match_code_chunks',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': match_threshold,
                    'match_count': match_count
                }
            ).execute()
            
            # Format and return results
            return self._format_results(results.data)
            
        except Exception as e:
            error_msg = f"Error querying code chunks: {str(e)}"
            raise Exception(error_msg)
