"""Model downloader for HuggingFace models."""

from pathlib import Path
from typing import Optional, Callable


class ModelDownloader:
    """Downloads models from HuggingFace."""
    
    def __init__(self, cache_dir: Path):
        """
        Initialize model downloader.
        
        Args:
            cache_dir: Directory to cache downloaded models
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def download_model(
        self,
        model_name: str,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Path:
        """
        Download a model from HuggingFace.
        
        Args:
            model_name: HuggingFace model identifier (e.g., "deepseek-ai/deepseek-coder-1.3b-base")
            progress_callback: Optional callback for progress updates (message, progress)
            
        Returns:
            Path to downloaded model directory
        """
        model_dir = self.cache_dir / model_name.replace("/", "_")
        
        if model_dir.exists() and (model_dir / "config.json").exists():
            if progress_callback:
                progress_callback(f"Model {model_name} already downloaded", 1.0)
            return model_dir
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from huggingface_hub import snapshot_download
            
            if progress_callback:
                progress_callback(f"Downloading {model_name}...", 0.0)
            
            # Download using snapshot_download for better progress tracking
            snapshot_download(
                repo_id=model_name,
                cache_dir=str(self.cache_dir),
                local_dir=str(model_dir),
                local_dir_use_symlinks=False,
            )
            
            if progress_callback:
                progress_callback(f"Downloaded {model_name}", 1.0)
            
            return model_dir
            
        except ImportError:
            # Fallback: use transformers directly
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                
                if progress_callback:
                    progress_callback(f"Downloading {model_name} using transformers...", 0.0)
                
                # This will download and cache
                tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=str(self.cache_dir))
                model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=str(self.cache_dir))
                
                # Save to local directory
                model_dir.mkdir(parents=True, exist_ok=True)
                tokenizer.save_pretrained(str(model_dir))
                model.save_pretrained(str(model_dir))
                
                if progress_callback:
                    progress_callback(f"Downloaded {model_name}", 1.0)
                
                return model_dir
                
            except Exception as e:
                raise RuntimeError(f"Failed to download model {model_name}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to download model {model_name}: {e}")
    
    def is_downloaded(self, model_name: str) -> bool:
        """Check if model is already downloaded."""
        model_dir = self.cache_dir / model_name.replace("/", "_")
        return model_dir.exists() and (model_dir / "config.json").exists()
    
    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Get path to downloaded model."""
        model_dir = self.cache_dir / model_name.replace("/", "_")
        if model_dir.exists() and (model_dir / "config.json").exists():
            return model_dir
        return None

