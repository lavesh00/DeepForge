"""WSL-based sandbox runner for Windows."""

import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class WSLExecutionResult:
    """Result of WSL execution."""
    exit_code: int
    stdout: str
    stderr: str


class WSLRunner:
    """Run code in Windows Subsystem for Linux."""
    
    def __init__(self, distro: str = "Ubuntu"):
        """Initialize WSL runner."""
        self.distro = distro
        self._wsl_available = None
    
    def is_available(self) -> bool:
        """Check if WSL is available."""
        if self._wsl_available is not None:
            return self._wsl_available
        
        if platform.system() != "Windows":
            self._wsl_available = False
            return False
        
        try:
            result = subprocess.run(
                ["wsl", "--list", "--quiet"],
                capture_output=True,
                timeout=5
            )
            self._wsl_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._wsl_available = False
        
        return self._wsl_available
    
    def execute(
        self,
        command: str,
        working_dir: Optional[Path] = None,
        env: Dict[str, str] = None,
        timeout: float = 30.0
    ) -> WSLExecutionResult:
        """Execute command in WSL."""
        if not self.is_available():
            return WSLExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="WSL is not available"
            )
        
        wsl_cmd = ["wsl", "-d", self.distro]
        
        if working_dir:
            wsl_path = self._to_wsl_path(working_dir)
            full_command = f"cd {wsl_path} && {command}"
        else:
            full_command = command
        
        if env:
            env_str = " ".join(f"{k}={v}" for k, v in env.items())
            full_command = f"{env_str} {full_command}"
        
        wsl_cmd.extend(["bash", "-c", full_command])
        
        try:
            result = subprocess.run(
                wsl_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return WSLExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )
        except subprocess.TimeoutExpired:
            return WSLExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="Execution timed out"
            )
    
    def _to_wsl_path(self, windows_path: Path) -> str:
        """Convert Windows path to WSL path."""
        path_str = str(windows_path.absolute())
        if len(path_str) >= 2 and path_str[1] == ':':
            drive = path_str[0].lower()
            rest = path_str[2:].replace('\\', '/')
            return f"/mnt/{drive}{rest}"
        return path_str.replace('\\', '/')
    
    def run_python(
        self,
        script: str,
        timeout: float = 30.0
    ) -> WSLExecutionResult:
        """Run Python script in WSL."""
        escaped_script = script.replace("'", "'\"'\"'")
        command = f"python3 -c '{escaped_script}'"
        return self.execute(command, timeout=timeout)






