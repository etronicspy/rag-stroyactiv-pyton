"""Abstract interfaces for different database types.

Интерфейсы для работы с различными типами БД в мульти-БД архитектуре.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IVectorDatabase(ABC):
    """Abstract interface for vector databases (Qdrant, Weaviate, Pinecone).
    
    Абстрактный интерфейс для векторных БД с обязательными методами:
    search, upsert, delete, batch_upsert, get_by_id
    """
    
    @abstractmethod
    async def create_collection(self, name: str, vector_size: int, distance_metric: str = "cosine") -> bool:
        """Create a new collection for storing vectors.
        
        Args:
            name: Collection name
            vector_size: Dimension of vectors
            distance_metric: Distance calculation method
            
        Returns:
            True if collection created successfully
        """
    
    @abstractmethod
    async def collection_exists(self, name: str) -> bool:
        """Check if collection exists.
        
        Args:
            name: Collection name
            
        Returns:
            True if collection exists
        """
    
    @abstractmethod
    async def upsert(self, collection_name: str, vectors: List[Dict[str, Any]]) -> bool:
        """Insert or update vectors with metadata in collection.
        
        Args:
            collection_name: Target collection
            vectors: List of vector objects with id, vector, and payload
            
        Returns:
            True if upsert successful
        """
    
    @abstractmethod
    async def search(self, collection_name: str, query_vector: List[float], 
                    limit: int = 10, filter_conditions: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            collection_name: Collection to search in
            query_vector: Query vector
            limit: Maximum number of results
            filter_conditions: Optional filtering conditions
            
        Returns:
            List of search results with scores and metadata
        """
    
    @abstractmethod
    async def get_by_id(self, collection_name: str, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get vector by ID.
        
        Args:
            collection_name: Collection name
            vector_id: Vector ID
            
        Returns:
            Vector data or None if not found
        """
    
    @abstractmethod
    async def update_vector(self, collection_name: str, vector_id: str, 
                          vector: Optional[List[float]] = None, 
                          payload: Optional[Dict[str, Any]] = None) -> bool:
        """Update vector and/or its metadata.
        
        Args:
            collection_name: Collection name
            vector_id: Vector ID
            vector: New vector values
            payload: New metadata
            
        Returns:
            True if update successful
        """
    
    @abstractmethod
    async def delete(self, collection_name: str, vector_id: str) -> bool:
        """Delete vector by ID.
        
        Args:
            collection_name: Collection name
            vector_id: Vector ID
            
        Returns:
            True if deletion successful
        """
    
    @abstractmethod
    async def batch_upsert(self, collection_name: str, vectors: List[Dict[str, Any]], 
                          batch_size: int = 100) -> bool:
        """Insert or update multiple vectors in batches.
        
        Args:
            collection_name: Target collection
            vectors: List of vector objects with id, vector, and payload
            batch_size: Size of processing batches
            
        Returns:
            True if batch upsert successful
        """
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check database health status.
        
        Returns:
            Health status information
        """


class IRelationalDatabase(ABC):
    """Abstract interface for relational databases (PostgreSQL)."""
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Query results
        """
    
    @abstractmethod
    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute SQL command (INSERT, UPDATE, DELETE).
        
        Args:
            command: SQL command
            params: Command parameters
            
        Returns:
            Number of affected rows
        """
    
    @abstractmethod
    async def begin_transaction(self):
        """Begin database transaction as async context manager.
        
        Yields:
            Transaction session
        """
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check database health status.
        
        Returns:
            Health status information
        """


class ICacheDatabase(ABC):
    """Abstract interface for cache databases (Redis)."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value by key.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
    
    @abstractmethod
    async def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        """Set key-value pair.
        
        Args:
            key: Cache key
            value: Value to cache
            expire_seconds: TTL in seconds
            
        Returns:
            True if successful
        """
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check cache health status.
        
        Returns:
            Health status information
        """
