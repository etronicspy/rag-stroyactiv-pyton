"""
HTTP logging interfaces for the logging system.

This module defines interfaces for HTTP request and response logging:
- IRequestLogger: Interface for HTTP request and response logging
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, ContextManager, Union


class IRequestLogger(ABC):
    """Interface for HTTP request and response logging."""
    
    @abstractmethod
    def log_request(
        self, 
        method: str, 
        url: str, 
        headers: Optional[Dict[str, str]] = None, 
        body: Optional[Any] = None, 
        **kwargs
    ) -> None:
        """
        Log an HTTP request.
        
        Args:
            method: The HTTP method
            url: The URL
            headers: The request headers
            body: The request body
            **kwargs: Additional context for the log message
        """
        pass
    
    @abstractmethod
    def log_response(
        self, 
        status_code: int, 
        headers: Optional[Dict[str, str]] = None, 
        body: Optional[Any] = None, 
        duration_ms: Optional[float] = None, 
        **kwargs
    ) -> None:
        """
        Log an HTTP response.
        
        Args:
            status_code: The HTTP status code
            headers: The response headers
            body: The response body
            duration_ms: The request duration in milliseconds
            **kwargs: Additional context for the log message
        """
        pass
    
    @abstractmethod
    def log_error(
        self, 
        error: Exception, 
        method: Optional[str] = None, 
        url: Optional[str] = None, 
        **kwargs
    ) -> None:
        """
        Log an HTTP error.
        
        Args:
            error: The error
            method: The HTTP method
            url: The URL
            **kwargs: Additional context for the log message
        """
        pass
    
    @abstractmethod
    def request_context(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> ContextManager[Dict[str, Any]]:
        """
        Context manager for HTTP requests.
        
        Args:
            method: The HTTP method
            url: The URL
            **kwargs: Additional context for the log message
            
        Returns:
            A context manager that logs the request and response
        """
        pass


class IMiddlewareLogger(IRequestLogger):
    """Interface for middleware logging."""
    
    @abstractmethod
    def log_middleware_start(
        self, 
        middleware_name: str, 
        **kwargs
    ) -> None:
        """
        Log middleware start.
        
        Args:
            middleware_name: The middleware name
            **kwargs: Additional context for the log message
        """
        pass
    
    @abstractmethod
    def log_middleware_end(
        self, 
        middleware_name: str, 
        duration_ms: float, 
        **kwargs
    ) -> None:
        """
        Log middleware end.
        
        Args:
            middleware_name: The middleware name
            duration_ms: The middleware execution duration in milliseconds
            **kwargs: Additional context for the log message
        """
        pass
    
    @abstractmethod
    def log_middleware_error(
        self, 
        middleware_name: str, 
        error: Exception, 
        **kwargs
    ) -> None:
        """
        Log middleware error.
        
        Args:
            middleware_name: The middleware name
            error: The error
            **kwargs: Additional context for the log message
        """
        pass
    
    @abstractmethod
    def middleware_context(
        self, 
        middleware_name: str, 
        **kwargs
    ) -> ContextManager[Dict[str, Any]]:
        """
        Context manager for middleware execution.
        
        Args:
            middleware_name: The middleware name
            **kwargs: Additional context for the log message
            
        Returns:
            A context manager that logs the middleware execution
        """
        pass 