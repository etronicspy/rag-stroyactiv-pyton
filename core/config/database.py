"""
Database configuration factories and utilities.

This module provides configuration factories for all supported databases:
- Vector databases: Qdrant, Weaviate, Pinecone
- Relational databases: PostgreSQL
- Cache databases: Redis
"""

from typing import Dict, Any
from .constants import (
    DefaultTimeouts, 
    DatabaseNames, 
    ConnectionPools, 
    CacheSettings
)

class BaseDatabaseConfig:
    """Base configuration class with common database settings."""
    
    @staticmethod
    def _get_base_config(timeout: int = None, **kwargs) -> Dict[str, Any]:
        """Get base configuration common to all databases.
        
        Args:
            timeout: Connection timeout in seconds
            **kwargs: Additional configuration parameters
            
        Returns:
            Base configuration dictionary
        """
        config = {
            "timeout": timeout or DefaultTimeouts.DATABASE,
        }
        config.update(kwargs)
        return config

class VectorDatabaseConfig(BaseDatabaseConfig):
    """Configuration factory for vector databases."""
    
    @staticmethod
    def get_qdrant_config(
        url: str, 
        api_key: str, 
        collection_name: str = None,
        vector_size: int = 1536,
        timeout: int = None
    ) -> Dict[str, Any]:
        """Get Qdrant configuration.
        
        Args:
            url: Qdrant instance URL
            api_key: Qdrant API key
            collection_name: Collection name for materials
            vector_size: Vector dimension size
            timeout: Connection timeout in seconds
            
        Returns:
            Qdrant configuration dictionary
        """
        base = VectorDatabaseConfig._get_base_config(
            timeout=timeout,
            distance="cosine"
        )
        
        return {
            **base,
            "url": url,
            "api_key": api_key,
            "collection_name": collection_name or DatabaseNames.QDRANT_COLLECTION,
            "vector_size": vector_size,
        }
    
    @staticmethod
    def get_weaviate_config(
        url: str, 
        api_key: str, 
        class_name: str = None,
        vector_size: int = 1536,
        timeout: int = None
    ) -> Dict[str, Any]:
        """Get Weaviate configuration.
        
        Args:
            url: Weaviate instance URL
            api_key: Weaviate API key
            class_name: Weaviate class name for materials
            vector_size: Vector dimension size
            timeout: Connection timeout in seconds
            
        Returns:
            Weaviate configuration dictionary
        """
        base = VectorDatabaseConfig._get_base_config(timeout=timeout)
        
        return {
            **base,
            "url": url,
            "api_key": api_key,
            "class_name": class_name or DatabaseNames.WEAVIATE_CLASS,
            "vector_size": vector_size,
        }
    
    @staticmethod
    def get_pinecone_config(
        api_key: str, 
        environment: str, 
        index_name: str = None,
        vector_size: int = 1536,
        timeout: int = None
    ) -> Dict[str, Any]:
        """Get Pinecone configuration.
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment (e.g., 'us-west1-gcp')
            index_name: Pinecone index name
            vector_size: Vector dimension size
            timeout: Connection timeout in seconds
            
        Returns:
            Pinecone configuration dictionary
        """
        base = VectorDatabaseConfig._get_base_config(timeout=timeout)
        
        return {
            **base,
            "api_key": api_key,
            "environment": environment,
            "index_name": index_name or DatabaseNames.PINECONE_INDEX,
            "vector_size": vector_size,
        }

class RelationalDatabaseConfig(BaseDatabaseConfig):
    """Configuration factory for relational databases."""
    
    @staticmethod
    def get_postgresql_config(
        connection_string: str, 
        pool_size: int = None, 
        max_overflow: int = None,
        timeout: int = None
    ) -> Dict[str, Any]:
        """Get PostgreSQL configuration.
        
        Args:
            connection_string: PostgreSQL connection string
            pool_size: Connection pool size
            max_overflow: Maximum pool overflow
            timeout: Connection timeout in seconds
            
        Returns:
            PostgreSQL configuration dictionary
        """
        base = RelationalDatabaseConfig._get_base_config(
            timeout=timeout or DefaultTimeouts.CONNECTION_POOL,
            echo=False  # Set to True for SQL logging
        )
        
        return {
            **base,
            "connection_string": connection_string,
            "pool_size": pool_size or ConnectionPools.POSTGRESQL_POOL_SIZE,
            "max_overflow": max_overflow or ConnectionPools.POSTGRESQL_MAX_OVERFLOW,
            "pool_timeout": DefaultTimeouts.CONNECTION_POOL,
            "pool_recycle": 3600  # 1 hour
        }

class CacheDatabaseConfig(BaseDatabaseConfig):
    """Configuration factory for cache databases."""
    
    @staticmethod
    def get_redis_config(
        redis_url: str, 
        max_connections: int = None, 
        retry_on_timeout: bool = True,
        timeout: int = None
    ) -> Dict[str, Any]:
        """Get Redis configuration.
        
        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in pool
            retry_on_timeout: Whether to retry on timeout
            timeout: Connection timeout in seconds
            
        Returns:
            Redis configuration dictionary
        """
        base = CacheDatabaseConfig._get_base_config(
            timeout=timeout,
            decode_responses=True
        )
        
        return {
            **base,
            "redis_url": redis_url,
            "max_connections": max_connections or ConnectionPools.REDIS_MAX_CONNECTIONS,
            "retry_on_timeout": retry_on_timeout,
            "socket_timeout": base["timeout"],
            "socket_connect_timeout": base["timeout"],
            "health_check_interval": CacheSettings.HEALTH_CHECK_INTERVAL,
            "default_ttl": CacheSettings.REDIS_DEFAULT_TTL,
            "key_prefix": DatabaseNames.REDIS_KEY_PREFIX
        }

class DatabaseConfig:
    """Unified database configuration factory."""
    
    # Vector databases
    get_qdrant_config = VectorDatabaseConfig.get_qdrant_config
    get_weaviate_config = VectorDatabaseConfig.get_weaviate_config
    get_pinecone_config = VectorDatabaseConfig.get_pinecone_config
    
    # Relational databases
    get_postgresql_config = RelationalDatabaseConfig.get_postgresql_config
    
    # Cache databases
    get_redis_config = CacheDatabaseConfig.get_redis_config 