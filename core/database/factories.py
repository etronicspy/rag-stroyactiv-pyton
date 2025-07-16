"""Database client factories with runtime switching and caching support.

Фабрики для создания клиентов различных БД с кешированием и runtime переключением.
"""

from functools import lru_cache
from typing import Optional, Dict, Any, Callable
from core.logging import get_logger

from core.config import settings, DatabaseType, AIProvider
from core.database.interfaces import IVectorDatabase, IRelationalDatabase, ICacheDatabase
from core.database.exceptions import ConfigurationError, ConnectionError


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
            logger.error("PostgreSQL connection disabled, but mock adapters are removed. No fallback available.")
            raise ConnectionError("PostgreSQL connection disabled and no mock available.")
        
        # Check if we're in Qdrant-only mode
        if getattr(settings, 'QDRANT_ONLY_MODE', True):
            logger.error("Qdrant-only mode enabled, but mock adapters are removed. No fallback available.")
            raise ConnectionError("Qdrant-only mode enabled and no mock available.")
        
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
                logger.error("Fallback to mock PostgreSQL requested, but mock adapters are removed. No fallback available.")
                raise ConnectionError("Fallback to mock PostgreSQL requested and no mock available.")
                
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
            logger.error("Redis connection disabled, but mock adapters are removed. No fallback available.")
            raise ConnectionError("Redis connection disabled and no mock available.")
        
        # Check if we're in Qdrant-only mode
        if getattr(settings, 'QDRANT_ONLY_MODE', True):
            logger.error("Qdrant-only mode enabled, but mock adapters are removed. No fallback available.")
            raise ConnectionError("Qdrant-only mode enabled and no mock available.")
        
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
                logger.error("Fallback to mock Redis cache requested, but mock adapters are removed. No fallback available.")
                raise ConnectionError("Fallback to mock Redis cache requested and no mock available.")
                
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


class AllDatabasesUnavailableError(Exception):
    """Raised when all databases are unavailable for operation."""
    def __init__(self, errors: Dict[str, str]):
        super().__init__("All databases are unavailable")
        self.errors = errors

