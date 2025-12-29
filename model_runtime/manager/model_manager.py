"""
Model Manager
Manages AI model lifecycle, loading, and memory.
"""

from typing import Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import psutil
import os


class ModelState(Enum):
    """Model state."""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    ERROR = "error"


@dataclass
class ModelInfo:
    """Model information."""
    model_id: str
    model_path: Optional[Path] = None
    state: ModelState = ModelState.NOT_LOADED
    memory_mb: float = 0.0
    loaded_at: Optional[float] = None


class ModelManager:
    """Manages AI models."""
    
    def __init__(self, max_memory_mb: int = 16384):
        """
        Initialize model manager.
        
        Args:
            max_memory_mb: Maximum memory for models in MB
        """
        self.max_memory_mb = max_memory_mb
        self._models: Dict[str, ModelInfo] = {}
        self._loaded_models: Dict[str, any] = {}
    
    def register_model(
        self,
        model_id: str,
        model_path: Optional[Path] = None
    ):
        """
        Register a model.
        
        Args:
            model_id: Model identifier
            model_path: Path to model files
        """
        self._models[model_id] = ModelInfo(
            model_id=model_id,
            model_path=model_path,
            state=ModelState.NOT_LOADED
        )
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model info."""
        return self._models.get(model_id)
    
    def list_models(self) -> List[str]:
        """List all registered models."""
        return list(self._models.keys())
    
    def get_available_memory_mb(self) -> float:
        """Get available memory in MB."""
        return self.max_memory_mb - sum(
            m.memory_mb for m in self._models.values()
            if m.state == ModelState.LOADED
        )
    
    def can_load_model(self, estimated_memory_mb: float) -> bool:
        """Check if model can be loaded."""
        return self.get_available_memory_mb() >= estimated_memory_mb






