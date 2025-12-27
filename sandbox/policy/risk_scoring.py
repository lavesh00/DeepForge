"""Risk scoring for code execution."""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    level: RiskLevel
    score: float
    factors: List[str]
    requires_approval: bool


class RiskScorer:
    """Score risk of code execution operations."""
    
    HIGH_RISK_PATTERNS = [
        "subprocess", "os.system", "eval", "exec",
        "open(", "write(", "remove", "rmdir", "unlink",
        "shutil", "pathlib", "socket", "requests",
        "urllib", "http", "ftp", "ssh"
    ]
    
    CRITICAL_PATTERNS = [
        "rm -rf", "format", "del /", "deltree",
        "__import__", "importlib", "ctypes",
        "sys.exit", "os._exit"
    ]
    
    def __init__(self):
        """Initialize risk scorer."""
        self.approval_threshold = 0.6
    
    def assess(self, code: str, context: Dict[str, Any] = None) -> RiskAssessment:
        """Assess risk of code."""
        if context is None:
            context = {}
        
        factors = []
        score = 0.0
        
        code_lower = code.lower()
        
        for pattern in self.CRITICAL_PATTERNS:
            if pattern.lower() in code_lower:
                factors.append(f"Critical pattern: {pattern}")
                score += 0.4
        
        for pattern in self.HIGH_RISK_PATTERNS:
            if pattern.lower() in code_lower:
                factors.append(f"High-risk pattern: {pattern}")
                score += 0.15
        
        if "network" in context.get("capabilities", []):
            factors.append("Network access requested")
            score += 0.2
        
        if "filesystem" in context.get("capabilities", []):
            factors.append("Filesystem access requested")
            score += 0.1
        
        score = min(score, 1.0)
        
        if score >= 0.8:
            level = RiskLevel.CRITICAL
        elif score >= 0.6:
            level = RiskLevel.HIGH
        elif score >= 0.3:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        
        return RiskAssessment(
            level=level,
            score=score,
            factors=factors,
            requires_approval=score >= self.approval_threshold
        )




