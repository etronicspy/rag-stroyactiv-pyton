"""
Optimization module.

This module provides components for optimizing logging performance.
"""

from core.logging.optimized.async_logging import (
    AsyncLogger,
    BatchProcessor,
    LoggingQueue,
    AsyncWorker,
)
from core.logging.optimized.memory import (
    LoggerPool,
    MessageCache,
    StructuredLogCache,
    get_logger,
    get_default_pool,
    get_default_message_cache,
    get_default_structured_log_cache,
)
from core.logging.optimized.context import (
    ContextPool,
    ContextPropagator,
    ContextSnapshot,
    get_context,
    get_default_propagator,
    create_snapshot,
)

__all__ = [
    # Async logging
    "AsyncLogger",
    "BatchProcessor",
    "LoggingQueue",
    "AsyncWorker",
    
    # Memory optimization
    "LoggerPool",
    "MessageCache",
    "StructuredLogCache",
    "get_logger",
    "get_default_pool",
    "get_default_message_cache",
    "get_default_structured_log_cache",
    
    # Context optimization
    "ContextPool",
    "ContextPropagator",
    "ContextSnapshot",
    "get_context",
    "get_default_propagator",
    "create_snapshot",
] 