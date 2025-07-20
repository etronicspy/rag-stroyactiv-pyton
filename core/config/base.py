"""
Core configuration settings for RAG Construction Materials API.

This module contains the main Settings class and core application configuration.
It uses a modular approach with separate modules for different concerns.
"""

import os
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

from .ai import AIConfig
from .database import DatabaseConfig
from .type_definitions import AIProvider, DatabaseType, Environment


# Helper functions for environment variables
def get_env_int(key: str, default: int) -> int:
    """Get integer value from environment variable."""
    return int(os.getenv(key, str(default)))


def get_env_str(key: str, default: str) -> str:
    """Get string value from environment variable."""
    return os.getenv(key, default)


def get_env_float(key: str, default: float) -> float:
    """Get float value from environment variable."""
    return float(os.getenv(key, str(default)))


# Constants moved to environment variables
class VectorSize:
    """Standard vector dimensions for different embedding models."""
    OPENAI_SMALL = get_env_int("VECTOR_SIZE_OPENAI_SMALL", 1536)
    OPENAI_LARGE = get_env_int("VECTOR_SIZE_OPENAI_LARGE", 3072)
    OPENAI_ADA_002 = get_env_int("VECTOR_SIZE_OPENAI_ADA_002", 1536)
    HUGGINGFACE_MINI = get_env_int("VECTOR_SIZE_HUGGINGFACE_MINI", 384)
    HUGGINGFACE_BASE = get_env_int("VECTOR_SIZE_HUGGINGFACE_BASE", 768)


class DefaultTimeouts:
    """Default timeout values for various operations."""
    DATABASE = get_env_int("DEFAULT_TIMEOUT_DATABASE", 30)
    AI_CLIENT = get_env_int("DEFAULT_TIMEOUT_AI_CLIENT", 30)
    CONNECTION_POOL = get_env_int("DEFAULT_TIMEOUT_CONNECTION_POOL", 30)
    REDIS = get_env_int("DEFAULT_TIMEOUT_REDIS", 10)
    SSH_TUNNEL = get_env_int("DEFAULT_TIMEOUT_SSH_TUNNEL", 30)


class DefaultPorts:
    """Default port numbers for various services."""
    POSTGRESQL = get_env_int("DEFAULT_PORT_POSTGRESQL", 5432)
    REDIS = get_env_int("DEFAULT_PORT_REDIS", 6379)
    SSH_TUNNEL_LOCAL = get_env_int("DEFAULT_PORT_SSH_TUNNEL_LOCAL", 5435)


class FileSizeLimits:
    """File size limits for uploads and processing."""
    MAX_UPLOAD_BYTES = get_env_int("FILE_SIZE_MAX_UPLOAD_BYTES", 52428800)  # 50MB
    MAX_UPLOAD_MB = get_env_int("FILE_SIZE_MAX_UPLOAD_MB", 50)
    MAX_CONFIG_FILE_BYTES = get_env_int("FILE_SIZE_MAX_CONFIG_FILE_BYTES", 104857600)  # 100MB
    MAX_CONFIG_FILE_MB = get_env_int("FILE_SIZE_MAX_CONFIG_FILE_MB", 100)


class DatabaseNames:
    """Database and collection names."""
    QDRANT_COLLECTION = get_env_str("DATABASE_NAME_QDRANT_COLLECTION", "materials")
    WEAVIATE_CLASS = get_env_str("DATABASE_NAME_WEAVIATE_CLASS", "Material")
    PINECONE_INDEX = get_env_str("DATABASE_NAME_PINECONE_INDEX", "materials")
    POSTGRESQL_DB = get_env_str("DATABASE_NAME_POSTGRESQL_DB", "stbr_rag1")
    REDIS_KEY_PREFIX = get_env_str("DATABASE_NAME_REDIS_KEY_PREFIX", "rag:")


