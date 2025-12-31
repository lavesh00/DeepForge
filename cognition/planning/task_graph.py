"""Task graph."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    """Task node in graph."""
    task_id: str
    description: str
    task_type: str
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    estimated_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskGraph:
    """Task execution graph."""
    
    def __init__(self):
        """Initialize task graph."""
        self._tasks: Dict[str, TaskNode] = {}
    
    def add_task(self, task: TaskNode):
        """Add a task to the graph."""
        self._tasks[task.task_id] = task
    
    def get_task(self, task_id: str) -> Optional[TaskNode]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_ready_tasks(self) -> List[TaskNode]:
        """Get tasks that are ready to execute."""
        ready = []
        for task in self._tasks.values():
            if task.status == TaskStatus.PENDING:
                if all(
                    self._tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                    if dep_id in self._tasks
                ):
                    task.status = TaskStatus.READY
                    ready.append(task)
        return ready
    
    def mark_completed(self, task_id: str):
        """Mark a task as completed."""
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.COMPLETED
    
    def mark_failed(self, task_id: str):
        """Mark a task as failed."""
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.FAILED
    
    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
            for task in self._tasks.values()
        )
    
    def get_execution_order(self) -> List[str]:
        """Get execution order of tasks."""
        order = []
        completed = set()
        
        while len(order) < len(self._tasks):
            for task in self._tasks.values():
                if task.task_id not in order:
                    if all(dep in completed for dep in task.dependencies):
                        order.append(task.task_id)
                        completed.add(task.task_id)
        
        return order








