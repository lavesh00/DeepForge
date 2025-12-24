"""Event bus."""

import asyncio
import queue
import threading
from typing import Dict, List, Callable, Optional, Set
from collections import defaultdict
from .event_envelope import EventEnvelope
from .event_types import EventType
from .listeners.base_listener import BaseListener


_global_event_bus: Optional["EventBus"] = None


def get_event_bus() -> "EventBus":
    """Get or create global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


class EventBus:
    """Central event bus for pub-sub communication."""
    
    def __init__(self):
        """Initialize event bus."""
        self._listeners: Dict[EventType, List[Callable]] = defaultdict(list)
        self._wildcard_listeners: List[Callable] = []
        self._event_queue: queue.Queue = queue.Queue()
        self._dead_letter_queue: List[EventEnvelope] = []
        self._running: bool = False
        self._worker_thread: Optional[threading.Thread] = None
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event type."""
        self._listeners[event_type].append(handler)
    
    def subscribe_all(self, handler: Callable):
        """Subscribe to all events."""
        self._wildcard_listeners.append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe from an event type."""
        if handler in self._listeners[event_type]:
            self._listeners[event_type].remove(handler)
    
    def publish(self, event: EventEnvelope):
        """Publish an event synchronously."""
        self._event_queue.put(event)
    
    async def publish_async(self, event: EventEnvelope):
        """Publish an event asynchronously."""
        await self._process_event(event)
    
    def _process_event_sync(self, event: EventEnvelope):
        """Process a single event synchronously."""
        handlers = []
        
        specific_handlers = self._listeners.get(event.event_type, [])
        handlers.extend(specific_handlers)
        handlers.extend(self._wildcard_listeners)
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(handler(event))
                        else:
                            loop.run_until_complete(handler(event))
                    except RuntimeError:
                        asyncio.run(handler(event))
                else:
                    handler(event)
            except Exception as e:
                self._dead_letter_queue.append(event)
    
    async def _process_event(self, event: EventEnvelope):
        """Process a single event asynchronously."""
        handlers = []
        
        specific_handlers = self._listeners.get(event.event_type, [])
        handlers.extend(specific_handlers)
        handlers.extend(self._wildcard_listeners)
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self._dead_letter_queue.append(event)
    
    async def start(self):
        """Start the event bus worker."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
    
    async def stop(self):
        """Stop the event bus worker."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
    
    def _worker(self):
        """Background worker to process events."""
        while self._running:
            try:
                event = self._event_queue.get(timeout=0.1)
                self._process_event_sync(event)
            except queue.Empty:
                continue
            except Exception as e:
                pass
    
    def get_dead_letters(self) -> List[EventEnvelope]:
        """Get dead letter queue."""
        return self._dead_letter_queue.copy()
    
    def clear_dead_letters(self):
        """Clear the dead letter queue."""
        self._dead_letter_queue.clear()

