"""Environment detection for DeepForge."""

import platform
import os
import shutil
from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass
class EnvironmentInfo:
    """System environment information."""
    os_name: str
    os_version: str
    python_version: str
    architecture: str
    cpu_count: int
    memory_gb: float
    gpu_available: bool
    gpu_name: Optional[str]
    docker_available: bool
    wsl_available: bool
    git_available: bool
    installed_tools: Dict[str, str]


def detect_environment() -> EnvironmentInfo:
    """Detect the current system environment."""
    import sys
    
    os_name = platform.system()
    os_version = platform.version()
    python_version = sys.version
    architecture = platform.machine()
    cpu_count = os.cpu_count() or 1
    
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
    except ImportError:
        memory_gb = 0.0
    
    gpu_available, gpu_name = _detect_gpu()
    docker_available = _check_docker()
    wsl_available = _check_wsl() if os_name == "Windows" else False
    git_available = shutil.which("git") is not None
    
    installed_tools = _detect_tools()
    
    return EnvironmentInfo(
        os_name=os_name,
        os_version=os_version,
        python_version=python_version,
        architecture=architecture,
        cpu_count=cpu_count,
        memory_gb=round(memory_gb, 2),
        gpu_available=gpu_available,
        gpu_name=gpu_name,
        docker_available=docker_available,
        wsl_available=wsl_available,
        git_available=git_available,
        installed_tools=installed_tools
    )


def _detect_gpu() -> tuple[bool, Optional[str]]:
    """Detect GPU availability."""
    try:
        import torch
        if torch.cuda.is_available():
            return True, torch.cuda.get_device_name(0)
    except ImportError:
        pass
    return False, None


def _check_docker() -> bool:
    """Check if Docker is available."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_wsl() -> bool:
    """Check if WSL is available on Windows."""
    import subprocess
    try:
        result = subprocess.run(
            ["wsl", "--list", "--quiet"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _detect_tools() -> Dict[str, str]:
    """Detect installed development tools."""
    tools = {}
    tool_list = ["python", "pip", "git", "node", "npm", "docker", "cargo", "go"]
    
    for tool in tool_list:
        path = shutil.which(tool)
        if path:
            tools[tool] = path
    
    return tools


