"""
LEGACY CONFIGURATION FILE - BACKWARD COMPATIBILITY

This file is maintained for backward compatibility only.
New code should use the modular configuration from core.config package.

Example:
    from core.config import settings, get_settings
    from core.config import DatabaseType, AIProvider, LogLevel
"""

import warnings
from core.config import (
    Settings,
    get_settings,
    DatabaseType,
    AIProvider, 
    LogLevel,
    Environment,
    DatabaseConfig,
    AIConfig,
    VectorSize,
    DefaultTimeouts,
    get_vector_db_client,
    get_ai_client
)

# Issue deprecation warning
warnings.warn(
    "Direct import from core.config is deprecated. "
    "Use 'from core.config import settings' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Legacy global settings instance for backward compatibility
settings = get_settings()

# Re-export all the functionality from the new modular structure
__all__ = [
    "Settings", "get_settings", "settings",
    "DatabaseType", "AIProvider", "LogLevel", "Environment",
    "DatabaseConfig", "AIConfig", "VectorSize", "DefaultTimeouts",
    "get_vector_db_client", "get_ai_client"
]

# Note: All functionality now available through the modular configuration
# Example usage:
#   from core.config import settings
#   print(settings.QDRANT_URL) 