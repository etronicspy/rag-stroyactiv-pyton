"""
Formatter factory implementation.

This module provides an implementation of the IFormatterFactory interface.
"""

from functools import lru_cache
from typing import Dict, Optional

from core.logging.interfaces import IFormatterFactory, IFormatter
from core.logging.core import (
    TextFormatter,
    JsonFormatter,
    ColoredFormatter
)


class FormatterFactory(IFormatterFactory):
    """Implementation of the IFormatterFactory interface."""
    
    def __init__(self):
        """Initialize a new formatter factory."""
        self._formatters: Dict[str, IFormatter] = {}
    
    def create_formatter(self, formatter_type: str, **kwargs) -> IFormatter:
        """
        Create a formatter.
        
        Args:
            formatter_type: The formatter type
            **kwargs: Additional configuration for the formatter
            
        Returns:
            A formatter instance
        """
        # Create the formatter based on the type
        if formatter_type == "json":
            formatter = JsonFormatter(**kwargs)
        elif formatter_type == "colored":
            formatter = ColoredFormatter(**kwargs)
        else:
            # Default to text formatter
            formatter = TextFormatter(**kwargs)
        
        return formatter
    
    def get_formatter(self, formatter_type: str, **kwargs) -> IFormatter:
        """
        Get a formatter, creating it if it doesn't exist.
        
        Args:
            formatter_type: The formatter type
            **kwargs: Additional configuration for the formatter
            
        Returns:
            A formatter instance
        """
        # Generate a cache key
        cache_key = self._generate_cache_key(formatter_type, **kwargs)
        
        # Check if the formatter exists
        if cache_key in self._formatters:
            return self._formatters[cache_key]
        
        # Create the formatter
        formatter = self.create_formatter(formatter_type, **kwargs)
        
        # Cache the formatter
        self._formatters[cache_key] = formatter
        
        return formatter
    
    def _generate_cache_key(self, formatter_type: str, **kwargs) -> str:
        """
        Generate a cache key for a formatter.
        
        Args:
            formatter_type: The formatter type
            **kwargs: Additional configuration for the formatter
            
        Returns:
            A cache key
        """
        # Start with the formatter type
        key = formatter_type
        
        # Add kwargs to the key
        for k, v in sorted(kwargs.items()):
            key += f"_{k}_{v}"
        
        return key


# Global singleton instance
_formatter_factory = FormatterFactory()


def get_formatter_factory() -> IFormatterFactory:
    """
    Get the global formatter factory.
    
    Returns:
        The global formatter factory
    """
    return _formatter_factory


@lru_cache(maxsize=32)
def get_text_formatter(
    timestamp_format: str = "%Y-%m-%d %H:%M:%S",
    template: str = "{timestamp} - {name} - {level_name} - {message}"
) -> IFormatter:
    """
    Get a text formatter with caching.
    
    Args:
        timestamp_format: The timestamp format
        template: The template string
        
    Returns:
        A text formatter instance
    """
    return _formatter_factory.get_formatter(
        "text",
        timestamp_format=timestamp_format,
        template=template
    )


@lru_cache(maxsize=32)
def get_json_formatter(
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
) -> IFormatter:
    """
    Get a JSON formatter with caching.
    
    Args:
        timestamp_format: The timestamp format
        
    Returns:
        A JSON formatter instance
    """
    return _formatter_factory.get_formatter(
        "json",
        timestamp_format=timestamp_format
    )


@lru_cache(maxsize=32)
def get_colored_formatter(
    timestamp_format: str = "%Y-%m-%d %H:%M:%S",
    template: str = "{timestamp} - {name} - {level_name} - {message}",
    use_colors: bool = True
) -> IFormatter:
    """
    Get a colored formatter with caching.
    
    Args:
        timestamp_format: The timestamp format
        template: The template string
        use_colors: Whether to use colors
        
    Returns:
        A colored formatter instance
    """
    return _formatter_factory.get_formatter(
        "colored",
        timestamp_format=timestamp_format,
        template=template,
        use_colors=use_colors
    ) 