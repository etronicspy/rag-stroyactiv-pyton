"""
Type definitions and enums for configuration management.

This module centralizes all configuration-related types and enums
to ensure consistency across the application.
"""

from enum import Enum

class DatabaseType(str, Enum):
    """Supported database types for vector storage."""
    QDRANT_CLOUD = "qdrant_cloud"
    QDRANT_LOCAL = "qdrant_local"
    WEAVIATE = "weaviate"
    PINECONE = "pinecone"

class AIProvider(str, Enum):
    """Supported AI providers for embedding generation."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"

class LogLevel(str, Enum):
    """Supported logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"  
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"
    TEST = "test"  # legacy alias for unit tests

class LogFormat(str, Enum):
    """Log output formats."""
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json" 