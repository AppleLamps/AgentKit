import os
from typing import List, Dict, Optional, Any
from supabase import create_client, Client as SupabaseClient
import google.generativeai as genai
from ..tool import Tool

# Default model for synthesis, can be overridden
DEFAULT_SYNTHESIS_MODEL = "gemini-2.5-pro-preview-03-25" 
# Number of initial candidates to fetch for the LLM to synthesize from
DEFAULT_CANDIDATE_COUNT = 15 

class CodeQueryTool(Tool):
    """
    Tool for querying code chunks using natural language, fetching context,
    and synthesizing an answer using an LLM.
    """

    def __init__(self, 
                 name: str = "CodeQuery", 
                 synthesis_model: str = DEFAULT_SYNTHESIS_MODEL,
                 embedding_model: str = "models/text-embedding-004",
                 code_table_name: str = "code_chunks", # Make table name configurable
                 rpc_match_function: str = "match_code_chunks" # Make RPC name configurable
                 ):
        super().__init__(name)
        self.synthesis_model_name = synthesis_model
        self.embedding_model_name = embedding_model
        self.code_table_name = code_table_name
        self.rpc_match_function = rpc_match_function
        
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        self.supabase: SupabaseClient = create_client(supabase_url, supabase_key)

        # Initialize the Generative AI client (used for both embedding and synthesis)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY must be set")
        genai.configure(api_key=google_api_key)
        self.synthesis_model = genai.GenerativeModel(self.synthesis_model_name)
        # Note: Embedding client is used directly via genai.embed_content

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for the query text."""
        try:
            result = genai.embed_content(
                model=self.embedding_model_name,
                content=text,
                task_type="RETRIEVAL_QUERY" 
            )
            # Ensure embedding exists and is valid
            if not result['embedding']:
                 raise ValueError("Failed to generate embedding, received empty result.")
            # Convert embedding tuple to list of floats
            return [float(x) for x in result['embedding']]
        except Exception as e:
            # Log the error for debugging
            print(f"Error generating embedding: {e}") 
            raise ValueError(f"Failed to generate embedding: {e}") from e

    def _fetch_contextual_chunks(self, primary_chunk_data: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Fetch preceding and succeeding chunks for a given primary chunk."""
        metadata = primary_chunk_data.get('metadata', {})
        file_path = metadata.get('file_path')
        chunk_index = metadata.get('chunk_index')

        context_before_content: Optional[str] = None
        context_after_content: Optional[str] = None

        if file_path is None or chunk_index is None:
            # Log warning or handle missing essential metadata
            print(f"Warning: Missing file_path or chunk_index in metadata for chunk: {primary_chunk_data.get('id', 'N/A')}")
            return {'context_before': None, 'context_after': None}

        try:
            # Fetch preceding chunk
            if chunk_index > 0:
                context_before_res = self.supabase.table(self.code_table_name)\
                    .select('content')\
                    .eq('file_path', file_path)\
                    .eq('chunk_index', chunk_index - 1)\
                    .limit(1)\
                    .execute()
                if context_before_res.data:
                    context_before_content = context_before_res.data[0]['content']

            # Fetch succeeding chunk 
            # (No need to check against total_chunks if not strictly necessary, 
            # the query just won't return data if it doesn't exist)
            context_after_res = self.supabase.table(self.code_table_name)\
                .select('content')\
                .eq('file_path', file_path)\
                .eq('chunk_index', chunk_index + 1)\
                .limit(1)\
                .execute()
            if context_after_res.data:
                context_after_content = context_after_res.data[0]['content']

        except Exception as e:
            # Log the error, but don't fail the whole process, just return no context
            print(f"Error fetching context for chunk {chunk_index} in {file_path}: {e}")

        return {
            'context_before': context_before_content,
            'context_after': context_after_content
        }

    def _format_chunks_for_llm(self, detailed_chunks: List[Dict[str, Any]]) -> str:
        """Format the retrieved chunks and their context into a string for the LLM."""
        formatted_texts = []
        for i, item in enumerate(detailed_chunks):
            primary = item['primary']
            content = primary.get('content', '')
            metadata = primary.get('metadata', {})
            similarity = primary.get('similarity', 'N/A') # Similarity from RPC result
            context_before = item.get('context_before')
            context_after = item.get('context_after')

            # --- Build Header ---
            header_parts = [f"Candidate {i+1}: File: {metadata.get('file_path', 'N/A')}"]
            start = metadata.get('start_line')
            end = metadata.get('end_line')
            if start is not None and end is not None:
                 header_parts.append(f"Lines: {start}-{end}")
            if metadata.get('parent_function'):
                header_parts.append(f"In Function: {metadata['parent_function']}")
            if metadata.get('parent_class'):
                 header_parts.append(f"In Class: {metadata['parent_class']}")
            header_parts.append(f"(Relevance Score: {similarity:.3f})") # Show similarity
            chunk_header = "\n".join(header_parts)

            # --- Format Content ---
            formatted_content = ""
            if context_before:
                formatted_content += f"Context Before:\n```\n{context_before}\n```\n"
            
            formatted_content += f"Matched Chunk:\n```\n{content}\n```"
            
            if context_after:
                 formatted_content += f"\nContext After:\n```\n{context_after}\n```"
            
            formatted_texts.append(f"---\n{chunk_header}\n{formatted_content}\n---")

        return "\n\n".join(formatted_texts)


    def _synthesize_answer_with_llm(self, query: str, formatted_chunks_string: str) -> str:
        """Use an LLM to synthesize an answer based on the query and retrieved context."""
        
        prompt = f"""You are an expert programming assistant. Analyze the following code context retrieved based on the user's query and provide a comprehensive and accurate answer.

User Query:
"{query}"

Retrieved Code Context:
{formatted_chunks_string}

Based *only* on the provided code context and the user query:
1. Summarize how the relevant code snippets address the query.
2. Point out the key functions, classes, or logic involved.
3. If the context provides a direct answer, state it clearly.
4. If the context is insufficient or doesn't directly answer, explain what information is present and what might be missing.
5. Format your answer clearly using markdown where appropriate (e.g., for code mentions). Do not just repeat the code chunks.

Synthesized Answer:
"""
        try:
            response = self.synthesis_model.generate_content(prompt)
            # Consider adding more robust error checking for response.parts, safety ratings etc.
            if not response.text:
                 return "Error: The AI model returned an empty response."
            return response.text
        except Exception as e:
            print(f"Error during LLM synthesis: {e}")
            # Fallback: return the formatted chunks if synthesis fails? Or a specific error message.
            # return f"Error synthesising answer: {e}\n\nRaw Context:\n{formatted_chunks_string}" 
            raise Exception(f"Error during LLM synthesis: {e}") from e


    def run(self, query: str, 
            initial_match_count: int = DEFAULT_CANDIDATE_COUNT, # How many candidates to fetch initially
            match_threshold: float = 0.5 # Minimum similarity for initial candidates
           ) -> str:
        """
        Search for relevant code, fetch context, and synthesize an answer using an LLM.

        Args:
            query (str): Natural language query about the code.
            initial_match_count (int): Number of candidate code chunks to retrieve
                                       before LLM synthesis. More candidates give the
                                       LLM more context but increase processing time.
            match_threshold (float): Minimum similarity threshold (0-1) for chunks
                                     retrieved from vector search.

        Returns:
            str: A synthesized answer from the LLM based on the retrieved code context,
                 or an error message / "No relevant code found" message.
        """
        print(f"Running CodeQueryTool for query: '{query}'") # Log entry
        try:
            # 1. Generate embedding for the query
            query_embedding = self._generate_embedding(query)
            
            # 2. Search for initial candidate chunks using Supabase RPC
            print(f"Searching for {initial_match_count} candidates with threshold {match_threshold}...")
            results = self.supabase.rpc(
                self.rpc_match_function,
                {
                    'query_embedding': query_embedding,
                    'match_threshold': match_threshold,
                    'match_count': initial_match_count 
                }
            ).execute()

            if not results.data:
                print("No relevant code chunks found matching the criteria.")
                return "No relevant code found for your query based on the current criteria."
            
            print(f"Found {len(results.data)} initial candidates. Fetching context...")

            # 3. Fetch contextual chunks (before/after) for each candidate
            detailed_chunks_data = []
            for result_data in results.data:
                # Ensure result_data is a dict, handle potential errors if needed
                if not isinstance(result_data, dict):
                    print(f"Warning: Skipping invalid result data format: {result_data}")
                    continue 
                
                context = self._fetch_contextual_chunks(result_data)
                detailed_chunks_data.append({
                    'primary': result_data,
                    **context # Adds 'context_before' and 'context_after' keys
                })
            
            if not detailed_chunks_data:
                 # This might happen if all initial results had errors during context fetch
                 print("Error: Could not gather detailed context for any candidate.")
                 return "Found initial code matches, but failed to retrieve detailed context."

            # 4. Format the detailed chunks for the LLM prompt
            print("Formatting chunks for LLM synthesis...")
            formatted_context = self._format_chunks_for_llm(detailed_chunks_data)

            # 5. Synthesize the final answer using the LLM
            print(f"Synthesizing answer using {self.synthesis_model_name}...")
            final_answer = self._synthesize_answer_with_llm(query, formatted_context)
            
            print("Synthesis complete.")
            return final_answer
            
        except Exception as e:
            # Log the full error for debugging
            import traceback
            print(f"Error running CodeQueryTool: {e}\n{traceback.format_exc()}") 
            # Return a user-friendly error
            return f"An error occurred while processing your code query: {str(e)}"

# Example Usage (assuming Tool base class and environment variables are set)
# if __name__ == '__main__':
#     try:
#         code_query_tool = CodeQueryTool()
#         user_query = "How is user authentication handled?" 
#         # Or "Find the function that processes CSV uploads"
#         # Or "Where is the database connection string configured?"
#         response = code_query_tool.run(query=user_query)
#         print("\n=== Final Answer ===")
#         print(response)
#     except Exception as e:
#         print(f"Tool initialization or run failed: {e}")