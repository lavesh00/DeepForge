"""Composer Engine - Multi-file orchestration with DAG."""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import asyncio
from dataclasses import dataclass, field
from execution.codegen.code_engine import CodeEngine
from model_runtime.serving.local_api import LocalModelAPI
from model_runtime.serving.router import ModelRouter
from core.registry import get_service
from state.state_store_sqlite import SQLiteStateStore


@dataclass
class ComposerNode:
    """Node in the composer DAG."""
    node_id: str
    task: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    output: Optional[str] = None
    error: Optional[str] = None
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ComposerEngine:
    """Orchestrates multi-file tasks with dynamic DAG."""
    
    def __init__(self, mission_id: str, workspace_dir: str):
        """
        Initialize composer engine.
        
        Args:
            mission_id: Mission identifier
            workspace_dir: Workspace directory path
        """
        self.mission_id = mission_id
        self.workspace_dir = Path(workspace_dir)
        self.nodes: Dict[str, ComposerNode] = {}
        
        # Get model API
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
    
    def create_plan(self, goal: str) -> Dict[str, Any]:
        """
        Create a dynamic DAG plan from high-level goal.
        
        Args:
            goal: High-level goal (e.g., "Build secure Flask auth API with React frontend")
            
        Returns:
            Plan with nodes and dependencies
        """
        # Use DeepSeek to decompose goal into steps
        prompt = f"""Decompose this goal into a dependency graph of executable steps:
Goal: {goal}

Return JSON:
{{
    "steps": [
        {{
            "id": "step_1",
            "task": "Create backend skeleton",
            "dependencies": [],
            "files": ["backend/schema.py", "backend/app.py"]
        }},
        {{
            "id": "step_2",
            "task": "Implement auth routes",
            "dependencies": ["step_1"],
            "files": ["backend/auth.py"]
        }}
    ]
}}

Rules:
- Each step should be atomic and executable
- Dependencies form a DAG (no cycles)
- Files list what will be created/modified
- Steps can run in parallel if no dependencies
"""
        
        try:
            if self.model_api:
                response = self.model_api.chat_completion(
                    model="deepseek-coder",
                    messages=[
                        {"role": "system", "content": "You are a software architect. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2048,
                )
                content = response["choices"][0]["message"]["content"]
                
                # Extract JSON
                import json
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    content = content[json_start:json_end]
                
                plan_data = json.loads(content)
                
                # Create nodes
                for step in plan_data.get("steps", []):
                    node = ComposerNode(
                        node_id=step["id"],
                        task=step["task"],
                        dependencies=step.get("dependencies", []),
                        files_created=step.get("files", [])
                    )
                    self.nodes[node.node_id] = node
            else:
                # Fallback: Simple linear plan
                self._create_fallback_plan(goal)
        except Exception as e:
            # Fallback plan
            self._create_fallback_plan(goal)
        
        return {
            "nodes": {nid: {
                "task": node.task,
                "dependencies": node.dependencies,
                "status": node.status,
                "files": node.files_created
            } for nid, node in self.nodes.items()},
            "total_nodes": len(self.nodes)
        }
    
    def _create_fallback_plan(self, goal: str):
        """Create a simple fallback plan."""
        steps = [
            ("step_1", "Create project structure", []),
            ("step_2", "Implement core features", ["step_1"]),
            ("step_3", "Add tests", ["step_2"]),
            ("step_4", "Package for deployment", ["step_3"])
        ]
        
        for node_id, task, deps in steps:
            self.nodes[node_id] = ComposerNode(
                node_id=node_id,
                task=task,
                dependencies=deps
            )
    
    def get_ready_nodes(self) -> List[ComposerNode]:
        """Get nodes ready to execute (all dependencies completed)."""
        ready = []
        for node in self.nodes.values():
            if node.status == "pending":
                deps_ready = all(
                    self.nodes[dep].status == "completed"
                    for dep in node.dependencies
                    if dep in self.nodes
                )
                if deps_ready:
                    ready.append(node)
        return ready
    
    async def execute_node(self, node: ComposerNode) -> bool:
        """
        Execute a single node.
        
        Args:
            node: Node to execute
            
        Returns:
            True if successful
        """
        node.status = "running"
        node.started_at = datetime.utcnow()
        
        try:
            # Gather context from previous steps
            context = self._gather_context(node)
            
            # Generate code for this step
            code = self.code_engine.generate_code(
                prompt=node.task,
                context={
                    "mission_description": f"Composer step: {node.task}",
                    "previous_steps": context,
                    "workspace_files": self._list_workspace_files()
                },
                language="python"
            )
            
            # Write files
            for file_path in node.files_created:
                full_path = self.workspace_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                if file_path.endswith('.py'):
                    full_path.write_text(code, encoding='utf-8')
                else:
                    # Generate appropriate content based on file type
                    content = self._generate_file_content(file_path, code)
                    full_path.write_text(content, encoding='utf-8')
                
                node.files_created.append(str(full_path))
            
            node.status = "completed"
            node.completed_at = datetime.utcnow()
            node.output = f"Generated {len(node.files_created)} files"
            return True
            
        except Exception as e:
            node.status = "failed"
            node.error = str(e)
            node.completed_at = datetime.utcnow()
            return False
    
    def _gather_context(self, node: ComposerNode) -> str:
        """Gather context from completed dependency nodes."""
        context_parts = []
        for dep_id in node.dependencies:
            if dep_id in self.nodes:
                dep_node = self.nodes[dep_id]
                if dep_node.status == "completed" and dep_node.output:
                    context_parts.append(f"{dep_node.task}: {dep_node.output}")
        return "\n".join(context_parts)
    
    def _list_workspace_files(self) -> str:
        """List all files in workspace for context."""
        if not self.workspace_dir.exists():
            return ""
        
        files = []
        for file_path in self.workspace_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.html', '.json']:
                try:
                    content = file_path.read_text(encoding='utf-8')[:500]
                    files.append(f"{file_path.relative_to(self.workspace_dir)}:\n{content}")
                except Exception:
                    pass
        
        return "\n---\n".join(files)
    
    def _generate_file_content(self, file_path: str, code: str) -> str:
        """Generate content for non-Python files."""
        if file_path.endswith('.json'):
            return '{"generated": true}'
        elif file_path.endswith('.html'):
            return f"<!DOCTYPE html>\n<html>\n<body>\n{code}\n</body>\n</html>"
        elif file_path.endswith('.js'):
            return f"// Generated file\n{code}"
        else:
            return code
    
    async def execute_plan(self) -> Dict[str, Any]:
        """
        Execute the entire plan, respecting dependencies.
        
        Returns:
            Execution results
        """
        completed = 0
        failed = 0
        
        while True:
            ready_nodes = self.get_ready_nodes()
            if not ready_nodes:
                break
            
            # Execute ready nodes (can be parallelized)
            results = await asyncio.gather(
                *[self.execute_node(node) for node in ready_nodes],
                return_exceptions=True
            )
            
            for success in results:
                if success is True:
                    completed += 1
                else:
                    failed += 1
        
        return {
            "completed": completed,
            "failed": failed,
            "total": len(self.nodes),
            "nodes": {nid: {
                "status": node.status,
                "output": node.output,
                "error": node.error
            } for nid, node in self.nodes.items()}
        }





