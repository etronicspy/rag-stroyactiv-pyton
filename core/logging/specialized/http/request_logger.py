"""
Request logger implementation.

This module provides a logger for HTTP requests.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

from core.logging.interfaces import IRequestLogger
from core.logging.core import Logger


class RequestLogger(Logger, IRequestLogger):
    """Logger for HTTP requests."""
    
    def __init__(
        self,
        name: str,
        level: Union[int, str] = logging.INFO,
        log_request_body: bool = True,
        log_response_body: bool = True,
        log_headers: bool = True,
        mask_sensitive_headers: bool = True,
        max_body_size: int = 10000
    ):
        """
        Initialize a new request logger.
        
        Args:
            name: The logger name
            level: The log level
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            log_headers: Whether to log headers
            mask_sensitive_headers: Whether to mask sensitive headers
            max_body_size: The maximum body size to log
        """
        super().__init__(name, level)
        self._log_request_body = log_request_body
        self._log_response_body = log_response_body
        self._log_headers = log_headers
        self._mask_sensitive_headers = mask_sensitive_headers
        self._max_body_size = max_body_size
        
        # List of sensitive headers to mask
        self._sensitive_headers = [
            "authorization",
            "x-api-key",
            "api-key",
            "token",
            "cookie",
            "set-cookie",
            "x-auth-token",
            "x-forwarded-for",
            "x-real-ip",
            "proxy-authorization",
        ]
    
    def log_request(
        self,
        method: str,
        url: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        request_headers: Optional[Dict[str, str]] = None,
        request_body: Optional[Any] = None,
        response_headers: Optional[Dict[str, str]] = None,
        response_body: Optional[Any] = None,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log an HTTP request.
        
        Args:
            method: The HTTP method
            url: The URL
            status_code: The status code
            duration_ms: The duration in milliseconds
            request_headers: The request headers
            request_body: The request body
            response_headers: The response headers
            response_body: The response body
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # Build the log message
        message = f"{method} {url}"
        if status_code:
            message = f"{message} - {status_code}"
        
        # Build the context
        context = {
            "method": method,
            "url": url,
        }
        
        # Add status code if available
        if status_code is not None:
            context["status_code"] = status_code
        
        # Add duration if available
        if duration_ms is not None:
            context["duration_ms"] = duration_ms
        
        # Add request headers if enabled
        if self._log_headers and request_headers:
            context["request_headers"] = self._process_headers(request_headers)
        
        # Add request body if enabled
        if self._log_request_body and request_body:
            context["request_body"] = self._process_body(request_body)
        
        # Add response headers if enabled
        if self._log_headers and response_headers:
            context["response_headers"] = self._process_headers(response_headers)
        
        # Add response body if enabled
        if self._log_response_body and response_body:
            context["response_body"] = self._process_body(response_body)
        
        # Add error information if available
        if error:
            context["error"] = str(error)
            context["error_type"] = type(error).__name__
        
        # Add additional context
        context.update(kwargs)
        
        # Determine the log level based on status code
        if status_code is None:
            level = logging.INFO
        elif status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO
        
        # Log the message
        self.log(level, message, **context)
    
    def log_incoming_request(
        self,
        method: str,
        path: str,
        request_headers: Optional[Dict[str, str]] = None,
        request_body: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Log an incoming HTTP request.
        
        Args:
            method: The HTTP method
            path: The path
            request_headers: The request headers
            request_body: The request body
            **kwargs: Additional context for the log message
            
        Returns:
            A request context for the response logger
        """
        # Build the log message
        message = f"Incoming {method} {path}"
        
        # Build the context
        context = {
            "method": method,
            "path": path,
        }
        
        # Add request headers if enabled
        if self._log_headers and request_headers:
            context["request_headers"] = self._process_headers(request_headers)
        
        # Add request body if enabled
        if self._log_request_body and request_body:
            context["request_body"] = self._process_body(request_body)
        
        # Add additional context
        context.update(kwargs)
        
        # Log the message
        self.info(message, **context)
        
        # Return a request context for the response logger
        return {
            "method": method,
            "path": path,
            "start_time": time.time(),
            "context": context,
        }
    
    def log_incoming_response(
        self,
        request_context: Dict[str, Any],
        status_code: int,
        response_headers: Optional[Dict[str, str]] = None,
        response_body: Optional[Any] = None,
        **kwargs
    ) -> None:
        """
        Log an incoming HTTP response.
        
        Args:
            request_context: The request context from log_incoming_request
            status_code: The status code
            response_headers: The response headers
            response_body: The response body
            **kwargs: Additional context for the log message
        """
        # Extract request information
        method = request_context["method"]
        path = request_context["path"]
        start_time = request_context["start_time"]
        context = request_context["context"].copy()
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Build the log message
        message = f"Response {method} {path} - {status_code}"
        
        # Update the context
        context["status_code"] = status_code
        context["duration_ms"] = duration_ms
        
        # Add response headers if enabled
        if self._log_headers and response_headers:
            context["response_headers"] = self._process_headers(response_headers)
        
        # Add response body if enabled
        if self._log_response_body and response_body:
            context["response_body"] = self._process_body(response_body)
        
        # Add additional context
        context.update(kwargs)
        
        # Determine the log level based on status code
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO
        
        # Log the message
        self.log(level, message, **context)
    
    def _process_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Process headers for logging.
        
        Args:
            headers: The headers
            
        Returns:
            The processed headers
        """
        if not self._mask_sensitive_headers:
            return headers
        
        # Create a copy of the headers
        processed_headers = {}
        
        # Mask sensitive headers
        for name, value in headers.items():
            if name.lower() in self._sensitive_headers:
                processed_headers[name] = "********"
            else:
                processed_headers[name] = value
        
        return processed_headers
    
    def _process_body(self, body: Any) -> Any:
        """
        Process a body for logging.
        
        Args:
            body: The body
            
        Returns:
            The processed body
        """
        # Convert the body to a string
        if isinstance(body, (dict, list)):
            body_str = json.dumps(body)
        else:
            body_str = str(body)
        
        # Truncate the body if it's too long
        if len(body_str) > self._max_body_size:
            return f"{body_str[:self._max_body_size]}... [truncated]"
        
        # Return the original body
        return body


class AsyncRequestLogger(RequestLogger):
    """Asynchronous logger for HTTP requests."""
    
    async def alog_request(
        self,
        method: str,
        url: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        request_headers: Optional[Dict[str, str]] = None,
        request_body: Optional[Any] = None,
        response_headers: Optional[Dict[str, str]] = None,
        response_body: Optional[Any] = None,
        error: Optional[Exception] = None,
        **kwargs
    ) -> None:
        """
        Log an HTTP request asynchronously.
        
        Args:
            method: The HTTP method
            url: The URL
            status_code: The status code
            duration_ms: The duration in milliseconds
            request_headers: The request headers
            request_body: The request body
            response_headers: The response headers
            response_body: The response body
            error: The error, if any
            **kwargs: Additional context for the log message
        """
        # For now, just call the synchronous method
        # In a real implementation, this would use an async queue
        self.log_request(
            method=method,
            url=url,
            status_code=status_code,
            duration_ms=duration_ms,
            request_headers=request_headers,
            request_body=request_body,
            response_headers=response_headers,
            response_body=response_body,
            error=error,
            **kwargs
        )
    
    async def alog_incoming_request(
        self,
        method: str,
        path: str,
        request_headers: Optional[Dict[str, str]] = None,
        request_body: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Log an incoming HTTP request asynchronously.
        
        Args:
            method: The HTTP method
            path: The path
            request_headers: The request headers
            request_body: The request body
            **kwargs: Additional context for the log message
            
        Returns:
            A request context for the response logger
        """
        # For now, just call the synchronous method
        # In a real implementation, this would use an async queue
        return self.log_incoming_request(
            method=method,
            path=path,
            request_headers=request_headers,
            request_body=request_body,
            **kwargs
        )
    
    async def alog_incoming_response(
        self,
        request_context: Dict[str, Any],
        status_code: int,
        response_headers: Optional[Dict[str, str]] = None,
        response_body: Optional[Any] = None,
        **kwargs
    ) -> None:
        """
        Log an incoming HTTP response asynchronously.
        
        Args:
            request_context: The request context from log_incoming_request
            status_code: The status code
            response_headers: The response headers
            response_body: The response body
            **kwargs: Additional context for the log message
        """
        # For now, just call the synchronous method
        # In a real implementation, this would use an async queue
        self.log_incoming_response(
            request_context=request_context,
            status_code=status_code,
            response_headers=response_headers,
            response_body=response_body,
            **kwargs
        ) 