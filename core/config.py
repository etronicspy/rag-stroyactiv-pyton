import os
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field, ConfigDict, validator
from enum import Enum

class DatabaseType(str, Enum):
    """Supported database types"""
    QDRANT_CLOUD = "qdrant_cloud"
    QDRANT_LOCAL = "qdrant_local"
    WEAVIATE = "weaviate"
    PINECONE = "pinecone"

class AIProvider(str, Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"

class DatabaseConfig:
    """Database configuration factory for all database types"""
    
    @staticmethod
    def get_qdrant_config(url: str, api_key: str, collection_name: str = "materials", vector_size: int = 1536) -> Dict[str, Any]:
        return {
            "url": url,
            "api_key": api_key,
            "collection_name": collection_name,
            "vector_size": vector_size,
            "distance": "cosine",
            "timeout": 30
        }
    
    @staticmethod
    def get_postgresql_config(connection_string: str, pool_size: int = 10, max_overflow: int = 20) -> Dict[str, Any]:
        """PostgreSQL configuration factory.
        
        Args:
            connection_string: PostgreSQL connection string
            pool_size: Connection pool size
            max_overflow: Maximum pool overflow
            
        Returns:
            PostgreSQL configuration dictionary
        """
        return {
            "connection_string": connection_string,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "echo": False,  # Set to True for SQL logging
            "pool_timeout": 30,
            "pool_recycle": 3600
        }
    
    @staticmethod
    def get_redis_config(redis_url: str, max_connections: int = 10, retry_on_timeout: bool = True) -> Dict[str, Any]:
        """Redis configuration factory.
        
        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in pool
            retry_on_timeout: Whether to retry on timeout
            
        Returns:
            Redis configuration dictionary
        """
        return {
            "redis_url": redis_url,
            "max_connections": max_connections,
            "retry_on_timeout": retry_on_timeout,
            "socket_timeout": 30,
            "socket_connect_timeout": 30,
            "decode_responses": True,
            "health_check_interval": 30,
            "default_ttl": 3600,  # 1 hour
            "key_prefix": "rag_materials:"
        }
    
    @staticmethod
    def get_weaviate_config(url: str, api_key: str, class_name: str = "Materials", vector_size: int = 1536) -> Dict[str, Any]:
        """Weaviate configuration factory.
        
        Args:
            url: Weaviate instance URL
            api_key: Weaviate API key
            class_name: Weaviate class name for materials
            vector_size: Vector dimension size
            
        Returns:
            Weaviate configuration dictionary
        """
        return {
            "url": url,
            "api_key": api_key,
            "class_name": class_name,
            "vector_size": vector_size,
            "timeout": 30
        }
    
    @staticmethod
    def get_pinecone_config(api_key: str, environment: str, index_name: str = "materials", vector_size: int = 1536) -> Dict[str, Any]:
        """Pinecone configuration factory.
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment (e.g., 'us-west1-gcp')
            index_name: Pinecone index name
            vector_size: Vector dimension size
            
        Returns:
            Pinecone configuration dictionary
        """
        return {
            "api_key": api_key,
            "environment": environment,
            "index_name": index_name,
            "vector_size": vector_size,
            "timeout": 30
        }

class AIConfig:
    """AI provider configuration factory"""
    
    @staticmethod
    def get_openai_config(api_key: str, model: str = "text-embedding-ada-002") -> Dict[str, Any]:
        return {
            "api_key": api_key,
            "model": model,
            "max_retries": 3,
            "timeout": 30
        }
    
    @staticmethod
    def get_azure_openai_config(api_key: str, endpoint: str, model: str) -> Dict[str, Any]:
        return {
            "api_key": api_key,
            "endpoint": endpoint,
            "model": model,
            "api_version": "2023-05-15"
        }
    
    @staticmethod
    def get_huggingface_config(model: str = "sentence-transformers/all-MiniLM-L6-v2") -> Dict[str, Any]:
        return {
            "model": model,
            "device": "cpu"  # или "cuda" для GPU
        }

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "RAG Construction Materials API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = []
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    
    # === DATABASE CONFIGURATION ===
    # Vector Database
    DATABASE_TYPE: DatabaseType = Field(default=DatabaseType.QDRANT_CLOUD)
    
    # Qdrant settings
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION_NAME: str = "materials"
    QDRANT_VECTOR_SIZE: int = 1536
    QDRANT_TIMEOUT: int = 30
    
    # Alternative vector databases (для будущего использования)
    WEAVIATE_URL: Optional[str] = None
    WEAVIATE_API_KEY: Optional[str] = None
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    
    # === POSTGRESQL CONFIGURATION ===
    # PostgreSQL settings (будет реализовано в Этапе 3)
    POSTGRESQL_URL: Optional[str] = Field(default=None, description="PostgreSQL connection URL")
    POSTGRESQL_USER: Optional[str] = None
    POSTGRESQL_PASSWORD: Optional[str] = None
    POSTGRESQL_HOST: Optional[str] = "localhost"
    POSTGRESQL_PORT: int = 5432
    POSTGRESQL_DATABASE: Optional[str] = "materials"
    POSTGRESQL_POOL_SIZE: int = 10
    POSTGRESQL_MAX_OVERFLOW: int = 20
    
    # === REDIS CONFIGURATION ===
    # Redis settings (будет реализовано в Этапе 4)
    REDIS_URL: Optional[str] = Field(default="redis://localhost:6379", description="Redis connection URL")
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_TIMEOUT: int = 30
    
    # === SSH TUNNEL SERVICE CONFIGURATION ===
    # Автоматический запуск SSH туннеля как сервиса
    ENABLE_SSH_TUNNEL: bool = Field(default=False, description="Enable SSH tunnel service")
    SSH_TUNNEL_LOCAL_PORT: int = Field(default=5435, description="Local port for SSH tunnel")
    SSH_TUNNEL_REMOTE_HOST: str = Field(default="31.130.148.200", description="Remote host for SSH tunnel")
    SSH_TUNNEL_REMOTE_USER: str = Field(default="root", description="Remote user for SSH tunnel")
    SSH_TUNNEL_REMOTE_PORT: int = Field(default=5432, description="Remote port for SSH tunnel")
    SSH_TUNNEL_KEY_PATH: str = Field(default="~/.ssh/postgres_key", description="SSH private key path")
    SSH_TUNNEL_TIMEOUT: int = Field(default=30, description="SSH tunnel connection timeout")
    SSH_TUNNEL_RETRY_ATTEMPTS: int = Field(default=3, description="SSH tunnel retry attempts")
    SSH_TUNNEL_RETRY_DELAY: int = Field(default=5, description="SSH tunnel retry delay in seconds")
    SSH_TUNNEL_HEARTBEAT_INTERVAL: int = Field(default=60, description="SSH tunnel heartbeat check interval")
    SSH_TUNNEL_AUTO_RESTART: bool = Field(default=True, description="Auto restart SSH tunnel on failure")
    
    # === AI CONFIGURATION ===
    AI_PROVIDER: AIProvider = Field(default=AIProvider.OPENAI)
    
    # OpenAI settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "text-embedding-3-small"  # 1536 dimensions
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_TIMEOUT: int = 30
    
    # Azure OpenAI settings (для будущего использования)
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_MODEL: Optional[str] = None
    
    # HuggingFace settings (для будущего использования)
    HUGGINGFACE_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    HUGGINGFACE_DEVICE: str = "cpu"
    
    # Ollama settings (для будущего использования)  
    OLLAMA_URL: Optional[str] = None
    OLLAMA_MODEL: Optional[str] = None
    
    # === DATABASE INITIALIZATION SETTINGS ===
    AUTO_MIGRATE: bool = Field(default=True, description="Automatically run migrations on startup")
    AUTO_SEED: bool = Field(default=True, description="Automatically seed reference data on startup")
    
    # === FALLBACK SETTINGS ===
    QDRANT_ONLY_MODE: bool = Field(default=True, description="Use only Qdrant without other databases")
    ENABLE_FALLBACK_DATABASES: bool = Field(default=True, description="Enable fallback to mock databases")
    DISABLE_REDIS_CONNECTION: bool = Field(default=True, description="Disable Redis connection (use mocks)")
    DISABLE_POSTGRESQL_CONNECTION: bool = Field(default=True, description="Disable PostgreSQL connection (use mocks)") 
    
    # === PERFORMANCE SETTINGS ===
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    BATCH_SIZE: int = 100
    MAX_CONCURRENT_UPLOADS: int = 5
    
    # === MIDDLEWARE SETTINGS ===
    # Security settings
    MAX_REQUEST_SIZE_MB: int = Field(default=50, description="Maximum request size in MB")
    ENABLE_SECURITY_HEADERS: bool = Field(default=True, description="Enable security headers")
    ENABLE_INPUT_VALIDATION: bool = Field(default=True, description="Enable input validation")
    
    # Rate limiting settings
    ENABLE_RATE_LIMITING: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_RPM: int = Field(default=60, description="Requests per minute limit")
    RATE_LIMIT_RPH: int = Field(default=1000, description="Requests per hour limit") 
    RATE_LIMIT_BURST: int = Field(default=10, description="Burst requests limit")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")
    LOG_REQUEST_BODY: bool = Field(default=True, description="Log request bodies")
    LOG_RESPONSE_BODY: bool = Field(default=False, description="Log response bodies")
    ENABLE_STRUCTURED_LOGGING: bool = Field(default=False, description="Enable JSON structured logging")
    ENABLE_REQUEST_LOGGING: bool = Field(default=True, description="Enable request logging middleware")
    
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=[
            ".env.local",           # Локальная разработка (приоритет)
            ".env.development",     # Development среда
            ".env.production",      # Production среда  
            ".env"                  # Fallback
        ],
        env_file_encoding='utf-8'
    )
    
    # === VALIDATION ===
    @validator('QDRANT_URL')
    def validate_qdrant_url(cls, v):
        """Validate Qdrant URL format"""
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('QDRANT_URL must be a valid HTTP/HTTPS URL')
        return v
    
    @validator('OPENAI_API_KEY')
    def validate_openai_key(cls, v):
        """Validate OpenAI API key format"""
        if not v or not v.startswith('sk-'):
            raise ValueError('OPENAI_API_KEY must start with "sk-"')
        return v
    
    @validator('POSTGRESQL_URL', pre=True)
    def validate_postgresql_url(cls, v):
        """Validate PostgreSQL URL if provided"""
        if v and not v.startswith('postgresql'):
            raise ValueError('POSTGRESQL_URL must start with "postgresql://" or "postgresql+asyncpg://"')
        return v
    
    @validator('REDIS_URL', pre=True) 
    def validate_redis_url(cls, v):
        """Validate Redis URL if provided"""
        if v and not v.startswith('redis://'):
            raise ValueError('REDIS_URL must start with "redis://"')
        return v
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment values"""
        allowed_envs = ['development', 'staging', 'production', 'test', 'testing']
        if v.lower() not in allowed_envs:
            raise ValueError(f'ENVIRONMENT must be one of: {", ".join(allowed_envs)}')
        return v.lower()
    
    @validator('MAX_UPLOAD_SIZE')
    def validate_max_upload_size(cls, v):
        """Validate upload size is reasonable"""
        max_allowed = 100 * 1024 * 1024  # 100MB
        if v > max_allowed:
            raise ValueError(f'MAX_UPLOAD_SIZE cannot exceed {max_allowed} bytes (100MB)')
        return v
    
    # === CONFIGURATION FACTORIES ===
    def get_vector_db_config(self) -> Dict[str, Any]:
        """Get current vector database configuration"""
        if self.DATABASE_TYPE == DatabaseType.QDRANT_CLOUD or self.DATABASE_TYPE == DatabaseType.QDRANT_LOCAL:
            return DatabaseConfig.get_qdrant_config(
                url=self.QDRANT_URL,
                api_key=self.QDRANT_API_KEY,
                collection_name=self.QDRANT_COLLECTION_NAME,
                vector_size=self.QDRANT_VECTOR_SIZE
            )
        elif self.DATABASE_TYPE == DatabaseType.WEAVIATE:
            if not all([self.WEAVIATE_URL, self.WEAVIATE_API_KEY]):
                raise ValueError("Weaviate configuration is incomplete. WEAVIATE_URL and WEAVIATE_API_KEY are required.")
            return DatabaseConfig.get_weaviate_config(
                url=self.WEAVIATE_URL,
                api_key=self.WEAVIATE_API_KEY,
                class_name="Materials",
                vector_size=self.QDRANT_VECTOR_SIZE  # Use same vector size
            )
        elif self.DATABASE_TYPE == DatabaseType.PINECONE:
            if not all([self.PINECONE_API_KEY, self.PINECONE_ENVIRONMENT]):
                raise ValueError("Pinecone configuration is incomplete. PINECONE_API_KEY and PINECONE_ENVIRONMENT are required.")
            return DatabaseConfig.get_pinecone_config(
                api_key=self.PINECONE_API_KEY,
                environment=self.PINECONE_ENVIRONMENT,
                index_name="materials",
                vector_size=self.QDRANT_VECTOR_SIZE  # Use same vector size
            )
        
        raise ValueError(f"Unsupported database type: {self.DATABASE_TYPE}")
    
    def get_relational_db_config(self) -> Dict[str, Any]:
        """Get relational database configuration (PostgreSQL)"""
        if self.POSTGRESQL_URL:
            connection_string = self.POSTGRESQL_URL
        else:
            # Build connection string from components
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
        """Get Redis cache configuration"""
        redis_url = self.REDIS_URL
        if self.REDIS_PASSWORD:
            # Insert password into URL if provided
            redis_url = redis_url.replace("://", f"://:{self.REDIS_PASSWORD}@")
        
        return DatabaseConfig.get_redis_config(
            redis_url=redis_url,
            max_connections=self.REDIS_MAX_CONNECTIONS,
            retry_on_timeout=True
        )
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get current AI provider configuration"""
        if self.AI_PROVIDER == AIProvider.OPENAI:
            return AIConfig.get_openai_config(
                api_key=self.OPENAI_API_KEY,
                model=self.OPENAI_MODEL
            )
        elif self.AI_PROVIDER == AIProvider.AZURE_OPENAI:
            if not all([self.AZURE_OPENAI_API_KEY, self.AZURE_OPENAI_ENDPOINT, self.AZURE_OPENAI_MODEL]):
                raise ValueError("Azure OpenAI configuration is incomplete")
            return AIConfig.get_azure_openai_config(
                api_key=self.AZURE_OPENAI_API_KEY,
                endpoint=self.AZURE_OPENAI_ENDPOINT,
                model=self.AZURE_OPENAI_MODEL
            )
        elif self.AI_PROVIDER == AIProvider.HUGGINGFACE:
            return AIConfig.get_huggingface_config(model=self.HUGGINGFACE_MODEL)
        
        raise ValueError(f"Unsupported AI provider: {self.AI_PROVIDER}")
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_testing(self) -> bool:
        """Check if running in test environment"""
        return self.ENVIRONMENT.lower() in ["test", "testing"]

