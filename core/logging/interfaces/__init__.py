"""
Interfaces for the logging system.

This module exports all interfaces for the logging system.
"""

# Core interfaces
# Context interfaces
from .context import IContextProvider, ICorrelationProvider
from .core import IFormatter, IHandler, ILogger, ILoggingContext

# Database interfaces
from .database import IDatabaseLogger, IVectorDatabaseLogger

# Factory interfaces
from .factories import IFormatterFactory, IHandlerFactory, ILoggerFactory

# HTTP interfaces
from .http_interface import IMiddlewareLogger, IRequestLogger

# Metrics interfaces
from .metrics import IMetricsCollector, IPerformanceTracker

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