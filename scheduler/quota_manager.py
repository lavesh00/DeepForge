"""Quota manager."""

from typing import Dict, Any


class QuotaManager:
    """Manages resource quotas."""
    
    def __init__(self):
        """Initialize quota manager."""
        self._quotas: Dict[str, Dict[str, Any]] = {}
    
    def set_quota(self, resource_type: str, limit: int):
        """Set quota for resource type."""
        self._quotas[resource_type] = {"limit": limit, "used": 0}
    
    def check_quota(self, resource_type: str, amount: int = 1) -> bool:
        """Check if quota allows allocation."""
        if resource_type not in self._quotas:
            return True
        
        quota = self._quotas[resource_type]
        return quota["used"] + amount <= quota["limit"]




