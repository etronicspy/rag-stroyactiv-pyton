"""
Context management for correlation ID and request tracking.

Provides thread-safe, async-safe correlation ID propagation.
"""

from .correlation import (
    CorrelationContext,
    get_correlation_id,
    set_correlation_id, 
    generate_correlation_id,
    get_or_generate_correlation_id,
    with_correlation_context,
    get_request_metadata,
    set_request_metadata,
    clear_correlation_context
)
from .adapters import CorrelationLoggingAdapter, log_with_correlation

__all__ = [
    "CorrelationContext",
    "get_correlation_id",
    "set_correlation_id",
    "generate_correlation_id", 
    "get_or_generate_correlation_id",
    "with_correlation_context",
    "get_request_metadata",
    "set_request_metadata",
    "clear_correlation_context",
    "CorrelationLoggingAdapter",
    "log_with_correlation"
] 