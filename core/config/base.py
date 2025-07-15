"""
Core configuration settings for RAG Construction Materials API.

This module contains the main Settings class and core application configuration.
It uses a modular approach with separate modules for different concerns.
"""

import os
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, field_validator

from .type_definitions import DatabaseType, AIProvider, Environment
from .constants import (
    VectorSize, 
    DefaultTimeouts, 
    DefaultPorts, 
    FileSizeLimits,
    DatabaseNames,
    ModelNames,
    ConnectionPools,
    RateLimits,
    SSHDefaults
)
from .database import DatabaseConfig
from .ai import AIConfig

class Settings(BaseSettings):
    """Main application settings with modular configuration."""
    
    # === PROJECT SETTINGS ===
    PROJECT_NAME: str = "RAG Construction Materials API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
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
    
    # === ENVIRONMENT SETTINGS ===
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT, 
        description="Application environment"
    )
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default_factory=list,
        description="CORS allowed origins"
    )
    
    # === VECTOR DATABASE CONFIGURATION ===
    DATABASE_TYPE: DatabaseType = Field(
        default=DatabaseType.QDRANT_CLOUD,
        description="Vector database type"
    )
    
    # Qdrant settings
    QDRANT_URL: str = Field(description="Qdrant instance URL")
    QDRANT_API_KEY: str = Field(description="Qdrant API key")
    QDRANT_COLLECTION_NAME: str = Field(
        default=DatabaseNames.QDRANT_COLLECTION,
        description="Qdrant collection name"
    )
    QDRANT_VECTOR_SIZE: int = Field(
        default=VectorSize.OPENAI_SMALL,
        description="Vector dimension size"
    )
    QDRANT_TIMEOUT: int = Field(
        default=DefaultTimeouts.DATABASE,
        description="Qdrant connection timeout"
    )
    
    # Alternative vector databases
    WEAVIATE_URL: Optional[str] = Field(default=None, description="Weaviate instance URL")
    WEAVIATE_API_KEY: Optional[str] = Field(default=None, description="Weaviate API key")
    PINECONE_API_KEY: Optional[str] = Field(default=None, description="Pinecone API key")
    PINECONE_ENVIRONMENT: Optional[str] = Field(default=None, description="Pinecone environment")
    
    # === POSTGRESQL CONFIGURATION ===
    POSTGRESQL_URL: Optional[str] = Field(
        default=None, 
        description="PostgreSQL connection URL"
    )
    POSTGRESQL_USER: Optional[str] = Field(default=None, description="PostgreSQL username")
    POSTGRESQL_PASSWORD: Optional[str] = Field(default=None, description="PostgreSQL password")
    POSTGRESQL_HOST: Optional[str] = Field(default="localhost", description="PostgreSQL host")
    POSTGRESQL_PORT: int = Field(default=DefaultPorts.POSTGRESQL, description="PostgreSQL port")
    POSTGRESQL_DATABASE: Optional[str] = Field(
        default=DatabaseNames.POSTGRESQL_DB,
        description="PostgreSQL database name"
    )
    POSTGRESQL_POOL_SIZE: int = Field(
        default=ConnectionPools.POSTGRESQL_POOL_SIZE,
        description="PostgreSQL connection pool size"
    )
    POSTGRESQL_MAX_OVERFLOW: int = Field(
        default=ConnectionPools.POSTGRESQL_MAX_OVERFLOW,
        description="PostgreSQL max pool overflow"
    )
    
    # === REDIS CONFIGURATION ===
    REDIS_URL: Optional[str] = Field(
        default=f"redis://localhost:{DefaultPorts.REDIS}",
        description="Redis connection URL"
    )
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_MAX_CONNECTIONS: int = Field(
        default=ConnectionPools.REDIS_MAX_CONNECTIONS,
        description="Redis max connections"
    )
    REDIS_TIMEOUT: int = Field(
        default=DefaultTimeouts.REDIS,
        description="Redis connection timeout"
    )
    
    # === SSH TUNNEL CONFIGURATION ===
    ENABLE_SSH_TUNNEL: bool = Field(
        default=False, 
        description="Enable SSH tunnel service"
    )
    SSH_TUNNEL_LOCAL_PORT: int = Field(
        default=DefaultPorts.SSH_TUNNEL_LOCAL,
        description="Local port for SSH tunnel"
    )
    SSH_TUNNEL_REMOTE_HOST: str = Field(
        default=SSHDefaults.REMOTE_HOST,
        description="Remote host for SSH tunnel"
    )
    SSH_TUNNEL_REMOTE_USER: str = Field(
        default=SSHDefaults.REMOTE_USER,
        description="Remote user for SSH tunnel"
    )
    SSH_TUNNEL_REMOTE_PORT: int = Field(
        default=DefaultPorts.POSTGRESQL,
        description="Remote port for SSH tunnel"
    )
    SSH_TUNNEL_KEY_PATH: str = Field(
        default=SSHDefaults.KEY_PATH,
        description="SSH private key path"
    )
    SSH_TUNNEL_KEY_PASSPHRASE: Optional[str] = Field(
        default=None,
        description="SSH key passphrase"
    )
    SSH_TUNNEL_TIMEOUT: int = Field(
        default=DefaultTimeouts.SSH_TUNNEL,
        description="SSH tunnel timeout"
    )
    SSH_TUNNEL_RETRY_ATTEMPTS: int = Field(
        default=SSHDefaults.RETRY_ATTEMPTS,
        description="SSH tunnel retry attempts"
    )
    SSH_TUNNEL_RETRY_DELAY: int = Field(
        default=SSHDefaults.RETRY_DELAY,
        description="SSH tunnel retry delay"
    )
    SSH_TUNNEL_HEARTBEAT_INTERVAL: int = Field(
        default=60,
        description="SSH tunnel heartbeat interval"
    )
    SSH_TUNNEL_AUTO_RESTART: bool = Field(
        default=True,
        description="Auto restart SSH tunnel"
    )
    SSH_TUNNEL_COMPRESSION: bool = Field(
        default=True,
        description="Enable SSH compression"
    )
    SSH_TUNNEL_KEEP_ALIVE: int = Field(
        default=SSHDefaults.KEEP_ALIVE,
        description="SSH keep alive interval"
    )
    SSH_TUNNEL_STRICT_HOST_KEY_CHECKING: bool = Field(
        default=False,
        description="Enable strict host key checking"
    )
    
    # === AI CONFIGURATION ===
    AI_PROVIDER: AIProvider = Field(
        default=AIProvider.OPENAI,
        description="AI provider for embeddings"
    )
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field(description="OpenAI API key")
    OPENAI_MODEL: str = Field(
        default=ModelNames.OPENAI_EMBEDDING,
        description="OpenAI embedding model"
    )
    OPENAI_MAX_RETRIES: int = Field(
        default=3,
        description="OpenAI max retries"
    )
    OPENAI_TIMEOUT: int = Field(
        default=DefaultTimeouts.AI_CLIENT,
        description="OpenAI request timeout"
    )
    
    # Azure OpenAI settings
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None, description="Azure OpenAI API key")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, description="Azure OpenAI endpoint")
    AZURE_OPENAI_MODEL: Optional[str] = Field(default=None, description="Azure OpenAI model")
    
    # HuggingFace settings
    HUGGINGFACE_MODEL: str = Field(
        default=ModelNames.HUGGINGFACE_DEFAULT,
        description="HuggingFace model name"
    )
    HUGGINGFACE_DEVICE: str = Field(
        default="cpu",
        description="HuggingFace device"
    )
    
    # Ollama settings
    OLLAMA_URL: Optional[str] = Field(default=None, description="Ollama server URL")
    OLLAMA_MODEL: Optional[str] = Field(default=None, description="Ollama model name")
    
    # === DATABASE INITIALIZATION ===
    AUTO_MIGRATE: bool = Field(
        default=True,
        description="Automatically run migrations"
    )
    AUTO_SEED: bool = Field(
        default=True,
        description="Automatically seed reference data"
    )
    
    # === FALLBACK SETTINGS ===
    QDRANT_ONLY_MODE: bool = Field(
        default=True,
        description="Use only Qdrant without other databases"
    )
    ENABLE_FALLBACK_DATABASES: bool = Field(
        default=True,
        description="Enable fallback to mock databases"
    )
    DISABLE_REDIS_CONNECTION: bool = Field(
        default=True,
        description="Disable Redis connection"
    )
    DISABLE_POSTGRESQL_CONNECTION: bool = Field(
        default=True,
        description="Disable PostgreSQL connection"
    )
    
    # === PERFORMANCE SETTINGS ===
    MAX_UPLOAD_SIZE: int = Field(
        default=FileSizeLimits.MAX_UPLOAD_BYTES,
        description="Maximum upload size in bytes"
    )
    BATCH_SIZE: int = Field(
        default=ConnectionPools.BATCH_SIZE,
        description="Batch processing size"
    )
    MAX_CONCURRENT_UPLOADS: int = Field(
        default=ConnectionPools.MAX_CONCURRENT_UPLOADS,
        description="Maximum concurrent uploads"
    )
    
    # === SECURITY SETTINGS ===
    MAX_REQUEST_SIZE_MB: int = Field(
        default=FileSizeLimits.MAX_UPLOAD_MB,
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
        default=RateLimits.REQUESTS_PER_MINUTE,
        description="Requests per minute limit"
    )
    RATE_LIMIT_RPH: int = Field(
        default=RateLimits.REQUESTS_PER_HOUR,
        description="Requests per hour limit"
    )
    RATE_LIMIT_BURST: int = Field(
        default=RateLimits.BURST_LIMIT,
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
        validate_assignment=True,
        extra='allow'
    )
    
    # === FIELD VALIDATORS ===
    @field_validator('QDRANT_URL')
    @classmethod
    def validate_qdrant_url(cls, v: str) -> str:
        """Validate Qdrant URL format."""
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('QDRANT_URL must be a valid HTTP/HTTPS URL')
        return v
    
    @field_validator('OPENAI_API_KEY')
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key format."""
        if not v or not v.startswith('sk-'):
            raise ValueError('OPENAI_API_KEY must start with "sk-"')
        return v
    
    @field_validator('POSTGRESQL_URL')
    @classmethod
    def validate_postgresql_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate PostgreSQL URL format."""
        if v and not v.startswith('postgresql'):
            raise ValueError('POSTGRESQL_URL must start with "postgresql://" or "postgresql+asyncpg://"')
        
        if v and '/stbr_rag1' not in v:
            raise ValueError('POSTGRESQL_URL must connect to stbr_rag1 database only!')
        
        return v
    
    @field_validator('POSTGRESQL_DATABASE')
    @classmethod
    def validate_postgresql_database(cls, v: Optional[str]) -> Optional[str]:
        """Validate PostgreSQL database name."""
        if v and v != DatabaseNames.POSTGRESQL_DB:
            raise ValueError(f'Only "{DatabaseNames.POSTGRESQL_DB}" database is allowed.')
        return v
    
    @field_validator('REDIS_URL')
    @classmethod
    def validate_redis_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate Redis URL format."""
        if v and not v.startswith('redis://'):
            raise ValueError('REDIS_URL must start with "redis://"')
        return v
    
    @field_validator('QDRANT_VECTOR_SIZE')
    @classmethod
    def validate_vector_size(cls, v: int) -> int:
        """Validate vector size."""
        valid_sizes = [size.value for size in VectorSize]
        if v not in valid_sizes:
            raise ValueError(f'QDRANT_VECTOR_SIZE must be one of: {valid_sizes}')
        return v
    
    @field_validator('MAX_UPLOAD_SIZE')
    @classmethod
    def validate_max_upload_size(cls, v: int) -> int:
        """Validate upload size is reasonable."""
        if v > FileSizeLimits.MAX_CONFIG_FILE_BYTES:
            raise ValueError(f'MAX_UPLOAD_SIZE cannot exceed {FileSizeLimits.MAX_CONFIG_FILE_MB}MB')
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
                f"postgresql+asyncpg://{self.POSTGRESQL_USER}:{self.POSTGRESQL_PASSWORD}"
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
    LOG_CACHE_TTL: int = Field(default=3600, description="Logger cache TTL in seconds")
    
    # Batch processing settings
    LOG_BATCH_SIZE: int = Field(default=100, description="Log batch size")
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
    METRICS_BATCH_SIZE: int = Field(default=500, description="Metrics batch size")
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