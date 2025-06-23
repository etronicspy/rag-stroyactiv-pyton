"""
Core interfaces for the logging system.

This module defines the fundamental interfaces for the logging system:
- ILogger: Base interface for all loggers
- IFormatter: Interface for log formatters
- IHandler: Interface for log handlers
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union


class IFormatter(ABC):
    """Interface for log formatters."""
    
    @abstractmethod
    def format(self, record: Dict[str, Any]) -> str:
        """
        Format a log record into a string.
        
        Args:
            record: The log record to format
            
        Returns:
            The formatted log record as a string
        """


class IHandler(ABC):
    """Interface for log handlers."""
    
    @abstractmethod
    def emit(self, record: Dict[str, Any]) -> None:
        """
        Emit a log record.
        
        Args:
            record: The log record to emit
        """
    
    @abstractmethod
    def set_formatter(self, formatter: IFormatter) -> None:
        """
        Set the formatter for this handler.
        
        Args:
            formatter: The formatter to use
        """
    
    @abstractmethod
    def close(self) -> None:
        """Close the handler and release any resources."""


class ILogger(ABC):
    """Base interface for all loggers."""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """
        Log a debug message.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """
        Log an info message.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """
        Log a warning message.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """
        Log an error message.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """
        Log a critical message.
        
        Args:
            message: The message to log
            **kwargs: Additional context for the log message
        """
    
    @abstractmethod
    def log(self, level: Union[int, str], message: str, **kwargs) -> None:
        """
        Log a message with the specified level.
        
        Args:
            level: The log level
            message: The message to log
            **kwargs: Additional context for the log message
        """
    
    @abstractmethod
    def add_handler(self, handler: IHandler) -> None:
        """
        Add a handler to this logger.
        
        Args:
            handler: The handler to add
        """
    
    @abstractmethod
    def remove_handler(self, handler: IHandler) -> None:
        """
        Remove a handler from this logger.
        
        Args:
            handler: The handler to remove
        """
    
    @abstractmethod
    def set_level(self, level: Union[int, str]) -> None:
        """
        Set the log level for this logger.
        
        Args:
            level: The log level
        """
    
    @abstractmethod
    def get_level(self) -> Union[int, str]:
        """
        Get the log level for this logger.
        
        Returns:
            The log level
        """


class ILoggingContext(ABC):
    """Interface for logging context management."""
    
    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        """
        Get the current logging context.
        
        Returns:
            The current logging context as a dictionary
        """
    
    @abstractmethod
    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set the current logging context.
        
        Args:
            context: The context to set
        """
    
    @abstractmethod
    def update_context(self, **kwargs) -> None:
        """
        Update the current logging context.
        
        Args:
            **kwargs: The context values to update
        """
    
    @abstractmethod
    def clear_context(self) -> None:
        """Clear the current logging context."""
