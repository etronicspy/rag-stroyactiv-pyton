"""
Context provider implementation.

This module provides a provider for context management.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Generator

from core.logging.interfaces import IContextProvider


# Context variable for context
_context_var: ContextVar[Dict[str, Any]] = ContextVar("context", default={})


class ContextProvider(IContextProvider):
    """Provider for context management."""
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get the current context.
        
        Returns:
            The current context
        """
        return _context_var.get().copy()
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set the current context.
        
        Args:
            context: The context to set
        """
        _context_var.set(context.copy())
    
    def add_to_context(self, key: str, value: Any) -> None:
        """
        Add a value to the current context.
        
        Args:
            key: The key to add
            value: The value to add
        """
        context = _context_var.get().copy()
        context[key] = value
        _context_var.set(context)
    
    def remove_from_context(self, key: str) -> None:
        """
        Remove a key from the current context.
        
        Args:
            key: The key to remove
        """
        context = _context_var.get().copy()
        if key in context:
            del context[key]
        _context_var.set(context)
    
    def clear_context(self) -> None:
        """Clear the current context."""
        _context_var.set({})
    
    @contextmanager
    def with_context(self, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        Context manager for setting context values.
        
        Args:
            **kwargs: The context values to set
            
        Yields:
            The updated context
        """
        # Save the previous context
        previous_context = self.get_context()
        
        # Update the context
        context = previous_context.copy()
        context.update(kwargs)
        token = _context_var.set(context)
        
        try:
            # Yield the updated context
            yield context
        finally:
            # Restore the previous context
            _context_var.reset(token)
    
    @contextmanager
    def with_merged_context(self, context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        Context manager for merging context values.
        
        Args:
            context: The context to merge
            
        Yields:
            The merged context
        """
        return self.with_context(**context) 