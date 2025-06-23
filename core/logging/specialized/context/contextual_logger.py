"""
Contextual logger implementation.

This module provides a logger implementation with context support.
"""

import logging
from typing import Any, Dict, Optional, Union

from core.logging.interfaces import ICorrelationProvider, IContextProvider
from core.logging.core import Logger
from core.logging.core.context import CorrelationProvider, ContextProvider


class ContextualLogger(Logger):
    """Logger implementation with context support."""
    
    def __init__(
        self, 
        name: str, 
        level: Union[int, str] = logging.INFO,
        correlation_provider: Optional[ICorrelationProvider] = None,
        context_provider: Optional[IContextProvider] = None
    ):
        """
        Initialize a new contextual logger.
        
        Args:
            name: The logger name
            level: The log level
            correlation_provider: The correlation provider to use
            context_provider: The context provider to use
        """
        super().__init__(name, level)
        self._correlation_provider = correlation_provider or CorrelationProvider()
        self._context_provider = context_provider or ContextProvider()
    
    def log(self, level: Union[int, str], message: str, **kwargs) -> None:
        """
        Log a message with the specified level, including context.
        
        Args:
            level: The log level
            message: The message to log
            **kwargs: Additional context for the log message
        """
        # Enrich the log message with context
        enriched_kwargs = self._enrich_context(**kwargs)
        
        # Call the parent log method
        super().log(level, message, **enriched_kwargs)
    
    def _enrich_context(self, **kwargs) -> Dict[str, Any]:
        """
        Enrich the log context with correlation ID and general context.
        
        Args:
            **kwargs: Additional context for the log message
            
        Returns:
            The enriched context
        """
        # Start with the provided kwargs
        enriched = dict(kwargs)
        
        # Add correlation ID if available
        correlation_id = self._correlation_provider.get_correlation_id()
        if correlation_id:
            enriched["correlation_id"] = correlation_id
        
        # Add general context
        context = self._context_provider.get_context()
        if context:
            # Avoid overriding explicit kwargs
            for key, value in context.items():
                if key not in enriched:
                    enriched[key] = value
        
        return enriched


class AsyncContextualLogger(ContextualLogger):
    """Asynchronous contextual logger implementation."""
    
    async def alog(self, level: Union[int, str], message: str, **kwargs) -> None:
        """
        Log a message asynchronously with context.
        
        Args:
            level: The log level
            message: The message to log
            **kwargs: Additional context for the log message
        """
        # Enrich the log message with context
        enriched_kwargs = self._enrich_context(**kwargs)
        
        # Log synchronously for now
        # In a real implementation, this would use an async queue
        super().log(level, message, **enriched_kwargs)
    
    async def adebug(self, message: str, **kwargs) -> None:
        """
        Log a debug message asynchronously.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
        await self.alog(logging.DEBUG, message, **kwargs)
    
    async def ainfo(self, message: str, **kwargs) -> None:
        """
        Log an info message asynchronously.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
        await self.alog(logging.INFO, message, **kwargs)
    
    async def awarning(self, message: str, **kwargs) -> None:
        """
        Log a warning message asynchronously.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
        await self.alog(logging.WARNING, message, **kwargs)
    
    async def aerror(self, message: str, **kwargs) -> None:
        """
        Log an error message asynchronously.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
        await self.alog(logging.ERROR, message, **kwargs)
    
    async def acritical(self, message: str, **kwargs) -> None:
        """
        Log a critical message asynchronously.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
        await self.alog(logging.CRITICAL, message, **kwargs) 