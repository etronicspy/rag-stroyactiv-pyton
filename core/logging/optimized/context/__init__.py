"""
Context optimization module.

This module provides components for optimizing context management in logging.
"""

from core.logging.optimized.context.context_pool import (
    ContextPool,
    get_context,
    get_default_pool,
)
from core.logging.optimized.context.context_propagator import (
    ContextPropagator,
    ContextSnapshot,
    create_snapshot,
    get_default_propagator,
)

__all__ = [
    "ContextPool",
    "get_context",
    "get_default_pool",
    "ContextPropagator",
    "ContextSnapshot",
    "create_snapshot",
    "get_default_propagator",
] 