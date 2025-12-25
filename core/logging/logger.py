"""Logger."""

import logging
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logging(log_dir: Optional[Path] = None, level: str = "INFO"):
    """Setup logging."""
    if log_dir is None:
        log_dir = Path.home() / ".deepforge" / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, level),
        format='{"timestamp": "%(asctime)sZ", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler()
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger."""
    return logging.getLogger(f"deepforge.{name}")


