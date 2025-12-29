"""Docker-based sandbox runner."""

import subprocess
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class DockerExecutionResult:
    """Result of Docker execution."""
    exit_code: int
    stdout: str
    stderr: str
    container_id: Optional[str] = None


class DockerRunner:
    """Run code in Docker containers for isolation."""
    
    def __init__(
        self,
        image: str = "python:3.9-slim",
        memory_limit: str = "512m",
        cpu_limit: float = 1.0
    ):
        """Initialize Docker runner."""
        self.image = image
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self._docker_available = None
    
    def is_available(self) -> bool:
        """Check if Docker is available."""
        if self._docker_available is not None:
            return self._docker_available
        
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                timeout=5
            )
            self._docker_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._docker_available = False
        
        return self._docker_available
    
    def execute(
        self,
        command: str,
        working_dir: Optional[Path] = None,
        env: Dict[str, str] = None,
        timeout: float = 30.0
    ) -> DockerExecutionResult:
        """Execute command in Docker container."""
        if not self.is_available():
            return DockerExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="Docker is not available"
            )
        
        docker_cmd = [
            "docker", "run",
            "--rm",
            f"--memory={self.memory_limit}",
            f"--cpus={self.cpu_limit}",
            "--network=none",
        ]
        
        if working_dir:
            docker_cmd.extend(["-v", f"{working_dir}:/app", "-w", "/app"])
        
        if env:
            for key, value in env.items():
                docker_cmd.extend(["-e", f"{key}={value}"])
        
        docker_cmd.extend([self.image, "sh", "-c", command])
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return DockerExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )
        except subprocess.TimeoutExpired:
            return DockerExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="Execution timed out"
            )
    
    def run_python(
        self,
        script: str,
        timeout: float = 30.0
    ) -> DockerExecutionResult:
        """Run Python script in container."""
        escaped_script = script.replace("'", "'\"'\"'")
        command = f"python -c '{escaped_script}'"
        return self.execute(command, timeout=timeout)






