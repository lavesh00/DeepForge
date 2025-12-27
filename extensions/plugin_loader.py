"""Plugin loader for DeepForge extensions."""

import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PluginInfo:
    """Information about a loaded plugin."""
    name: str
    version: str
    description: str
    module: Any
    enabled: bool = True


class PluginLoader:
    """Load and manage plugins."""
    
    def __init__(self, plugin_dir: Path):
        """Initialize plugin loader."""
        self.plugin_dir = plugin_dir
        self._plugins: Dict[str, PluginInfo] = {}
    
    def discover(self) -> List[str]:
        """Discover available plugins."""
        if not self.plugin_dir.exists():
            return []
        
        plugins = []
        for path in self.plugin_dir.iterdir():
            if path.is_dir() and (path / "__init__.py").exists():
                plugins.append(path.name)
            elif path.suffix == ".py" and path.name != "__init__.py":
                plugins.append(path.stem)
        
        return plugins
    
    def load(self, plugin_name: str) -> Optional[PluginInfo]:
        """Load a plugin by name."""
        if plugin_name in self._plugins:
            return self._plugins[plugin_name]
        
        plugin_path = self.plugin_dir / plugin_name
        
        if plugin_path.is_dir():
            init_path = plugin_path / "__init__.py"
            if not init_path.exists():
                return None
            spec = importlib.util.spec_from_file_location(plugin_name, init_path)
        else:
            py_path = self.plugin_dir / f"{plugin_name}.py"
            if not py_path.exists():
                return None
            spec = importlib.util.spec_from_file_location(plugin_name, py_path)
        
        if spec is None or spec.loader is None:
            return None
        
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            info = PluginInfo(
                name=getattr(module, "__plugin_name__", plugin_name),
                version=getattr(module, "__version__", "0.0.1"),
                description=getattr(module, "__description__", ""),
                module=module
            )
            
            self._plugins[plugin_name] = info
            return info
        except Exception:
            return None
    
    def load_all(self) -> List[PluginInfo]:
        """Load all discovered plugins."""
        loaded = []
        for name in self.discover():
            info = self.load(name)
            if info:
                loaded.append(info)
        return loaded
    
    def get_plugin(self, name: str) -> Optional[PluginInfo]:
        """Get a loaded plugin."""
        return self._plugins.get(name)
    
    def list_loaded(self) -> List[str]:
        """List loaded plugin names."""
        return list(self._plugins.keys())
    
    def unload(self, name: str) -> bool:
        """Unload a plugin."""
        if name in self._plugins:
            del self._plugins[name]
            return True
        return False




