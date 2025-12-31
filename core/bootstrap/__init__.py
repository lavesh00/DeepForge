"""Bootstrap module for system initialization."""

from .env_detect import detect_environment
from .first_run import FirstRunWizard

__all__ = ["detect_environment", "FirstRunWizard"]








