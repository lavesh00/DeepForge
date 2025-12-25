"""Service registry."""

from typing import Dict, Any, Optional, TypeVar, Type

T = TypeVar("T")


class ServiceRegistry:
    """Service registry for dependency injection."""
    
    _instance: Optional["ServiceRegistry"] = None
    
    def __init__(self):
        """Initialize service registry."""
        self._services: Dict[str, Any] = {}
    
    @classmethod
    def get_instance(cls) -> "ServiceRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register(self, name: str, service: Any):
        """Register a service."""
        self._services[name] = service
    
    def get(self, name: str) -> Optional[Any]:
        """Get a service."""
        return self._services.get(name)
    
    def get_typed_service(self, name: str, service_type: Type[T]) -> Optional[T]:
        """Get a service by name with type checking."""
        service = self._services.get(name)
        if service is not None and isinstance(service, service_type):
            return service
        return None


_registry = ServiceRegistry.get_instance()


def get_service(name: str) -> Optional[Any]:
    """Get a service from the global registry."""
    return _registry.get(name)


def register_service(name: str, service: Any):
    """Register a service in the global registry."""
    _registry.register(name, service)


