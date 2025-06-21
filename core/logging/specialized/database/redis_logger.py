"""
Redis logger implementation.

This module provides a logger for Redis operations.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from core.logging.specialized.database.database_logger import DatabaseLogger, AsyncDatabaseLogger


class RedisLogger(DatabaseLogger):
    """Logger for Redis operations."""
    
    def __init__(
        self,
        name: str,
        level: Union[int, str] = logging.INFO,
        max_value_length: int = 100
    ):
        """
        Initialize a new Redis logger.
        
        Args:
            name: The logger name
            level: The log level
            max_value_length: The maximum value length to log
        """
        super().__init__(name, "redis", level)
        self._max_value_length = max_value_length
    
    def log_command(
        self,
        command: str,
        key: Optional[str] = None,
        args: Optional[List[Any]] = None,
        duration_ms: float = 0.0,
        result_type: Optional[str] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a Redis command.
        
        Args:
            command: The Redis command
            key: The key
            args: The command arguments
            duration_ms: The duration in milliseconds
            result_type: The result type
            success: Whether the command was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "command": command,
            "duration_ms": duration_ms,
        }
        
        # Add key if available
        if key:
            context["key"] = key
        
        # Add args if available
        if args:
            context["args"] = self._process_args(args)
        
        # Add result type if available
        if result_type:
            context["result_type"] = result_type
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        self.log_operation(
            operation=command,
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    def log_get(
        self,
        key: str,
        value: Optional[Any] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a Redis GET operation.
        
        Args:
            key: The key
            value: The value
            duration_ms: The duration in milliseconds
            success: Whether the operation was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "key": key,
            "duration_ms": duration_ms,
        }
        
        # Add value if available
        if value is not None:
            context["value"] = self._process_value(value)
            context["value_type"] = type(value).__name__
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        self.log_operation(
            operation="GET",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    def log_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a Redis SET operation.
        
        Args:
            key: The key
            value: The value
            ttl: The TTL in seconds
            duration_ms: The duration in milliseconds
            success: Whether the operation was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "key": key,
            "value": self._process_value(value),
            "value_type": type(value).__name__,
            "duration_ms": duration_ms,
        }
        
        # Add TTL if available
        if ttl is not None:
            context["ttl"] = ttl
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        self.log_operation(
            operation="SET",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    def log_delete(
        self,
        key: str,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a Redis DELETE operation.
        
        Args:
            key: The key
            duration_ms: The duration in milliseconds
            success: Whether the operation was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "key": key,
            "duration_ms": duration_ms,
        }
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        self.log_operation(
            operation="DELETE",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    def _process_args(self, args: List[Any]) -> List[Any]:
        """
        Process command arguments for logging.
        
        Args:
            args: The command arguments
            
        Returns:
            The processed arguments
        """
        processed_args = []
        
        for arg in args:
            if isinstance(arg, (str, bytes)):
                processed_args.append(self._process_value(arg))
            else:
                processed_args.append(arg)
        
        return processed_args
    
    def _process_value(self, value: Any) -> Any:
        """
        Process a value for logging.
        
        Args:
            value: The value
            
        Returns:
            The processed value
        """
        # Handle string values
        if isinstance(value, str):
            if len(value) > self._max_value_length:
                return f"{value[:self._max_value_length]}... [truncated]"
            return value
        
        # Handle bytes values
        if isinstance(value, bytes):
            if len(value) > self._max_value_length:
                return f"{value[:self._max_value_length]}... [truncated]"
            return value
        
        # Return other values as is
        return value


class AsyncRedisLogger(AsyncDatabaseLogger, RedisLogger):
    """Asynchronous logger for Redis operations."""
    
    async def alog_command(
        self,
        command: str,
        key: Optional[str] = None,
        args: Optional[List[Any]] = None,
        duration_ms: float = 0.0,
        result_type: Optional[str] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a Redis command asynchronously.
        
        Args:
            command: The Redis command
            key: The key
            args: The command arguments
            duration_ms: The duration in milliseconds
            result_type: The result type
            success: Whether the command was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "command": command,
            "duration_ms": duration_ms,
        }
        
        # Add key if available
        if key:
            context["key"] = key
        
        # Add args if available
        if args:
            context["args"] = self._process_args(args)
        
        # Add result type if available
        if result_type:
            context["result_type"] = result_type
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        await self.alog_operation(
            operation=command,
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    async def alog_get(
        self,
        key: str,
        value: Optional[Any] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a Redis GET operation asynchronously.
        
        Args:
            key: The key
            value: The value
            duration_ms: The duration in milliseconds
            success: Whether the operation was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "key": key,
            "duration_ms": duration_ms,
        }
        
        # Add value if available
        if value is not None:
            context["value"] = self._process_value(value)
            context["value_type"] = type(value).__name__
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        await self.alog_operation(
            operation="GET",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    async def alog_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a Redis SET operation asynchronously.
        
        Args:
            key: The key
            value: The value
            ttl: The TTL in seconds
            duration_ms: The duration in milliseconds
            success: Whether the operation was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "key": key,
            "value": self._process_value(value),
            "value_type": type(value).__name__,
            "duration_ms": duration_ms,
        }
        
        # Add TTL if available
        if ttl is not None:
            context["ttl"] = ttl
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        await self.alog_operation(
            operation="SET",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        )
    
    async def alog_delete(
        self,
        key: str,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log a Redis DELETE operation asynchronously.
        
        Args:
            key: The key
            duration_ms: The duration in milliseconds
            success: Whether the operation was successful
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the context
        context = {
            "key": key,
            "duration_ms": duration_ms,
        }
        
        # Add additional context
        context.update(kwargs)
        
        # Log the operation
        await self.alog_operation(
            operation="DELETE",
            duration_ms=duration_ms,
            success=success,
            error=error,
            **context
        ) 