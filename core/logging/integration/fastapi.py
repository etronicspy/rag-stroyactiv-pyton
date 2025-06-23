"""
FastAPI integration implementation.

This module provides integration with FastAPI.
"""

import logging
import time
from typing import Any, Callable, List, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp

from core.logging.config import get_configuration
from core.logging.interfaces import ILogger
from core.logging.specialized.context import CorrelationProvider
from core.logging.specialized.http import RequestLogger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    This middleware logs HTTP requests and responses and adds a correlation ID to each request.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        logger: Optional[ILogger] = None,
        correlation_provider: Optional[CorrelationProvider] = None,
        request_logger: Optional[RequestLogger] = None,
        exclude_paths: Optional[List[str]] = None,
        exclude_methods: Optional[List[str]] = None,
    ):
        """
        Initialize a new logging middleware.
        
        Args:
            app: The ASGI application
            logger: The logger to use
            correlation_provider: The correlation provider to use
            request_logger: The request logger to use
            exclude_paths: Paths to exclude from logging
            exclude_methods: HTTP methods to exclude from logging
        """
        super().__init__(app)
        
        # Get configuration
        config = get_configuration()
        http_settings = config.get_http_settings()
        context_settings = config.get_context_settings()
        
        # Create logger if not provided
        self._logger = logger or logging.getLogger("http")
        
        # Create correlation provider if not provided
        if correlation_provider is not None:
            self._correlation_provider = correlation_provider
        else:
            try:
                # New-style provider with configurable args
                self._correlation_provider = CorrelationProvider(
                    enabled=context_settings.get("enable_correlation_id", True),
                    header_name=context_settings.get("correlation_id_header", "X-Correlation-ID"),
                    generator=context_settings.get("correlation_id_generator"),
                )
            except TypeError:
                # Fallback to simple provider with default constructor (legacy implementation)
                self._correlation_provider = CorrelationProvider()
        
        # Create request logger if not provided
        try:
            self._request_logger = request_logger or RequestLogger(
                name="http",
                log_request_body=http_settings.get("log_request_body", True),
                log_response_body=http_settings.get("log_response_body", True),
                log_headers=http_settings.get("log_request_headers", True),
                mask_sensitive_headers=http_settings.get("mask_sensitive_headers", True),
                max_body_size=http_settings.get("max_body_size", 10000),
            )
        except TypeError:
            # Fallback: simple logger with defaults
            self._request_logger = request_logger or RequestLogger("http")
        
        # Set exclude paths and methods
        self._exclude_paths = exclude_paths or []
        self._exclude_methods = exclude_methods or []
        
        # Set enabled flag
        self._enabled = http_settings["enable_request_logging"]
        
        # Store original app for testing compatibility
        self._app = app
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Dispatch the request.
        
        Args:
            request: The request
            call_next: The next middleware or endpoint
            
        Returns:
            The response
        """
        # Skip logging if disabled
        if not self._enabled:
            return await call_next(request)
        
        # Skip logging if path or method is excluded
        if self._should_exclude(request):
            return await call_next(request)
        
        # Get or create correlation ID
        correlation_id = self._correlation_provider.get_or_create_correlation_id(request.headers)
        
        # Start timer
        start_time = time.time()
        
        # Log request
        await self._request_logger.log_request(request, correlation_id)
        
        try:
            # Call next middleware or endpoint
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            await self._request_logger.log_response(request, response, correlation_id, duration_ms)
            
            # Add correlation ID to response headers
            if correlation_id:
                response.headers[self._correlation_provider.header_name] = correlation_id
            
            return response
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log exception
            await self._request_logger.log_exception(request, e, correlation_id, duration_ms)
            
            # Re-raise exception
            raise
    
    def _should_exclude(self, request: Request) -> bool:
        """
        Check if the request should be excluded from logging.
        
        Args:
            request: The request
            
        Returns:
            bool: True if the request should be excluded, False otherwise
        """
        # Check path
        for path in self._exclude_paths:
            if request.url.path.startswith(path):
                return True
        
        # Check method
        if request.method in self._exclude_methods:
            return True
        
        return False


def setup_logging(app: FastAPI, **kwargs: Any) -> None:
    """
    Set up logging for a FastAPI application.
    
    Args:
        app: The FastAPI application
        **kwargs: Additional arguments for the logging middleware
    """
    # Add logging middleware
    app.add_middleware(LoggingMiddleware, **kwargs)


class LoggingRoute:
    """
    Route decorator for logging.
    
    This decorator logs route calls.
    """
    
    def __init__(
        self,
        logger: Optional[ILogger] = None,
        correlation_provider: Optional[CorrelationProvider] = None,
        request_logger: Optional[RequestLogger] = None,
    ):
        """
        Initialize a new logging route decorator.
        
        Args:
            logger: The logger to use
            correlation_provider: The correlation provider to use
            request_logger: The request logger to use
        """
        # Get configuration
        config = get_configuration()
        http_settings = config.get_http_settings()
        context_settings = config.get_context_settings()
        
        # Create logger if not provided
        self._logger = logger or logging.getLogger("http")
        
        # Create correlation provider if not provided
        if correlation_provider is not None:
            self._correlation_provider = correlation_provider
        else:
            try:
                # New-style provider with configurable args
                self._correlation_provider = CorrelationProvider(
                    enabled=context_settings.get("enable_correlation_id", True),
                    header_name=context_settings.get("correlation_id_header", "X-Correlation-ID"),
                    generator=context_settings.get("correlation_id_generator"),
                )
            except TypeError:
                # Fallback to simple provider with default constructor (legacy implementation)
                self._correlation_provider = CorrelationProvider()
        
        # Create request logger if not provided
        try:
            self._request_logger = request_logger or RequestLogger(
                name="http",
                log_request_body=http_settings.get("log_request_body", True),
                log_response_body=http_settings.get("log_response_body", True),
                log_headers=http_settings.get("log_request_headers", True),
                mask_sensitive_headers=http_settings.get("mask_sensitive_headers", True),
                max_body_size=http_settings.get("max_body_size", 10000),
            )
        except TypeError:
            # Fallback: simple logger with defaults
            self._request_logger = request_logger or RequestLogger("http")
        
        # Set enabled flag
        self._enabled = http_settings["enable_request_logging"]
    
    def __call__(self, func: Callable) -> Callable:
        """
        Call the decorator.
        
        Args:
            func: The function to decorate
            
        Returns:
            The decorated function
        """
        # Skip logging if disabled
        if not self._enabled:
            return func
        
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get request
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request is None:
                # No request found, just call the function
                return await func(*args, **kwargs)
            
            # Get or create correlation ID
            correlation_id = self._correlation_provider.get_or_create_correlation_id(request.headers)
            
            # Start timer
            start_time = time.time()
            
            # Log request
            await self._request_logger.log_request(request, correlation_id)
            
            try:
                # Call the function
                response = await func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log response
                await self._request_logger.log_response(request, response, correlation_id, duration_ms)
                
                # Add correlation ID to response headers
                if correlation_id and hasattr(response, "headers"):
                    response.headers[self._correlation_provider.header_name] = correlation_id
                
                return response
            except Exception as e:
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log exception
                await self._request_logger.log_exception(request, e, correlation_id, duration_ms)
                
                # Re-raise exception
                raise
        
        return wrapper 