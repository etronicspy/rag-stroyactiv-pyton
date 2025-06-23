"""
Request logging middleware implementation.

This module provides a middleware for logging HTTP requests.
"""

import time
from typing import Any, Callable, Dict, Optional
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from core.logging.interfaces import IRequestLogger
from core.logging.specialized.http.request_logger import AsyncRequestLogger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests."""
    
    def __init__(
        self,
        app: ASGIApp,
        request_logger: Optional[IRequestLogger] = None,
        exclude_paths: Optional[list[str]] = None,
        exclude_methods: Optional[list[str]] = None,
        log_request_body: bool = True,
        log_response_body: bool = True,
        log_health_checks: bool = False,
    ):
        """
        Initialize a new request logging middleware.
        
        Args:
            app: The ASGI application
            request_logger: The request logger to use
            exclude_paths: Paths to exclude from logging
            exclude_methods: Methods to exclude from logging
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            log_health_checks: Whether to log health check requests
        """
        super().__init__(app)
        self._request_logger = request_logger or AsyncRequestLogger("request")
        self._exclude_paths = exclude_paths or []
        self._exclude_methods = exclude_methods or []
        self._log_request_body = log_request_body
        self._log_response_body = log_response_body
        self._log_health_checks = log_health_checks
        
        # Add health check paths to exclude if not logging them
        if not log_health_checks:
            self._exclude_paths.extend([
                "/health",
                "/healthz",
                "/ready",
                "/readyz",
                "/live",
                "/livez",
            ])
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Dispatch the request with logging.
        
        Args:
            request: The request
            call_next: The next middleware to call
            
        Returns:
            The response
        """
        # Check if the request should be logged
        if not self._should_log_request(request):
            return await call_next(request)
        
        # Get the request body
        request_body = None
        if self._log_request_body:
            request_body = await self._get_request_body(request)
        
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        # Prefer async logging if available, otherwise use sync method in thread executor
        if hasattr(self._request_logger, "alog_incoming_request"):
            request_context = await self._request_logger.alog_incoming_request(
                method=request.method,
                path=request.url.path,
                request_headers=dict(request.headers),
                request_body=request_body,
                query_params=dict(request.query_params),
                client_host=request.client.host if request.client else None,
                correlation_id=correlation_id,
            )
            # Ensure correlation ID is preserved for later use in response logging
            request_context["correlation_id"] = correlation_id
        else:
            # Fallback to synchronous logger in a background thread to avoid blocking event loop
            from functools import partial
            import anyio

            sync_func = partial(
                self._request_logger.log_incoming_request,
                method=request.method,
                path=request.url.path,
                request_headers=dict(request.headers),
                request_body=request_body,
                query_params=dict(request.query_params),
                client_host=request.client.host if request.client else None,
                correlation_id=correlation_id,
            )
            request_context = await anyio.to_thread.run_sync(sync_func)
        
        # Process the request
        time.time()
        response = None
        try:
            response = await call_next(request)
            return await self._log_response(response, request_context)
        except Exception as e:
            # Log the error
            if hasattr(self._request_logger, "alog_incoming_response"):
                await self._request_logger.alog_incoming_response(
                    request_context=request_context,
                    status_code=500,
                    error=e,
                )
            else:
                from functools import partial
                import anyio

                sync_err = partial(
                    self._request_logger.log_incoming_response,
                    request_context,
                    500,
                    None,
                    None,
                    e,
                )
                await anyio.to_thread.run_sync(sync_err)
            raise
    
    async def _log_response(self, response: Response, request_context: Dict[str, Any]) -> Response:
        """
        Log the response.
        
        Args:
            response: The response
            request_context: The request context
            
        Returns:
            The response
        """
        # Get the response body
        response_body = None
        if self._log_response_body:
            response_body = await self._get_response_body(response)
        
        # Log the response
        if hasattr(self._request_logger, "alog_incoming_response"):
            await self._request_logger.alog_incoming_response(
                request_context=request_context,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                response_body=response_body,
            )
        else:
            from functools import partial
            import anyio

            sync_resp = partial(
                self._request_logger.log_incoming_response,
                request_context,
                response.status_code,
                dict(response.headers),
                response_body,
            )
            await anyio.to_thread.run_sync(sync_resp)
        
        # Add correlation ID header if present
        if correlation_id := request_context.get("correlation_id"):
            response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    def _should_log_request(self, request: Request) -> bool:
        """
        Check if the request should be logged.
        
        Args:
            request: The request
            
        Returns:
            Whether the request should be logged
        """
        # Check if the method is excluded
        if request.method.upper() in [m.upper() for m in self._exclude_methods]:
            return False
        
        # Check if the path is excluded
        for path in self._exclude_paths:
            if request.url.path.startswith(path):
                return False
        
        return True
    
    async def _get_request_body(self, request: Request) -> Optional[Any]:
        """
        Get the request body.
        
        Args:
            request: The request
            
        Returns:
            The request body
        """
        try:
            body = await request.body()
            if not body:
                return None
            
            # Try to parse as JSON
            try:
                return await request.json()
            except:
                # Return as string
                return body.decode("utf-8")
        except:
            return None
    
    async def _get_response_body(self, response: Response) -> Optional[Any]:
        """
        Get the response body.
        
        Args:
            response: The response
            
        Returns:
            The response body
        """
        try:
            # Get the response body
            body = response.body
            if not body:
                return None
            
            # Try to parse as JSON
            try:
                import json
                return json.loads(body.decode("utf-8"))
            except:
                # Return as string
                return body.decode("utf-8")
        except:
            return None

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def mask_sensitive_data(headers: Dict[str, str], mask: str = "***") -> Dict[str, str]:
        """Mask potentially sensitive header values.

        Args:
            headers: Original headers dictionary.
            mask: Replacement for masked values.

        Returns:
            Dict[str, str]: New dictionary with sensitive values masked.
        """
        sensitive_keywords = [
            "authorization",
            "token",
            "secret",
            "api-key",
            "x-api-key",
            "key",
        ]

        masked_headers: Dict[str, str] = {}
        for k, v in headers.items():
            if any(keyword in k.lower() for keyword in sensitive_keywords):
                # Preserve scheme if present (e.g., "Bearer abc")
                parts = v.split(" ", 1)
                if len(parts) == 2:
                    masked_headers[k] = f"{parts[0]} {mask}"
                else:
                    masked_headers[k] = mask
            else:
                masked_headers[k] = v
        return masked_headers


