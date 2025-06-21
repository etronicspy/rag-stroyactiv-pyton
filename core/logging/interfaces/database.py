"""
Database logging interfaces for the logging system.

This module defines interfaces for database operation logging:
- IDatabaseLogger: Interface for database operation logging
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, ContextManager, Union


class IDatabaseLogger(ABC):
    """Interface for database operation logging."""
    
    @abstractmethod
    def log_operation(
        self, 
        operation: str, 
        duration_ms: float, 
        success: bool, 
        **kwargs
    ) -> None:
        """
        Log a database operation.
        
        Args:
            operation: The operation name
            duration_ms: The operation duration in milliseconds
            success: Whether the operation was successful
            **kwargs: Additional context for the log message
        """
        pass
    
    @abstractmethod
    def log_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None, 
        duration_ms: Optional[float] = None, 
        success: bool = True, 
        **kwargs
    ) -> None:
        """
        Log a database query.
        
        Args:
            query: The query string
            parameters: The query parameters
            duration_ms: The query duration in milliseconds
            success: Whether the query was successful
            **kwargs: Additional context for the log message
        """
        pass
    
    @abstractmethod
    def log_connection(
        self, 
        success: bool, 
        duration_ms: Optional[float] = None, 
        error: Optional[Exception] = None, 
        **kwargs
    ) -> None:
        """
        Log a database connection attempt.
        
        Args:
            success: Whether the connection was successful
            duration_ms: The connection duration in milliseconds
            error: The error if the connection failed
            **kwargs: Additional context for the log message
        """
        pass
    
    @abstractmethod
    def operation_context(
        self, 
        operation: str, 
        **kwargs
    ) -> ContextManager[Dict[str, Any]]:
        """
        Context manager for database operations.
        
        Args:
            operation: The operation name
            **kwargs: Additional context for the log message
            
        Returns:
            A context manager that logs the operation
        """
        pass


class IVectorDatabaseLogger(IDatabaseLogger):
    """Interface for vector database operation logging."""
    
    @abstractmethod
    def log_vector_operation(
        self, 
        operation: str, 
        vector_count: int, 
        dimension: int, 
        duration_ms: float, 
        success: bool, 
        **kwargs
    ) -> None:
        """
        Log a vector database operation.
        
        Args:
            operation: The operation name
            vector_count: The number of vectors
            dimension: The vector dimension
            duration_ms: The operation duration in milliseconds
            success: Whether the operation was successful
            **kwargs: Additional context for the log message
        """
        pass
    
    @abstractmethod
    def log_search_operation(
        self, 
        query_vector: Union[list, Any], 
        top_k: int, 
        duration_ms: float, 
        result_count: int, 
        success: bool, 
        **kwargs
    ) -> None:
        """
        Log a vector search operation.
        
        Args:
            query_vector: The query vector
            top_k: The number of results requested
            duration_ms: The operation duration in milliseconds
            result_count: The number of results returned
            success: Whether the operation was successful
            **kwargs: Additional context for the log message
        """
        pass 