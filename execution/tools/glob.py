"""Glob tool implementation."""

from pathlib import Path
from typing import List


def glob_tool(pattern: str, base_dir: str = ".") -> List[str]:
    """
    Search files by glob pattern.
    
    Args:
        pattern: Glob pattern
        base_dir: Base directory
        
    Returns:
        List of matching file paths
    """
    base = Path(base_dir)
    matches = list(base.rglob(pattern))
    return [str(m.relative_to(base)) for m in matches if m.is_file()]





