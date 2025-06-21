"""Database client factories with runtime switching and caching support.

Фабрики для создания клиентов различных БД с кешированием и runtime переключением.
"""

from functools import lru_cache
from typing import Optional, Dict, Any
from core.logging import get_logger
from enum import Enum

from core.config import settings, DatabaseType, AIProvider
from core.database.interfaces import IVectorDatabase, IRelationalDatabase, ICacheDatabase
from core.database.exceptions import ConfigurationError, ConnectionError
from core.database.mocks import (
    create_mock_redis_client, 
    create_mock_postgresql_database,
    MockRedisClient,
    MockPostgreSQLAdapter
)
from core.database.adapters.mock_adapters import (
    create_mock_relational_adapter,
    create_mock_cache_adapter
)


logger = get_logger(__name__)


class DatabaseFactory:
    """Factory for creating database clients with runtime switching support.
    
    Фабрика для создания клиентов БД с поддержкой runtime переключения
    и кеширования подключений через @lru_cache.
    """
    
    @staticmethod
    @lru_cache(maxsize=10)
    def create_vector_database(
        db_type: str = None,
        config_override: Optional[Dict[str, Any]] = None
    ) -> IVectorDatabase:
        """Create vector database client with caching.
        
        Args:
            db_type: Database type override (qdrant_cloud, qdrant_local, weaviate, pinecone)
            config_override: Optional configuration override
            
        Returns:
            Vector database client instance
            
        Raises:
            ConfigurationError: If configuration is invalid
            ConnectionError: If connection fails
        """
        try:
            # Use override or default from settings
            database_type = db_type or settings.DATABASE_TYPE.value
            config = config_override or settings.get_vector_db_config()
            
            logger.info(f"Creating vector database client: {database_type}")
            
            if database_type in [DatabaseType.QDRANT_CLOUD.value, DatabaseType.QDRANT_LOCAL.value]:
                return DatabaseFactory._create_qdrant_client(config)
            elif database_type == DatabaseType.WEAVIATE.value:
                return DatabaseFactory._create_weaviate_client(config)
            elif database_type == DatabaseType.PINECONE.value:
                return DatabaseFactory._create_pinecone_client(config)
            else:
                raise ConfigurationError(
                    config_key="DATABASE_TYPE",
                    message=f"Unsupported vector database type: {database_type}"
                )
                
        except Exception as e:
            logger.error(f"Failed to create vector database client: {e}")
            if isinstance(e, (ConfigurationError, ConnectionError)):
                raise
            else:
                raise ConnectionError(
                    database_type=database_type,
                    message="Failed to create vector database client",
                    details=str(e)
                )
    
    @staticmethod
    @lru_cache(maxsize=5)
    def create_relational_database(
        connection_string: str = None,
        config_override: Optional[Dict[str, Any]] = None
    ) -> IRelationalDatabase:
        """Create relational database client with caching and fallback support.
        
        Args:
            connection_string: Database connection string override
            config_override: Optional configuration override
            
        Returns:
            Relational database client instance (real or mock)
            
        Raises:
            ConfigurationError: If configuration is invalid
            ConnectionError: If connection fails and fallback is disabled
        """
        # Check if PostgreSQL connection is disabled
        if getattr(settings, 'DISABLE_POSTGRESQL_CONNECTION', True):
            logger.info("PostgreSQL connection disabled, using mock database")
            return create_mock_relational_adapter()
        
        # Check if we're in Qdrant-only mode
        if getattr(settings, 'QDRANT_ONLY_MODE', True):
            logger.info("Qdrant-only mode enabled, using mock PostgreSQL database")
            return create_mock_relational_adapter()
        
        try:
            if config_override:
                config = config_override
            elif connection_string:
                config = {"connection_string": connection_string}
            else:
                # Use settings configuration
                config = settings.get_relational_db_config()
            
            logger.info("Creating relational database client (PostgreSQL)")
            
            # Import here to avoid circular imports
            from core.database.adapters.postgresql_adapter import PostgreSQLAdapter
            return PostgreSQLAdapter(config)
            
        except Exception as e:
            logger.error(f"Failed to create relational database client: {e}")
            
            # Use fallback if enabled
            if getattr(settings, 'ENABLE_FALLBACK_DATABASES', True):
                logger.warning("Using mock PostgreSQL database as fallback")
                return create_mock_relational_adapter()
                
            if isinstance(e, NotImplementedError):
                raise e  # Pass through NotImplementedError
            raise ConnectionError(
                database_type="PostgreSQL",
                message="Failed to create relational database client",
                details=str(e)
            )
    
    @staticmethod
    @lru_cache(maxsize=5)  
    def create_cache_database(
        redis_url: str = None,
        config_override: Optional[Dict[str, Any]] = None
    ) -> ICacheDatabase:
        """Create cache database client with caching and fallback support.
        
        Args:
            redis_url: Redis connection URL override
            config_override: Optional configuration override
            
        Returns:
            Cache database client instance (real or mock)
            
        Raises:
            ConfigurationError: If configuration is invalid
            ConnectionError: If connection fails and fallback is disabled
        """
        # Check if Redis connection is disabled
        if getattr(settings, 'DISABLE_REDIS_CONNECTION', True):
            logger.info("Redis connection disabled, using mock cache")
            return create_mock_cache_adapter()
        
        # Check if we're in Qdrant-only mode
        if getattr(settings, 'QDRANT_ONLY_MODE', True):
            logger.info("Qdrant-only mode enabled, using mock Redis cache")
            return create_mock_cache_adapter()
        
        try:
            config = config_override or {
                "redis_url": redis_url or "redis://localhost:6379"
            }
            
            logger.info("Creating cache database client (Redis)")
            
            # Import here to avoid circular imports
            from core.database.adapters.redis_adapter import RedisDatabase
            return RedisDatabase(config)
            
        except Exception as e:
            logger.error(f"Failed to create cache database client: {e}")
            
            # Use fallback if enabled
            if getattr(settings, 'ENABLE_FALLBACK_DATABASES', True):
                logger.warning("Using mock Redis cache as fallback")
                return create_mock_cache_adapter()
                
            if isinstance(e, NotImplementedError):
                raise e  # Pass through NotImplementedError
            raise ConnectionError(
                database_type="Redis",
                message="Failed to create cache database client",
                details=str(e)
            )
    
    @staticmethod
    def _create_qdrant_client(config: Dict[str, Any]) -> IVectorDatabase:
        """Create Qdrant client instance.
        
        Args:
            config: Qdrant configuration
            
        Returns:
            Qdrant vector database client
        """
        from core.database.adapters.qdrant_adapter import QdrantVectorDatabase
        return QdrantVectorDatabase(config)
    
    @staticmethod
    def _create_weaviate_client(config: Dict[str, Any]) -> IVectorDatabase:
        """Create Weaviate client instance.
        
        Args:
            config: Weaviate configuration
            
        Returns:
            Weaviate vector database client
        """
        from core.database.adapters.weaviate_adapter import WeaviateVectorDatabase
        return WeaviateVectorDatabase(config)
    
    @staticmethod
    def _create_pinecone_client(config: Dict[str, Any]) -> IVectorDatabase:
        """Create Pinecone client instance.
        
        Args:
            config: Pinecone configuration
            
        Returns:
            Pinecone vector database client
        """
        from core.database.adapters.pinecone_adapter import PineconeVectorDatabase
        return PineconeVectorDatabase(config)
    
    @staticmethod
    def clear_cache() -> None:
        """Clear all cached database clients.
        
        Полезно для тестирования или при изменении конфигурации.
        """
        logger.info("Clearing database client caches")
        DatabaseFactory.create_vector_database.cache_clear()
        DatabaseFactory.create_relational_database.cache_clear()
        DatabaseFactory.create_cache_database.cache_clear()
    
    @staticmethod
    def get_cache_info() -> Dict[str, Any]:
        """Get information about cached database clients.
        
        Returns:
            Cache statistics for monitoring
        """
        return {
            "vector_db_cache": DatabaseFactory.create_vector_database.cache_info()._asdict(),
            "relational_db_cache": DatabaseFactory.create_relational_database.cache_info()._asdict(),
            "cache_db_cache": DatabaseFactory.create_cache_database.cache_info()._asdict(),
        }


