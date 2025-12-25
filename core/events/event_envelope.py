"""Event envelope."""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from .event_types import EventType


class EventEnvelope:
    """Event envelope."""
    
    def __init__(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        source: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize event envelope."""
        self.event_type = event_type
        self.payload = payload
        self.source = source
        self.timestamp = datetime.utcnow().timestamp()
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.causation_id = causation_id
        self.metadata = metadata or {}


def create_event(
    event_type: EventType,
    payload: Dict[str, Any],
    source: str,
    correlation_id: Optional[str] = None,
    causation_id: Optional[str] = None
) -> EventEnvelope:
    """Create an event envelope."""
    return EventEnvelope(
        event_type=event_type,
        payload=payload,
        source=source,
        correlation_id=correlation_id,
        causation_id=causation_id
    )


