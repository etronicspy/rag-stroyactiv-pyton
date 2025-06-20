"""
Correlation ID context management system.

Provides thread-safe, async-safe correlation ID propagation.
Extracted and refactored from core/monitoring/context.py.
"""

import uuid
import sys
import asyncio
from contextvars import ContextVar
from typing import Optional, Callable, Any, Dict
from functools import wraps

from ..base.interfaces import ContextManagerInterface

# Context variables with clear defaults
_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
_request_metadata: ContextVar[Dict[str, Any]] = ContextVar('request_metadata', default={})

# Backward compatibility aliases
correlation_id = _correlation_id
request_metadata = _request_metadata


def generate_correlation_id() -> str:
    """
    Generate new correlation ID with basic fallback.
    
    Returns:
        New correlation ID
    """
    try:
        return str(uuid.uuid4())
    except Exception:
        # Simple fallback - timestamp-based ID
        import time
        return f"fallback-{int(time.time() * 1000000)}"


def set_correlation_id(correlation_id_value: Optional[str] = None) -> str:
    """
    Set correlation ID in current context.
    
    Args:
        correlation_id_value: ID to set (generates new if None)
        
    Returns:
        Set correlation ID
    """
    if correlation_id_value is None:
        correlation_id_value = generate_correlation_id()
    
    try:
        _correlation_id.set(correlation_id_value)
    except Exception as e:
        sys.stderr.write(f"[CONTEXT-ERROR] Failed to set correlation ID: {e}\n")
        sys.stderr.flush()
    
    return correlation_id_value


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID from context.
    
    Returns:
        Current correlation ID or None if not set
    """
    try:
        return _correlation_id.get()
    except Exception as e:
        sys.stderr.write(f"[CONTEXT-ERROR] Failed to get correlation ID: {e}\n")
        sys.stderr.flush()
        return None


def get_or_generate_correlation_id() -> str:
    """
    Get current correlation ID or generate new one if not exists.
    
    Returns:
        Correlation ID (existing or newly generated)
    """
    current_id = get_correlation_id()
    if current_id is None:
        current_id = set_correlation_id()
    return current_id


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


class CorrelationContext(ContextManagerInterface):
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
    
    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID from context."""
        return get_correlation_id()
        
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID in current context."""
        set_correlation_id(correlation_id)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get current request metadata."""
        return get_request_metadata()
    
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
    def get_metadata() -> Dict[str, Any]:
        """Get current request metadata."""
        return get_request_metadata()
    
    @staticmethod
    def update_request_metadata(key: str, value: Any) -> None:
        """Update specific key in request metadata."""
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
        """Diagnose current context state."""
        return {
            "correlation_id": get_correlation_id(),
            "metadata": get_request_metadata(),
            "context_vars": {
                "correlation_id_set": _correlation_id.get() is not None,
                "metadata_set": bool(_request_metadata.get())
            }
        }
    
    @classmethod
    def with_correlation_id(cls, corr_id: Optional[str] = None):
        """
        Context manager for correlation ID.
        
        Args:
            corr_id: Correlation ID to use (generates new if None)
            
        Returns:
            Context manager
        """
        class CorrelationContextManager:
            def __init__(self, correlation_id_value: Optional[str]):
                self.correlation_id = correlation_id_value
                self.previous_id = None
                
            def __enter__(self):
                self.previous_id = get_correlation_id()
                if self.correlation_id is None:
                    self.correlation_id = generate_correlation_id()
                set_correlation_id(self.correlation_id)
                return self.correlation_id
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.previous_id is not None:
                    set_correlation_id(self.previous_id)
                else:
                    clear_correlation_context()
                return False
                
        return CorrelationContextManager(corr_id)
    
    @classmethod
    def with_request_context(cls, corr_id: Optional[str] = None, 
                           metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for full request context.
        
        Args:
            corr_id: Correlation ID to use 
            metadata: Request metadata to set
            
        Returns:
            Context manager
        """
        class RequestContextManager:
            def __init__(self, correlation_id_value: Optional[str], 
                       metadata_value: Optional[Dict[str, Any]]):
                self.correlation_id = correlation_id_value
                self.metadata = metadata_value or {}
                self.previous_id = None
                self.previous_metadata = None
                
            def __enter__(self):
                self.previous_id = get_correlation_id()
                self.previous_metadata = get_request_metadata()
                
                if self.correlation_id is None:
                    self.correlation_id = generate_correlation_id()
                set_correlation_id(self.correlation_id)
                set_request_metadata(self.metadata)
                
                return self.correlation_id
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.previous_id is not None:
                    set_correlation_id(self.previous_id)
                if self.previous_metadata:
                    set_request_metadata(self.previous_metadata)
                else:
                    clear_correlation_context()
                return False
                
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