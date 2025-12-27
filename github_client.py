"""
GitHub Client
=============
Fetches repository data from GitHub API.
"""

import re
import base64
from typing import Optional
from dataclasses import dataclass
import httpx


@dataclass
class RepoInfo:
    """Repository information."""
    owner: str
    name: str
    full_name: str
    description: str
    default_branch: str
    stars: int
    language: str


class GitHubClient:
    """Async client for GitHub API operations."""
    
    BASE_URL = "https://api.github.com"
    
    ANALYZABLE_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".json", ".yaml", ".yml", ".toml",
        ".md", ".txt"
    }
    
    SKIP_PATTERNS = {
        "node_modules", "__pycache__", ".git", 
        "dist", "build", ".next", "venv", ".venv",
        "package-lock.json", "yarn.lock", "uv.lock",
        ".pyc", ".pyo", ".egg-info"
    }
    
    MAX_FILE_SIZE = 100 * 1024  # 100KB
    
    def __init__(self, token: Optional[str] = None):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentLens/1.0"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    @staticmethod
    def parse_repo_url(url: str) -> tuple[str, str]:
        """Parse GitHub URL to extract owner and repo name."""
        patterns = [
            r"github\.com[/:]([^/]+)/([^/.]+?)(?:\.git)?/?$",
            r"github\.com[/:]([^/]+)/([^/.]+?)/?$",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url.strip())
            if match:
                return match.group(1), match.group(2)
        
        raise ValueError(f"Invalid GitHub repository URL: {url}")
    
    async def validate_repo(self, owner: str, repo: str) -> RepoInfo:
        """Validate repository exists and is accessible."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}",
                headers=self.headers,
                timeout=30.0
            )
            
            if response.status_code == 404:
                raise ValueError(f"Repository {owner}/{repo} not found or not public")
            elif response.status_code == 403:
                raise ValueError("GitHub API rate limit exceeded")
            elif response.status_code != 200:
                raise ValueError(f"GitHub API error: {response.status_code}")
            
            data = response.json()
            
            return RepoInfo(
                owner=owner,
                name=repo,
                full_name=data.get("full_name", f"{owner}/{repo}"),
                description=data.get("description", "") or "",
                default_branch=data.get("default_branch", "main"),
                stars=data.get("stargazers_count", 0),
                language=data.get("language", "Unknown") or "Unknown"
            )
    
    async def get_file_tree(self, owner: str, repo: str, branch: str = "main") -> list[dict]:
        """Get file tree using Git Trees API (faster)."""
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            response = await client.get(url, headers=self.headers, timeout=30.0)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            items = data.get("tree", [])
            
            result = []
            for item in items:
                path = item.get("path", "")
                
                if any(skip in path for skip in self.SKIP_PATTERNS):
                    continue
                
                if item.get("type") == "blob":
                    result.append({
                        "path": path,
                        "type": "file",
                        "size": item.get("size", 0),
                        "sha": item.get("sha", "")
                    })
            
            return result
    
    async def get_file_content(self, owner: str, repo: str, path: str, branch: str = "main") -> Optional[str]:
        """Get content of a specific file."""
        if not any(path.endswith(ext) for ext in self.ANALYZABLE_EXTENSIONS):
            if "readme" not in path.lower():
                return None
        
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
            params = {"ref": branch}
            
            response = await client.get(url, headers=self.headers, params=params, timeout=30.0)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if data.get("size", 0) > self.MAX_FILE_SIZE:
                return None
            
            if data.get("encoding") == "base64":
                try:
                    return base64.b64decode(data["content"]).decode("utf-8")
                except Exception:
                    return None
            
            return data.get("content")
    
    async def fetch_repo_contents(self, owner: str, repo: str, branch: str = "main", max_files: int = 40) -> dict[str, str]:
        """Fetch contents of analyzable files."""
        file_tree = await self.get_file_tree(owner, repo, branch)
        
        # Priority sort
        def priority(f):
            path = f["path"].lower()
            if "readme" in path:
                return 0
            if path.endswith(".py") and ("agent" in path or "main" in path or "app" in path):
                return 1
            if path.endswith(".py"):
                return 2
            if any(path.endswith(ext) for ext in [".yaml", ".yml", ".json", ".toml"]):
                return 3
            return 4
        
        file_tree.sort(key=priority)
        file_tree = file_tree[:max_files]
        
        contents = {}
        for file_info in file_tree:
            content = await self.get_file_content(owner, repo, file_info["path"], branch)
            if content:
                contents[file_info["path"]] = content
        
        return contents
