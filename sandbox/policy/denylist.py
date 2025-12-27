"""Denylist for dangerous operations."""

from typing import Set, List
import re


class Denylist:
    """Manage denied operations and patterns."""
    
    DANGEROUS_MODULES = {
        "os", "subprocess", "shutil", "sys",
        "ctypes", "socket", "pickle", "marshal"
    }
    
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf",
        r"del\s+/[fs]",
        r"format\s+[a-z]:",
        r"__import__\s*\(",
        r"exec\s*\(",
        r"eval\s*\(",
        r"compile\s*\(",
        r"globals\s*\(",
        r"locals\s*\(",
        r"getattr\s*\(\s*__builtins__",
    ]
    
    def __init__(self):
        """Initialize denylist."""
        self._denied_modules: Set[str] = set(self.DANGEROUS_MODULES)
        self._denied_patterns: List[re.Pattern] = [
            re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS
        ]
    
    def add_module(self, module: str) -> None:
        """Add module to denylist."""
        self._denied_modules.add(module)
    
    def add_pattern(self, pattern: str) -> None:
        """Add pattern to denylist."""
        self._denied_patterns.append(re.compile(pattern, re.IGNORECASE))
    
    def is_module_denied(self, module: str) -> bool:
        """Check if module is denied."""
        return module in self._denied_modules
    
    def check_code(self, code: str) -> tuple[bool, List[str]]:
        """Check code for denied patterns."""
        violations = []
        
        for pattern in self._denied_patterns:
            if pattern.search(code):
                violations.append(f"Denied pattern: {pattern.pattern}")
        
        return len(violations) == 0, violations
    
    def get_denied_modules(self) -> List[str]:
        """Get list of denied modules."""
        return sorted(self._denied_modules)




