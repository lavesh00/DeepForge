"""Auto-refactor engine for bug fixes and optimizations."""

import ast
import traceback
from typing import Dict, Any, Optional
from pathlib import Path
from cognition.chat.chat_engine import ChatEngine


class RefactorEngine:
    """Handles automatic refactoring based on errors or user requests."""
    
    def __init__(self, chat_engine: ChatEngine):
        """
        Initialize refactor engine.
        
        Args:
            chat_engine: Chat engine instance for DeepSeek calls
        """
        self.chat_engine = chat_engine
    
    def refactor_on_error(
        self,
        error_trace: str,
        affected_file: str = "main.py",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Refactor code based on error traceback.
        
        Args:
            error_trace: Error traceback string
            affected_file: File to refactor
            max_retries: Maximum retry attempts
            
        Returns:
            Refactor result
        """
        issue = self._extract_issue(error_trace)
        query = f"Fix this bug in {affected_file}: {issue}. Provide a working fix as a diff."
        
        result = self.chat_engine.handle_query(query)
        
        # If confidence is low, try to improve
        if result.get("confidence", 0) < 0.6 and max_retries > 0:
            # Try more specific query
            query2 = f"Analyze this error: {error_trace[:500]}. Fix {affected_file} with proper error handling."
            result = self.chat_engine.handle_query(query2)
        
        return result
    
    def refactor_for_performance(self, file_path: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Refactor code for performance optimization.
        
        Args:
            file_path: File to optimize
            context: Optional context about performance issues
            
        Returns:
            Refactor result
        """
        query = f"Optimize {file_path} for performance. {context or 'Focus on bottlenecks and inefficiencies.'} Provide optimized code as diff."
        return self.chat_engine.handle_query(query)
    
    def refactor_for_security(self, file_path: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Refactor code for security improvements.
        
        Args:
            file_path: File to secure
            context: Optional context about security concerns
            
        Returns:
            Refactor result
        """
        query = f"Improve security in {file_path}. {context or 'Fix vulnerabilities, add input validation, secure authentication.'} Provide secure code as diff."
        return self.chat_engine.handle_query(query)
    
    def _extract_issue(self, trace: str) -> str:
        """Extract key issue from traceback."""
        lines = trace.split('\n')
        
        # Look for error type and message
        error_info = []
        for line in lines:
            if 'Error:' in line or 'Exception:' in line or 'Traceback' in line:
                error_info.append(line.strip())
        
        # Get last meaningful line
        for line in reversed(lines):
            if line.strip() and not line.strip().startswith('File'):
                return line.strip()[:200]
        
        return trace[:200] if trace else "Unknown error"
    
    def analyze_ast(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze file AST for potential issues.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Analysis results
        """
        if not file_path.exists() or not file_path.suffix == '.py':
            return {"issues": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            issues = []
            
            # Check for common issues
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for eval/exec
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ('eval', 'exec', 'compile'):
                            issues.append(f"Security: {node.func.id}() call at line {node.lineno}")
                
                if isinstance(node, ast.For):
                    # Check for inefficient loops
                    if isinstance(node.iter, ast.Call):
                        if isinstance(node.iter.func, ast.Name):
                            if node.iter.func.id == 'range' and len(node.iter.args) > 1:
                                issues.append(f"Performance: Large range() at line {node.lineno}")
            
            return {"issues": issues, "file": str(file_path)}
        except SyntaxError as e:
            return {"issues": [f"Syntax error: {e}"], "file": str(file_path)}
        except Exception as e:
            return {"issues": [f"Analysis error: {e}"], "file": str(file_path)}