class DatabaseFallbackManager:
    """
    Centralized fallback manager for database operations.

    Tracks health of vector and relational DBs, provides unified DB operations with fallback,
    and raises a controlled error if all DBs are unavailable.

    Args:
        sql_client: Relational DB client implementing IRelationalDatabase
        vector_client: Vector DB client implementing IVectorDatabase
    """
    def __init__(self, sql_client: Optional[Any], vector_client: Optional[Any]):
        self.sql_client = sql_client
        self.vector_client = vector_client
        self.status = {'sql': sql_client is not None, 'vector': vector_client is not None}
        self.logger = get_logger("core.database.factories.DatabaseFallbackManager")

    def _try(self, op: str, *args, **kwargs):
        """
        Try to perform operation `op` on available DBs, fallback if one fails.
        If all fail, raise AllDatabasesUnavailableError.
        """
        errors = {}
        for db, client in [('sql', self.sql_client), ('vector', self.vector_client)]:
            if self.status[db] and client is not None:
                try:
                    return getattr(client, op)(*args, **kwargs)
                except Exception as e:
                    self.status[db] = False
                    errors[db] = str(e)
                    self.logger.error(f"{db} DB operation '{op}' failed: {e}")
        if errors:
            self.logger.error(f"All DBs down for operation '{op}': {errors}")
            raise AllDatabasesUnavailableError(errors)

    # Example unified methods (to be expanded)
    def search(self, *args, **kwargs):
        return self._try('search', *args, **kwargs)

    def upsert(self, *args, **kwargs):
        return self._try('upsert', *args, **kwargs)

    def get_by_id(self, *args, **kwargs):
        return self._try('get_by_id', *args, **kwargs)

    def get_processing_statistics(self, *args, **kwargs):
        """
        Unified method to get processing statistics from the relational DB.
        Returns:
            ProcessingStatistics object from the relational DB.
        Raises:
            AllDatabasesUnavailableError: If all DBs are unavailable.
        """
        if self.sql_client is not None:
            try:
                return self.sql_client.get_processing_statistics(*args, **kwargs)
            except Exception as e:
                self.status['sql'] = False
                self.logger.error(f"Relational DB get_processing_statistics failed: {e}")
        self.logger.error("All DBs down for get_processing_statistics")
        raise AllDatabasesUnavailableError({'sql': 'Unavailable for get_processing_statistics'})

    async def search_materials(self, query: str, limit: int = 10) -> list:
        """
        Search materials using fallback: vector search → SQL LIKE search if 0 results.
        Args:
            query: Search query
            limit: Max results
        Returns:
            List of materials (dicts or models)
        Raises:
            AllDatabasesUnavailableError: if all DBs are unavailable
        """
        errors = {}
        # Try vector search first
        if self.vector_client is not None:
            try:
                results = await self.vector_client.search_materials(query, limit)
                if results:
                    return results
            except Exception as e:
                self.status['vector'] = False
                self.logger.error(f"Vector DB search_materials failed: {e}")
                errors['vector'] = str(e)
        # Fallback: SQL LIKE search
        if self.sql_client is not None:
            try:
                results = await self.sql_client.search_materials(query, limit)
                if results:
                    return results
            except Exception as e:
                self.status['sql'] = False
                self.logger.error(f"SQL DB search_materials failed: {e}")
                errors['sql'] = str(e)
        if errors or (self.vector_client is None and self.sql_client is None):
            self.logger.error(f"All DBs down for search_materials: {errors}")
            raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})
        return []

    async def find_sku_by_material_data(self, *args, **kwargs):
        """
        Unified SKU search with fallback. Currently only vector DB is supported.
        Args:
            *args, **kwargs: forwarded to vector_client.find_sku_by_material_data
        Returns:
            SKUSearchResponse
        Raises:
            AllDatabasesUnavailableError: if all DBs are unavailable
        """
        errors = {}
        if self.vector_client is not None:
            try:
                return await self.vector_client.find_sku_by_material_data(*args, **kwargs)
            except Exception as e:
                self.status['vector'] = False
                self.logger.error(f"Vector DB find_sku_by_material_data failed: {e}")
                errors['vector'] = str(e)
        # (Можно добавить SQL fallback в будущем)
        if errors or self.vector_client is None:
            self.logger.error(f"All DBs down for find_sku_by_material_data: {errors}")
            raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def save_processed_material(self, *args, **kwargs):
        """
        Unified save for processed material with fallback. Currently only sql_client is supported.
        Args:
            *args, **kwargs: forwarded to sql_client.save_processed_material
        Returns:
            DatabaseSaveResult
        Raises:
            AllDatabasesUnavailableError: if all DBs are unavailable
        """
        errors = {}
        if self.sql_client is not None:
            try:
                return await self.sql_client.save_processed_material(*args, **kwargs)
            except Exception as e:
                self.status['sql'] = False
                self.logger.error(f"SQL DB save_processed_material failed: {e}")
                errors['sql'] = str(e)
        # (Можно добавить vector fallback в будущем)
        if errors or self.sql_client is None:
            self.logger.error(f"All DBs down for save_processed_material: {errors}")
            raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def vector_search(self, query: str, limit: int = 10, threshold: float = 0.7) -> list:
        """Vector search with fallback."""
        errors = {}
        if self.vector_client is not None:
            try:
                return await self.vector_client.vector_search(query=query, limit=limit, threshold=threshold)
            except Exception as e:
                self.status['vector'] = False
                self.logger.error(f"Vector DB vector_search failed: {e}")
                errors['vector'] = str(e)
        if errors or self.vector_client is None:
            self.logger.error(f"All DBs down for vector_search: {errors}")
            raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def sql_search(self, query: str, limit: int = 10) -> list:
        """SQL search with fallback."""
        errors = {}
        if self.sql_client is not None:
            try:
                return await self.sql_client.sql_search(query=query, limit=limit)
            except Exception as e:
                self.status['sql'] = False
                self.logger.error(f"SQL DB sql_search failed: {e}")
                errors['sql'] = str(e)
        if errors or self.sql_client is None:
            self.logger.error(f"All DBs down for sql_search: {errors}")
            raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def fuzzy_search(self, query: str, limit: int = 10, threshold: float = 0.8) -> list:
        """Fuzzy search with fallback."""
        errors = {}
        if self.sql_client is not None:
            try:
                return await self.sql_client.fuzzy_search(query=query, limit=limit, threshold=threshold)
            except Exception as e:
                self.status['sql'] = False
                self.logger.error(f"SQL DB fuzzy_search failed: {e}")
                errors['sql'] = str(e)
        if errors or self.sql_client is None:
            self.logger.error(f"All DBs down for fuzzy_search: {errors}")
            raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def hybrid_search(self, query: str, limit: int = 10, threshold: float = 0.7) -> list:
        """Hybrid search: vector + sql + fuzzy with fallback."""
        errors = {}
        results = []
        try:
            vector_results = await self.vector_search(query, limit, threshold)
            results.extend(vector_results)
        except Exception as e:
            errors['vector'] = str(e)
        try:
            sql_results = await self.sql_search(query, limit)
            results.extend(sql_results)
        except Exception as e:
            errors['sql'] = str(e)
        try:
            fuzzy_results = await self.fuzzy_search(query, limit, threshold)
            results.extend(fuzzy_results)
        except Exception as e:
            errors['fuzzy'] = str(e)
        if not results:
            self.logger.error(f"All DBs down for hybrid_search: {errors}")
            raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})
        return results

    # === Batch Processing Fallback Methods ===
    async def create_processing_records(self, request_id: str, materials: list) -> list:
        """Create initial records for batch processing with fallback."""
        errors = {}
        for db, client in [('sql', self.sql_client), ('vector', self.vector_client)]:
            if client is not None:
                try:
                    return await client.create_processing_records(request_id, materials)
                except Exception as e:
                    self.status[db] = False
                    errors[db] = str(e)
                    self.logger.error(f"{db} DB create_processing_records failed: {e}")
        self.logger.error(f"All DBs down for create_processing_records: {errors}")
        raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def update_processing_status(self, request_id: str, material_id: str, status: str, error: str = None, **kwargs) -> bool:
        """Update processing status for a material in a batch with fallback."""
        errors = {}
        for db, client in [('sql', self.sql_client), ('vector', self.vector_client)]:
            if client is not None:
                try:
                    return await client.update_processing_status(request_id, material_id, status, error, **kwargs)
                except Exception as e:
                    self.status[db] = False
                    errors[db] = str(e)
                    self.logger.error(f"{db} DB update_processing_status failed: {e}")
        self.logger.error(f"All DBs down for update_processing_status: {errors}")
        raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def get_processing_progress(self, request_id: str):
        """Get processing progress for a batch request with fallback."""
        errors = {}
        for db, client in [('sql', self.sql_client), ('vector', self.vector_client)]:
            if client is not None:
                try:
                    return await client.get_processing_progress(request_id)
                except Exception as e:
                    self.status[db] = False
                    errors[db] = str(e)
                    self.logger.error(f"{db} DB get_processing_progress failed: {e}")
        self.logger.error(f"All DBs down for get_processing_progress: {errors}")
        raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def get_processing_results(self, request_id: str, limit: int = None, offset: int = None) -> list:
        """Get processing results for a batch request with fallback."""
        errors = {}
        for db, client in [('sql', self.sql_client), ('vector', self.vector_client)]:
            if client is not None:
                try:
                    return await client.get_processing_results(request_id, limit, offset)
                except Exception as e:
                    self.status[db] = False
                    errors[db] = str(e)
                    self.logger.error(f"{db} DB get_processing_results failed: {e}")
        self.logger.error(f"All DBs down for get_processing_results: {errors}")
        raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def get_processing_statistics(self):
        """Get overall processing statistics with fallback."""
        errors = {}
        for db, client in [('sql', self.sql_client), ('vector', self.vector_client)]:
            if client is not None:
                try:
                    return await client.get_processing_statistics()
                except Exception as e:
                    self.status[db] = False
                    errors[db] = str(e)
                    self.logger.error(f"{db} DB get_processing_statistics failed: {e}")
        self.logger.error(f"All DBs down for get_processing_statistics: {errors}")
        raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def cleanup_old_records(self, days_old: int = 30) -> int:
        """Cleanup old processing records with fallback."""
        errors = {}
        for db, client in [('sql', self.sql_client), ('vector', self.vector_client)]:
            if client is not None:
                try:
                    return await client.cleanup_old_records(days_old)
                except Exception as e:
                    self.status[db] = False
                    errors[db] = str(e)
                    self.logger.error(f"{db} DB cleanup_old_records failed: {e}")
        self.logger.error(f"All DBs down for cleanup_old_records: {errors}")
        raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def get_failed_materials_for_retry(self, max_retries=3, retry_delay_minutes=10):
        errors = {}
        for db, client in [('sql', self.sql_client), ('vector', self.vector_client)]:
            if client is not None:
                try:
                    return await client.get_failed_materials_for_retry(max_retries, retry_delay_minutes)
                except Exception as e:
                    self.status[db] = False
                    errors[db] = str(e)
                    self.logger.error(f"{db} DB get_failed_materials_for_retry failed: {e}")
        self.logger.error(f"All DBs down for get_failed_materials_for_retry: {errors}")
        raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def increment_retry_count(self, material_id: str):
        errors = {}
        for db, client in [('sql', self.sql_client), ('vector', self.vector_client)]:
            if client is not None:
                try:
                    return await client.increment_retry_count(material_id)
                except Exception as e:
                    self.status[db] = False
                    errors[db] = str(e)
                    self.logger.error(f"{db} DB increment_retry_count failed: {e}")
        self.logger.error(f"All DBs down for increment_retry_count: {errors}")
        raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    async def embedding_search(self, collection: str, embedding: list, top_k: int = 3, threshold: float = 0.7, **kwargs):
        """
        Search for similar items in a collection using embedding (vector search) with fallback to suggestion_search.

        Args:
            collection (str): Target collection name (e.g., 'colors', 'units', 'materials').
            embedding (list): Query embedding vector.
            top_k (int): Number of results to return.
            threshold (float): Similarity threshold.
            **kwargs: Additional arguments for vector client.

        Returns:
            list: List of found items (dicts or models).

        Raises:
            AllDatabasesUnavailableError: If all DBs are unavailable.
        """
        errors = {}
        # Try vector search first
        if self.vector_client is not None:
            try:
                results = await self.vector_client.search(
                    collection_name=collection,
                    query_vector=embedding,
                    limit=top_k,
                    filter_conditions=kwargs.get("filter_conditions")
                )
                if results:
                    # Фильтруем по threshold, если есть score
                    filtered = [r for r in results if r.get("score", 1.0) >= threshold]
                    if filtered:
                        return filtered
            except Exception as e:
                self.status['vector'] = False
                self.logger.error(f"Vector DB embedding_search failed: {e}")
                errors['vector'] = str(e)
        # Fallback: suggestion_search
        return await self.suggestion_search(collection, kwargs.get("query", ""), top_k=top_k)

    async def suggestion_search(self, collection: str, query: str, top_k: int = 3, **kwargs):
        """
        Suggestion/fuzzy search in a collection (fallback for embedding_search).

        Args:
            collection (str): Target collection name (e.g., 'colors', 'units', 'materials').
            query (str): Query string.
            top_k (int): Number of results to return.
            **kwargs: Additional arguments for sql client.

        Returns:
            list: List of found items (dicts or models).

        Raises:
            AllDatabasesUnavailableError: If all DBs are unavailable.
        """
        errors = {}
        if self.sql_client is not None:
            try:
                # Предполагается, что sql_client реализует метод fuzzy_search_by_collection
                return await self.sql_client.fuzzy_search_by_collection(collection, query, limit=top_k)
            except Exception as e:
                self.status['sql'] = False
                self.logger.error(f"SQL DB suggestion_search failed: {e}")
                errors['sql'] = str(e)
        self.logger.error(f"All DBs down for suggestion_search: {errors}")
        raise AllDatabasesUnavailableError(errors or {'all': 'No DB clients available'})

    # ... add more as needed for your DB interface ...


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


@lru_cache(maxsize=1)
def get_fallback_manager() -> DatabaseFallbackManager:
    """
    Get a singleton instance of DatabaseFallbackManager with current DB clients.
    Returns:
        DatabaseFallbackManager: Centralized fallback manager for DB operations.
    """
    # Получаем клиентов через существующие фабрики
    try:
        vector_db = DatabaseFactory.create_vector_database()
    except Exception as e:
        logger.error(f"Vector DB unavailable: {e}")
        vector_db = None
    try:
        sql_db = DatabaseFactory.create_relational_database()
    except Exception as e:
        logger.error(f"Relational DB unavailable: {e}")
        sql_db = None
    return DatabaseFallbackManager(sql_client=sql_db, vector_client=vector_db) 