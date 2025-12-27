"""Health checking for DeepForge components."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: str
    checked_at: datetime
    details: Optional[Dict] = None


class HealthChecker:
    """Check health of system components."""
    
    def __init__(self):
        """Initialize health checker."""
        self._components: Dict[str, callable] = {}
    
    def register(self, name: str, check_func: callable) -> None:
        """Register a component health check."""
        self._components[name] = check_func
    
    def check(self, name: str) -> ComponentHealth:
        """Check health of a specific component."""
        if name not in self._components:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="Component not registered",
                checked_at=datetime.now()
            )
        
        try:
            result = self._components[name]()
            
            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "OK" if result else "Failed"
                details = None
            elif isinstance(result, dict):
                status = HealthStatus(result.get("status", "unknown"))
                message = result.get("message", "")
                details = result.get("details")
            else:
                status = HealthStatus.UNKNOWN
                message = str(result)
                details = None
            
            return ComponentHealth(
                name=name,
                status=status,
                message=message,
                checked_at=datetime.now(),
                details=details
            )
        except Exception as e:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                checked_at=datetime.now()
            )
    
    def check_all(self) -> List[ComponentHealth]:
        """Check health of all registered components."""
        results = []
        for name in self._components:
            results.append(self.check(name))
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        results = self.check_all()
        
        if not results:
            return HealthStatus.UNKNOWN
        
        unhealthy = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        degraded = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
        
        if unhealthy > 0:
            return HealthStatus.UNHEALTHY
        elif degraded > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY




