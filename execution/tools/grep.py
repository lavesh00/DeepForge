"""Grep tool implementation."""

import re
from pathlib import Path
from typing import List, Dict


def grep_tool(pattern: str, path: str = ".") -> List[Dict[str, Any]]:
    """
    Search files with regex pattern.
    
    Args:
        pattern: Regex pattern
        path: File or directory path
        
    Returns:
        List of matches
    """
    results = []
    base_path = Path(path)
    
    if base_path.is_file():
        files = [base_path]
    else:
        files = list(base_path.rglob("*"))
        files = [f for f in files if f.is_file()]
    
    try:
        regex = re.compile(pattern)
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8')
                for line_num, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        results.append({
                            "file": str(file_path),
                            "line": line_num,
                            "content": line.strip()
                        })
            except Exception:
                pass
    except re.error:
        return [{"error": f"Invalid regex pattern: {pattern}"}]
    
    return results





