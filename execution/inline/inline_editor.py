"""Inline Editor - Cmd+K style edits with diff preview."""

from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import difflib
from execution.codegen.code_engine import CodeEngine
from model_runtime.serving.local_api import LocalModelAPI
from model_runtime.serving.router import ModelRouter
from core.registry import get_service


class InlineEditor:
    """Handles inline code edits with diff preview."""
    
    def __init__(self):
        """Initialize inline editor."""
        try:
            model_manager = get_service("model_manager")
            if model_manager:
                router = ModelRouter(model_manager=model_manager)
                self.model_api = LocalModelAPI(router)
            else:
                self.model_api = None
        except Exception:
            self.model_api = None
        
        self.code_engine = CodeEngine(model_api=self.model_api)
    
    def edit_code(
        self,
        file_path: str,
        selected_code: str,
        query: str,
        context_lines: int = 500
    ) -> Dict[str, Any]:
        """
        Edit code based on selection and query.
        
        Args:
            file_path: Path to file
            selected_code: Selected code snippet
            query: User intent (e.g., "make this async and add caching")
            context_lines: Number of surrounding lines to include
            
        Returns:
            Edit result with diff and confidence
        """
        file = Path(file_path)
        if not file.exists():
            return {
                "error": "File not found",
                "diff": None,
                "confidence": 0.0
            }
        
        # Read full file context
        full_content = file.read_text(encoding='utf-8')
        lines = full_content.splitlines(keepends=True)
        
        # Find selected code position
        selected_start, selected_end = self._find_selection(lines, selected_code)
        
        # Get context window
        context_start = max(0, selected_start - context_lines)
        context_end = min(len(lines), selected_end + context_lines)
        context = "".join(lines[context_start:context_end])
        
        # Build prompt for DeepSeek
        prompt = f"""Given this file context:
{context}

Selected code:
{selected_code}

User intent: {query}

Output ONLY a minimal diff or replacement block. Explain in 1 sentence.
Return JSON:
{{
    "explanation": "Brief explanation",
    "replacement": "New code to replace selection",
    "diff": "Unified diff format",
    "confidence": 0.0-1.0
}}
"""
        
        try:
            if self.model_api:
                response = self.model_api.chat_completion(
                    model="deepseek-coder",
                    messages=[
                        {"role": "system", "content": "You are a code editor. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1024,
                    temperature=0.2  # Lower temp for code fidelity
                )
                
                content = response["choices"][0]["message"]["content"]
                
                # Extract JSON
                import json
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    content = content[json_start:json_end]
                
                result = json.loads(content)
                
                # Generate unified diff
                new_lines = lines.copy()
                if result.get("replacement"):
                    new_lines[selected_start:selected_end] = [result["replacement"] + "\n"]
                elif result.get("diff"):
                    # Apply diff
                    new_lines = self._apply_diff(lines, result["diff"], selected_start)
                
                diff = self._generate_unified_diff(
                    lines[selected_start:selected_end],
                    new_lines[selected_start:selected_end],
                    file_path,
                    selected_start + 1
                )
                
                return {
                    "explanation": result.get("explanation", "Edit applied"),
                    "diff": diff,
                    "confidence": result.get("confidence", 0.5),
                    "new_content": "".join(new_lines),
                    "file_path": file_path
                }
            else:
                raise ValueError("Model API not available")
        except Exception as e:
            return {
                "error": str(e),
                "diff": None,
                "confidence": 0.0
            }
    
    def _find_selection(self, lines: list, selected_code: str) -> Tuple[int, int]:
        """Find the line range of selected code."""
        selected_lines = selected_code.splitlines()
        if not selected_lines:
            return 0, 0
        
        # Simple search for first matching line
        for i, line in enumerate(lines):
            if selected_lines[0].strip() in line:
                # Check if subsequent lines match
                match = True
                for j, sel_line in enumerate(selected_lines[1:], 1):
                    if i + j >= len(lines) or sel_line.strip() not in lines[i + j]:
                        match = False
                        break
                if match:
                    return i, i + len(selected_lines)
        
        return 0, len(lines)
    
    def _apply_diff(self, lines: list, diff_str: str, start_line: int) -> list:
        """Apply unified diff to lines."""
        # Simplified diff application
        new_lines = lines.copy()
        # This would need proper diff parsing
        return new_lines
    
    def _generate_unified_diff(
        self,
        old_lines: list,
        new_lines: list,
        file_path: str,
        start_line: int
    ) -> str:
        """Generate unified diff format."""
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=file_path,
            tofile=file_path,
            lineterm='',
            n=3
        )
        return "\n".join(diff)
    
    def apply_edit(self, file_path: str, new_content: str) -> bool:
        """
        Apply edit to file.
        
        Args:
            file_path: Path to file
            new_content: New file content
            
        Returns:
            True if successful
        """
        try:
            file = Path(file_path)
            # Validate syntax if Python
            if file.suffix == '.py':
                compile(new_content, file_path, 'exec')
            
            file.write_text(new_content, encoding='utf-8')
            return True
        except SyntaxError as e:
            return False
        except Exception:
            return False





