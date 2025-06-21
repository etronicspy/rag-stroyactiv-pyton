"""
Configuration package for RAG Construction Materials API.

This package provides modular configuration management with separation of concerns:
- base: Core application settings
- database: Database configurations (Vector, PostgreSQL, Redis)
- ai: AI provider configurations
- security: Security and middleware settings  
- logging: Logging configuration
- factories: Client factory functions
- constants: Application constants
"""

from functools import lru_cache
from typing import Optional, Dict, Any
import os

from .base import Settings, get_settings, get_environment_name, is_production, is_development
from .constants import (
    VectorSize,
    DefaultTimeouts,
    DefaultPorts,
    FileSizeLimits,
    DatabaseNames,
    ModelNames,
    ConnectionPools,
    RateLimits
)
from .database import DatabaseConfig
from .ai import AIConfig
from .factories import get_vector_db_client, get_ai_client, get_relational_db_client, get_redis_client
from .type_definitions import DatabaseType, AIProvider, LogLevel
from .log_config import LoggingConfig

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
    # Main configuration
    "Settings",
    "get_settings", 
    "settings",
    
    # Configuration factories
    "DatabaseConfig",
    "AIConfig",
    
    # Client factories
    "get_vector_db_client",
    "get_ai_client",
    "get_relational_db_client",
    "get_redis_client",
    
    # Types and enums
    "DatabaseType",
    "AIProvider", 
    "LogLevel",
    
    # Constants
    "VectorSize",
    "DefaultTimeouts",
    "DefaultPorts",
    "FileSizeLimits",
    "DatabaseNames",
    "ModelNames",
    "logging_config",
    "get_logging_config",
    "get_environment_name",
    "is_production",
    "is_development"
] 