class AsyncRequestLoggingMiddleware:
    """Async middleware for logging HTTP requests."""
    
    def __init__(
        self,
        app: ASGIApp,
        request_logger: Optional[IRequestLogger] = None,
        exclude_paths: Optional[list[str]] = None,
        exclude_methods: Optional[list[str]] = None,
        log_request_body: bool = True,
        log_response_body: bool = True,
        log_health_checks: bool = False,
    ):
        """
        Initialize a new async request logging middleware.
        
        Args:
            app: The ASGI application
            request_logger: The request logger to use
            exclude_paths: Paths to exclude from logging
            exclude_methods: Methods to exclude from logging
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            log_health_checks: Whether to log health check requests
        """
        self.app = app
        self._request_logger = request_logger or AsyncRequestLogger("request")
        self._exclude_paths = exclude_paths or []
        self._exclude_methods = exclude_methods or []
        self._log_request_body = log_request_body
        self._log_response_body = log_response_body
        self._log_health_checks = log_health_checks
        
        # Add health check paths to exclude if not logging them
        if not log_health_checks:
            self._exclude_paths.extend([
                "/health",
                "/healthz",
                "/ready",
                "/readyz",
                "/live",
                "/livez",
            ])
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process the request with logging.
        
        Args:
            scope: The ASGI scope
            receive: The ASGI receive function
            send: The ASGI send function
        """
        if scope["type"] != "http":
            # Pass through non-HTTP requests
            await self.app(scope, receive, send)
            return
        
        # Extract request information
        method = scope["method"]
        path = scope["path"]
        headers = dict(scope["headers"])
        
        # Check if the request should be logged
        if not self._should_log_request(method, path):
            await self.app(scope, receive, send)
            return
        
        # Get the request body
        request_body = None
        if self._log_request_body:
            request_body = await self._get_request_body(receive)
        
        # Generate or extract correlation ID
        correlation_id = headers.get("X-Correlation-ID") or str(uuid.uuid4())
        # Prefer async logging if available, otherwise use sync method in thread executor
        if hasattr(self._request_logger, "alog_incoming_request"):
            request_context = await self._request_logger.alog_incoming_request(
                method=method,
                path=path,
                request_headers=headers,
                request_body=request_body,
                query_params=dict(scope["query_string"]),
                client_host=scope["client"][0] if "client" in scope else None,
                correlation_id=correlation_id,
            )
        else:
            # Fallback to synchronous logger in a background thread to avoid blocking event loop
            from functools import partial
            import anyio

            sync_func = partial(
                self._request_logger.log_incoming_request,
                method=method,
                path=path,
                request_headers=headers,
                request_body=request_body,
                query_params=dict(scope["query_string"]),
                client_host=scope["client"][0] if "client" in scope else None,
                correlation_id=correlation_id,
            )
            request_context = await anyio.to_thread.run_sync(sync_func)
        
        # Preserve correlation ID for response logging
        request_context["correlation_id"] = correlation_id
        
        # Process the request
        time.time()
        
        # Wrap the send function to capture the response
        async def send_wrapper(message: Dict[str, Any]) -> None:
            """
            Wrap the send function to log the response.
            
            Args:
                message: The ASGI message
            """
            if message["type"] == "http.response.start":
                # Extract response information
                status_code = message["status"]
                headers = dict(message["headers"])
                
                # Log the response
                await self._request_logger.alog_incoming_response(
                    request_context=request_context,
                    status_code=status_code,
                    response_headers=headers,
                    response_body=None,  # We can't get the response body in this middleware
                )
            
            await send(message)
        
        # Process the request
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Log the error
            if hasattr(self._request_logger, "alog_incoming_response"):
                await self._request_logger.alog_incoming_response(
                    request_context=request_context,
                    status_code=500,
                    error=e,
                )
            else:
                from functools import partial
                import anyio

                sync_err = partial(
                    self._request_logger.log_incoming_response,
                    request_context,
                    500,
                    None,
                    None,
                    e,
                )
                await anyio.to_thread.run_sync(sync_err)
            raise
    
    def _should_log_request(self, method: str, path: str) -> bool:
        """
        Check if the request should be logged.
        
        Args:
            method: The HTTP method
            path: The path
            
        Returns:
            Whether the request should be logged
        """
        # Check if the method is excluded
        if method.upper() in [m.upper() for m in self._exclude_methods]:
            return False
        
        # Check if the path is excluded
        for exclude_path in self._exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        return True
    
    async def _get_request_body(self, receive: Callable) -> Optional[Any]:
        """
        Get the request body.
        
        Args:
            receive: The ASGI receive function
            
        Returns:
            The request body
        """
        try:
            # Receive the request body
            message = await receive()
            if message["type"] != "http.request":
                return None
            
            body = message.get("body", b"")
            if not body:
                return None
            
            # Try to parse as JSON
            try:
                import json
                return json.loads(body.decode("utf-8"))
            except:
                # Return as string
                return body.decode("utf-8")
        except:
            return None


def get_request_logging_middleware(
    request_logger: Optional[IRequestLogger] = None,
    exclude_paths: Optional[list[str]] = None,
    exclude_methods: Optional[list[str]] = None,
    log_request_body: bool = True,
    log_response_body: bool = True,
    log_health_checks: bool = False
) -> Callable[[ASGIApp], BaseHTTPMiddleware]:
    """
    Get a request logging middleware factory.
    
    Args:
        request_logger: The request logger to use
        exclude_paths: Paths to exclude from logging
        exclude_methods: Methods to exclude from logging
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        log_health_checks: Whether to log health check requests
        
    Returns:
        A middleware factory function
    """
    def middleware_factory(app: ASGIApp) -> BaseHTTPMiddleware:
        return RequestLoggingMiddleware(
            app=app,
            request_logger=request_logger,
            exclude_paths=exclude_paths,
            exclude_methods=exclude_methods,
            log_request_body=log_request_body,
            log_response_body=log_response_body,
            log_health_checks=log_health_checks,
        )
    
    return middleware_factory 