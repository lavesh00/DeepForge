"""Agent API routes."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio
from execution.agent.agent_loop import AgentLoop

router = APIRouter()


@router.post("/missions/{mission_id}/agent/run")
async def run_agent(mission_id: str, request: Dict[str, Any]):
    """Run agent loop for mission."""
    from interface.api.server import initialize, _workspace_manager, _state_store
    
    initialize()
    
    goal = request.get("goal", "")
    if not goal:
        raise HTTPException(status_code=400, detail="Goal is required")
    
    workspace_dir = _workspace_manager.get_workspace(mission_id)
    if not workspace_dir:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    agent_loop = AgentLoop(str(workspace_dir), mission_id)
    results = await agent_loop.run(goal)
    
    return results


@router.post("/missions/{mission_id}/agent/iterate")
async def agent_iterate(mission_id: str, request: Dict[str, Any]):
    """Single agent iteration."""
    from interface.api.server import initialize, _workspace_manager
    
    initialize()
    
    query = request.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    workspace_dir = _workspace_manager.get_workspace(mission_id)
    if not workspace_dir:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    agent_loop = AgentLoop(str(workspace_dir), mission_id)
    step = await agent_loop.iterate(query)
    
    return {
        "step_id": step.step_id,
        "status": step.status,
        "tool_calls": [{"name": tc.name, "arguments": tc.arguments} for tc in step.tool_calls],
        "tool_results": step.tool_results,
        "error": step.error
    }