class ModelNames:
    """AI model names for different providers."""
    OPENAI_EMBEDDING = get_env_str("MODEL_NAME_OPENAI_EMBEDDING", "text-embedding-3-small")
    HUGGINGFACE_DEFAULT = get_env_str("MODEL_NAME_HUGGINGFACE_DEFAULT", "sentence-transformers/all-MiniLM-L6-v2")
    AZURE_API_VERSION = get_env_str("MODEL_NAME_AZURE_API_VERSION", "2023-05-15")


class ConnectionPools:
    """Connection pool configuration."""
    POSTGRESQL_POOL_SIZE = get_env_int("CONNECTION_POOL_POSTGRESQL_POOL_SIZE", 10)
    POSTGRESQL_MAX_OVERFLOW = get_env_int("CONNECTION_POOL_POSTGRESQL_MAX_OVERFLOW", 20)
    REDIS_MAX_CONNECTIONS = get_env_int("CONNECTION_POOL_REDIS_MAX_CONNECTIONS", 50)
    BATCH_SIZE = get_env_int("CONNECTION_POOL_BATCH_SIZE", 100)
    MAX_CONCURRENT_UPLOADS = get_env_int("CONNECTION_POOL_MAX_CONCURRENT_UPLOADS", 5)


class RateLimits:
    """Rate limiting configuration."""
    REQUESTS_PER_MINUTE = get_env_int("RATE_LIMIT_REQUESTS_PER_MINUTE", 60)
    REQUESTS_PER_HOUR = get_env_int("RATE_LIMIT_REQUESTS_PER_HOUR", 1000)
    BURST_LIMIT = get_env_int("RATE_LIMIT_BURST_LIMIT", 10)


class SSHDefaults:
    """SSH tunnel default configuration."""
    REMOTE_HOST = get_env_str("SSH_DEFAULT_REMOTE_HOST", "31.130.148.200")
    REMOTE_USER = get_env_str("SSH_DEFAULT_REMOTE_USER", "root")
    KEY_PATH = get_env_str("SSH_DEFAULT_KEY_PATH", "~/.ssh/postgres_key")
    RETRY_ATTEMPTS = get_env_int("SSH_DEFAULT_RETRY_ATTEMPTS", 3)
    RETRY_DELAY = get_env_int("SSH_DEFAULT_RETRY_DELAY", 5)
    KEEP_ALIVE = get_env_int("SSH_DEFAULT_KEEP_ALIVE", 60)


class CacheSettings:
    """Cache configuration settings."""
    REDIS_DEFAULT_TTL = get_env_int("CACHE_REDIS_DEFAULT_TTL", 3600)  # 1 hour


class ParserConstants:
    """Constants for parser operations."""
    DEFAULT_OPENAI_MODEL = get_env_str("PARSER_CONSTANT_DEFAULT_OPENAI_MODEL", "gpt-4o-mini")
    DEFAULT_EMBEDDING_MODEL = get_env_str("PARSER_CONSTANT_DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small")
    DEFAULT_EMBEDDING_DIMENSIONS = get_env_int("PARSER_CONSTANT_DEFAULT_EMBEDDING_DIMENSIONS", 1536)
    DEFAULT_BATCH_SIZE = get_env_int("PARSER_CONSTANT_DEFAULT_BATCH_SIZE", 10)
    MAX_BATCH_SIZE = get_env_int("PARSER_CONSTANT_MAX_BATCH_SIZE", 50)
    MIN_BATCH_SIZE = get_env_int("PARSER_CONSTANT_MIN_BATCH_SIZE", 1)
    DEFAULT_CONFIDENCE_THRESHOLD = get_env_float("PARSER_CONSTANT_DEFAULT_CONFIDENCE_THRESHOLD", 0.85)
    MIN_CONFIDENCE_THRESHOLD = get_env_float("PARSER_CONSTANT_MIN_CONFIDENCE_THRESHOLD", 0.1)
    MAX_CONFIDENCE_THRESHOLD = get_env_float("PARSER_CONSTANT_MAX_CONFIDENCE_THRESHOLD", 1.0)
    DEFAULT_PARSER_TIMEOUT = get_env_int("PARSER_CONSTANT_DEFAULT_PARSER_TIMEOUT", 30)
    DEFAULT_AI_REQUEST_TIMEOUT = get_env_int("PARSER_CONSTANT_DEFAULT_AI_REQUEST_TIMEOUT", 45)
    DEFAULT_BATCH_TIMEOUT = get_env_int("PARSER_CONSTANT_DEFAULT_BATCH_TIMEOUT", 300)
    DEFAULT_RETRY_ATTEMPTS = get_env_int("PARSER_CONSTANT_DEFAULT_RETRY_ATTEMPTS", 3)
    MAX_RETRY_ATTEMPTS = get_env_int("PARSER_CONSTANT_MAX_RETRY_ATTEMPTS", 10)
    DEFAULT_CACHE_TTL = get_env_int("PARSER_CONSTANT_DEFAULT_CACHE_TTL", 3600)  # 1 hour
    DEFAULT_EMBEDDING_CACHE_TTL = get_env_int("PARSER_CONSTANT_DEFAULT_EMBEDDING_CACHE_TTL", 86400)  # 24 hours


