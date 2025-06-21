"""
Memory optimization module.

This module provides components for optimizing memory usage in logging.
"""

from core.logging.optimized.memory.logger_pool import LoggerPool, get_logger, get_default_pool
from core.logging.optimized.memory.message_cache import (
    MessageCache,
    StructuredLogCache,
    get_default_message_cache,
    get_default_structured_log_cache,
)

__all__ = [
    "LoggerPool",
    "get_logger",
    "get_default_pool",
    "MessageCache",
    "StructuredLogCache",
    "get_default_message_cache",
    "get_default_structured_log_cache",
] 