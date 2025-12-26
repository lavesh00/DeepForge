"""
Model Router
Routes requests to appropriate model backend.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from .adapters.transformers_adapter import TransformersAdapter
from core.registry import get_service


class ModelRouter:
    """Routes model requests to appropriate backend."""
    
    def __init__(self, model_manager=None):
        """Initialize model router."""
        self._adapters: Dict[str, Any] = {}
        if model_manager is None:
            model_manager = get_service("model_manager")
        self.model_manager = model_manager
    
    def get_adapter(
        self,
        model_id: str,
        model_path: Optional[Path] = None,
        backend: Optional[str] = None
    ):
        """
        Get adapter for a model.
        
        Args:
            model_id: Model identifier
            model_path: Path to model (optional)
            backend: Backend type (optional)
            
        Returns:
            Model adapter instance
        """
        if model_id in self._adapters:
            return self._adapters[model_id]
        
        if model_path is None and self.model_manager:
            model_info = self.model_manager.get_model(model_id)
            if model_info and model_info.model_path:
                model_path = Path(model_info.model_path)
            else:
                model_path = None
        
        if backend is None:
            backend = self._detect_backend(model_path)
        
        adapter = self._create_adapter(backend, model_path, model_id)
        if adapter:
            self._adapters[model_id] = adapter
            return adapter
        
        raise ValueError(f"No suitable adapter found for {model_id}")
    
    def _detect_backend(self, model_path: Optional[Path]) -> str:
        """Detect appropriate backend."""
        if model_path and model_path.exists():
            if (model_path / "config.json").exists():
                return "transformers"
        
        return "transformers"
    
    def _create_adapter(
        self,
        backend: str,
        model_path: Optional[Path],
        model_id: str
    ):
        """Create adapter instance."""
        if backend == "transformers":
            try:
                adapter = TransformersAdapter(model_path=model_path, model_name=model_id)
                return adapter
            except Exception as e:
                return None
        
        return None



