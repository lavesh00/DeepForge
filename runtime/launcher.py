"""System launcher."""

from pathlib import Path
from typing import Optional
from core.config import load_config
from core.registry import ServiceRegistry
from core.events import get_event_bus
from core.logging import setup_logging, get_logger
from state.state_store_sqlite import SQLiteStateStore
from model_runtime.manager import ModelManager
from scheduler.mission_queue import MissionQueue
from scheduler.resource_allocator import ResourceAllocator
from scheduler.quota_manager import QuotaManager
from runtime.lifecycle import LifecycleManager

_config = None
_registry = None
_lifecycle = None
_event_bus = None
_logger = None


def launch_system(
    config_dir: Optional[Path] = None,
    skip_bootstrap: bool = False
):
    """Launch DeepForge system."""
    global _config, _registry, _lifecycle, _event_bus, _logger
    
    _config = load_config(config_dir)
    _registry = ServiceRegistry.get_instance()
    _lifecycle = LifecycleManager(_registry)
    _event_bus = get_event_bus()
    
    log_dir = Path(_config.get_paths().get("logs", {}).get("dir", ""))
    setup_logging(log_dir)
    _logger = get_logger("launcher")
    
    _logger.info("Starting DeepForge system")
    
    _initialize_services()
    
    from core.events import create_event, EventType
    _event_bus.publish(create_event(
        EventType.SYSTEM_STARTED,
        {"version": "0.1.0"},
        "launcher"
    ))
    
    _logger.info("DeepForge system started successfully")


def _initialize_services():
    """Initialize all system services."""
    global _config, _registry, _lifecycle, _event_bus, _logger
    
    paths = _config.get_paths()
    state_dir = Path(paths.get("state", {}).get("missions", ""))
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_store = SQLiteStateStore(state_dir / "state.db")
    _registry.register("state_store", state_store)
    
    model_config = _config.get_section("models")
    max_memory_mb = model_config.get("max_memory_mb", 16384)
    model_manager = ModelManager(max_memory_mb=max_memory_mb)
    
    # Setup DeepSeek model with auto-download (try v2 first, fallback to 1.3b)
    model_name = model_config.get("model_name", "deepseek-ai/deepseek-coder-v2-lite-instruct")
    fallback_model = model_config.get("fallback_model", "deepseek-ai/deepseek-coder-1.3b-base")
    auto_download = model_config.get("auto_download", True)
    default_model_id = model_config.get("default_model", "deepseek-coder")
    
    models_cache = Path(paths.get("models", {}).get("cache", Path.home() / ".deepforge" / "models"))
    models_cache.mkdir(parents=True, exist_ok=True)
    
    if auto_download:
        try:
            from model_runtime.download import ModelDownloader
            
            if _logger:
                _logger.info(f"Checking for DeepSeek model: {model_name}")
            
            downloader = ModelDownloader(models_cache)
            
            def progress_callback(message: str, progress: float):
                if _logger:
                    _logger.info(f"Model download: {message} ({progress*100:.1f}%)")
            
            # Try v2 first, fallback to 1.3b
            model_path = None
            if not downloader.is_downloaded(model_name):
                if _logger:
                    _logger.info(f"Attempting to download DeepSeek v2: {model_name}")
                try:
                    model_path = downloader.download_model(model_name, progress_callback)
                except Exception as e:
                    if _logger:
                        _logger.warning(f"Failed to download v2 model: {e}. Falling back to 1.3b.")
                    model_name = fallback_model
            else:
                model_path = downloader.get_model_path(model_name)
                if _logger:
                    _logger.info(f"DeepSeek model already downloaded: {model_path}")
            
            # If v2 failed, try fallback
            if not model_path and model_name != fallback_model:
                if _logger:
                    _logger.info(f"Trying fallback model: {fallback_model}")
                if not downloader.is_downloaded(fallback_model):
                    model_path = downloader.download_model(fallback_model, progress_callback)
                else:
                    model_path = downloader.get_model_path(fallback_model)
                    model_name = fallback_model
            
            if model_path:
                model_manager.register_model(default_model_id, model_path=model_path)
                if _logger:
                    _logger.info(f"Registered DeepSeek model: {default_model_id} at {model_path}")
            else:
                if _logger:
                    _logger.warning("Failed to download DeepSeek model, using placeholder")
                model_manager.register_model(default_model_id)
        except Exception as e:
            if _logger:
                _logger.warning(f"Failed to auto-download DeepSeek model: {e}")
            model_manager.register_model(default_model_id)
    else:
        model_manager.register_model(default_model_id)
    
    _registry.register("model_manager", model_manager)
    
    mission_queue = MissionQueue()
    _registry.register("mission_queue", mission_queue)
    
    resource_allocator = ResourceAllocator()
    _registry.register("resource_allocator", resource_allocator)
    
    quota_manager = QuotaManager()
    _registry.register("quota_manager", quota_manager)
    
    # Event bus is now managed by FastAPI lifespan
    # Don't register it here to avoid async issues
    
    _lifecycle.start_all()


def shutdown_system():
    """Shutdown DeepForge system."""
    global _lifecycle, _logger
    
    if _logger:
        _logger.info("Shutting down DeepForge system")
    
    if _lifecycle:
        _lifecycle.shutdown_all()
    
    # Event bus shutdown is handled by FastAPI lifespan