class AIClientFactory:
    """Factory for creating AI provider clients with caching support.
    
    Фабрика для создания клиентов AI провайдеров с кешированием.
    """
    
    @staticmethod
    @lru_cache(maxsize=5)
    def create_ai_client(
        provider: str = None,
        config_override: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Create AI client with caching.
        
        Args:
            provider: AI provider override (openai, azure_openai, huggingface, ollama)
            config_override: Optional configuration override
            
        Returns:
            AI client instance
            
        Raises:
            ConfigurationError: If configuration is invalid
            ConnectionError: If connection fails
        """
        try:
            # Use override or default from settings
            ai_provider = provider or settings.AI_PROVIDER.value
            config = config_override or settings.get_ai_config()
            
            logger.info(f"Creating AI client: {ai_provider}")
            
            if ai_provider == AIProvider.OPENAI.value:
                return AIClientFactory._create_openai_client(config)
            elif ai_provider == AIProvider.AZURE_OPENAI.value:
                return AIClientFactory._create_azure_openai_client(config)
            elif ai_provider == AIProvider.HUGGINGFACE.value:
                return AIClientFactory._create_huggingface_client(config)
            elif ai_provider == AIProvider.OLLAMA.value:
                return AIClientFactory._create_ollama_client(config)
            else:
                raise ConfigurationError(
                    config_key="AI_PROVIDER",
                    message=f"Unsupported AI provider: {ai_provider}"
                )
                
        except Exception as e:
            logger.error(f"Failed to create AI client: {e}")
            if isinstance(e, (ConfigurationError, ConnectionError)):
                raise
            else:
                raise ConnectionError(
                    database_type=f"AI:{ai_provider}",
                    message="Failed to create AI client",
                    details=str(e)
                )
    
    @staticmethod
    def _create_openai_client(config: Dict[str, Any]) -> Any:
        """Create OpenAI client instance."""
        import openai
        return openai.AsyncOpenAI(
            api_key=config["api_key"],
            max_retries=config.get("max_retries", 3),
            timeout=config.get("timeout", 30)
        )
    
    @staticmethod
    def _create_azure_openai_client(config: Dict[str, Any]) -> Any:
        """Create Azure OpenAI client instance."""
        import openai
        return openai.AsyncAzureOpenAI(
            api_key=config["api_key"],
            azure_endpoint=config["endpoint"],
            api_version=config.get("api_version", "2023-05-15")
        )
    
    @staticmethod
    def _create_huggingface_client(config: Dict[str, Any]) -> Any:
        """Create HuggingFace client instance."""
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(
            config["model"],
            device=config.get("device", "cpu")
        )
    
    @staticmethod
    def _create_ollama_client(config: Dict[str, Any]) -> Any:
        """Create Ollama client instance."""
        # Will be implemented when Ollama support is added
        raise NotImplementedError("Ollama support will be added later")
    
    @staticmethod
    def clear_cache() -> None:
        """Clear all cached AI clients."""
        logger.info("Clearing AI client cache")
        AIClientFactory.create_ai_client.cache_clear()
    
    @staticmethod
    def get_cache_info() -> Dict[str, Any]:
        """Get information about cached AI clients."""
        return {
            "ai_client_cache": AIClientFactory.create_ai_client.cache_info()._asdict()
        }


# Convenience functions for easy access
@lru_cache(maxsize=1)
def get_vector_database() -> IVectorDatabase:
    """Get default vector database client instance.
    
    Returns:
        Default vector database client
    """
    return DatabaseFactory.create_vector_database()


@lru_cache(maxsize=1)
def get_ai_client() -> Any:
    """Get default AI client instance.
    
    Returns:
        Default AI client
    """
    return AIClientFactory.create_ai_client() 