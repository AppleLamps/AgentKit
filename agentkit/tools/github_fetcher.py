import os
from typing import Dict, List
from pathlib import Path
import requests
from base64 import b64decode
from ..tool import Tool

class GitHubFetcherTool(Tool):
    """Tool for fetching code from GitHub repositories."""
    
    def __init__(self, name: str = "GitHubFetcher"):
        super().__init__(name)
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"token {self.github_token}"} if self.github_token else {}
        self.allowed_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c',
            '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.swift',
            '.kt', '.scala', '.md', '.rst', '.yaml', '.yml', '.json',
            '.xml', '.html', '.css', '.scss', '.sass', '.less'
        }
    
    def _is_allowed_file(self, file_path: str) -> bool:
        print(f"Debug: Checking file {file_path}")
        """Check if the file should be included based on extension and patterns."""
        path = Path(file_path)
        
        # Skip hidden files and directories
        if any(part.startswith('.') for part in path.parts):
            return False
            
        # Skip common non-source directories
        skip_dirs = {'node_modules', 'venv', 'dist', 'build', '__pycache__'}
        if any(part in skip_dirs for part in path.parts):
            return False
            
        return path.suffix.lower() in self.allowed_extensions
    
    def _read_file_content(self, file_path: str) -> str:
        """Read file content with proper encoding handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Skip binary files or files with unknown encoding
            return ""
    
    def _extract_repo_info(self, repo_url: str) -> tuple:
        """Extract owner and repo name from GitHub URL."""
        path = repo_url.replace("https://github.com/", "").replace(".git", "")
        owner, repo = path.split("/")
        return owner, repo
    
    def _get_repo_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """Get contents of a repository directory using GitHub API."""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get repo contents: {response.text}")

    def _get_file_content(self, url: str) -> str:
        """Get content of a specific file using GitHub API."""
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            # For raw content URLs, the response is already the text content
            return response.text
        else:
            raise Exception(f"Failed to get file content: {response.status_code}")

    def run(self, repo_url: str) -> Dict[str, str]:
        """Fetch code files from a GitHub repository using the GitHub API.

        Args:
            repo_url (str): URL of the GitHub repository

        Returns:
            Dict[str, str]: Dictionary mapping file paths to their contents
        """
        try:
            owner, repo = self._extract_repo_info(repo_url)
            print(f"Debug: Fetching contents for {owner}/{repo}")

            # Get all files recursively
            to_process = [(self._get_repo_contents(owner, repo), "")]
            code_files = {}

            while to_process:
                contents, current_path = to_process.pop(0)
                for item in contents:
                    full_path = os.path.join(current_path, item["name"])

                    if item["type"] == "dir":
                        # Queue directory contents for processing
                        dir_contents = self._get_repo_contents(owner, repo, item["path"])
                        to_process.append((dir_contents, full_path))
                    elif item["type"] == "file" and self._is_allowed_file(full_path):
                        # Get file content if it's an allowed type
                        print(f"Debug: Fetching file {full_path}")
                        try:
                            content = self._get_file_content(item["download_url"])
                            if content:  # Only include non-empty files
                                code_files[full_path] = content
                        except Exception as e:
                            print(f"Debug: Error fetching {full_path}: {str(e)}")
                            continue

            print(f"Debug: Successfully fetched {len(code_files)} files")
            return code_files
            
        except Exception as e:
            error_msg = f"Error fetching repository: {str(e)}"
            raise Exception(error_msg)
