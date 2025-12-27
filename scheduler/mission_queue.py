"""Mission queue."""

from typing import List
from collections import deque


class MissionQueue:
    """Mission execution queue."""
    
    def __init__(self):
        """Initialize mission queue."""
        self._queue: deque = deque()
    
    def enqueue(self, mission_id: str, priority: int = 0):
        """Enqueue a mission."""
        self._queue.append((priority, mission_id))
        self._queue = deque(sorted(self._queue, key=lambda x: -x[0]))
    
    def dequeue(self) -> str:
        """Dequeue a mission."""
        if self._queue:
            return self._queue.popleft()[1]
        return None
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._queue) == 0




