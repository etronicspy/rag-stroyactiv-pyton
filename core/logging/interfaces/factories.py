"""
Factory interfaces for the logging system.

This module defines interfaces for factory classes:
- ILoggerFactory: Interface for logger factories
- IFormatterFactory: Interface for formatter factories
- IHandlerFactory: Interface for handler factories
"""

from abc import ABC, abstractmethod

from .core import ILogger, IFormatter, IHandler


class ILoggerFactory(ABC):
    """Interface for logger factories."""
    
    @abstractmethod
    def create_logger(self, name: str, **kwargs) -> ILogger:
        """
        Create a logger.
        
        Args:
            name: The logger name
            **kwargs: Additional configuration for the logger
            
        Returns:
            A logger instance
        """
    
    @abstractmethod
    def get_logger(self, name: str, **kwargs) -> ILogger:
        """
        Get a logger, creating it if it doesn't exist.
        
        Args:
            name: The logger name
            **kwargs: Additional configuration for the logger
            
        Returns:
            A logger instance
        """


class IFormatterFactory(ABC):
    """Interface for formatter factories."""
    
    @abstractmethod
    def create_formatter(self, formatter_type: str, **kwargs) -> IFormatter:
        """
        Create a formatter.
        
        Args:
            formatter_type: The formatter type
            **kwargs: Additional configuration for the formatter
            
        Returns:
            A formatter instance
        """
    
    @abstractmethod
    def get_formatter(self, formatter_type: str, **kwargs) -> IFormatter:
        """
        Get a formatter, creating it if it doesn't exist.
        
        Args:
            formatter_type: The formatter type
            **kwargs: Additional configuration for the formatter
            
        Returns:
            A formatter instance
        """


class IHandlerFactory(ABC):
    """Interface for handler factories."""
    
    @abstractmethod
    def create_handler(self, handler_type: str, **kwargs) -> IHandler:
        """
        Create a handler.
        
        Args:
            handler_type: The handler type
            **kwargs: Additional configuration for the handler
            
        Returns:
            A handler instance
        """
    
    @abstractmethod
    def get_handler(self, handler_type: str, **kwargs) -> IHandler:
        """
        Get a handler, creating it if it doesn't exist.
        
        Args:
            handler_type: The handler type
            **kwargs: Additional configuration for the handler
            
        Returns:
            A handler instance
        """
