"""
Database logger implementation.

This module provides a logger for database operations.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional, Union

from core.logging.interfaces import IDatabaseLogger
from core.logging.core import Logger


class DatabaseLogger(Logger, IDatabaseLogger):
    """Logger for database operations."""
    
    def __init__(
        self,
        name: str,
        db_type: str,
        level: Union[int, str] = logging.INFO
    ):
        """
        Initialize a new database logger.
        
        Args:
            name: The logger name
            db_type: The database type (e.g., 'postgresql', 'qdrant', 'redis')
            level: The log level
        """
        super().__init__(name, level)
        self._db_type = db_type
    
    def log_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a database operation.
        
        Args:
            operation: The operation name
            duration_ms: The duration in milliseconds
            success: Whether the operation was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the log message
        message = f"{self._db_type} {operation}"
        if not success:
            message = f"{message} failed"
        
        # Build the context
        context = {
            "db_type": self._db_type,
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
        }
        
        # Add error information if available
        if error:
            context["error"] = str(error)
            context["error_type"] = type(error).__name__
        
        # Add additional context
        context.update(kwargs)
        
        # Log the message
        if success:
            self.info(message, **context)
        else:
            self.error(message, **context)
    
    @contextmanager
    def operation_context(self, operation: str, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        Context manager for logging database operations.
        
        Args:
            operation: The operation name
            **kwargs: Additional context for the log message
            
        Yields:
            A dictionary for storing operation context
        """
        # Create a context dictionary
        context = {
            "db_type": self._db_type,
            "operation": operation,
            **kwargs
        }
        
        # Record the start time
        start_time = time.time()
        
        # Initialize the operation context
        op_context = {
            "record_count": None,
            "affected_rows": None,
            "query_params": None,
            "additional_context": {}
        }
        
        try:
            # Yield the operation context
            yield op_context
            
            # Calculate the duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the successful operation
            self.log_operation(
                operation=operation,
                duration_ms=duration_ms,
                success=True,
                record_count=op_context["record_count"],
                affected_rows=op_context["affected_rows"],
                query_params=op_context["query_params"],
                **op_context["additional_context"],
                **kwargs
            )
        except Exception as e:
            # Calculate the duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the failed operation
            self.log_operation(
                operation=operation,
                duration_ms=duration_ms,
                success=False,
                error=e,
                record_count=op_context["record_count"],
                affected_rows=op_context["affected_rows"],
                query_params=op_context["query_params"],
                **op_context["additional_context"],
                **kwargs
            )
            
            # Re-raise the exception
            raise


class AsyncDatabaseLogger(DatabaseLogger):
    """Asynchronous logger for database operations."""
    
    async def alog_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a database operation asynchronously.
        
        Args:
            operation: The operation name
            duration_ms: The duration in milliseconds
            success: Whether the operation was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # For now, just call the synchronous method
        # In a real implementation, this would use an async queue
        self.log_operation(operation, duration_ms, success, error, **kwargs)
    
    @contextmanager
    async def aoperation_context(self, operation: str, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        Async context manager for logging database operations.
        
        Args:
            operation: The operation name
            **kwargs: Additional context for the log message
            
        Yields:
            A dictionary for storing operation context
        """
        # Create a context dictionary
        context = {
            "db_type": self._db_type,
            "operation": operation,
            **kwargs
        }
        
        # Record the start time
        start_time = time.time()
        
        # Initialize the operation context
        op_context = {
            "record_count": None,
            "affected_rows": None,
            "query_params": None,
            "additional_context": {}
        }
        
        try:
            # Yield the operation context
            yield op_context
            
            # Calculate the duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the successful operation
            await self.alog_operation(
                operation=operation,
                duration_ms=duration_ms,
                success=True,
                record_count=op_context["record_count"],
                affected_rows=op_context["affected_rows"],
                query_params=op_context["query_params"],
                **op_context["additional_context"],
                **kwargs
            )
        except Exception as e:
            # Calculate the duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log the failed operation
            await self.alog_operation(
                operation=operation,
                duration_ms=duration_ms,
                success=False,
                error=e,
                record_count=op_context["record_count"],
                affected_rows=op_context["affected_rows"],
                query_params=op_context["query_params"],
                **op_context["additional_context"],
                **kwargs
            )
            
            # Re-raise the exception
            raise 