"""Base repository class with common functionality.

Базовый класс репозитория с общей функциональностью для мульти-БД архитектуры.
"""

from abc import ABC
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from core.database.interfaces import IVectorDatabase, IRelationalDatabase, ICacheDatabase
from core.database.exceptions import DatabaseError, QueryError


class BaseRepository(ABC):
    """Base repository class with common database operations.
    
    Базовый репозиторий с поддержкой векторных, реляционных БД и кеширования.
    Включает логирование, обработку ошибок и health checks для всех БД.
    """
    
    def __init__(self, 
                 vector_db: Optional[IVectorDatabase] = None,
                 relational_db: Optional[IRelationalDatabase] = None,
                 cache_db: Optional[ICacheDatabase] = None,
                 ai_client: Optional[Any] = None):
        """Initialize base repository.
        
        Args:
            vector_db: Vector database client
            relational_db: Relational database client  
            cache_db: Cache database client
            ai_client: AI client for embeddings
        """
        self.vector_db = vector_db
        self.relational_db = relational_db
        self.cache_db = cache_db
        self.ai_client = ai_client
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def _handle_database_error(self, operation: str, error: Exception) -> None:
        """Handle database errors with proper logging.
        
        Args:
            operation: Operation that failed
            error: Exception that occurred
            
        Raises:
            DatabaseError: Wrapped database error
        """
        error_message = f"Database operation '{operation}' failed: {str(error)}"
        self.logger.error(error_message, exc_info=True)
        
        if isinstance(error, DatabaseError):
            raise error
        else:
            raise DatabaseError(error_message, details=str(error))
    
    async def _cache_get(self, key: str) -> Optional[str]:
        """Get value from cache if cache is available.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.cache_db:
            return None
            
        try:
            return await self.cache_db.get(key)
        except Exception as e:
            self.logger.warning(f"Cache get failed for key '{key}': {e}")
            return None
    
    async def _cache_set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        """Set value in cache if cache is available.
        
        Args:
            key: Cache key
            value: Value to cache
            expire_seconds: TTL in seconds
            
        Returns:
            True if successful
        """
        if not self.cache_db:
            return False
            
        try:
            return await self.cache_db.set(key, value, expire_seconds)
        except Exception as e:
            self.logger.warning(f"Cache set failed for key '{key}': {e}")
            return False
    
    async def _cache_delete(self, key: str) -> bool:
        """Delete value from cache if cache is available.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        if not self.cache_db:
            return False
            
        try:
            return await self.cache_db.delete(key)
        except Exception as e:
            self.logger.warning(f"Cache delete failed for key '{key}': {e}")
            return False
    
    def _generate_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key from prefix and arguments.
        
        Args:
            prefix: Cache key prefix
            *args: Arguments to include in key
            
        Returns:
            Generated cache key
        """
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)
    
    def _get_current_timestamp(self) -> datetime:
        """Get current UTC timestamp.
        
        Returns:
            Current UTC datetime
        """
        return datetime.utcnow()
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check health of all connected databases.
        
        Returns:
            Health status for each database
        """
        health_status = {}
        
        # Check vector database
        if self.vector_db:
            try:
                vector_health = await self.vector_db.health_check()
                health_status["vector_db"] = {
                    "status": "healthy",
                    "details": vector_health
                }
            except Exception as e:
                health_status["vector_db"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Check relational database
        if self.relational_db:
            try:
                relational_health = await self.relational_db.health_check()
                health_status["relational_db"] = {
                    "status": "healthy", 
                    "details": relational_health
                }
            except Exception as e:
                health_status["relational_db"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Check cache database
        if self.cache_db:
            try:
                cache_health = await self.cache_db.health_check()
                health_status["cache_db"] = {
                    "status": "healthy",
                    "details": cache_health
                }
            except Exception as e:
                health_status["cache_db"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status
    
    async def _log_operation(self, operation: str, details: Dict[str, Any] = None) -> None:
        """Log repository operation for monitoring.
        
        Args:
            operation: Operation name
            details: Additional operation details
        """
        log_data = {
            "operation": operation,
            "timestamp": self._get_current_timestamp().isoformat(),
            "repository": self.__class__.__name__
        }
        
        if details:
            log_data.update(details)
        
        self.logger.info(f"Repository operation: {operation}", extra=log_data)
    
    async def get_embedding(self, text: str) -> list:
        """Get embedding for text using AI client.
        
        Args:
            text: Text to get embedding for
            
        Returns:
            List of float values representing the embedding
            
        Raises:
            DatabaseError: If embedding generation fails
        """
        if not self.ai_client:
            # NO FALLBACK - AI client is required for embeddings
            raise DatabaseError(
                message="AI client not available - cannot generate embeddings",
                details="OpenAI API client not properly initialized"
            )
        
        try:
            # For real OpenAI client (primary)
            if hasattr(self.ai_client, 'embeddings'):
                self.logger.info(f"🧠 Using OpenAI embeddings for: {text[:50]}...")
                response = await self.ai_client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small",
                    dimensions=1536
                )
                return response.data[0].embedding
            
            # For mock AI client (testing only)
            elif hasattr(self.ai_client, 'get_embedding'):
                self.logger.info(f"🔧 Using mock AI client for testing: {text[:50]}...")
                return await self.ai_client.get_embedding(text)
            
            # No valid AI client interface
            else:
                raise DatabaseError(
                    message="AI client doesn't support embedding generation",
                    details=f"Client type: {type(self.ai_client)}, Available methods: {dir(self.ai_client)}"
                )
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding for text: {e}")
            # NO FALLBACK - embedding generation must work
            raise DatabaseError(
                message="Failed to generate embedding",
                details=str(e)
            )
    
    async def get_embeddings_batch(self, texts: list) -> list:
        """Get embeddings for multiple texts.
        
        Args:
            texts: List of texts to get embeddings for
            
        Returns:
            List of embeddings
        """
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    async def _generate_mock_embedding(self, text: str) -> list:
        """Generate mock embedding for testing/fallback.
        
        Args:
            text: Input text
            
        Returns:
            Mock embedding vector
        """
        import hashlib
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        mock_embedding = []
        for i in range(1536):  # OpenAI embedding size
            mock_embedding.append(float(int(text_hash[i % len(text_hash)], 16)) / 15.0 - 0.5)
        return mock_embedding 