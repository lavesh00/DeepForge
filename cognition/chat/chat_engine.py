"""Iterative chat layer for code refinement."""

import json
import os
import difflib
from typing import Dict, Any, List, Optional
from pathlib import Path
from execution.codegen.code_engine import CodeEngine
from model_runtime.serving.local_api import LocalModelAPI
from model_runtime.serving.router import ModelRouter
from core.registry import get_service
from state.session_memory import SessionMemory


class ChatEngine:
    """Handles iterative chat-based code refinement."""
    
    def __init__(self, mission_id: str, workspace_dir: str):
        """
        Initialize chat engine.
        
        Args:
            mission_id: Mission identifier
            workspace_dir: Path to workspace directory
        """
        self.mission_id = mission_id
        self.workspace_dir = Path(workspace_dir)
        
        # Get model API - route through DeepSeek
        model_manager = get_service("model_manager")
        if model_manager:
            router = ModelRouter(model_manager=model_manager)
            self.model_api = LocalModelAPI(router)
        else:
            self.model_api = None
        
        self.code_engine = CodeEngine(model_api=self.model_api)
        
        # Session memory
        from state.state_store_sqlite import SQLiteStateStore
        from core.config import load_config
        config = load_config()
        paths = config.get_paths()
        state_dir = Path(paths.get("state", {}).get("missions", ""))
        state_store = SQLiteStateStore(state_dir / "state.db")
        self.session_memory = SessionMemory(state_store, mission_id)
    
    def handle_query(self, query: str) -> Dict[str, Any]:
        """
        Handle a chat query and apply changes.
        
        Args:
            query: User query (e.g., "add delete endpoint")
            
        Returns:
            Result with explanation, diff, and patched files
        """
        # Gather workspace context
        files_context = self._gather_files_context()
        history = self.session_memory.get_last_n(5)
        history_str = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in history])
        
        # Build DeepSeek prompt
        prompt = f"""Current workspace files:
{files_context}

Chat history:
{history_str}

User query: {query}

Respond as a senior developer. Analyze the code and suggest changes.
Return JSON:
{{
    "explanation": "Brief explanation of changes",
    "diff": "Unified diff format (--- a/file.py\\n+++ b/file.py\\n@@ ...)",
    "confidence": 0.0-1.0,
    "target_file": "main.py"
}}

Use deepseek-coder style: concise, correct code only. Focus on the specific change requested.
"""
        
        # Call DeepSeek via existing API
        try:
            if self.model_api:
                response = self.model_api.chat_completion(
                    model="deepseek-coder",
                    messages=[
                        {"role": "system", "content": "You are a code editor assistant. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1024,
                )
                content = response["choices"][0]["message"]["content"]
                
                # Extract JSON from response
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    content = content[json_start:json_end]
                
                ai_response = json.loads(content)
                
                if ai_response.get("confidence", 0) < 0.7:
                    raise ValueError("Low confidence")
            else:
                raise ValueError("Model API not available")
        except (json.JSONDecodeError, KeyError, ValueError, Exception) as e:
            # Fallback to template-based edit
            ai_response = {
                "explanation": f"Fallback edit applied: {str(e)}",
                "diff": self._generate_fallback_diff(query, files_context),
                "confidence": 0.5,
                "target_file": "main.py"
            }
        
        # Apply patch
        target_file = ai_response.get("target_file", "main.py")
        patched_files = self._apply_patch(ai_response["diff"], target_file)
        
        # Store in session memory
        self.session_memory.add_turn(query, ai_response["explanation"])
        
        return {
            "explanation": ai_response["explanation"],
            "diff": ai_response["diff"],
            "patched_files": patched_files,
            "confidence": ai_response.get("confidence", 0.5),
            "history": self.session_memory.get_last_n(3)
        }
    
    def _gather_files_context(self) -> str:
        """Gather context from workspace files."""
        context = ""
        if not self.workspace_dir.exists():
            return context
        
        for root, _, files in os.walk(self.workspace_dir):
            for file in files:
                if file.endswith(('.py', '.js', '.html', '.css', '.json')):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text(encoding='utf-8')[:2000]
                        rel_path = file_path.relative_to(self.workspace_dir)
                        context += f"File: {rel_path}\n{content}\n---\n"
                    except Exception:
                        pass
        return context
    
    def _apply_patch(self, diff_str: str, target_file: str) -> List[str]:
        """Apply unified diff to target file with validation."""
        patched = []
        file_path = self.workspace_dir / target_file
        
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("", encoding='utf-8')
        
        # Backup original for rollback
        old_content = file_path.read_text(encoding='utf-8')
        old_lines = old_content.splitlines(keepends=True) if old_content else []
        
        try:
            # Try to extract code from JSON response if diff is malformed
            if "```" in diff_str:
                parts = diff_str.split("```")
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Code blocks
                        code = part.split("\n", 1)[1] if "\n" in part else part
                        if code.strip() and len(code) > 10:
                            # Validate before applying
                            test_content = old_content + "\n\n" + code
                            if self._validate_patch(test_content, file_path):
                                file_path.write_text(test_content, encoding='utf-8')
                                patched.append(target_file)
                                return patched
            
            # Parse unified diff properly
            new_lines = []
            in_hunk = False
            old_idx = 0
            hunk_started = False
            
            for line in diff_str.splitlines():
                if line.startswith("+++"):
                    continue
                elif line.startswith("@@"):
                    # Parse hunk header: @@ -start,count +start,count @@
                    parts = line.split()
                    if len(parts) >= 2:
                        old_info = parts[1]
                        if old_info.startswith("-"):
                            try:
                                old_idx = int(old_info.split(",")[0][1:]) - 1
                                if old_idx < 0:
                                    old_idx = 0
                            except (ValueError, IndexError):
                                old_idx = 0
                    in_hunk = True
                    hunk_started = True
                    # Start new lines from before the hunk
                    new_lines = old_lines[:old_idx] if old_idx < len(old_lines) else []
                elif in_hunk and hunk_started:
                    if line.startswith(" "):
                        # Context line - keep it
                        new_lines.append(line[1:] + ("\n" if not line[1:].endswith("\n") else ""))
                        old_idx += 1
                    elif line.startswith("-"):
                        # Deletion - skip this line
                        old_idx += 1
                    elif line.startswith("+"):
                        # Addition - add this line
                        new_lines.append(line[1:] + ("\n" if not line[1:].endswith("\n") else ""))
            
            # Append remaining old lines
            if old_idx < len(old_lines):
                new_lines.extend(old_lines[old_idx:])
            
            # Validate before writing
            new_content = "".join(new_lines)
            if self._validate_patch(new_content, file_path):
                file_path.write_text(new_content, encoding='utf-8')
                patched.append(target_file)
            else:
                # Rollback
                file_path.write_text(old_content, encoding='utf-8')
                raise ValueError("Patch validation failed - syntax error detected")
        except Exception as e:
            # Rollback on any error
            try:
                file_path.write_text(old_content, encoding='utf-8')
            except Exception:
                pass
            # Log to session memory
            self.session_memory.add_turn(
                f"Patch failed for {target_file}",
                f"Error: {str(e)}"
            )
            raise
        
        return patched
    
    def _validate_patch(self, content: str, file_path: Path) -> bool:
        """Validate patched content - check syntax for Python files."""
        if file_path.suffix != '.py':
            return True  # Skip validation for non-Python files
        
        try:
            compile(content, str(file_path), 'exec')
            return True
        except SyntaxError as e:
            # Log syntax error
            import logging
            logger = logging.getLogger("deepforge.chat")
            logger.warning(f"Syntax error in patched file {file_path}: {e}")
            return False
        except Exception:
            return True  # Other errors might be OK (imports, etc.)
    
    def _generate_fallback_diff(self, query: str, context: str) -> str:
        """Generate fallback diff when model fails."""
        # Use code engine to generate code based on query
        try:
            code = self.code_engine.generate_code(
                prompt=query,
                context={"existing_code": context},
                language="python"
            )
            return f"""--- a/main.py
+++ b/main.py
@@ -1,0 +1,{len(code.splitlines())} @@
+{code}
"""
        except Exception:
            return """--- a/main.py
+++ b/main.py
@@ -1,0 +1,1 @@
+# Edit applied
"""
    
    def chain_refine(self, query: str, max_steps: int = 5) -> Dict[str, Any]:
        """
        Multi-step chain refinement - breaks complex queries into steps.
        
        Args:
            query: Complex query (e.g., "Secure todo API with OAuth")
            max_steps: Maximum refinement steps
            
        Returns:
            Chain result with all steps
        """
        steps = []
        current_query = query
        
        for step_num in range(max_steps):
            # Get context from previous steps
            history = self.session_memory.get_last_n(3)
            context_prompt = f"Step {step_num + 1} of {max_steps}: {current_query}"
            if history:
                context_prompt += f"\nPrevious steps: {[h['ai'] for h in history]}"
            
            result = self.handle_query(context_prompt)
            steps.append({
                "step": step_num + 1,
                "query": context_prompt,
                "result": result
            })
            
            # If high confidence, we're done
            if result.get("confidence", 0) > 0.9:
                break
            
            # If low confidence, refine the query for next step
            if result.get("confidence", 0) < 0.7:
                current_query = f"Refine and improve: {current_query}"
        
        return {
            "query": query,
            "steps": steps,
            "total_steps": len(steps),
            "final_confidence": steps[-1]["result"].get("confidence", 0) if steps else 0
        }

