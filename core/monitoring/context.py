"""
🎯 Simplified Correlation ID Context Management System

Provides thread-safe, async-safe correlation ID propagation with simplified architecture.
REFACTORED: Eliminated duplicate classes and excessive fallback mechanisms.

Features:
- Single unified CorrelationContext class
- Simplified error handling with essential fallbacks only
- Thread-safe and async-safe context variables
- Integration with logging system
"""

import uuid
import sys
import asyncio
from contextvars import ContextVar
from typing import Optional, Callable, Any, Dict
from functools import wraps
import logging

# Import centralized correlation functions and context vars to eliminate duplication
from core.logging.context.correlation import (
    generate_correlation_id,
    set_correlation_id, 
    get_correlation_id,
    get_or_generate_correlation_id,
    _correlation_id,
    _request_metadata
)

# Backward compatibility aliases
correlation_id = _correlation_id
request_metadata = _request_metadata


def set_request_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Set request metadata in current context.
    
    Args:
        metadata: Metadata dictionary to set
        
    Returns:
        True if successful
    """
    try:
        _request_metadata.set(metadata.copy() if metadata else {})
        return True
    except Exception as e:
        sys.stderr.write(f"[CONTEXT-ERROR] Failed to set request metadata: {e}\n")
        sys.stderr.flush()
        return False


def get_request_metadata() -> Dict[str, Any]:
    """
    Get current request metadata.
    
    Returns:
        Current request metadata dictionary
    """
    try:
        return _request_metadata.get() or {}
    except Exception as e:
        sys.stderr.write(f"[CONTEXT-ERROR] Failed to get request metadata: {e}\n")
        sys.stderr.flush()
        return {}


def clear_correlation_context() -> bool:
    """
    Clear correlation context (both ID and metadata).
    
    Returns:
        True if successful
    """
    try:
        _correlation_id.set(None)
        _request_metadata.set({})
        return True
    except Exception as e:
        sys.stderr.write(f"[CONTEXT-ERROR] Failed to clear correlation context: {e}\n")
        sys.stderr.flush()
        return False


class CorrelationContext:
    """
    🎯 Unified Correlation ID context manager and utilities.
    
    Provides:
    - Automatic correlation ID generation
    - Context propagation through async/sync calls
    - Integration with logging system
    - Request metadata management
    
    SIMPLIFIED: Single class with essential functionality only.
    """
    
    @staticmethod
    def create(correlation_id_value: Optional[str] = None) -> str:
        """Create new correlation context."""
        return set_correlation_id(correlation_id_value)
    
    @staticmethod
    def get() -> Optional[str]:
        """Get current correlation ID."""
        return get_correlation_id()
    
    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get current correlation ID from context."""
        return get_correlation_id()
    
    @staticmethod
    def set_correlation_id(corr_id: Optional[str]) -> None:
        """Set correlation ID in current context."""
        set_correlation_id(corr_id)
    
    @staticmethod
    def generate_correlation_id() -> str:
        """Generate new correlation ID and set it in context."""
        return set_correlation_id()
    
    @staticmethod
    def get_or_generate_correlation_id() -> str:
        """Get current correlation ID or generate new one if not exists."""
        return get_or_generate_correlation_id()
    
    @staticmethod
    def get_request_metadata() -> Dict[str, Any]:
        """Get current request metadata."""
        return get_request_metadata()
    
    @staticmethod
    def set_request_metadata(metadata: Dict[str, Any]) -> None:
        """Set request metadata in current context."""
        set_request_metadata(metadata)
    
    @staticmethod
    def set_metadata(metadata: Dict[str, Any]) -> bool:
        """Set request metadata (legacy compatibility)."""
        return set_request_metadata(metadata)
    
    @staticmethod
    def get_metadata() -> Dict[str, Any]:
        """Get request metadata (legacy compatibility)."""
        return get_request_metadata()
    
    @staticmethod
    def update_request_metadata(key: str, value: Any) -> None:
        """Update single key in request metadata."""
        try:
            current_metadata = get_request_metadata()
            current_metadata[key] = value
            set_request_metadata(current_metadata)
        except Exception as e:
            sys.stderr.write(f"[CONTEXT-ERROR] Failed to update request metadata: {e}\n")
            sys.stderr.flush()
    
    @staticmethod
    def clear() -> bool:
        """Clear correlation context."""
        return clear_correlation_context()
    
    @staticmethod
    def diagnose() -> Dict[str, Any]:
        """Get diagnostic information about current context state."""
        try:
            return {
                "correlation_id": get_correlation_id(),
                "metadata": get_request_metadata(),
                "context_vars_available": True,
                "status": "healthy"
            }
        except Exception as e:
            return {
                "correlation_id": None,
                "metadata": {},
                "context_vars_available": False,
                "status": f"error: {e}"
            }
    
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
                self.correlation_id_value = correlation_id_value or generate_correlation_id()
                self.token = None
            
            def __enter__(self):
                try:
                    self.token = _correlation_id.set(self.correlation_id_value)
                    return self.correlation_id_value
                except Exception as e:
                    sys.stderr.write(f"[CONTEXT-MANAGER-ERROR] Failed to enter correlation context: {e}\n")
                    sys.stderr.flush()
                    return self.correlation_id_value
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                try:
                    if self.token is not None:
                        _correlation_id.reset(self.token)
                except Exception as e:
                    sys.stderr.write(f"[CONTEXT-MANAGER-ERROR] Failed to exit correlation context: {e}\n")
                    sys.stderr.flush()
        
        return CorrelationContextManager(corr_id)
    
    @classmethod
    def with_request_context(cls, corr_id: Optional[str] = None, 
                           metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager to set both correlation ID and metadata.
        
        Args:
            corr_id: Correlation ID to use (generates new if None)
            metadata: Request metadata to set
        """
        class RequestContextManager:
            def __init__(self, correlation_id_value: Optional[str], 
                       metadata_value: Optional[Dict[str, Any]]):
                self.correlation_id_value = correlation_id_value or generate_correlation_id()
                self.metadata_value = metadata_value or {}
                self.corr_token = None
                self.meta_token = None
            
            def __enter__(self):
                try:
                    self.corr_token = _correlation_id.set(self.correlation_id_value)
                    self.meta_token = _request_metadata.set(self.metadata_value.copy())
                    return self.correlation_id_value
                except Exception as e:
                    sys.stderr.write(f"[REQUEST-CONTEXT-ERROR] Failed to enter request context: {e}\n")
                    sys.stderr.flush()
                    return self.correlation_id_value
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                try:
                    if self.corr_token is not None:
                        _correlation_id.reset(self.corr_token)
                    if self.meta_token is not None:
                        _request_metadata.reset(self.meta_token)
                except Exception as e:
                    sys.stderr.write(f"[REQUEST-CONTEXT-ERROR] Failed to exit request context: {e}\n")
                    sys.stderr.flush()
        
        return RequestContextManager(corr_id, metadata)


def with_correlation_context(func: Callable) -> Callable:
    """
    Decorator to ensure correlation context is available in function.
    
    Usage:
        @with_correlation_context
        def my_function():
            # Will automatically have correlation ID if not already set
            pass
    """
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Ensure correlation ID exists
            get_or_generate_correlation_id()
            return await func(*args, **kwargs)
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Ensure correlation ID exists
            get_or_generate_correlation_id()
            return func(*args, **kwargs)
        return sync_wrapper


# Import centralized log_with_correlation from core.logging.context.adapters
from core.logging.context.adapters import log_with_correlation


# CorrelationLoggingAdapter moved to core.logging.context.adapters for better modularity
# Import from the centralized location for backward compatibility
from core.logging.context.adapters import CorrelationLoggingAdapter


# Backward compatibility functions (marked as legacy)
def safe_generate_correlation_id() -> str:
    """LEGACY: Use generate_correlation_id() instead."""
    return generate_correlation_id()


def get_correlation_id_safe() -> Optional[str]:
    """LEGACY: Use get_correlation_id() instead.""" 
    return get_correlation_id()


def set_correlation_id_safe(corr_id: Optional[str] = None) -> str:
    """LEGACY: Use set_correlation_id() instead."""
    return set_correlation_id(corr_id)


def generate_correlation_id_safe() -> str:
    """LEGACY: Use generate_correlation_id() instead."""
    return generate_correlation_id()


def get_or_generate_correlation_id_safe() -> str:
    """LEGACY: Use get_or_generate_correlation_id() instead."""
    return get_or_generate_correlation_id()


# Compatibility aliases for existing code
get_request_metadata_compat = get_request_metadata
set_request_metadata_compat = set_request_metadata  
clear_correlation_context_compat = clear_correlation_context 