"""
Logger factory implementation.

This module provides an implementation of the ILoggerFactory interface.
"""

import logging
from functools import lru_cache
from typing import Dict, Optional, Union

from core.logging.interfaces import ILoggerFactory, ILogger
from core.logging.core import Logger, AsyncLogger


class LoggerFactory(ILoggerFactory):
    """Implementation of the ILoggerFactory interface."""
    
    def __init__(self):
        """Initialize a new logger factory."""
        self._loggers: Dict[str, ILogger] = {}
    
    def create_logger(self, name: str, **kwargs) -> ILogger:
        """
        Create a logger.
        
        Args:
            name: The logger name
            **kwargs: Additional configuration for the logger
            
        Returns:
            A logger instance
        """
        # Get the logger type
        logger_type = kwargs.pop("logger_type", "sync")
        
        # Create the logger
        if logger_type == "async":
            logger = AsyncLogger(name, **kwargs)
        else:
            logger = Logger(name, **kwargs)
        
        # Add handlers if provided
        handlers = kwargs.pop("handlers", [])
        for handler in handlers:
            logger.add_handler(handler)
        
        return logger
    
    def get_logger(self, name: str, **kwargs) -> ILogger:
        """
        Get a logger, creating it if it doesn't exist.
        
        Args:
            name: The logger name
            **kwargs: Additional configuration for the logger
            
        Returns:
            A logger instance
        """
        # Check if the logger exists
        if name in self._loggers:
            return self._loggers[name]
        
        # Create the logger
        logger = self.create_logger(name, **kwargs)
        
        # Cache the logger
        self._loggers[name] = logger
        
        return logger


# Global singleton instance
_logger_factory = LoggerFactory()


def get_logger_factory() -> ILoggerFactory:
    """
    Get the global logger factory.
    
    Returns:
        The global logger factory
    """
    return _logger_factory


@lru_cache(maxsize=128)
def get_logger(name: str, level: Union[int, str] = logging.INFO) -> ILogger:
    """
    Get a logger with caching.
    
    Args:
        name: The logger name
        level: The log level
        
    Returns:
        A logger instance
    """
    return _logger_factory.get_logger(name, level=level)


@lru_cache(maxsize=128)
def get_async_logger(name: str, level: Union[int, str] = logging.INFO) -> AsyncLogger:
    """
    Get an async logger with caching.
    
    Args:
        name: The logger name
        level: The log level
        
    Returns:
        An async logger instance
    """
    return _logger_factory.get_logger(name, logger_type="async", level=level) 