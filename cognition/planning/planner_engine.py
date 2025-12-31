"""Planner engine."""

from .decomposition import TaskDecomposition
from .task_graph import TaskGraph


class PlannerEngine:
    """Mission planning engine."""
    
    def __init__(self):
        """Initialize planner engine."""
        self.decomposition = TaskDecomposition()
    
    def create_plan(self, description: str) -> TaskGraph:
        """
        Create a plan from mission description.
        
        Args:
            description: Mission description
            
        Returns:
            TaskGraph with execution plan
        """
        return self.decomposition.decompose(description)








