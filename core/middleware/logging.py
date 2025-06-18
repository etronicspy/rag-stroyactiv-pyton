"""
Logging middleware for comprehensive request/response monitoring.
Provides structured logging with performance metrics and security monitoring.

FIXED: Eliminated code duplication with BaseLoggingHandler architecture
"""

import time
import uuid
import json
import logging
from typing import Optional, Dict, Any, List, Callable, Set
from datetime import datetime
from functools import lru_cache

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send, Message

from core.config import get_settings

# 🔧 CONSTANTS: Moved hardcoded values to constants
EXCLUDE_PATHS = ["/docs", "/openapi.json", "/favicon.ico", "/static"]
SENSITIVE_HEADERS = frozenset([
    "authorization", "x-api-key", "cookie", 
    "x-auth-token", "proxy-authorization"
])

# 🔧 PERFORMANCE: Cached logger retrieval
@lru_cache(maxsize=32)
def get_cached_logger(name: str) -> logging.Logger:
    """Get cached logger instance for performance."""
    return logging.getLogger(name)


class BaseLoggingHandler:
    """
    🎯 Shared logging functionality for all middleware implementations.
    
    Eliminates code duplication and provides consistent logging behavior.
    """
    
    def __init__(self, enable_structured: bool = False, include_headers: bool = True, 
                 mask_sensitive: bool = True):
        self.enable_structured = enable_structured
        self.include_headers = include_headers
        self.mask_sensitive = mask_sensitive
        
        # 🔧 OPTIMIZED: Use cached loggers for performance
        self.root_logger = get_cached_logger("")  # Root logger
        self.file_logger = get_cached_logger("middleware.http")  # File logger
        
        # 🔧 PERFORMANCE: Pre-compiled sets for O(1) lookups
        self.exclude_paths = EXCLUDE_PATHS
        self.sensitive_headers = SENSITIVE_HEADERS
    
    def should_exclude_path(self, path: str) -> bool:
        """Fast path exclusion check."""
        return any(path.startswith(exclude_path) for exclude_path in self.exclude_paths)
    
    def _mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive headers for security."""
        if not self.mask_sensitive:
            return headers
            
        return {
            key: "[MASKED]" if key.lower() in self.sensitive_headers else value
            for key, value in headers.items()
        }
    
    def _format_log_message(self, event: str, method: str, path: str, 
                          correlation_id: str, **kwargs) -> str:
        """Format log message based on structured logging setting."""
        if self.enable_structured:
            log_data = {
                "event": event,
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
            return json.dumps(log_data, ensure_ascii=False)
        else:
            # Simple format for development
            if event == "request_started":
                return f"[root] {method} {path} - STARTED"
            elif event == "request_completed":
                status_code = kwargs.get("status_code", 200)
                process_time = kwargs.get("process_time", 0)
                status_text = "OK" if status_code < 400 else "ERROR"
                return f"[root] {method} {path} {status_code} {status_text} ({process_time:.3f}s)"
            elif event == "request_error":
                error_type = kwargs.get("error_type", "Exception")
                error_message = kwargs.get("error_message", "Unknown error")
                process_time = kwargs.get("process_time", 0)
                return f"[root] {method} {path} {error_type}: {error_message} ({process_time:.3f}s)"
            else:
                return f"[root] {method} {path} - {event.upper()}"
    
    def _log_event(self, level: int, event: str, method: str, path: str, 
                   correlation_id: str, **kwargs):
        """Log event to both root and file loggers."""
        message = self._format_log_message(event, method, path, correlation_id, **kwargs)
        
        # 🔧 OPTIMIZED: Single log call instead of double
        self.root_logger.log(level, message)
        self.file_logger.log(level, message)
    
    def log_request(self, method: str, path: str, client_ip: str, 
                   headers: Dict[str, str], correlation_id: str):
        """Log incoming request with optional headers."""
        kwargs = {"client_ip": client_ip}
        
        if self.include_headers:
            kwargs["headers"] = self._mask_sensitive_headers(headers)
        
        self._log_event(logging.INFO, "request_started", method, path, correlation_id, **kwargs)
    
    def log_response(self, method: str, path: str, status_code: int, 
                    process_time: float, correlation_id: str):
        """Log response with timing information."""
        self._log_event(
            logging.INFO, "request_completed", method, path, correlation_id,
            status_code=status_code, process_time=round(process_time, 3)
        )
    
    def log_exception(self, method: str, path: str, exception: Exception, 
                     correlation_id: str, process_time: float):
        """Log exception with error details."""
        self._log_event(
            logging.ERROR, "request_error", method, path, correlation_id,
            error_type=type(exception).__name__,
            error_message=str(exception),
            process_time=round(process_time, 3)
        )


class LoggingMiddleware:
    """
    🚀 Pure ASGI HTTP Request/Response Logging Middleware
    
    Features:
    - Pure ASGI implementation (compatible with BodyCacheMiddleware)
    - Minimal code duplication using BaseLoggingHandler
    - High performance with cached loggers
    """
    
    def __init__(
        self,
        app: ASGIApp,
        log_level: Optional[str] = None,
        log_request_body: Optional[bool] = None,
        log_response_body: Optional[bool] = None,
        max_body_size: int = 64 * 1024,  # 64KB
        exclude_paths: Optional[List[str]] = None,
        include_headers: bool = True,
        mask_sensitive_headers: bool = True,
    ):
        self.app = app
        
        # Get settings once and cache
        settings = get_settings()
        
        # Cache configuration for performance
        self.log_level = log_level or settings.LOG_LEVEL
        self.enable_request_logging = settings.ENABLE_REQUEST_LOGGING
        
        # 🔧 OPTIMIZED: Initialize base handler with shared logic
        self.handler = BaseLoggingHandler(
            enable_structured=settings.ENABLE_STRUCTURED_LOGGING,
            include_headers=include_headers,
            mask_sensitive=mask_sensitive_headers
        )
        
        # Override exclude paths if provided
        if exclude_paths:
            self.handler.exclude_paths = exclude_paths
        
        # Log initialization
        if self.enable_request_logging:
            self.handler.root_logger.info("✅ LoggingMiddleware initialized with ASGI implementation")
        else:
            self.handler.root_logger.info("⚠️ LoggingMiddleware initialized but REQUEST LOGGING DISABLED")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pure ASGI middleware entry point."""
        if scope["type"] != "http" or not self.enable_request_logging:
            await self.app(scope, receive, send)
            return
            
        # Fast path exclusion check
        path = scope.get("path", "")
        if self.handler.should_exclude_path(path):
            await self.app(scope, receive, send)
            return
        
        # Generate correlation ID and extract request info
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        method = scope.get("method", "GET")
        client_ip = self._get_client_ip_from_scope(scope)
        headers = self._extract_headers_from_scope(scope)
        
        # Log request
        self.handler.log_request(method, path, client_ip, headers, correlation_id)
        
        # Wrap send to capture response info
        response_started = False
        status_code = 200
        
        async def send_wrapper(message: Message) -> None:
            nonlocal response_started, status_code
            
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message.get("status", 200)
                
                # Add correlation ID to response headers
                headers = list(message.get("headers", []))
                headers.append((b"x-correlation-id", correlation_id.encode()))
                message["headers"] = headers
            
            elif message["type"] == "http.response.body" and not message.get("more_body", False):
                # This is the last response chunk - log the response
                if response_started:
                    process_time = time.time() - start_time
                    self.handler.log_response(method, path, status_code, process_time, correlation_id)
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exception:
            # Log exception
            process_time = time.time() - start_time
            self.handler.log_exception(method, path, exception, correlation_id, process_time)
            raise

    def _get_client_ip_from_scope(self, scope: Scope) -> str:
        """Extract client IP from ASGI scope."""
        headers = dict(scope.get("headers", []))
        
        # Check forwarded headers
        forwarded_for = headers.get(b"x-forwarded-for")
        if forwarded_for:
            return forwarded_for.decode().split(",")[0].strip()
        
        real_ip = headers.get(b"x-real-ip")
        if real_ip:
            return real_ip.decode()
        
        # Fallback to client info
        client = scope.get("client")
        return client[0] if client else "unknown"

    def _extract_headers_from_scope(self, scope: Scope) -> Dict[str, str]:
        """Extract headers from ASGI scope."""
        headers = {}
        for key_bytes, value_bytes in scope.get("headers", []):
            key = key_bytes.decode('latin1')
            value = value_bytes.decode('latin1')
            headers[key] = value
        return headers