class Settings(BaseSettings):
    """Main application settings with environment variable support."""
    
    # === PROJECT SETTINGS ===
    PROJECT_NAME: str = Field(default="RAG Construction Materials API", description="Project name")
    VERSION: str = Field(default="1.0.0", description="API version")
    API_V1_STR: str = Field(default="/api/v1", description="API version string")
    
    # === OPENAPI DOCUMENTATION ===
    DESCRIPTION: str = """
    🏗️ **RAG Construction Materials API** - AI-Powered Semantic Search & Management System
    
    ## Features
    - 🔍 **Semantic Search**: AI-powered vector search for construction materials
    - 📊 **Reference Data**: Categories, units, and colors management
    - 📈 **Batch Processing**: Efficient bulk operations with progress tracking
    - 🔐 **Security**: Rate limiting, input validation, and CORS protection
    - 📝 **Documentation**: Interactive API documentation with examples
    
    ## Quick Start
    1. **Search Materials**: `GET /api/v1/materials/search?query=cement`
    2. **Create Category**: `POST /api/v1/reference/categories/`
    3. **Upload Prices**: `POST /api/v1/prices/upload`
    
    ## Authentication
    Currently supports API key authentication (configure via environment variables).
    
    ## Support
    For technical support, contact the development team.
    """
    
    CONTACT: Dict[str, str] = {
        "name": "RAG Construction Materials API Team",
        "email": "support@construction-materials-api.com",
        "url": "https://github.com/construction-materials-api"
    }
    
    LICENSE_INFO: Dict[str, str] = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    SERVERS: List[Dict[str, str]] = [
        {
            "url": "/",
            "description": "Current host"
        },
        {
            "url": "https://api.construction-materials.com",
            "description": "Production server"
        }
    ]
    
    OPENAPI_TAGS: List[Dict[str, str]] = [
        {
            "name": "materials",
            "description": "Material management operations"
        },
        {
            "name": "reference", 
            "description": "Reference data management (categories, units, colors)"
        },
        {
            "name": "prices",
            "description": "Price list processing and management"
        },
        {
            "name": "search",
            "description": "Semantic search operations"
        },
        {
            "name": "health",
            "description": "Health check and monitoring endpoints"
        },
        {
            "name": "tunnel",
            "description": "SSH tunnel management"
        }
    ]
    
    # === ENVIRONMENT ===
    ENVIRONMENT: str = Field(default="development", description="Application environment")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # === DATABASE CONFIGURATION ===
    # Qdrant Vector Database
    QDRANT_URL: str = Field(
        default="https://your-cluster.qdrant.tech:6333",
        description="Qdrant cluster URL"
    )
    QDRANT_API_KEY: str = Field(
        default="your_qdrant_api_key",
        description="Qdrant API key"
    )
    QDRANT_COLLECTION_NAME: str = Field(
        default=os.getenv("DATABASE_NAME_QDRANT_COLLECTION", "materials"),
        description="Qdrant collection name"
    )
    QDRANT_VECTOR_SIZE: int = Field(
        default=int(os.getenv("VECTOR_SIZE_OPENAI_SMALL", "1536")),
        description="Vector dimensions for embeddings"
    )
    QDRANT_TIMEOUT: int = Field(
        default=int(os.getenv("DEFAULT_TIMEOUT_DATABASE", "30")),
        description="Qdrant connection timeout"
    )
    
    # PostgreSQL Database
    POSTGRESQL_URL: str = Field(
        default="postgresql+asyncpg://user:pass@localhost:5432/stbr_rag1",
        description="PostgreSQL connection URL"
    )
    POSTGRESQL_DATABASE: str = Field(
        default=os.getenv("DATABASE_NAME_POSTGRESQL_DB", "stbr_rag1"),
        description="PostgreSQL database name"
    )
    POSTGRES_USER: str = Field(
        default=os.getenv("POSTGRES_USER", "user"), 
        description="PostgreSQL username"
    )
    POSTGRES_PASSWORD: str = Field(
        default=os.getenv("POSTGRES_PASSWORD", "pass"), 
        description="PostgreSQL password"
    )
    POSTGRESQL_HOST: str = Field(
        default=os.getenv("POSTGRES_HOST", "localhost"), 
        description="PostgreSQL host"
    )
    POSTGRESQL_PORT: int = Field(
        default=int(os.getenv("POSTGRES_PORT", os.getenv("DEFAULT_PORT_POSTGRESQL", "5432"))),
        description="PostgreSQL port"
    )
    POSTGRESQL_POOL_SIZE: int = Field(
        default=int(os.getenv("CONNECTION_POOL_POSTGRESQL_POOL_SIZE", "10")),
        description="PostgreSQL connection pool size"
    )
    POSTGRESQL_MAX_OVERFLOW: int = Field(
        default=int(os.getenv("CONNECTION_POOL_POSTGRESQL_MAX_OVERFLOW", "20")),
        description="PostgreSQL connection pool max overflow"
    )
    
    # Redis Cache
    REDIS_URL: str = Field(
        default=f"redis://localhost:{os.getenv('DEFAULT_PORT_REDIS', '6379')}",
        description="Redis connection URL"
    )
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_MAX_CONNECTIONS: int = Field(
        default=int(os.getenv("CONNECTION_POOL_REDIS_MAX_CONNECTIONS", "50")),
        description="Redis max connections"
    )
    REDIS_TIMEOUT: int = Field(
        default=int(os.getenv("DEFAULT_TIMEOUT_REDIS", "10")),
        description="Redis connection timeout"
    )
    
    # SSH Tunnel Configuration
    ENABLE_SSH_TUNNEL: bool = Field(default=False, description="Enable SSH tunnel")
    SSH_TUNNEL_LOCAL_PORT: int = Field(
        default=int(os.getenv("DEFAULT_PORT_SSH_TUNNEL_LOCAL", "5435")),
        description="SSH tunnel local port"
    )
    SSH_TUNNEL_REMOTE_HOST: str = Field(
        default=os.getenv("SSH_DEFAULT_REMOTE_HOST", "31.130.148.200"),
        description="SSH tunnel remote host"
    )
    SSH_TUNNEL_REMOTE_USER: str = Field(
        default=os.getenv("SSH_DEFAULT_REMOTE_USER", "root"),
        description="SSH tunnel remote user"
    )
    SSH_TUNNEL_REMOTE_PORT: int = Field(
        default=int(os.getenv("DEFAULT_PORT_POSTGRESQL", "5432")),
        description="SSH tunnel remote port"
    )
    SSH_TUNNEL_KEY_PATH: str = Field(
        default=os.getenv("SSH_DEFAULT_KEY_PATH", "~/.ssh/postgres_key"),
        description="SSH tunnel key path"
    )
    SSH_TUNNEL_TIMEOUT: int = Field(
        default=int(os.getenv("DEFAULT_TIMEOUT_SSH_TUNNEL", "30")),
        description="SSH tunnel connection timeout"
    )
    SSH_TUNNEL_RETRY_ATTEMPTS: int = Field(
        default=int(os.getenv("SSH_DEFAULT_RETRY_ATTEMPTS", "3")),
        description="SSH tunnel retry attempts"
    )
    SSH_TUNNEL_RETRY_DELAY: int = Field(
        default=int(os.getenv("SSH_DEFAULT_RETRY_DELAY", "5")),
        description="SSH tunnel retry delay"
    )
    SSH_TUNNEL_KEEP_ALIVE: int = Field(
        default=int(os.getenv("SSH_DEFAULT_KEEP_ALIVE", "60")),
        description="SSH tunnel keep alive interval"
    )
    SSH_TUNNEL_KEEP_ALIVE_INTERVAL: int = Field(
        default=int(os.getenv("SSH_DEFAULT_KEEP_ALIVE", "60")),
        description="SSH tunnel keep alive interval"
    )
    
    # === AI CONFIGURATION ===
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(
        default="sk-your_openai_api_key",
        description="OpenAI API key"
    )
    OPENAI_MODEL: str = Field(
        default=os.getenv("MODEL_NAME_OPENAI_EMBEDDING", "text-embedding-3-small"),
        description="OpenAI embedding model"
    )
    OPENAI_MAX_RETRIES: int = Field(
        default=int(os.getenv("PARSER_CONSTANT_DEFAULT_RETRY_ATTEMPTS", "3")),
        description="OpenAI max retry attempts"
    )
    OPENAI_TIMEOUT: int = Field(
        default=int(os.getenv("DEFAULT_TIMEOUT_AI_CLIENT", "30")),
        description="OpenAI request timeout"
    )
    
    # HuggingFace Configuration
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None, description="HuggingFace API key")
    HUGGINGFACE_MODEL: str = Field(
        default=os.getenv("MODEL_NAME_HUGGINGFACE_DEFAULT", "sentence-transformers/all-MiniLM-L6-v2"),
        description="HuggingFace model name"
    )
    
    # === DATABASE TYPE CONFIGURATION ===
    DATABASE_TYPE: DatabaseType = Field(
        default=DatabaseType.QDRANT_CLOUD,
        description="Primary vector database type"
    )
    AI_PROVIDER: AIProvider = Field(
        default=AIProvider.OPENAI,
        description="Primary AI provider for embeddings"
    )
    
    # === FEATURE FLAGS ===
    ENABLE_FALLBACK_DATABASES: bool = Field(
        default=True,
        description="Enable fallback to mock databases"
    )
    QDRANT_ONLY_MODE: bool = Field(
        default=False,
        description="Use only Qdrant database"
    )
    DISABLE_QDRANT_CONNECTION: bool = Field(
        default=True,
        description="Disable Qdrant connection"
    )
    DISABLE_REDIS_CONNECTION: bool = Field(
        default=True,
        description="Disable Redis connection"
    )
    DISABLE_POSTGRESQL_CONNECTION: bool = Field(
        default=False,
        description="Disable PostgreSQL connection"
    )
    
    # === PERFORMANCE SETTINGS ===
    MAX_UPLOAD_SIZE: int = Field(
        default=int(os.getenv("FILE_SIZE_MAX_UPLOAD_BYTES", "52428800")),
        description="Maximum upload size in bytes"
    )
    BATCH_SIZE: int = Field(
        default=int(os.getenv("CONNECTION_POOL_BATCH_SIZE", "100")),
        description="Batch processing size"
    )
    MAX_CONCURRENT_UPLOADS: int = Field(
        default=int(os.getenv("CONNECTION_POOL_MAX_CONCURRENT_UPLOADS", "5")),
        description="Maximum concurrent uploads"
    )
    
    # === SECURITY SETTINGS ===
    MAX_REQUEST_SIZE_MB: int = Field(
        default=int(os.getenv("FILE_SIZE_MAX_UPLOAD_MB", "50")),
        description="Maximum request size in MB"
    )
    ENABLE_SECURITY_HEADERS: bool = Field(
        default=True,
        description="Enable security headers"
    )
    ENABLE_INPUT_VALIDATION: bool = Field(
        default=True,
        description="Enable input validation"
    )
    
    # === RATE LIMITING ===
    ENABLE_RATE_LIMITING: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    RATE_LIMIT_RPM: int = Field(
        default=int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
        description="Requests per minute limit"
    )
    RATE_LIMIT_RPH: int = Field(
        default=int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "1000")),
        description="Requests per hour limit"
    )
    RATE_LIMIT_BURST: int = Field(
        default=int(os.getenv("RATE_LIMIT_BURST_LIMIT", "10")),
        description="Burst requests limit"
    )
    
    # === MODEL CONFIGURATION ===
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=[
            ".env.local",
            ".env.development",
            ".env.production",
            ".env"
        ],
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    # === VALIDATORS ===
    @field_validator('POSTGRESQL_DATABASE')
    def validate_postgresql_database(cls, v):
        """Validate PostgreSQL database name."""
        if v and v != os.getenv("DATABASE_NAME_POSTGRESQL_DB", "stbr_rag1"):
            raise ValueError(f'Only "{os.getenv("DATABASE_NAME_POSTGRESQL_DB", "stbr_rag1")}" database is allowed.')
        return v
    
    @field_validator('MAX_UPLOAD_SIZE')
    def validate_max_upload_size(cls, v):
        """Validate maximum upload size."""
        max_config_size = int(os.getenv("FILE_SIZE_MAX_CONFIG_FILE_BYTES", "104857600"))
        if v > max_config_size:
            max_mb = int(os.getenv("FILE_SIZE_MAX_CONFIG_FILE_MB", "100"))
            raise ValueError(f'MAX_UPLOAD_SIZE cannot exceed {max_mb}MB')
        return v
    
    # === CONFIGURATION FACTORIES ===
    def get_vector_db_config(self) -> Dict[str, Any]:
        """Get vector database configuration."""
        if self.DATABASE_TYPE in [DatabaseType.QDRANT_CLOUD, DatabaseType.QDRANT_LOCAL]:
            return DatabaseConfig.get_qdrant_config(
                url=self.QDRANT_URL,
                api_key=self.QDRANT_API_KEY,
                collection_name=self.QDRANT_COLLECTION_NAME,
                vector_size=self.QDRANT_VECTOR_SIZE,
                timeout=self.QDRANT_TIMEOUT
            )
        elif self.DATABASE_TYPE == DatabaseType.WEAVIATE:
            if not all([self.WEAVIATE_URL, self.WEAVIATE_API_KEY]):
                raise ValueError("Weaviate configuration incomplete")
            return DatabaseConfig.get_weaviate_config(
                url=self.WEAVIATE_URL,
                api_key=self.WEAVIATE_API_KEY,
                vector_size=self.QDRANT_VECTOR_SIZE
            )
        elif self.DATABASE_TYPE == DatabaseType.PINECONE:
            if not all([self.PINECONE_API_KEY, self.PINECONE_ENVIRONMENT]):
                raise ValueError("Pinecone configuration incomplete")
            return DatabaseConfig.get_pinecone_config(
                api_key=self.PINECONE_API_KEY,
                environment=self.PINECONE_ENVIRONMENT,
                vector_size=self.QDRANT_VECTOR_SIZE
            )
        
        raise ValueError(f"Unsupported database type: {self.DATABASE_TYPE}")
    
    def get_relational_db_config(self) -> Dict[str, Any]:
        """Get PostgreSQL configuration."""
        if self.POSTGRESQL_URL:
            connection_string = self.POSTGRESQL_URL
        else:
            connection_string = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRESQL_HOST}:{self.POSTGRESQL_PORT}/{self.POSTGRESQL_DATABASE}"
            )
        
        return DatabaseConfig.get_postgresql_config(
            connection_string=connection_string,
            pool_size=self.POSTGRESQL_POOL_SIZE,
            max_overflow=self.POSTGRESQL_MAX_OVERFLOW
        )
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        redis_url = self.REDIS_URL
        if self.REDIS_PASSWORD:
            redis_url = redis_url.replace("://", f"://:{self.REDIS_PASSWORD}@")
        
        return DatabaseConfig.get_redis_config(
            redis_url=redis_url,
            max_connections=self.REDIS_MAX_CONNECTIONS,
            timeout=self.REDIS_TIMEOUT
        )
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI provider configuration."""
        if self.AI_PROVIDER == AIProvider.OPENAI:
            return AIConfig.get_openai_config(
                api_key=self.OPENAI_API_KEY,
                model=self.OPENAI_MODEL,
                timeout=self.OPENAI_TIMEOUT,
                max_retries=self.OPENAI_MAX_RETRIES
            )
        elif self.AI_PROVIDER == AIProvider.AZURE_OPENAI:
            if not all([self.AZURE_OPENAI_API_KEY, self.AZURE_OPENAI_ENDPOINT, self.AZURE_OPENAI_MODEL]):
                raise ValueError("Azure OpenAI configuration incomplete")
            return AIConfig.get_azure_openai_config(
                api_key=self.AZURE_OPENAI_API_KEY,
                endpoint=self.AZURE_OPENAI_ENDPOINT,
                model=self.AZURE_OPENAI_MODEL
            )
        elif self.AI_PROVIDER == AIProvider.HUGGINGFACE:
            return AIConfig.get_huggingface_config(
                model=self.HUGGINGFACE_MODEL,
                device=self.HUGGINGFACE_DEVICE
            )
        elif self.AI_PROVIDER == AIProvider.OLLAMA:
            return AIConfig.get_ollama_config(
                url=self.OLLAMA_URL,
                model=self.OLLAMA_MODEL
            )
        
        raise ValueError(f"Unsupported AI provider: {self.AI_PROVIDER}")
    
    def get_ssh_tunnel_config(self) -> Dict[str, Any]:
        """Get SSH tunnel configuration."""
        return {
            "enabled": self.ENABLE_SSH_TUNNEL,
            "local_port": self.SSH_TUNNEL_LOCAL_PORT,
            "remote_host": self.SSH_TUNNEL_REMOTE_HOST,
            "remote_user": self.SSH_TUNNEL_REMOTE_USER,
            "remote_port": self.SSH_TUNNEL_REMOTE_PORT,
            "key_path": self.SSH_TUNNEL_KEY_PATH,
            "key_passphrase": self.SSH_TUNNEL_KEY_PASSPHRASE,
            "timeout": self.SSH_TUNNEL_TIMEOUT,
            "retry_attempts": self.SSH_TUNNEL_RETRY_ATTEMPTS,
            "retry_delay": self.SSH_TUNNEL_RETRY_DELAY,
            "heartbeat_interval": self.SSH_TUNNEL_HEARTBEAT_INTERVAL,
            "auto_restart": self.SSH_TUNNEL_AUTO_RESTART,
            "compression": self.SSH_TUNNEL_COMPRESSION,
            "keep_alive": self.SSH_TUNNEL_KEEP_ALIVE,
            "strict_host_key_checking": self.SSH_TUNNEL_STRICT_HOST_KEY_CHECKING
        }
    
    # === UTILITY METHODS ===
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    def is_testing(self) -> bool:
        """Check if running in test environment."""
        return self.ENVIRONMENT == Environment.TESTING
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    # 🚀 ЭТАП 4.7: PERFORMANCE OPTIMIZATION SETTINGS
    # Enable/disable performance optimizations  
    ENABLE_PERFORMANCE_OPTIMIZATION: bool = Field(default=True, description="Enable performance optimizations")
    ENABLE_LOG_BATCHING: bool = Field(default=True, description="Enable log batching")
    ENABLE_ASYNC_LOG_PROCESSING: bool = Field(default=True, description="Enable async log processing")
    
    # Logger caching settings
    LOG_CACHE_MAX_SIZE: int = Field(default=1000, description="Maximum logger cache size")
    LOG_CACHE_TTL: int = Field(default=CacheSettings.REDIS_DEFAULT_TTL, description="Logger cache TTL in seconds")
    
    # Batch processing settings
    LOG_BATCH_SIZE: int = Field(default=ConnectionPools.BATCH_SIZE, description="Log batch size")
    LOG_FLUSH_INTERVAL: float = Field(default=1.0, description="Log flush interval in seconds")
    LOG_MAX_QUEUE_SIZE: int = Field(default=10000, description="Maximum log queue size")
    
    # Performance thresholds
    LOG_SLOW_OPERATION_THRESHOLD_MS: int = Field(default=1000, description="Slow operation threshold in ms")
    LOG_BATCH_EFFICIENCY_THRESHOLD: float = Field(default=0.8, description="Batch efficiency threshold")
    
    # JSON serialization optimization
    ENABLE_JSON_SERIALIZATION_CACHE: bool = Field(default=True, description="Enable JSON serialization cache")
    JSON_CACHE_MAX_SIZE: int = Field(default=500, description="JSON cache maximum size")
    
    # Correlation ID optimization
    ENABLE_CORRELATION_ID_CACHE: bool = Field(default=True, description="Enable correlation ID cache")
    CORRELATION_CACHE_SIZE: int = Field(default=128, description="Correlation ID cache size")
    
    # Background processing
    LOG_BACKGROUND_PROCESSING_THREADS: int = Field(default=2, description="Background processing threads")
    LOG_BACKGROUND_FLUSH_INTERVAL: float = Field(default=0.1, description="Background flush interval")
    
    # Memory management
    LOG_MEMORY_LIMIT_MB: int = Field(default=100, description="Log memory limit in MB")
    LOG_ENABLE_MEMORY_MONITORING: bool = Field(default=True, description="Enable memory monitoring")
    
    # Performance metrics
    LOG_OPTIMIZATION_METRICS: bool = Field(default=True, description="Enable optimization metrics")
    LOG_CACHE_METRICS: bool = Field(default=True, description="Enable cache metrics")
    
    # 🎯 ЭТАП 5.6: Metrics Integration Settings
    ENABLE_METRICS_INTEGRATION: bool = Field(default=True, description="Enable metrics integration with logging")
    METRICS_COLLECTION_INTERVAL: float = Field(default=30.0, description="Metrics collection interval in seconds")
    METRICS_BATCH_SIZE: int = Field(default=ConnectionPools.BATCH_SIZE, description="Metrics batch size")
    METRICS_AUTO_EXPORT: bool = Field(default=True, description="Enable automatic metrics export")
    METRICS_EXPORT_INTERVAL: float = Field(default=60.0, description="Metrics export interval in seconds")
    METRICS_RETENTION_HOURS: int = Field(default=24, description="Metrics retention period in hours")
    ENABLE_APPLICATION_EVENT_METRICS: bool = Field(default=True, description="Enable application event metrics")
    ENABLE_HTTP_REQUEST_METRICS: bool = Field(default=True, description="Enable HTTP request metrics")
    ENABLE_DATABASE_OPERATION_METRICS: bool = Field(default=True, description="Enable database operation metrics")
    METRICS_CARDINALITY_LIMIT: int = Field(default=10000, description="Maximum metric cardinality")
    ENABLE_METRICS_SUMMARY: bool = Field(default=True, description="Enable metrics summary generation")

def get_settings() -> Settings:
    """
    Factory function to get settings instance.
    
    Supports automatic env file selection based on environment:
    - .env.local (local development, highest priority)
    - .env.development (dev environment)
    - .env.production (production environment)
    - .env (fallback)
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()

def get_environment_name() -> str:
    """
    Determine current environment from various indicators.
    
    Returns:
        str: Environment name (development, staging, production)
    """
    env = os.getenv('ENVIRONMENT', '').lower()
    if env in ['development', 'staging', 'production', 'testing']:
        return env
    
    # Check config files
    if os.path.exists('.env.production'):
        return 'production'
    elif os.path.exists('.env.staging'):
        return 'staging'
    elif os.path.exists('.env.development'):
        return 'development'
    else:
        return 'development'

def is_production() -> bool:
    """Check if running in production."""
    return get_environment_name() == 'production'

def is_development() -> bool:
    """Check if running in development."""
    return get_environment_name() == 'development' 