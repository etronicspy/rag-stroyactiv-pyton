"""
Context interfaces for the logging system.

This module defines interfaces for context management and correlation ID tracking:
- ICorrelationProvider: Interface for correlation ID management
- IContextProvider: Interface for general context management
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, ContextManager

T = TypeVar('T')


class ICorrelationProvider(ABC):
    """Interface for correlation ID management."""
    
    @abstractmethod
    def get_correlation_id(self) -> Optional[str]:
        """
        Get the current correlation ID.
        
        Returns:
            The current correlation ID or None if not set
        """
    
    @abstractmethod
    def set_correlation_id(self, correlation_id: str) -> None:
        """
        Set the current correlation ID.
        
        Args:
            correlation_id: The correlation ID to set
        """
    
    @abstractmethod
    def generate_correlation_id(self) -> str:
        """
        Generate a new correlation ID.
        
        Returns:
            A new correlation ID
        """
    
    @abstractmethod
    def clear_correlation_id(self) -> None:
        """Clear the current correlation ID."""
    
    @abstractmethod
    def with_correlation_id(self, correlation_id: Optional[str] = None) -> ContextManager[str]:
        """
        Context manager for correlation ID.
        
        Args:
            correlation_id: The correlation ID to use, or None to generate a new one
            
        Returns:
            A context manager that sets and clears the correlation ID
        """


class IContextProvider(ABC):
    """Interface for general context management."""
    
    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        """
        Get the current context.
        
        Returns:
            The current context as a dictionary
        """
    
    @abstractmethod
    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set the current context.
        
        Args:
            context: The context to set
        """
    
    @abstractmethod
    def update_context(self, **kwargs) -> None:
        """
        Update the current context.
        
        Args:
            **kwargs: The context values to update
        """
    
    @abstractmethod
    def clear_context(self) -> None:
        """Clear the current context."""
    
    @abstractmethod
    def with_context(self, **kwargs) -> ContextManager[Dict[str, Any]]:
        """
        Context manager for context.
        
        Args:
            **kwargs: The context values to set
            
        Returns:
            A context manager that sets and clears the context
        """
