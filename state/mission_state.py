"""Mission state."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class MissionStatus(str, Enum):
    """Mission status."""
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MissionState:
    """Mission state."""
    mission_id: str
    status: MissionStatus
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_steps: int = 0
    completed_steps: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

