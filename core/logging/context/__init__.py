"""
Context management for correlation ID and request tracking.

Provides thread-safe, async-safe correlation ID propagation.
"""

from .adapters import CorrelationLoggingAdapter, log_with_correlation
from .correlation import (
    CorrelationContext,
    clear_correlation_context,
    generate_correlation_id,
    get_correlation_id,
    get_or_generate_correlation_id,
    get_request_metadata,
    set_correlation_id,
    set_request_metadata,
    with_correlation_context,
)

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