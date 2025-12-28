"""Composer API routes."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pathlib import Path
from cognition.composer.composer_engine import ComposerEngine

router = APIRouter()


@router.post("/api/missions/{mission_id}/composer")
async def create_composer_plan(mission_id: str, request: Dict[str, Any]):
    """Create a composer plan from goal."""
    from interface.api.server import initialize, _workspace_manager
    
    initialize()
    
    goal = request.get("goal", "")
    if not goal:
        raise HTTPException(status_code=400, detail="Goal is required")
    
    workspace_dir = _workspace_manager.get_workspace(mission_id)
    if not workspace_dir:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    composer = ComposerEngine(mission_id, str(workspace_dir))
    plan = composer.create_plan(goal)
    
    return plan


@router.post("/missions/{mission_id}/composer/execute")
async def execute_composer_plan(mission_id: str):
    """Execute composer plan."""
    from interface.api.server import initialize, _workspace_manager
    import asyncio
    
    initialize()
    
    workspace_dir = _workspace_manager.get_workspace(mission_id)
    if not workspace_dir:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    composer = ComposerEngine(mission_id, str(workspace_dir))
    results = await composer.execute_plan()
    
    return results

