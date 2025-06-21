"""
Core logger implementation.

This module provides the base implementation of the ILogger interface.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from core.logging.interfaces import ILogger, IHandler


class Logger(ILogger):
    """Base implementation of the ILogger interface."""
    
    def __init__(self, name: str, level: Union[int, str] = logging.INFO):
        """
        Initialize a new logger.
        
        Args:
            name: The logger name
            level: The log level
        """
        self._name = name
        self._logger = logging.getLogger(name)
        self._handlers: List[IHandler] = []
        self.set_level(level)
    
    def debug(self, message: str, **kwargs) -> None:
        """
        Log a debug message.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
        self.log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """
        Log an info message.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
        self.log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """
        Log a warning message.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
        self.log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """
        Log an error message.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
        self.log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """
        Log a critical message.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
        self.log(logging.CRITICAL, message, **kwargs)
    
    def log(self, level: Union[int, str], message: str, **kwargs) -> None:
        """
        Log a message with the specified level.
        
        Args:
            level: The log level
            message: The message to log
            **kwargs: Additional context for the log message
        """
        # Convert string level to int if needed
        if isinstance(level, str):
            level = self._get_level_from_string(level)
        
        # Check if this level is enabled
        if not self._logger.isEnabledFor(level):
            return
        
        # Create the log record
        record = self._create_log_record(level, message, **kwargs)
        
        # Pass the record to all handlers
        for handler in self._handlers:
            handler.emit(record)
        
        # Also log using the standard logger
        self._logger.log(level, message, **kwargs)
    
    def add_handler(self, handler: IHandler) -> None:
        """
        Add a handler to this logger.
        
        Args:
            handler: The handler to add
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
    
    def remove_handler(self, handler: IHandler) -> None:
        """
        Remove a handler from this logger.
        
        Args:
            handler: The handler to remove
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
    
    def set_level(self, level: Union[int, str]) -> None:
        """
        Set the log level for this logger.
        
        Args:
            level: The log level
        """
        if isinstance(level, str):
            level = self._get_level_from_string(level)
        
        self._logger.setLevel(level)
    
    def get_level(self) -> int:
        """
        Get the log level for this logger.
        
        Returns:
            The log level
        """
        return self._logger.level
    
    def _create_log_record(self, level: int, message: str, **kwargs) -> Dict[str, Any]:
        """
        Create a log record.
        
        Args:
            level: The log level
            message: The message to log
            **kwargs: Additional context for the log message
            
        Returns:
            The log record
        """
        return {
            "name": self._name,
            "level": level,
            "level_name": logging.getLevelName(level),
            "message": message,
            "context": kwargs
        }
    
    def _get_level_from_string(self, level: str) -> int:
        """
        Convert a string level to an int.
        
        Args:
            level: The level string
            
        Returns:
            The level int
        """
        level_upper = level.upper()
        if hasattr(logging, level_upper):
            return getattr(logging, level_upper)
        
        # Default to INFO if the level is not recognized
        return logging.INFO


class AsyncLogger(Logger):
    """Asynchronous implementation of the Logger."""
    
    async def alog(self, level: Union[int, str], message: str, **kwargs) -> None:
        """
        Log a message asynchronously.
        
        Args:
            level: The log level
            message: The message to log
            **kwargs: Additional context for the log message
        """
        # This is a simple implementation that just calls the sync method
        # In a real implementation, this would use an async queue
        self.log(level, message, **kwargs)
    
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