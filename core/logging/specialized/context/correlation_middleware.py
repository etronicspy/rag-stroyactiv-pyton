"""
Correlation middleware implementation.

This module provides a middleware for setting correlation ID in requests.
"""

import time
from typing import Any, Callable, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from core.logging.interfaces import ICorrelationProvider
from core.logging.core.context import CorrelationProvider


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware for setting correlation ID in requests."""
    
    def __init__(
        self,
        app: ASGIApp,
        correlation_provider: Optional[ICorrelationProvider] = None,
        header_name: str = "X-Correlation-ID"
    ):
        """
        Initialize a new correlation middleware.
        
        Args:
            app: The ASGI application
            correlation_provider: The correlation provider to use
            header_name: The header name to use for correlation ID
        """
        super().__init__(app)
        self._correlation_provider = correlation_provider or CorrelationProvider()
        self._header_name = header_name
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Dispatch the request with correlation ID.
        
        Args:
            request: The request
            call_next: The next middleware to call
            
        Returns:
            The response
        """
        # Get correlation ID from request header or generate a new one
        correlation_id = request.headers.get(self._header_name)
        if not correlation_id:
            correlation_id = self._correlation_provider.generate_correlation_id()
        
        # Set correlation ID in context
        with self._correlation_provider.with_correlation_id(correlation_id):
            # Process the request
            response = await call_next(request)
            
            # Add correlation ID to response header
            response.headers[self._header_name] = correlation_id
            
            return response


class AsyncCorrelationMiddleware:
    """Async middleware for setting correlation ID in requests."""
    
    def __init__(
        self,
        correlation_provider: Optional[ICorrelationProvider] = None,
        header_name: str = "X-Correlation-ID"
    ):
        """
        Initialize a new async correlation middleware.
        
        Args:
            correlation_provider: The correlation provider to use
            header_name: The header name to use for correlation ID
        """
        self._correlation_provider = correlation_provider or CorrelationProvider()
        self._header_name = header_name
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process the request with correlation ID.
        
        Args:
            scope: The ASGI scope
            receive: The ASGI receive function
            send: The ASGI send function
        """
        if scope["type"] != "http":
            # Pass through non-HTTP requests
            await self.app(scope, receive, send)
            return
        
        # Get correlation ID from request headers or generate a new one
        correlation_id = None
        headers = scope.get("headers", [])
        for name, value in headers:
            if name.decode("latin1").lower() == self._header_name.lower():
                correlation_id = value.decode("latin1")
                break
        
        if not correlation_id:
            correlation_id = self._correlation_provider.generate_correlation_id()
        
        # Set correlation ID in context
        with self._correlation_provider.with_correlation_id(correlation_id):
            # Process the request
            async def send_wrapper(message: Dict[str, Any]) -> None:
                """
                Wrap the send function to add correlation ID to response headers.
                
                Args:
                    message: The ASGI message
                """
                if message["type"] == "http.response.start":
                    # Add correlation ID to response headers
                    headers = message.get("headers", [])
                    headers.append(
                        (
                            self._header_name.encode("latin1"),
                            correlation_id.encode("latin1")
                        )
                    )
                    message["headers"] = headers
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)


def get_correlation_middleware(
    correlation_provider: Optional[ICorrelationProvider] = None,
    header_name: str = "X-Correlation-ID"
) -> BaseHTTPMiddleware:
    """
    Get a correlation middleware.
    
    Args:
        correlation_provider: The correlation provider to use
        header_name: The header name to use for correlation ID
        
    Returns:
        A correlation middleware
    """
    return lambda app: CorrelationMiddleware(
        app,
        correlation_provider=correlation_provider,
        header_name=header_name
    ) 