"""
Vector database logger implementation.

This module provides a logger for vector database operations.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Union

from core.logging.specialized.database.database_logger import DatabaseLogger, AsyncDatabaseLogger


class VectorDbLogger(DatabaseLogger):
    """Logger for vector database operations."""
    
    def __init__(
        self,
        name: str,
        db_type: str,
        level: Union[int, str] = logging.INFO,
        log_vectors: bool = False,
        max_vector_size: int = 5,
        max_payload_size: int = 1000
    ):
        """
        Initialize a new vector database logger.
        
        Args:
            name: The logger name
            db_type: The database type (e.g., 'qdrant', 'weaviate', 'pinecone')
            level: The log level
            log_vectors: Whether to log vector values
            max_vector_size: The maximum number of vector elements to log
            max_payload_size: The maximum payload size to log
        """
        super().__init__(name, db_type, level)
        self._log_vectors = log_vectors
        self._max_vector_size = max_vector_size
        self._max_payload_size = max_payload_size
    
    def log_search(
        self,
        collection: str,
        query_vector: Optional[List[float]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        duration_ms: float = 0.0,
        result_count: Optional[int] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a vector search operation.
        
        Args:
            collection: The collection name
            query_vector: The query vector
            filter_params: The filter parameters
            limit: The limit
            duration_ms: The duration in milliseconds
            result_count: The number of results
            success: Whether the search was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "collection": collection,
            "duration_ms": duration_ms,
        }
        
        # Add query vector if enabled
        if self._log_vectors and query_vector:
            context["query_vector"] = self._process_vector(query_vector)
        
        # Add filter parameters if available
        if filter_params:
            context["filter_params"] = self._process_payload(filter_params)
        
        # Add limit if available
        if limit is not None:
            context["limit"] = limit
        
        # Add result count if available
        if result_count is not None:
            context["result_count"] = result_count
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        self.log_operation(
            operation="search",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    def log_upsert(
        self,
        collection: str,
        points_count: int,
        batch_size: Optional[int] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a vector upsert operation.
        
        Args:
            collection: The collection name
            points_count: The number of points
            batch_size: The batch size
            duration_ms: The duration in milliseconds
            success: Whether the upsert was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "collection": collection,
            "points_count": points_count,
            "duration_ms": duration_ms,
        }
        
        # Add batch size if available
        if batch_size is not None:
            context["batch_size"] = batch_size
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        self.log_operation(
            operation="upsert",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    def log_delete(
        self,
        collection: str,
        points_count: Optional[int] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a vector delete operation.
        
        Args:
            collection: The collection name
            points_count: The number of points
            filter_params: The filter parameters
            duration_ms: The duration in milliseconds
            success: Whether the delete was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "collection": collection,
            "duration_ms": duration_ms,
        }
        
        # Add points count if available
        if points_count is not None:
            context["points_count"] = points_count
        
        # Add filter parameters if available
        if filter_params:
            context["filter_params"] = self._process_payload(filter_params)
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        self.log_operation(
            operation="delete",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    def log_connection(
        self,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs,
    ) -> None:
        """Log opening a connection to the vector database."""
        self.log_operation(
            operation="connect",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **kwargs,
        )

    def log_query(
        self,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs,
    ) -> None:
        """Log an arbitrary query/command against the vector database.

        Args:
            operation: Human-readable operation name (e.g. 'search', 'delete').
            parameters: Parameters passed to the operation.
            duration_ms: Execution time in milliseconds.
            success: Whether the operation succeeded.
            error: The raised exception, if any.
        """
        extra: Dict[str, Any] = {}
        if parameters is not None:
            extra["parameters"] = parameters
        extra.update(kwargs)
        self.log_operation(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error,
            **extra,
        )
    
    def _process_vector(self, vector: List[float]) -> Union[List[float], str]:
        """
        Process a vector for logging.
        
        Args:
            vector: The vector
            
        Returns:
            The processed vector
        """
        # If vector logging is disabled, return a placeholder
        if not self._log_vectors:
            return f"[vector of size {len(vector)}]"
        
        # Truncate the vector if it's too long
        if len(vector) > self._max_vector_size:
            return vector[:self._max_vector_size] + [f"... ({len(vector) - self._max_vector_size} more)"]
        
        return vector
    
    def _process_payload(self, payload: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Process a payload for logging.
        
        Args:
            payload: The payload
            
        Returns:
            The processed payload
        """
        # Convert to JSON and check size
        payload_json = json.dumps(payload)
        
        # Truncate the payload if it's too long
        if len(payload_json) > self._max_payload_size:
            return f"{payload_json[:self._max_payload_size]}... [truncated]"
        
        return payload


class AsyncVectorDbLogger(AsyncDatabaseLogger, VectorDbLogger):
    """Asynchronous logger for vector database operations."""
    
    async def alog_search(
        self,
        collection: str,
        query_vector: Optional[List[float]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        duration_ms: float = 0.0,
        result_count: Optional[int] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a vector search operation asynchronously.
        
        Args:
            collection: The collection name
            query_vector: The query vector
            filter_params: The filter parameters
            limit: The limit
            duration_ms: The duration in milliseconds
            result_count: The number of results
            success: Whether the search was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "collection": collection,
            "duration_ms": duration_ms,
        }
        
        # Add query vector if enabled
        if self._log_vectors and query_vector:
            context["query_vector"] = self._process_vector(query_vector)
        
        # Add filter parameters if available
        if filter_params:
            context["filter_params"] = self._process_payload(filter_params)
        
        # Add limit if available
        if limit is not None:
            context["limit"] = limit
        
        # Add result count if available
        if result_count is not None:
            context["result_count"] = result_count
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        await self.alog_operation(
            operation="search",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    async def alog_upsert(
        self,
        collection: str,
        points_count: int,
        batch_size: Optional[int] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a vector upsert operation asynchronously.
        
        Args:
            collection: The collection name
            points_count: The number of points
            batch_size: The batch size
            duration_ms: The duration in milliseconds
            success: Whether the upsert was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "collection": collection,
            "points_count": points_count,
            "duration_ms": duration_ms,
        }
        
        # Add batch size if available
        if batch_size is not None:
            context["batch_size"] = batch_size
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        await self.alog_operation(
            operation="upsert",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    async def alog_delete(
        self,
        collection: str,
        points_count: Optional[int] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a vector delete operation asynchronously.
        
        Args:
            collection: The collection name
            points_count: The number of points
            filter_params: The filter parameters
            duration_ms: The duration in milliseconds
            success: Whether the delete was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "collection": collection,
            "duration_ms": duration_ms,
        }
        
        # Add points count if available
        if points_count is not None:
            context["points_count"] = points_count
        
        # Add filter parameters if available
        if filter_params:
            context["filter_params"] = self._process_payload(filter_params)
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        await self.alog_operation(
            operation="delete",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        ) 