"""
Base components for the logging system.

Provides fundamental interfaces, base classes, and formatters.
"""

from .formatters import BaseColorFormatter, ColoredFormatter, StructuredFormatter
from .interfaces import LoggerInterface
from .loggers import get_logger, setup_structured_logging

__all__ = [
    "LoggerInterface",
    "get_logger", 
    "setup_structured_logging",
    "StructuredFormatter",
    "ColoredFormatter", 
    "BaseColorFormatter"
] 