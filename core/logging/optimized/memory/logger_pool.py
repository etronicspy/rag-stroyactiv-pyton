"""
Logger pool implementation.

This module provides a pool of loggers for efficient reuse.
"""

import logging
import threading
from typing import Dict, Optional, Union, Any, Type

from core.logging.interfaces import ILogger
from core.logging.core import Logger


class LoggerPool:
    """
    Pool of loggers for efficient reuse.
    
    This pool maintains a cache of loggers to avoid creating new instances.
    """
    
    def __init__(self, logger_class: Type[ILogger] = Logger, max_size: int = 100):
        """
        Initialize a new logger pool.
        
        Args:
            logger_class: The logger class to use
            max_size: The maximum pool size
        """
        self._logger_class = logger_class
        self._max_size = max_size
        self._loggers: Dict[str, ILogger] = {}
        self._lock = threading.RLock()
        self._hit_count = 0
        self._miss_count = 0
    
    def get_logger(self, name: str, level: Union[int, str] = logging.INFO, **kwargs: Any) -> ILogger:
        """
        Get a logger from the pool.
        
        Args:
            name: The logger name
            level: The log level
            **kwargs: Additional arguments for the logger
            
        Returns:
            A logger instance
        """
        with self._lock:
            # Check if the logger exists in the pool
            if name in self._loggers:
                # Update hit count
                self._hit_count += 1
                
                # Get the logger
                logger = self._loggers[name]
                
                # Update the level if needed
                if logger.level != level:
                    logger.setLevel(level)
                
                return logger
            
            # Update miss count
            self._miss_count += 1
            
            # Check if the pool is full
            if len(self._loggers) >= self._max_size:
                # Remove the least recently used logger
                self._remove_lru_logger()
            
            # Create a new logger
            logger = self._logger_class(name, level, **kwargs)
            
            # Add to the pool
            self._loggers[name] = logger
            
            return logger
    
    def remove_logger(self, name: str) -> None:
        """
        Remove a logger from the pool.
        
        Args:
            name: The logger name
        """
        with self._lock:
            if name in self._loggers:
                del self._loggers[name]
    
    def clear(self) -> None:
        """Clear the pool."""
        with self._lock:
            self._loggers.clear()
    
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
                "size": len(self._loggers),
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
    
    def _remove_lru_logger(self) -> None:
        """Remove the least recently used logger from the pool."""
        # Simple implementation: remove the first logger
        if self._loggers:
            name = next(iter(self._loggers))
            del self._loggers[name]


# Singleton instance
_default_pool: Optional[LoggerPool] = None
_pool_lock = threading.RLock()


def get_default_pool() -> LoggerPool:
    """
    Get the default logger pool.
    
    Returns:
        The default logger pool
    """
    global _default_pool
    
    with _pool_lock:
        if _default_pool is None:
            _default_pool = LoggerPool()
        
        return _default_pool


def get_logger(name: str, level: Union[int, str] = logging.INFO, **kwargs: Any) -> ILogger:
    """
    Get a logger from the default pool.
    
    Args:
        name: The logger name
        level: The log level
        **kwargs: Additional arguments for the logger
        
    Returns:
        A logger instance
    """
    return get_default_pool().get_logger(name, level, **kwargs) 