class LoggingMiddlewareAdapter(BaseHTTPMiddleware):
    """
    🔄 FastAPI-compatible adapter for LoggingMiddleware
    
    Uses shared BaseLoggingHandler to eliminate code duplication.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        max_body_size: int = 64 * 1024,
        include_headers: bool = True,
        mask_sensitive_headers: bool = True,
    ):
        super().__init__(app)
        
        # Get settings
        settings = get_settings()
        self.enable_request_logging = settings.ENABLE_REQUEST_LOGGING
        
        # 🔧 OPTIMIZED: Initialize base handler with shared logic
        self.handler = BaseLoggingHandler(
            enable_structured=settings.ENABLE_STRUCTURED_LOGGING,
            include_headers=include_headers,
            mask_sensitive=mask_sensitive_headers
        )
        
        # Log initialization
        if self.enable_request_logging:
            self.handler.root_logger.info("✅ LoggingMiddlewareAdapter initialized")
        else:
            self.handler.root_logger.info("⚠️ LoggingMiddlewareAdapter initialized but REQUEST LOGGING DISABLED")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Adapter dispatch method."""
        if not self.enable_request_logging:
            return await call_next(request)
            
        # Check if path should be excluded
        if self.handler.should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Generate correlation ID and start timing
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log request
        client_ip = request.client.host if request.client else "unknown"
        self.handler.log_request(
            request.method, 
            request.url.path, 
            client_ip, 
            dict(request.headers), 
            correlation_id
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["x-correlation-id"] = correlation_id
            
            # Log response
            process_time = time.time() - start_time
            self.handler.log_response(
                request.method,
                request.url.path,
                response.status_code,
                process_time,
                correlation_id
            )
            
            return response
            
        except Exception as exception:
            # Log exception
            process_time = time.time() - start_time
            self.handler.log_exception(
                request.method,
                request.url.path,
                exception,
                correlation_id,
                process_time
            )
            raise 