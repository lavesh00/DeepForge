"""Agent Orchestrator - Replaces rigid mission controller."""

from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from execution.agent.agent_loop import AgentLoop
from state.mission_state import MissionState, MissionStatus
from state.persistence import StatePersistence
from core.events import get_event_bus, create_event, EventType


class AgentOrchestrator:
    """Agent-first orchestrator replacing mission controller."""
    
    def __init__(
        self,
        mission: MissionState,
        persistence: StatePersistence,
        workspace_dir: str
    ):
        """
        Initialize agent orchestrator.
        
        Args:
            mission: Mission state
            persistence: State persistence
            workspace_dir: Workspace directory
        """
        self.mission = mission
        self.persistence = persistence
        self.workspace_dir = workspace_dir
        self.agent_loop = AgentLoop(workspace_dir, mission.mission_id)
        self.event_bus = get_event_bus()
    
    def start(self) -> bool:
        """Start agent execution."""
        self.mission.status = MissionStatus.EXECUTING
        self.mission.started_at = datetime.utcnow()
        self.persistence.save_mission(self.mission)
        
        self.event_bus.publish(create_event(
            EventType.MISSION_STARTED,
            {"mission_id": self.mission.mission_id, "description": self.mission.description},
            source="agent_orchestrator"
        ))
        
        return True
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute agent loop.
        
        Returns:
            Execution results
        """
        results = await self.agent_loop.run(self.mission.description)
        
        if results["failed"] == 0:
            self.mission.status = MissionStatus.COMPLETED
        else:
            self.mission.status = MissionStatus.FAILED
        
        self.mission.completed_at = datetime.utcnow()
        self.persistence.save_mission(self.mission)
        
        self.event_bus.publish(create_event(
            EventType.MISSION_COMPLETED if self.mission.status == MissionStatus.COMPLETED else EventType.MISSION_FAILED,
            {"mission_id": self.mission.mission_id, "results": results},
            source="agent_orchestrator"
        ))
        
        return results





