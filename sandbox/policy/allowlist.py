"""Allowlist for safe operations."""

from typing import Set, List
from pathlib import Path


class Allowlist:
    """Manage allowed operations and paths."""
    
    SAFE_MODULES = {
        "json", "math", "datetime", "collections",
        "itertools", "functools", "dataclasses",
        "typing", "enum", "re", "string",
        "random", "hashlib", "base64", "uuid"
    }
    
    SAFE_BUILTINS = {
        "print", "len", "range", "enumerate", "zip",
        "map", "filter", "sorted", "reversed",
        "min", "max", "sum", "abs", "round",
        "str", "int", "float", "bool", "list",
        "dict", "set", "tuple", "type", "isinstance"
    }
    
    def __init__(self):
        """Initialize allowlist."""
        self._allowed_modules: Set[str] = set(self.SAFE_MODULES)
        self._allowed_paths: Set[Path] = set()
        self._allowed_commands: Set[str] = set()
    
    def add_module(self, module: str) -> None:
        """Add module to allowlist."""
        self._allowed_modules.add(module)
    
    def add_path(self, path: Path) -> None:
        """Add path to allowlist."""
        self._allowed_paths.add(path.resolve())
    
    def add_command(self, command: str) -> None:
        """Add command to allowlist."""
        self._allowed_commands.add(command)
    
    def is_module_allowed(self, module: str) -> bool:
        """Check if module is allowed."""
        return module in self._allowed_modules
    
    def is_path_allowed(self, path: Path) -> bool:
        """Check if path is allowed."""
        resolved = path.resolve()
        for allowed in self._allowed_paths:
            try:
                resolved.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False
    
    def is_command_allowed(self, command: str) -> bool:
        """Check if command is allowed."""
        return command.split()[0] in self._allowed_commands
    
    def get_allowed_modules(self) -> List[str]:
        """Get list of allowed modules."""
        return sorted(self._allowed_modules)




