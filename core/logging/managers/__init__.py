"""
Management layer for logging system.

Provides unified managers and factory classes for logger creation.
"""

from .unified import (
    LogLevel,
    OperationContext,
    UnifiedLoggingManager,
    get_unified_logging_manager,
    log_database_operation,
    log_database_operation_optimized,
)

__all__ = [
    "UnifiedLoggingManager",
    "get_unified_logging_manager",
    "log_database_operation",
    "log_database_operation_optimized",
    "OperationContext", 
    "LogLevel"
] 