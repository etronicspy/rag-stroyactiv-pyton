"""
Interfaces for the logging system.

This module exports all interfaces for the logging system.
"""

# Core interfaces
from .core import (
    ILogger,
    IFormatter,
    IHandler,
    ILoggingContext
)

# Context interfaces
from .context import (
    ICorrelationProvider,
    IContextProvider
)

# Database interfaces
from .database import (
    IDatabaseLogger,
    IVectorDatabaseLogger
)

# HTTP interfaces
from .http_interface import (
    IRequestLogger,
    IMiddlewareLogger
)

# Metrics interfaces
from .metrics import (
    IMetricsCollector,
    IPerformanceTracker
)

# Factory interfaces
from .factories import (
    ILoggerFactory,
    IFormatterFactory,
    IHandlerFactory
)

__all__ = [
    # Core interfaces
    "ILogger",
    "IFormatter",
    "IHandler",
    "ILoggingContext",
    
    # Context interfaces
    "ICorrelationProvider",
    "IContextProvider",
    
    # Database interfaces
    "IDatabaseLogger",
    "IVectorDatabaseLogger",
    
    # HTTP interfaces
    "IRequestLogger",
    "IMiddlewareLogger",
    
    # Metrics interfaces
    "IMetricsCollector",
    "IPerformanceTracker",
    
    # Factory interfaces
    "ILoggerFactory",
    "IFormatterFactory",
    "IHandlerFactory"
] 