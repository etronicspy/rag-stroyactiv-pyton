"""
🎯 Correlation ID Context Management System

Provides thread-safe, async-safe correlation ID propagation through the entire application.
ЭТАП 3: Полное покрытие correlation ID для 100% трассировки.
"""

import uuid
from contextvars import ContextVar
from typing import Optional, Callable, Any, Dict
from functools import wraps
import asyncio
import logging

# Context variable for correlation ID - thread-safe and async-safe
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

# Context variable for additional request metadata
request_metadata: ContextVar[Dict[str, Any]] = ContextVar('request_metadata', default={})


class CorrelationContext:
    """
    🎯 Correlation ID context manager and utilities.
    
    Provides:
    - Automatic correlation ID generation
    - Context propagation through async/sync calls
    - Integration with logging system
    - Request metadata management
    """
    
    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """
        Get current correlation ID from context.
        
        Returns:
            Current correlation ID or None if not set
        """
        return correlation_id.get()
    
    @staticmethod
    def set_correlation_id(corr_id: str) -> None:
        """
        Set correlation ID in current context.
        
        Args:
            corr_id: Correlation ID to set
        """
        correlation_id.set(corr_id)
    
    @staticmethod
    def generate_correlation_id() -> str:
        """
        Generate new correlation ID and set it in context.
        
        Returns:
            Generated correlation ID
        """
        new_id = str(uuid.uuid4())
        correlation_id.set(new_id)
        return new_id
    
    @staticmethod
    def get_or_generate_correlation_id() -> str:
        """
        Get current correlation ID or generate new one if not exists.
        
        Returns:
            Correlation ID (existing or newly generated)
        """
        current_id = correlation_id.get()
        if current_id is None:
            current_id = CorrelationContext.generate_correlation_id()
        return current_id
    
    @staticmethod
    def get_request_metadata() -> Dict[str, Any]:
        """
        Get current request metadata.
        
        Returns:
            Current request metadata dictionary
        """
        metadata = request_metadata.get()
        return metadata if metadata else {}
    
    @staticmethod
    def set_request_metadata(metadata: Dict[str, Any]) -> None:
        """
        Set request metadata in current context.
        
        Args:
            metadata: Metadata dictionary to set
        """
        request_metadata.set(metadata.copy())
    
    @staticmethod
    def update_request_metadata(key: str, value: Any) -> None:
        """
        Update single key in request metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        current_metadata = request_metadata.get({})
        current_metadata[key] = value
        request_metadata.set(current_metadata)
    
    @classmethod
    def with_correlation_id(cls, corr_id: Optional[str] = None):
        """
        Context manager to set correlation ID for a block of operations.
        
        Args:
            corr_id: Correlation ID to use (generates new if None)
            
        Usage:
            with CorrelationContext.with_correlation_id():
                # All operations here will have the same correlation ID
                logger.info("This log will have correlation ID")
        """
        class CorrelationContextManager:
            def __init__(self, correlation_id_value: Optional[str]):
                self.correlation_id_value = correlation_id_value or str(uuid.uuid4())
                self.token = None
            
            def __enter__(self):
                self.token = correlation_id.set(self.correlation_id_value)
                return self.correlation_id_value
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.token is not None:
                    correlation_id.reset(self.token)
        
        return CorrelationContextManager(corr_id)
    
    @classmethod
    def with_request_context(cls, corr_id: Optional[str] = None, 
                           metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager to set full request context.
        
        Args:
            corr_id: Correlation ID to use
            metadata: Request metadata to set
            
        Usage:
            with CorrelationContext.with_request_context(
                corr_id="12345", 
                metadata={"user_id": "user123", "ip": "1.2.3.4"}
            ):
                # All operations here will have correlation ID and metadata
                pass
        """
        class RequestContextManager:
            def __init__(self, correlation_id_value: Optional[str], 
                        metadata_value: Optional[Dict[str, Any]]):
                self.correlation_id_value = correlation_id_value or str(uuid.uuid4())
                self.metadata_value = metadata_value or {}
                self.corr_token = None
                self.meta_token = None
            
            def __enter__(self):
                self.corr_token = correlation_id.set(self.correlation_id_value)
                self.meta_token = request_metadata.set(self.metadata_value.copy())
                return self.correlation_id_value
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.corr_token is not None:
                    correlation_id.reset(self.corr_token)
                if self.meta_token is not None:
                    request_metadata.reset(self.meta_token)
        
        return RequestContextManager(corr_id, metadata)


def with_correlation_context(func: Callable) -> Callable:
    """
    Decorator to ensure function runs with correlation ID context.
    
    If correlation ID doesn't exist, generates new one.
    Preserves existing correlation ID if present.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with correlation context
        
    Usage:
        @with_correlation_context
        async def my_function():
            # This function will always have correlation ID available
            corr_id = CorrelationContext.get_correlation_id()
            logger.info(f"Processing with correlation ID: {corr_id}")
    """
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Ensure correlation ID exists
            CorrelationContext.get_or_generate_correlation_id()
            return await func(*args, **kwargs)
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Ensure correlation ID exists
            CorrelationContext.get_or_generate_correlation_id()
            return func(*args, **kwargs)
        return sync_wrapper


def log_with_correlation(logger_func: Callable) -> Callable:
    """
    Decorator to automatically add correlation ID to log messages.
    
    Args:
        logger_func: Logger function (logger.info, logger.error, etc.)
        
    Returns:
        Enhanced logger function with correlation ID
        
    Usage:
        @log_with_correlation
        def enhanced_info(message, *args, **kwargs):
            return logger.info(message, *args, **kwargs)
    """
    @wraps(logger_func)
    def wrapper(message: str, *args, **kwargs):
        corr_id = CorrelationContext.get_correlation_id()
        if corr_id:
            # Add correlation ID to extra fields
            extra = kwargs.get('extra', {})
            extra['correlation_id'] = corr_id
            kwargs['extra'] = extra
            
            # Prefix message with correlation ID for easy reading
            if not message.startswith('['):
                message = f"[{corr_id}] {message}"
        
        return logger_func(message, *args, **kwargs)
    return wrapper


class CorrelationLoggingAdapter(logging.LoggerAdapter):
    """
    Logging adapter that automatically adds correlation ID to all log records.
    
    Usage:
        logger = logging.getLogger(__name__)
        corr_logger = CorrelationLoggingAdapter(logger)
        corr_logger.info("This message will have correlation ID")
    """
    
    def process(self, msg, kwargs):
        """Add correlation ID to log record."""
        corr_id = CorrelationContext.get_correlation_id()
        metadata = CorrelationContext.get_request_metadata()
        
        # Add correlation ID to extra fields
        extra = kwargs.get('extra', {})
        if corr_id:
            extra['correlation_id'] = corr_id
        
        # Add request metadata to extra fields
        for key, value in metadata.items():
            if key not in extra:  # Don't override existing extra fields
                extra[key] = value
        
        if extra:
            kwargs['extra'] = extra
        
        # Prefix message with correlation ID for readability
        if corr_id and not str(msg).startswith('['):
            msg = f"[{corr_id}] {msg}"
        
        return msg, kwargs


# Convenience functions for easy import
get_correlation_id = CorrelationContext.get_correlation_id
set_correlation_id = CorrelationContext.set_correlation_id
generate_correlation_id = CorrelationContext.generate_correlation_id
get_or_generate_correlation_id = CorrelationContext.get_or_generate_correlation_id 