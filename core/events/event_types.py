"""Event types."""

from enum import Enum


class EventType(str, Enum):
    """Event type enumeration."""
    
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    
    MISSION_CREATED = "mission.created"
    MISSION_STARTED = "mission.started"
    MISSION_COMPLETED = "mission.completed"
    MISSION_FAILED = "mission.failed"
    MISSION_PAUSED = "mission.paused"
    MISSION_RESUMED = "mission.resumed"
    MISSION_CANCELLED = "mission.cancelled"
    
    PLAN_GENERATED = "plan.generated"
    
    STEP_STARTED = "step.started"
    STEP_COMPLETED = "step.completed"
    STEP_FAILED = "step.failed"
    STEP_APPROVAL_REQUIRED = "step.approval_required"
    
    CODE_GENERATED = "code.generated"
    CODE_MODIFIED = "code.modified"
    
    TEST_PASSED = "test.passed"
    TEST_FAILED = "test.failed"
    
    WORKSPACE_CREATED = "workspace.created"
    FILE_MODIFIED = "file.modified"


