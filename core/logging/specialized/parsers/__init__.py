"""
Specialized Parser Logging Package

This package provides specialized logging functionality for parser operations,
integrating with the main logging system to provide detailed tracking and monitoring.
"""

from .parser_logger import (
    ParserLogger,
    AIParserLogger,
    MaterialParserLogger,
    BatchParserLogger,
    get_parser_logger,
    get_ai_parser_logger,
    get_material_parser_logger,
    get_batch_parser_logger
)

from .parser_metrics import (
    ParserMetrics,
    AIParserMetrics,
    get_parser_metrics
)

# Version information
__version__ = "1.0.0"
__author__ = "RAG Construction Materials Team"
__description__ = "Specialized logging for parser operations"

# Export all logging types
__all__ = [
    'ParserLogger',
    'AIParserLogger',
    'MaterialParserLogger',
    'BatchParserLogger',
    'get_parser_logger',
    'get_ai_parser_logger',
    'get_material_parser_logger',
    'get_batch_parser_logger',
    'ParserMetrics',
    'AIParserMetrics',
    'get_parser_metrics',
    '__version__',
    '__author__',
    '__description__'
] 