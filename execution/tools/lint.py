"""Lint tool implementation."""

import ast
from pathlib import Path
from typing import List, Dict, Any


def lint_tool(paths: List[str]) -> List[Dict[str, Any]]:
    """
    Get linter errors for files.
    
    Args:
        paths: List of file paths
        
    Returns:
        List of lint errors
    """
    errors = []
    
    for path_str in paths:
        file_path = Path(path_str)
        if not file_path.exists() or file_path.suffix != '.py':
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8')
            ast.parse(content)
        except SyntaxError as e:
            errors.append({
                "file": str(file_path),
                "line": e.lineno or 0,
                "column": e.offset or 0,
                "message": e.msg,
                "type": "syntax_error"
            })
        except Exception as e:
            errors.append({
                "file": str(file_path),
                "line": 0,
                "column": 0,
                "message": str(e),
                "type": "error"
            })
    
    return errors





