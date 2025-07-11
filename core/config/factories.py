"""
Client factory functions for database and AI providers.

This module provides cached factory functions for creating client instances
for various services used by the application.
"""

from functools import lru_cache
from typing import Optional

from .type_definitions import DatabaseType, AIProvider
from .base import Settings, get_settings

@lru_cache(maxsize=1)
def get_vector_db_client(settings: Optional[Settings] = None):
    """
    Factory function to get vector database client with caching.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        Vector database client instance
        
    Raises:
        ValueError: If unsupported database type
        ImportError: If required package not installed
    """
    if settings is None:
        settings = get_settings()
        
    config = settings.get_vector_db_config()
    
    if settings.DATABASE_TYPE in [DatabaseType.QDRANT_CLOUD, DatabaseType.QDRANT_LOCAL]:
        try:
            from qdrant_client import QdrantClient
            return QdrantClient(
                url=config["url"],
                api_key=config["api_key"],
                timeout=config["timeout"]
            )
        except ImportError:
            raise ImportError("qdrant-client package is required for Qdrant support")
    
    elif settings.DATABASE_TYPE == DatabaseType.WEAVIATE:
        try:
            import weaviate
            return weaviate.Client(
                url=config["url"],
                auth_client_secret=weaviate.AuthApiKey(api_key=config["api_key"]),
                timeout_config=(config["timeout"], config["timeout"])
            )
        except ImportError:
            raise ImportError("weaviate-client package is required for Weaviate support")
    
    elif settings.DATABASE_TYPE == DatabaseType.PINECONE:
        try:
            import pinecone
            pinecone.init(
                api_key=config["api_key"],
                environment=config["environment"]
            )
            return pinecone.Index(config["index_name"])
        except ImportError:
            raise ImportError("pinecone-client package is required for Pinecone support")
    
    raise ValueError(f"Unsupported database type: {settings.DATABASE_TYPE}")

@lru_cache(maxsize=1)
def get_ai_client(settings: Optional[Settings] = None):
    """
    Factory function to get AI client with caching.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        AI client instance
        
    Raises:
        ValueError: If unsupported AI provider
        ImportError: If required package not installed
    """
    if settings is None:
        settings = get_settings()
        
    config = settings.get_ai_config()
    
    if settings.AI_PROVIDER == AIProvider.OPENAI:
        try:
            import openai
            return openai.AsyncOpenAI(
                api_key=config["api_key"],
                max_retries=config["max_retries"],
                timeout=config["timeout"]
            )
        except ImportError:
            raise ImportError("openai package is required for OpenAI support")
    
    elif settings.AI_PROVIDER == AIProvider.AZURE_OPENAI:
        try:
            import openai
            return openai.AsyncAzureOpenAI(
                api_key=config["api_key"],
                azure_endpoint=config["endpoint"],
                api_version=config["api_version"],
                max_retries=config["max_retries"],
                timeout=config["timeout"]
            )
        except ImportError:
            raise ImportError("openai package is required for Azure OpenAI support")
    
    elif settings.AI_PROVIDER == AIProvider.HUGGINGFACE:
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer(
                config["model"],
                device=config["device"]
            )
        except ImportError:
            raise ImportError("sentence-transformers package is required for HuggingFace support")
    
    elif settings.AI_PROVIDER == AIProvider.OLLAMA:
        try:
            import ollama
            return ollama.Client(host=config["url"])
        except ImportError:
            raise ImportError("ollama package is required for Ollama support")
    
    raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")

@lru_cache(maxsize=1)
def get_redis_client(settings: Optional[Settings] = None):
    """
    Factory function to get Redis client with caching.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        Redis client instance
        
    Raises:
        ImportError: If redis package not installed
    """
    if settings is None:
        settings = get_settings()
    
    config = settings.get_redis_config()
    
    try:
        import redis.asyncio as redis
        return redis.from_url(
            config["redis_url"],
            max_connections=config["max_connections"],
            retry_on_timeout=config["retry_on_timeout"],
            socket_timeout=config["socket_timeout"],
            socket_connect_timeout=config["socket_connect_timeout"],
            decode_responses=config["decode_responses"],
            health_check_interval=config["health_check_interval"]
        )
    except ImportError:
        raise ImportError("redis package is required for Redis support")

@lru_cache(maxsize=1) 
def get_postgresql_engine(settings: Optional[Settings] = None):
    """
    Factory function to get PostgreSQL async engine with caching.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        SQLAlchemy async engine instance
        
    Raises:
        ImportError: If required packages not installed
    """
    if settings is None:
        settings = get_settings()
    
    config = settings.get_relational_db_config()
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        return create_async_engine(
            config["connection_string"],
            pool_size=config["pool_size"],
            max_overflow=config["max_overflow"],
            echo=config["echo"],
            pool_timeout=config["pool_timeout"],
            pool_recycle=config["pool_recycle"]
        )
    except ImportError:
        raise ImportError("sqlalchemy and asyncpg packages are required for PostgreSQL support")

@lru_cache(maxsize=1)
def get_parser_ai_client(settings: Optional[Settings] = None):
    """
    Factory function to get AI client specifically for parser operations.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        AI client instance configured for parsing
        
    Raises:
        ValueError: If unsupported AI provider
        ImportError: If required package not installed
    """
    if settings is None:
        settings = get_settings()
    
    # Use specific parser timeout and retry settings
    config = settings.get_ai_config()
    
    if settings.AI_PROVIDER == AIProvider.OPENAI:
        try:
            import openai
            return openai.AsyncOpenAI(
                api_key=config["api_key"],
                max_retries=config["max_retries"],
                timeout=45  # Parser-specific timeout
            )
        except ImportError:
            raise ImportError("openai package is required for OpenAI support")
    
    elif settings.AI_PROVIDER == AIProvider.AZURE_OPENAI:
        try:
            import openai
            return openai.AsyncAzureOpenAI(
                api_key=config["api_key"],
                azure_endpoint=config["endpoint"],
                api_version=config["api_version"],
                max_retries=config["max_retries"],
                timeout=45  # Parser-specific timeout
            )
        except ImportError:
            raise ImportError("openai package is required for Azure OpenAI support")
    
    # For other providers, use default AI client
    return get_ai_client(settings)

@lru_cache(maxsize=1)
def get_parser_embedding_client(settings: Optional[Settings] = None):
    """
    Factory function to get embedding client for parser operations.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        Embedding client instance
        
    Raises:
        ValueError: If unsupported AI provider
        ImportError: If required package not installed
    """
    # For now, use the same AI client but with different configuration
    return get_ai_client(settings)

def clear_client_cache():
    """Clear all cached client instances."""
    get_vector_db_client.cache_clear()
    get_ai_client.cache_clear()
    get_redis_client.cache_clear()
    get_postgresql_engine.cache_clear()
    get_parser_ai_client.cache_clear()
    get_parser_embedding_client.cache_clear()

def get_cache_info():
    """Get cache information for all client factories."""
    return {
        "vector_db_cache": get_vector_db_client.cache_info()._asdict(),
        "ai_client_cache": get_ai_client.cache_info()._asdict(),
        "redis_cache": get_redis_client.cache_info()._asdict(),
        "postgresql_cache": get_postgresql_engine.cache_info()._asdict(),
        "parser_ai_cache": get_parser_ai_client.cache_info()._asdict(),
        "parser_embedding_cache": get_parser_embedding_client.cache_info()._asdict()
    } 