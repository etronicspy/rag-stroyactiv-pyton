"""
Handler factory implementation.

This module provides an implementation of the IHandlerFactory interface.
"""

import sys
from functools import lru_cache
from typing import Dict, Optional, TextIO

from core.logging.interfaces import IHandlerFactory, IHandler, IFormatter
from core.logging.core import (
    ConsoleHandler,
    FileHandler,
    RotatingFileHandler,
    NullHandler
)
from core.logging.factories.formatter_factory import get_text_formatter


class HandlerFactory(IHandlerFactory):
    """Implementation of the IHandlerFactory interface."""
    
    def __init__(self):
        """Initialize a new handler factory."""
        self._handlers: Dict[str, IHandler] = {}
    
    def create_handler(self, handler_type: str, **kwargs) -> IHandler:
        """
        Create a handler.
        
        Args:
            handler_type: The handler type
            **kwargs: Additional configuration for the handler
            
        Returns:
            A handler instance
        """
        # Get the formatter
        formatter = kwargs.pop("formatter", get_text_formatter())
        
        # Create the handler based on the type
        if handler_type == "console":
            stream = kwargs.pop("stream", sys.stdout)
            handler = ConsoleHandler(formatter=formatter, stream=stream)
        elif handler_type == "file":
            filename = kwargs.pop("filename")
            mode = kwargs.pop("mode", "a")
            encoding = kwargs.pop("encoding", "utf-8")
            handler = FileHandler(
                filename=filename,
                formatter=formatter,
                mode=mode,
                encoding=encoding
            )
        elif handler_type == "rotating_file":
            filename = kwargs.pop("filename")
            mode = kwargs.pop("mode", "a")
            encoding = kwargs.pop("encoding", "utf-8")
            max_bytes = kwargs.pop("max_bytes", 10 * 1024 * 1024)  # 10 MB
            backup_count = kwargs.pop("backup_count", 5)
            handler = RotatingFileHandler(
                filename=filename,
                formatter=formatter,
                mode=mode,
                encoding=encoding,
                max_bytes=max_bytes,
                backup_count=backup_count
            )
        elif handler_type == "null":
            handler = NullHandler(formatter=formatter)
        else:
            # Default to null handler
            handler = NullHandler(formatter=formatter)
        
        return handler
    
    def get_handler(self, handler_type: str, **kwargs) -> IHandler:
        """
        Get a handler, creating it if it doesn't exist.
        
        Args:
            handler_type: The handler type
            **kwargs: Additional configuration for the handler
            
        Returns:
            A handler instance
        """
        # Generate a cache key
        cache_key = self._generate_cache_key(handler_type, **kwargs)
        
        # Check if the handler exists
        if cache_key in self._handlers:
            return self._handlers[cache_key]
        
        # Create the handler
        handler = self.create_handler(handler_type, **kwargs)
        
        # Cache the handler
        self._handlers[cache_key] = handler
        
        return handler
    
    def _generate_cache_key(self, handler_type: str, **kwargs) -> str:
        """
        Generate a cache key for a handler.
        
        Args:
            handler_type: The handler type
            **kwargs: Additional configuration for the handler
            
        Returns:
            A cache key
        """
        # Start with the handler type
        key = handler_type
        
        # Add kwargs to the key
        for k, v in sorted(kwargs.items()):
            # Skip formatter since it's an object
            if k == "formatter":
                continue
            
            # Skip stream for console handler
            if k == "stream" and handler_type == "console":
                continue
            
            key += f"_{k}_{v}"
        
        return key


# Global singleton instance
_handler_factory = HandlerFactory()


def get_handler_factory() -> IHandlerFactory:
    """
    Get the global handler factory.
    
    Returns:
        The global handler factory
    """
    return _handler_factory


@lru_cache(maxsize=8)
def get_console_handler(
    formatter: Optional[IFormatter] = None,
    stream: TextIO = sys.stdout
) -> IHandler:
    """
    Get a console handler with caching.
    
    Args:
        formatter: The formatter to use
        stream: The stream to write to
        
    Returns:
        A console handler instance
    """
    return _handler_factory.get_handler(
        "console",
        formatter=formatter,
        stream=stream
    )


@lru_cache(maxsize=16)
def get_file_handler(
    filename: str,
    formatter: Optional[IFormatter] = None,
    mode: str = "a",
    encoding: str = "utf-8"
) -> IHandler:
    """
    Get a file handler with caching.
    
    Args:
        filename: The file to write to
        formatter: The formatter to use
        mode: The file mode
        encoding: The file encoding
        
    Returns:
        A file handler instance
    """
    return _handler_factory.get_handler(
        "file",
        filename=filename,
        formatter=formatter,
        mode=mode,
        encoding=encoding
    )


@lru_cache(maxsize=16)
def get_rotating_file_handler(
    filename: str,
    formatter: Optional[IFormatter] = None,
    mode: str = "a",
    encoding: str = "utf-8",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> IHandler:
    """
    Get a rotating file handler with caching.
    
    Args:
        filename: The file to write to
        formatter: The formatter to use
        mode: The file mode
        encoding: The file encoding
        max_bytes: The maximum file size in bytes
        backup_count: The number of backup files to keep
        
    Returns:
        A rotating file handler instance
    """
    return _handler_factory.get_handler(
        "rotating_file",
        filename=filename,
        formatter=formatter,
        mode=mode,
        encoding=encoding,
        max_bytes=max_bytes,
        backup_count=backup_count
    )


@lru_cache(maxsize=4)
def get_null_handler(
    formatter: Optional[IFormatter] = None
) -> IHandler:
    """
    Get a null handler with caching.
    
    Args:
        formatter: The formatter to use
        
    Returns:
        A null handler instance
    """
    return _handler_factory.get_handler(
        "null",
        formatter=formatter
    ) 