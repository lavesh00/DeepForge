"""Configuration loader."""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dataclasses import dataclass, field


@dataclass
class Config:
    """Configuration object."""
    
    _data: Dict[str, Any] = field(default_factory=dict)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get configuration section."""
        return self._data.get(section, {})
    
    def get_paths(self) -> Dict[str, Any]:
        """Get paths configuration."""
        paths = self._data.get("paths", {})
        if not paths:
            paths = {
                "workspace": {"base_dir": str(Path.home() / "deepforge_workspaces")},
                "state": {"missions": str(Path.home() / ".deepforge" / "state" / "missions")},
                "logs": {"dir": str(Path.home() / ".deepforge" / "logs")},
            }
        return paths


def load_config(config_dir: Optional[Path] = None) -> Config:
    """
    Load configuration.
    
    Args:
        config_dir: Configuration directory
        
    Returns:
        Config object
    """
    config = Config()
    
    if config_dir is None:
        config_dir = Path.home() / ".deepforge" / "config"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    
    defaults_file = config_dir / "defaults.yaml"
    if not defaults_file.exists():
        defaults_file.write_text("""paths:
  workspace:
    base_dir: ${HOME}/deepforge_workspaces
  state:
    missions: ${HOME}/.deepforge/state/missions
  logs:
    dir: ${HOME}/.deepforge/logs

models:
  max_memory_mb: 16384
  default_model: gpt2
""")
    
    if defaults_file.exists():
        with open(defaults_file) as f:
            data = yaml.safe_load(f) or {}
            config._data.update(data)
    
    return config

