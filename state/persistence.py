"""State persistence interface."""

from abc import ABC, abstractmethod
from typing import Optional
from .mission_state import MissionState
from .step_state import StepState


class StatePersistence(ABC):
    """State persistence interface."""
    
    @abstractmethod
    def save_mission(self, mission: MissionState):
        """Save mission state."""
        pass
    
    @abstractmethod
    def load_mission(self, mission_id: str) -> Optional[MissionState]:
        """Load mission state."""
        pass
    
    @abstractmethod
    def save_step(self, step: StepState):
        """Save step state."""
        pass


