"""Lifecycle manager."""

from typing import Dict, Callable, Optional, List
from core.registry import ServiceRegistry


class LifecycleManager:
    """Manages service lifecycle."""
    
    def __init__(self, registry: ServiceRegistry):
        """Initialize lifecycle manager."""
        self.registry = registry
        self._services: Dict[str, Dict] = {}
    
    def register_service(
        self,
        name: str,
        init_func: Optional[Callable] = None,
        shutdown_func: Optional[Callable] = None
    ):
        """Register a service with lifecycle."""
        self._services[name] = {
            "init": init_func,
            "shutdown": shutdown_func,
            "started": False
        }
    
    def start_all(self):
        """Start all registered services."""
        for name, service in self._services.items():
            if service["init"] and not service["started"]:
                try:
                    result = service["init"]()
                    # Don't await async functions here - they should be sync or handled elsewhere
                    if hasattr(result, "__await__"):
                        # Skip async functions - they'll be handled by FastAPI lifespan
                        pass
                    service["started"] = True
                except Exception as e:
                    pass
    
    def shutdown_all(self):
        """Shutdown all registered services."""
        for name, service in reversed(list(self._services.items())):
            if service["shutdown"] and service["started"]:
                try:
                    result = service["shutdown"]()
                    # Don't await async functions here - they should be sync or handled elsewhere
                    if hasattr(result, "__await__"):
                        # Skip async functions - they'll be handled by FastAPI lifespan
                        pass
                except Exception as e:
                    pass

