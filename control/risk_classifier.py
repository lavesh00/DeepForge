"""Risk classifier for operations."""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class RiskCategory(Enum):
    """Risk categories."""
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    SYSTEM = "system"
    CODE_EXECUTION = "code_execution"
    DATA_ACCESS = "data_access"


@dataclass
class Classification:
    """Risk classification result."""
    level: str
    categories: List[RiskCategory]
    confidence: float
    explanation: str


class RiskClassifier:
    """Classify risk of operations."""
    
    CATEGORY_KEYWORDS = {
        RiskCategory.FILESYSTEM: [
            "file", "write", "read", "delete", "remove",
            "mkdir", "rmdir", "path", "directory"
        ],
        RiskCategory.NETWORK: [
            "http", "https", "socket", "request", "url",
            "download", "upload", "api", "fetch"
        ],
        RiskCategory.SYSTEM: [
            "subprocess", "os.", "sys.", "shell", "command",
            "execute", "run", "process"
        ],
        RiskCategory.CODE_EXECUTION: [
            "eval", "exec", "compile", "import", "__"
        ],
        RiskCategory.DATA_ACCESS: [
            "database", "sql", "query", "select", "insert",
            "password", "credential", "secret", "key"
        ]
    }
    
    def classify(
        self,
        operation: str,
        context: Dict[str, Any] = None
    ) -> Classification:
        """Classify an operation's risk."""
        if context is None:
            context = {}
        
        operation_lower = operation.lower()
        categories = []
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in operation_lower:
                    categories.append(category)
                    break
        
        if not categories:
            return Classification(
                level="low",
                categories=[],
                confidence=0.8,
                explanation="No high-risk patterns detected"
            )
        
        high_risk_categories = {
            RiskCategory.SYSTEM,
            RiskCategory.CODE_EXECUTION
        }
        
        if any(c in high_risk_categories for c in categories):
            level = "high"
        elif len(categories) > 2:
            level = "medium"
        else:
            level = "low"
        
        return Classification(
            level=level,
            categories=categories,
            confidence=0.7 + (0.1 * len(categories)),
            explanation=f"Detected categories: {[c.value for c in categories]}"
        )




