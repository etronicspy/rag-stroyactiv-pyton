"""
Core configuration module for RAG Construction Materials API.

This module provides a centralized access point to all configuration settings.
"""

from functools import lru_cache

from .ai import AIConfig
from .base import (
    Settings,
    get_environment_name,
    get_settings,
    is_development,
    is_production,
)
from .database import DatabaseConfig
from .factories import (
    get_ai_client,
    get_postgresql_engine,
    get_redis_client,
    get_vector_db_client,
)
from .log_config import LoggingConfig
from .type_definitions import AIProvider, DatabaseType, LogLevel

# Global settings instance (backward compatibility)
settings = get_settings()

# Initialize logging config once for the application
@lru_cache
def get_logging_config() -> LoggingConfig:
    """
    Get logging configuration with environment variable overrides.
    
    Uses LRU cache to avoid re-parsing environment variables on each call.
    """
    return LoggingConfig()

logging_config = get_logging_config()

__all__ = [
    # Main settings
    "settings",
    "get_settings",
    
    # Factories
    "get_vector_db_client",
    "get_ai_client",
    "get_redis_client",
    "get_postgresql_engine",
    
    # Types and enums
    "DatabaseType",
    "AIProvider",
    "LogLevel",
    
    # Configuration classes
    "Settings",
    "DatabaseConfig",
    "AIConfig",
    
    # Logging
    "logging_config",
    "get_logging_config",
    "get_environment_name",
    "is_production",
    "is_development"
] 