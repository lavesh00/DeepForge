"""Git version control adapter."""

import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class GitStatus:
    """Git repository status."""
    branch: str
    clean: bool
    modified: List[str]
    staged: List[str]
    untracked: List[str]


class GitAdapter:
    """Adapter for Git operations."""
    
    def __init__(self, repo_path: Path):
        """Initialize Git adapter."""
        self.repo_path = repo_path
        self._git_available = None
    
    def is_available(self) -> bool:
        """Check if Git is available."""
        if self._git_available is not None:
            return self._git_available
        
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                timeout=5
            )
            self._git_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._git_available = False
        
        return self._git_available
    
    def init(self) -> bool:
        """Initialize a new Git repository."""
        if not self.is_available():
            return False
        
        try:
            subprocess.run(
                ["git", "init"],
                cwd=str(self.repo_path),
                capture_output=True,
                check=True
            )
            
            gitignore = self.repo_path / ".gitignore"
            if not gitignore.exists():
                gitignore.write_text(
                    "__pycache__/\n"
                    "*.pyc\n"
                    ".env\n"
                    "venv/\n"
                    "node_modules/\n"
                    ".deepforge/\n"
                )
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def add(self, files: List[str] = None) -> bool:
        """Stage files for commit."""
        if not self.is_available():
            return False
        
        try:
            if files:
                cmd = ["git", "add"] + files
            else:
                cmd = ["git", "add", "."]
            
            subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def commit(self, message: str) -> bool:
        """Create a commit."""
        if not self.is_available():
            return False
        
        self.add()
        
        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(self.repo_path),
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def status(self) -> Optional[GitStatus]:
        """Get repository status."""
        if not self.is_available():
            return None
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "-b"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stdout.strip().split('\n')
            branch = lines[0].replace("## ", "").split("...")[0] if lines else "main"
            
            modified = []
            staged = []
            untracked = []
            
            for line in lines[1:]:
                if not line:
                    continue
                status = line[:2]
                filename = line[3:]
                
                if status[0] in "MADRC":
                    staged.append(filename)
                if status[1] in "MDRC":
                    modified.append(filename)
                if status == "??":
                    untracked.append(filename)
            
            return GitStatus(
                branch=branch,
                clean=len(modified) == 0 and len(staged) == 0 and len(untracked) == 0,
                modified=modified,
                staged=staged,
                untracked=untracked
            )
        except subprocess.CalledProcessError:
            return None
    
    def get_log(self, count: int = 10) -> List[dict]:
        """Get commit log."""
        if not self.is_available():
            return []
        
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--pretty=format:%H|%s|%an|%ad", "--date=short"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3]
                        })
            
            return commits
        except subprocess.CalledProcessError:
            return []




