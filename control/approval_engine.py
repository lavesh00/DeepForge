"""Approval engine for risky operations."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid


class ApprovalStatus(Enum):
    """Approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


@dataclass
class ApprovalRequest:
    """Request for approval."""
    request_id: str
    operation: str
    description: str
    risk_level: str
    context: Dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    reason: Optional[str] = None


class ApprovalEngine:
    """Engine for managing approval requests."""
    
    def __init__(self, auto_approve_low_risk: bool = True):
        """Initialize approval engine."""
        self.auto_approve_low_risk = auto_approve_low_risk
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._history: List[ApprovalRequest] = []
    
    def request_approval(
        self,
        operation: str,
        description: str,
        risk_level: str,
        context: Dict[str, Any] = None
    ) -> ApprovalRequest:
        """Create an approval request."""
        request_id = str(uuid.uuid4())
        
        request = ApprovalRequest(
            request_id=request_id,
            operation=operation,
            description=description,
            risk_level=risk_level,
            context=context or {}
        )
        
        if self.auto_approve_low_risk and risk_level == "low":
            request.status = ApprovalStatus.AUTO_APPROVED
            request.resolved_at = datetime.now()
            request.reason = "Auto-approved low-risk operation"
            self._history.append(request)
        else:
            self._pending_requests[request_id] = request
        
        return request
    
    def approve(
        self,
        request_id: str,
        approved_by: str = "user",
        reason: str = None
    ) -> Optional[ApprovalRequest]:
        """Approve a pending request."""
        request = self._pending_requests.pop(request_id, None)
        if request:
            request.status = ApprovalStatus.APPROVED
            request.resolved_at = datetime.now()
            request.resolved_by = approved_by
            request.reason = reason
            self._history.append(request)
        return request
    
    def deny(
        self,
        request_id: str,
        denied_by: str = "user",
        reason: str = None
    ) -> Optional[ApprovalRequest]:
        """Deny a pending request."""
        request = self._pending_requests.pop(request_id, None)
        if request:
            request.status = ApprovalStatus.DENIED
            request.resolved_at = datetime.now()
            request.resolved_by = denied_by
            request.reason = reason
            self._history.append(request)
        return request
    
    def get_pending(self) -> List[ApprovalRequest]:
        """Get all pending requests."""
        return list(self._pending_requests.values())
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request."""
        return self._pending_requests.get(request_id)
    
    def is_approved(self, request_id: str) -> bool:
        """Check if request is approved."""
        for req in self._history:
            if req.request_id == request_id:
                return req.status in (ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED)
        return False




