"""
Dependency injection container for the logging system.

This module provides a dependency injection container for the logging system.
"""

from functools import lru_cache
from typing import Dict, Any, Type, TypeVar

from core.logging.interfaces import (
    ILogger,
    IFormatter,
    IHandler,
    ILoggingContext,
    IContextProvider,
    ICorrelationProvider,
    ILoggerFactory,
    IFormatterFactory,
    IHandlerFactory
)
from core.logging.core import (
    Logger,
    TextFormatter,
    ConsoleHandler,
    LoggingContext,
    ContextProvider,
    CorrelationProvider
)
from core.logging.factories import (
    LoggerFactory,
    FormatterFactory,
    HandlerFactory
)


T = TypeVar('T')


class LoggingContainer:
    """Dependency injection container for the logging system."""
    
    def __init__(self):
        """Initialize a new container."""
        self._registry: Dict[Type, Any] = {}
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register default implementations."""
        # Register core implementations
        self.register(ILogger, Logger)
        self.register(IFormatter, TextFormatter)
        self.register(IHandler, ConsoleHandler)
        self.register(ILoggingContext, LoggingContext)
        self.register(IContextProvider, ContextProvider)
        self.register(ICorrelationProvider, CorrelationProvider)
        
        # Register factories
        self.register(ILoggerFactory, LoggerFactory)
        self.register(IFormatterFactory, FormatterFactory)
        self.register(IHandlerFactory, HandlerFactory)
        
        # Register singleton instances
        self.register_instance(ILoggerFactory, LoggerFactory())
        self.register_instance(IFormatterFactory, FormatterFactory())
        self.register_instance(IHandlerFactory, HandlerFactory())
        self.register_instance(IContextProvider, ContextProvider())
        self.register_instance(ICorrelationProvider, CorrelationProvider())
    
    def register(self, interface: Type[T], implementation: Type[T]) -> None:
        """
        Register an implementation for an interface.
        
        Args:
            interface: The interface
            implementation: The implementation
        """
        self._registry[interface] = implementation
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """
        Register an instance for an interface.
        
        Args:
            interface: The interface
            instance: The instance
        """
        self._registry[interface] = instance
    
    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve an implementation for an interface.
        
        Args:
            interface: The interface
            
        Returns:
            An implementation of the interface
            
        Raises:
            KeyError: If no implementation is registered for the interface
        """
        if interface not in self._registry:
            raise KeyError(f"No implementation registered for {interface}")
        
        implementation = self._registry[interface]
        
        # If the implementation is an instance, return it
        if not isinstance(implementation, type):
            return implementation
        
        # Otherwise, create a new instance
        return implementation()


# Global singleton instance
_container = LoggingContainer()


@lru_cache(maxsize=32)
def get_container() -> LoggingContainer:
    """
    Get the global dependency injection container.
    
    Returns:
        The global container
    """
    return _container 