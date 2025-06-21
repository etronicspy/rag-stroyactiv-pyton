"""
Context management for the logging system.

This module provides implementations for context management.
"""

import contextvars
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional, ContextManager, Iterator

from core.logging.interfaces import ILoggingContext, IContextProvider, ICorrelationProvider


class LoggingContext(ILoggingContext):
    """Implementation of the ILoggingContext interface."""
    
    def __init__(self):
        """Initialize a new logging context."""
        self._context = contextvars.ContextVar("logging_context", default={})
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get the current logging context.
        
        Returns:
            The current logging context as a dictionary
        """
        return self._context.get().copy()
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set the current logging context.
        
        Args:
            context: The context to set
        """
        self._context.set(context.copy())
    
    def update_context(self, **kwargs) -> None:
        """
        Update the current logging context.
        
        Args:
            **kwargs: The context values to update
        """
        context = self.get_context()
        context.update(kwargs)
        self.set_context(context)
    
    def clear_context(self) -> None:
        """Clear the current logging context."""
        self._context.set({})


class ContextProvider(IContextProvider):
    """Implementation of the IContextProvider interface."""
    
    def __init__(self):
        """Initialize a new context provider."""
        self._context = LoggingContext()
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get the current context.
        
        Returns:
            The current context as a dictionary
        """
        return self._context.get_context()
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set the current context.
        
        Args:
            context: The context to set
        """
        self._context.set_context(context)
    
    def update_context(self, **kwargs) -> None:
        """
        Update the current context.
        
        Args:
            **kwargs: The context values to update
        """
        self._context.update_context(**kwargs)
    
    def clear_context(self) -> None:
        """Clear the current context."""
        self._context.clear_context()
    
    @contextmanager
    def with_context(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Context manager for context.
        
        Args:
            **kwargs: The context values to set
            
        Returns:
            A context manager that sets and clears the context
        """
        # Save the current context
        old_context = self.get_context()
        
        try:
            # Update the context
            self.update_context(**kwargs)
            
            # Yield the new context
            yield self.get_context()
        finally:
            # Restore the old context
            self.set_context(old_context)


class CorrelationProvider(ICorrelationProvider):
    """Implementation of the ICorrelationProvider interface."""
    
    def __init__(self):
        """Initialize a new correlation provider."""
        self._correlation_id = contextvars.ContextVar("correlation_id", default=None)
    
    def get_correlation_id(self) -> Optional[str]:
        """
        Get the current correlation ID.
        
        Returns:
            The current correlation ID or None if not set
        """
        return self._correlation_id.get()
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """
        Set the current correlation ID.
        
        Args:
            correlation_id: The correlation ID to set
        """
        self._correlation_id.set(correlation_id)
    
    def generate_correlation_id(self) -> str:
        """
        Generate a new correlation ID.
        
        Returns:
            A new correlation ID
        """
        return str(uuid.uuid4())
    
    def clear_correlation_id(self) -> None:
        """Clear the current correlation ID."""
        self._correlation_id.set(None)
    
    @contextmanager
    def with_correlation_id(self, correlation_id: Optional[str] = None) -> Iterator[str]:
        """
        Context manager for correlation ID.
        
        Args:
            correlation_id: The correlation ID to use, or None to generate a new one
            
        Returns:
            A context manager that sets and clears the correlation ID
        """
        # Save the current correlation ID
        old_correlation_id = self.get_correlation_id()
        
        # Generate a new correlation ID if not provided
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()
        
        try:
            # Set the new correlation ID
            self.set_correlation_id(correlation_id)
            
            # Yield the correlation ID
            yield correlation_id
        finally:
            # Restore the old correlation ID
            if old_correlation_id is not None:
                self.set_correlation_id(old_correlation_id)
            else:
                self.clear_correlation_id() 