# === SETTINGS FACTORIES ===
def get_settings() -> Settings:
    """
    Factory function to get settings instance.
    
    Поддерживает автоматический выбор .env файла в зависимости от среды:
    - .env.local (для локальной разработки, высший приоритет)
    - .env.development (для dev среды)
    - .env.production (для production среды)
    - .env (fallback)
    
    Returns:
        Settings: Настройки приложения
    """
    return Settings()

# Global settings instance (для обратной совместимости)
settings = get_settings()

# === CLIENT FACTORIES ===
from functools import lru_cache

@lru_cache(maxsize=1)
def get_vector_db_client(settings: Settings = None):
    """Factory function to get vector database client with caching"""
    if settings is None:
        settings = get_settings()
        
    config = settings.get_vector_db_config()
    
    if settings.DATABASE_TYPE in [DatabaseType.QDRANT_CLOUD, DatabaseType.QDRANT_LOCAL]:
        from qdrant_client import QdrantClient
        return QdrantClient(
            url=config["url"],
            api_key=config["api_key"],
            timeout=config["timeout"]
        )
    
    raise ValueError(f"Unsupported database type: {settings.DATABASE_TYPE}")

@lru_cache(maxsize=1)
def get_ai_client(settings: Settings = None):
    """Factory function to get AI client with caching"""
    if settings is None:
        settings = get_settings()
        
    config = settings.get_ai_config()
    
    if settings.AI_PROVIDER == AIProvider.OPENAI:
        import openai
        return openai.AsyncOpenAI(
            api_key=config["api_key"],
            max_retries=config["max_retries"],
            timeout=config["timeout"]
        )
    elif settings.AI_PROVIDER == AIProvider.HUGGINGFACE:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(config["model"])
    
    raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")

# === ENVIRONMENT DETECTION ===
def get_environment_name() -> str:
    """
    Determine the current environment based on various indicators.
    
    Returns:
        str: Environment name (development, staging, production)
    """
    # Проверяем переменную окружения
    env = os.getenv('ENVIRONMENT', '').lower()
    if env in ['development', 'staging', 'production']:
        return env
        
    # Проверяем наличие файлов конфигурации
    if os.path.exists('.env.production'):
        return 'production'
    elif os.path.exists('.env.staging'):
        return 'staging'
    elif os.path.exists('.env.development'):
        return 'development'
    else:
        return 'development'  # default

def is_production() -> bool:
    """Check if running in production environment"""
    return get_environment_name() == 'production'

def is_development() -> bool:
    """Check if running in development environment"""
    return get_environment_name() == 'development' 