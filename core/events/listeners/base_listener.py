"""Base event listener."""

from abc import ABC, abstractmethod
from ..event_envelope import EventEnvelope


class BaseListener(ABC):
    """Base class for event listeners."""
    
    @abstractmethod
    def handle(self, event: EventEnvelope):
        """Handle an event."""
        pass






