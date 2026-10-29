"""Validated backend configuration. Never imports a native client."""
from .runtime import ConfigManager, ConfigurationError, get_manager

__all__ = ['ConfigManager', 'ConfigurationError', 'get_manager']
