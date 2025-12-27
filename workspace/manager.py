"""Workspace manager."""

from pathlib import Path
from typing import Optional
import uuid


class WorkspaceManager:
    """Manages project workspaces."""
    
    def __init__(self, base_dir: Path):
        """
        Initialize workspace manager.
        
        Args:
            base_dir: Base directory for workspaces
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_workspace(self, mission_id: str) -> Path:
        """
        Create a workspace for a mission.
        
        Args:
            mission_id: Mission identifier
            
        Returns:
            Path to workspace directory
        """
        workspace_dir = self.base_dir / mission_id
        workspace_dir.mkdir(parents=True, exist_ok=True)
        return workspace_dir
    
    def get_workspace(self, mission_id: str) -> Optional[Path]:
        """Get workspace path for mission."""
        workspace_dir = self.base_dir / mission_id
        if workspace_dir.exists():
            return workspace_dir
        return None
    
    def delete_workspace(self, mission_id: str):
        """Delete workspace for mission."""
        workspace_dir = self.base_dir / mission_id
        if workspace_dir.exists():
            import shutil
            shutil.rmtree(workspace_dir)




