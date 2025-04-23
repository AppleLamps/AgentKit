import os
from typing import Dict, List, Tuple, Optional
import json
import time
import random
import hashlib
from datetime import datetime
from supabase import create_client
from google import genai
from google.genai import types
from ..tool import Tool

class CodeVectorStoreTool(Tool):
    """Tool for storing code chunks in Supabase with vector embeddings."""
    
    def __init__(self, name: str = "CodeVectorStore"):
        super().__init__(name)
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.supabase = create_client(supabase_url, supabase_key)
        # Initialize Gemini API
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY must be set in environment variables")
        self.client = genai.Client(api_key=google_api_key)
        
        # Check if tables exist
        self._ensure_tables_exist()
        
    def _chunk_code(self, content: str, max_chunk_size: int = 1000) -> List[str]:
        """Split code into smaller chunks while preserving context."""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            if current_size + line_size > max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(line)
            current_size += line_size
            
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return chunks
        
    def _ensure_tables_exist(self):
        """Check if the required tables exist.
        
        Note: The tables should be created directly in Supabase SQL editor
        since the API key might not have permissions to create tables.
        """
        # Skip table creation - it should be created manually in Supabase
        pass
        
    def get_repo_metadata(self, repo_url: str) -> Optional[Dict]:
        """Get repository metadata from Supabase.
        
        Args:
            repo_url (str): URL of the GitHub repository
            
        Returns:
            Optional[Dict]: Repository metadata or None if not found
        """
        try:
            result = self.supabase.table('repo_metadata').select('*').eq('repo_url', repo_url).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error getting repository metadata: {str(e)}")
            return None
            
    def save_repo_metadata(self, repo_url: str, repo_name: str, file_hashes: Dict[str, str], file_count: int) -> bool:
        """Save repository metadata to Supabase.
        
        Args:
            repo_url (str): URL of the GitHub repository
            repo_name (str): Name of the repository
            file_hashes (Dict[str, str]): Dictionary mapping file paths to their MD5 hashes
            file_count (int): Number of files in the repository
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Call the upsert function
            self.supabase.rpc(
                'upsert_repo_metadata',
                {
                    'p_repo_url': repo_url,
                    'p_repo_name': repo_name,
                    'p_file_count': file_count,
                    'p_file_hashes': json.dumps(file_hashes)
                }
            ).execute()
            return True
        except Exception as e:
            print(f"Error saving repository metadata: {str(e)}")
            return False
            
    def calculate_file_hashes(self, code_files: Dict[str, str]) -> Dict[str, str]:
        """Calculate MD5 hashes for all files in the repository.
        
        Args:
            code_files (Dict[str, str]): Dictionary mapping file paths to their contents
            
        Returns:
            Dict[str, str]: Dictionary mapping file paths to their MD5 hashes
        """
        file_hashes = {}
        for file_path, content in code_files.items():
            file_hash = hashlib.md5(content.encode()).hexdigest()
            file_hashes[file_path] = file_hash
        return file_hashes
        
    def detect_file_changes(self, code_files: Dict[str, str], stored_hashes: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str], List[str]]:
        """Detect changes between the current files and stored hashes.
        
        Args:
            code_files (Dict[str, str]): Dictionary mapping file paths to their contents
            stored_hashes (Dict[str, str]): Dictionary mapping file paths to their stored MD5 hashes
            
        Returns:
            Tuple containing:
            - Dict[str, str]: New files (path -> content)
            - Dict[str, str]: Modified files (path -> content)
            - Dict[str, str]: Unchanged files (path -> content)
            - List[str]: Deleted file paths
        """
        # Calculate current file hashes
        current_hashes = self.calculate_file_hashes(code_files)
        
        # Find new, modified, and unchanged files
        new_files = {}
        modified_files = {}
        unchanged_files = {}
        
        for file_path, content in code_files.items():
            if file_path not in stored_hashes:
                new_files[file_path] = content
            elif current_hashes[file_path] != stored_hashes[file_path]:
                modified_files[file_path] = content
            else:
                unchanged_files[file_path] = content
        
        # Files that were deleted
        deleted_files = list(set(stored_hashes.keys()) - set(current_hashes.keys()))
        
        return new_files, modified_files, unchanged_files, deleted_files
        
    def _generate_embedding(self, text: str, max_retries=5) -> List[float]:
        """Generate embedding for a piece of text using Google's text-embedding-004 model.
        
        Includes retry logic for handling rate limit errors.
        """
        retry_count = 0
        backoff_time = 1  # Start with 1 second backoff
        
        while retry_count < max_retries:
            try:
                result = self.client.models.embed_content(
                    model="models/text-embedding-004",
                    contents=text,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                # Convert embeddings to list for JSON serialization
                embedding_values = result.embeddings[0].values
                return [float(x) for x in embedding_values]
            
            except Exception as e:
                error_str = str(e)
                if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise  # Re-raise the exception if we've exceeded retries
                    
                    # Add jitter to avoid thundering herd problem
                    jitter = random.uniform(0.5, 1.5)
                    sleep_time = backoff_time * jitter
                    print(f"Rate limit hit, backing off for {sleep_time:.2f} seconds (retry {retry_count}/{max_retries})")
                    time.sleep(sleep_time)
                    
                    # Exponential backoff
                    backoff_time *= 2
                else:
                    # If it's not a rate limit error, re-raise immediately
                    raise
        
    def run(self, code_files: Dict[str, str], repo_url: str = None, repo_name: str = None) -> str:
        """
        Process and store code files with their embeddings in Supabase.
        
        Args:
            code_files (Dict[str, str]): Dictionary mapping file paths to their contents
            repo_url (str, optional): URL of the GitHub repository
            repo_name (str, optional): Name of the repository
            
        Returns:
            str: Status message indicating number of chunks processed
        """
        try:
            total_chunks = 0
            # More conservative rate limiting parameters
            requests_per_minute = 60  # Much lower than the 150 limit for safety
            delay_between_requests = 60.0 / requests_per_minute  # in seconds
            
            for file_path, content in code_files.items():
                print(f"Processing file: {file_path}")
                # Split code into chunks
                chunks = self._chunk_code(content)
                print(f"File split into {len(chunks)} chunks")
                
                for chunk_index, chunk in enumerate(chunks):
                    # Add delay for rate limiting
                    if chunk_index > 0:
                        # Add some jitter to the delay to avoid synchronized requests
                        jitter = random.uniform(0.8, 1.2)
                        actual_delay = delay_between_requests * jitter
                        time.sleep(actual_delay)
                    
                    print(f"Processing chunk {chunk_index+1}/{len(chunks)} for {file_path}")
                    # Generate embedding with retry logic
                    embedding = self._generate_embedding(chunk)
                    
                    # Prepare metadata
                    metadata = {
                        'file_path': file_path,
                        'chunk_index': chunk_index,
                        'total_chunks': len(chunks),
                        'repo_url': repo_url
                    }
                    
                    # Store in Supabase
                    self.supabase.table('code_chunks').insert({
                        'content': chunk,
                        'embedding': embedding,
                        'metadata': metadata
                    }).execute()
                    
                    total_chunks += 1
                    print(f"Successfully stored chunk {chunk_index+1}/{len(chunks)} for {file_path}")
            
            # Save repository metadata if URL and name are provided
            if repo_url and repo_name:
                file_hashes = self.calculate_file_hashes(code_files)
                self.save_repo_metadata(repo_url, repo_name, file_hashes, len(code_files))
            
            return f"Successfully processed and stored {total_chunks} code chunks from {len(code_files)} files"
            
        except Exception as e:
            error_msg = f"Error storing code chunks: {str(e)}"
            raise Exception(error_msg)
