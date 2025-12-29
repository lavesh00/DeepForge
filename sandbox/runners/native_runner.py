"""Native code runner for local execution."""

import subprocess
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of code execution."""
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float


class NativeRunner:
    """Run code natively on the host system."""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize native runner."""
        self.working_dir = working_dir or Path.cwd()
    
    def execute(
        self,
        command: str,
        args: list = None,
        env: Dict[str, str] = None,
        timeout: float = 30.0
    ) -> ExecutionResult:
        """Execute a command natively."""
        import time
        
        if args is None:
            args = []
        
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [command] + args,
                cwd=str(self.working_dir),
                env=full_env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=duration_ms
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="Execution timed out",
                duration_ms=timeout * 1000
            )
        except FileNotFoundError:
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command not found: {command}",
                duration_ms=0
            )
    
    def run_python(
        self,
        script: str,
        args: list = None,
        timeout: float = 30.0
    ) -> ExecutionResult:
        """Run a Python script."""
        script_path = self.working_dir / "temp_script.py"
        script_path.write_text(script)
        
        try:
            result = self.execute(
                "python",
                [str(script_path)] + (args or []),
                timeout=timeout
            )
        finally:
            script_path.unlink(missing_ok=True)
        
        return result
    
    def validate_python(self, code: str) -> tuple[bool, str]:
        """Validate Python code syntax."""
        import py_compile
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            py_compile.compile(temp_path, doraise=True)
            return True, ""
        except py_compile.PyCompileError as e:
            return False, str(e)
        finally:
            Path(temp_path).unlink(missing_ok=True)






