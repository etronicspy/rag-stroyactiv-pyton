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

from .base import Settings, get_settings
from .constants import (
    VectorSize,
    DefaultTimeouts,
    DefaultPorts,
    FileSizeLimits,
    DatabaseNames,
    ModelNames
)
from .database import DatabaseConfig
from .ai import AIConfig
from .factories import get_vector_db_client, get_ai_client
from .types import DatabaseType, AIProvider, LogLevel

# Global settings instance (backward compatibility)
settings = get_settings()

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
    "ModelNames"
] 