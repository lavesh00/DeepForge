"""First-run setup wizard."""

from pathlib import Path
from typing import Dict, Any
from .env_detect import detect_environment


class FirstRunWizard:
    """Interactive first-run setup wizard."""
    
    def __init__(self, config_dir: Path):
        """Initialize wizard."""
        self.config_dir = config_dir
        self.completed = False
        self.settings: Dict[str, Any] = {}
    
    def run(self, interactive: bool = True) -> Dict[str, Any]:
        """Run the setup wizard."""
        env = detect_environment()
        
        self.settings = {
            "environment": {
                "os": env.os_name,
                "python": env.python_version,
                "gpu": env.gpu_available,
                "docker": env.docker_available,
            },
            "paths": {
                "workspace": str(Path.home() / "deepforge_workspaces"),
                "models": str(Path.home() / ".deepforge" / "models"),
                "cache": str(Path.home() / ".deepforge" / "cache"),
            },
            "execution": {
                "sandbox": "native" if not env.docker_available else "docker",
                "max_memory_mb": 8192,
                "timeout_seconds": 300,
            },
            "models": {
                "default_model": "code-generation",
                "max_loaded": 2,
            }
        }
        
        self._create_directories()
        self._save_config()
        self.completed = True
        
        return self.settings
    
    def _create_directories(self) -> None:
        """Create required directories."""
        for path in self.settings["paths"].values():
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def _save_config(self) -> None:
        """Save configuration."""
        import yaml
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.config_dir / "config.yaml"
        
        with open(config_file, "w") as f:
            yaml.dump(self.settings, f, default_flow_style=False)
    
    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        config_file = self.config_dir / "config.yaml"
        return not config_file.exists()


