"""
Correlation provider implementation.

This module provides a provider for correlation ID management.
"""

import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generator, Optional

from core.logging.interfaces import ICorrelationProvider


# Context variable for correlation ID
_correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class CorrelationProvider(ICorrelationProvider):
    """Provider for correlation ID management."""
    
    def generate_correlation_id(self) -> str:
        """
        Generate a new correlation ID.
        
        Returns:
            A new correlation ID
        """
        return str(uuid.uuid4())
    
    def get_correlation_id(self) -> Optional[str]:
        """
        Get the current correlation ID.
        
        Returns:
            The current correlation ID, or None if not set
        """
        return _correlation_id_var.get()
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """
        Set the current correlation ID.
        
        Args:
            correlation_id: The correlation ID to set
        """
        _correlation_id_var.set(correlation_id)
    
    def clear_correlation_id(self) -> None:
        """Clear the current correlation ID."""
        _correlation_id_var.set(None)
    
    @contextmanager
    def with_correlation_id(self, correlation_id: Optional[str] = None) -> Generator[str, None, None]:
        """
        Context manager for setting a correlation ID.
        
        Args:
            correlation_id: The correlation ID to set, or None to generate a new one
            
        Yields:
            The correlation ID
        """
        # Generate a new correlation ID if not provided
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()
        
        # Save the previous correlation ID
        self.get_correlation_id()
        
        # Set the new correlation ID
        token = _correlation_id_var.set(correlation_id)
        try:
            # Yield the correlation ID
            yield correlation_id
        finally:
            # Restore the previous correlation ID
            _correlation_id_var.reset(token) 