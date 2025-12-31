"""Task decomposition."""

from typing import List, Dict, Any
from .task_graph import TaskGraph, TaskNode, TaskStatus


class TaskDecomposition:
    """Decomposes high-level tasks into atomic steps."""
    
    def __init__(self):
        """Initialize task decomposition."""
        self._decomposition_rules: Dict[str, callable] = {}
    
    def decompose(self, description: str, context: Dict[str, Any] = None) -> TaskGraph:
        """
        Decompose a mission description into task graph.
        
        Args:
            description: Mission description
            context: Additional context
            
        Returns:
            TaskGraph with decomposed tasks
        """
        if context is None:
            context = {}
        
        graph = TaskGraph()
        
        tasks = self._generate_tasks(description, context)
        
        for task_data in tasks:
            task = TaskNode(
                task_id=task_data["id"],
                description=task_data["description"],
                task_type=task_data.get("type", "generic"),
                dependencies=task_data.get("dependencies", []),
                estimated_time_seconds=task_data.get("estimated_time", 0.0),
                metadata=task_data.get("metadata", {}),
            )
            graph.add_task(task)
        
        return graph
    
    def _generate_tasks(self, description: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate task list from description."""
        tasks = []
        
        description_lower = description.lower()
        
        if "web" in description_lower or "app" in description_lower:
            tasks.extend(self._decompose_web_app(description, context))
        elif "api" in description_lower:
            tasks.extend(self._decompose_api(description, context))
        elif "cli" in description_lower or "command" in description_lower:
            tasks.extend(self._decompose_cli(description, context))
        else:
            tasks.extend(self._decompose_generic(description, context))
        
        return tasks
    
    def _decompose_web_app(self, description: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose web application tasks."""
        return [
            {"id": "1", "description": "Create project structure", "type": "setup", "dependencies": []},
            {"id": "2", "description": "Set up frontend framework", "type": "frontend", "dependencies": ["1"]},
            {"id": "3", "description": "Set up backend server", "type": "backend", "dependencies": ["1"]},
            {"id": "4", "description": "Implement core features", "type": "development", "dependencies": ["2", "3"]},
            {"id": "5", "description": "Write tests", "type": "testing", "dependencies": ["4"]},
            {"id": "6", "description": "Package for deployment", "type": "packaging", "dependencies": ["5"]},
        ]
    
    def _decompose_api(self, description: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose API tasks."""
        return [
            {"id": "1", "description": "Create project structure", "type": "setup", "dependencies": []},
            {"id": "2", "description": "Define API endpoints", "type": "design", "dependencies": ["1"]},
            {"id": "3", "description": "Implement endpoints", "type": "development", "dependencies": ["2"]},
            {"id": "4", "description": "Add authentication", "type": "security", "dependencies": ["3"]},
            {"id": "5", "description": "Write API tests", "type": "testing", "dependencies": ["4"]},
        ]
    
    def _decompose_cli(self, description: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose CLI application tasks."""
        return [
            {"id": "1", "description": "Create project structure", "type": "setup", "dependencies": []},
            {"id": "2", "description": "Define CLI interface", "type": "design", "dependencies": ["1"]},
            {"id": "3", "description": "Implement commands", "type": "development", "dependencies": ["2"]},
            {"id": "4", "description": "Add help and documentation", "type": "documentation", "dependencies": ["3"]},
            {"id": "5", "description": "Write tests", "type": "testing", "dependencies": ["3"]},
        ]
    
    def _decompose_generic(self, description: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose generic project tasks."""
        return [
            {"id": "1", "description": "Create project structure", "type": "setup", "dependencies": []},
            {"id": "2", "description": "Implement core functionality", "type": "development", "dependencies": ["1"]},
            {"id": "3", "description": "Write tests", "type": "testing", "dependencies": ["2"]},
            {"id": "4", "description": "Create documentation", "type": "documentation", "dependencies": ["2"]},
        ]








