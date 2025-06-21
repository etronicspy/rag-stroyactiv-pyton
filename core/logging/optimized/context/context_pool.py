"""
Context pool implementation.

This module provides a pool of logging contexts for efficient reuse.
"""

import threading
from typing import Dict, Any, Optional, Type

from core.logging.interfaces import ILoggingContext


class ContextPool:
    """
    Pool of logging contexts for efficient reuse.
    
    This pool maintains a cache of contexts to avoid creating new instances.
    """
    
    def __init__(self, context_class: Type[ILoggingContext], max_size: int = 100):
        """
        Initialize a new context pool.
        
        Args:
            context_class: The context class to use
            max_size: The maximum pool size
        """
        self._context_class = context_class
        self._max_size = max_size
        self._contexts: Dict[str, ILoggingContext] = {}
        self._lock = threading.RLock()
        self._hit_count = 0
        self._miss_count = 0
    
    def get_context(self, name: str, **kwargs: Any) -> ILoggingContext:
        """
        Get a context from the pool.
        
        Args:
            name: The context name
            **kwargs: Additional arguments for the context
            
        Returns:
            A context instance
        """
        with self._lock:
            # Check if the context exists in the pool
            if name in self._contexts:
                # Update hit count
                self._hit_count += 1
                
                # Get the context
                context = self._contexts[name]
                
                # Reset the context
                context.reset(**kwargs)
                
                return context
            
            # Update miss count
            self._miss_count += 1
            
            # Check if the pool is full
            if len(self._contexts) >= self._max_size:
                # Remove the least recently used context
                self._remove_lru_context()
            
            # Create a new context
            context = self._context_class(name, **kwargs)
            
            # Add to the pool
            self._contexts[name] = context
            
            return context
    
    def remove_context(self, name: str) -> None:
        """
        Remove a context from the pool.
        
        Args:
            name: The context name
        """
        with self._lock:
            if name in self._contexts:
                del self._contexts[name]
    
    def clear(self) -> None:
        """Clear the pool."""
        with self._lock:
            self._contexts.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the pool.
        
        Returns:
            Statistics about the pool
        """
        with self._lock:
            hit_rate = 0.0
            if self._hit_count + self._miss_count > 0:
                hit_rate = self._hit_count / (self._hit_count + self._miss_count)
            
            return {
                "size": len(self._contexts),
                "max_size": self._max_size,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
            }
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        with self._lock:
            self._hit_count = 0
            self._miss_count = 0
    
    def _remove_lru_context(self) -> None:
        """Remove the least recently used context from the pool."""
        # Simple implementation: remove the first context
        if self._contexts:
            name = next(iter(self._contexts))
            del self._contexts[name]


# Singleton instance
_default_pool: Optional[ContextPool] = None
_pool_lock = threading.RLock()


def get_default_pool(context_class: Type[ILoggingContext]) -> ContextPool:
    """
    Get the default context pool.
    
    Args:
        context_class: The context class to use
        
    Returns:
        The default context pool
    """
    global _default_pool
    
    with _pool_lock:
        if _default_pool is None:
            _default_pool = ContextPool(context_class)
        
        return _default_pool


def get_context(context_class: Type[ILoggingContext], name: str, **kwargs: Any) -> ILoggingContext:
    """
    Get a context from the default pool.
    
    Args:
        context_class: The context class to use
        name: The context name
        **kwargs: Additional arguments for the context
        
    Returns:
        A context instance
    """
    return get_default_pool(context_class).get_context(name, **kwargs) 