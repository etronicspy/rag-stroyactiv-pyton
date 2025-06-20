"""
Logging adapters for correlation ID integration.

Provides adapters to automatically inject correlation IDs into log records.
Extracted and refactored from core/monitoring/context.py.
"""

import logging
from typing import Callable, Dict, Any
from functools import wraps

from .correlation import get_correlation_id, get_or_generate_correlation_id


def log_with_correlation(logger_func: Callable) -> Callable:
    """
    Decorator to automatically add correlation ID to log messages.
    
    Usage:
        enhanced_info = log_with_correlation(logger.info)
        enhanced_info("This message will have correlation ID")
        
    Args:
        logger_func: Logger function to enhance
        
    Returns:
        Enhanced logger function with correlation ID
    """
    @wraps(logger_func)
    def wrapper(message: str, *args, **kwargs):
        # Get current correlation ID
        correlation_id = get_correlation_id()
        
        # Add correlation ID to extra if not already present
        extra = kwargs.get('extra', {})
        if correlation_id and 'correlation_id' not in extra:
            extra['correlation_id'] = correlation_id
            kwargs['extra'] = extra
        
        return logger_func(message, *args, **kwargs)
    
    return wrapper


class CorrelationLoggingAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically adds correlation ID to log records.
    
    Ensures all log messages from this adapter include the current correlation ID.
    """
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        """
        Initialize correlation logging adapter.
        
        Args:
            logger: Logger instance to adapt
            extra: Extra fields to always include
        """
        super().__init__(logger, extra)
    
    def process(self, msg, kwargs):
        """
        Process log record to add correlation ID.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Processed message and kwargs with correlation ID
        """
        # Get current correlation ID
        correlation_id = get_correlation_id()
        
        # Prepare extra fields
        extra = kwargs.get('extra', {}).copy()
        
        # Add correlation ID if available and not already present
        if correlation_id and 'correlation_id' not in extra:
            extra['correlation_id'] = correlation_id
        
        # Add adapter's extra fields
        extra.update(self.extra)
        
        # Update kwargs
        kwargs['extra'] = extra
        
        return msg, kwargs 