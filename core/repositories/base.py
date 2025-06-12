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
                 cache_db: Optional[ICacheDatabase] = None):
        """Initialize base repository.
        
        Args:
            vector_db: Vector database client
            relational_db: Relational database client  
            cache_db: Cache database client
        """
        self.vector_db = vector_db
        self.relational_db = relational_db
        self.cache_db = cache_db
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