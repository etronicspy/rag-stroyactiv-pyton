"""
Logging middleware for comprehensive request/response monitoring.
Provides structured logging with performance metrics and security monitoring.

FIXED: Pure ASGI implementation for compatibility with BodyCacheMiddleware
"""

import time
import uuid
import json
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send, Message

from core.config import get_settings


class LoggingMiddleware:
    """
    🚀 Pure ASGI HTTP Request/Response Logging Middleware
    
    Features:
    - Pure ASGI implementation (compatible with BodyCacheMiddleware)
    - Correlation ID tracking
    - Configurable formatting (simple/structured)
    - Smart path exclusion
    - File and console logging
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
        self.log_request_body = log_request_body if log_request_body is not None else settings.LOG_REQUEST_BODY
        self.log_response_body = log_response_body if log_response_body is not None else settings.LOG_RESPONSE_BODY
        self.enable_structured = settings.ENABLE_STRUCTURED_LOGGING
        
        # 🔧 UNIFIED LOGGER STRATEGY: Use root logger for terminal + named logger for file
        self.logger = logging.getLogger()  # Корневой логгер для терминала
        self.file_logger = logging.getLogger("middleware.http")  # Именованный для файла
        
        # Force set level to ensure it works in all contexts
        self.logger.setLevel(getattr(logging, self.log_level.upper()))
        self.file_logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # Also ensure handlers have correct level
        for handler in self.logger.handlers:
            handler.setLevel(getattr(logging, self.log_level.upper()))
        
        # Performance optimizations
        self.max_body_size = max_body_size
        self.include_headers = include_headers
        self.mask_sensitive = mask_sensitive_headers
        
        # Optimized path exclusion (compile once)
        self.exclude_paths = exclude_paths or [
            "/docs", "/openapi.json", "/favicon.ico", "/static"
        ]
        
        # Pre-compiled sensitive headers set for O(1) lookup
        self.sensitive_headers = frozenset([
            "authorization", "x-api-key", "cookie", 
            "x-auth-token", "proxy-authorization"
        ])
        
        # Log successful initialization
        self.logger.info("✅ LoggingMiddleware initialized with ASGI implementation")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pure ASGI middleware entry point."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # Fast path exclusion check
        path = scope.get("path", "")
        
        if any(path.startswith(exclude_path) for exclude_path in self.exclude_paths):
            await self.app(scope, receive, send)
            return
        
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract request info
        method = scope.get("method", "GET")
        client_ip = self._get_client_ip_from_scope(scope)
        headers = dict(scope.get("headers", []))
        
        # Log request
        await self._log_request(method, path, client_ip, headers, correlation_id)
        
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
                    await self._log_response(method, path, status_code, process_time, correlation_id)
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exception:
            # Log exception
            process_time = time.time() - start_time
            await self._log_exception(method, path, exception, correlation_id, process_time)
            raise

    async def _log_request(self, method: str, path: str, client_ip: str, headers: Dict, correlation_id: str):
        """Log incoming request."""
        if self.enable_structured:
            # Structured logging for production
            log_data = {
                "event": "request_started",
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Add headers if enabled
            if self.include_headers:
                if self.mask_sensitive:
                    # Mask sensitive headers
                    headers = {
                        key: "[MASKED]" if key.lower() in self.sensitive_headers else value
                        for key, value in headers.items()
                    }
                log_data["headers"] = headers
            
            self.logger.info(json.dumps(log_data, ensure_ascii=False))
        else:
            # Compact format: INFO [root] METHOD /path - STARTED
            message = f"[root] {method} {path} - STARTED"
            self.logger.info(message)
            
            # Также записываем в файл через специальный логгер
            file_logger = logging.getLogger("middleware.http")
            file_logger.info(message)

    async def _log_response(self, method: str, path: str, status_code: int, process_time: float, correlation_id: str):
        """Log response."""
        if self.enable_structured:
            log_data = {
                "event": "request_completed",
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "process_time": round(process_time, 3),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.logger.info(json.dumps(log_data, ensure_ascii=False))
        else:
            # Compact format: INFO [root] METHOD /path STATUS TEXT (time)
            status_text = "OK" if status_code < 400 else "ERROR"
            message = f"[root] {method} {path} {status_code} {status_text} ({process_time:.3f}s)"
            self.logger.info(message)
            
            # Также записываем в файл через специальный логгер
            file_logger = logging.getLogger("middleware.http")
            file_logger.info(message)

    async def _log_exception(self, method: str, path: str, exception: Exception, correlation_id: str, process_time: float):
        """Log exception."""
        if self.enable_structured:
            log_data = {
                "event": "request_error",
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "error_type": type(exception).__name__,
                "error_message": str(exception),
                "process_time": round(process_time, 3),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.logger.error(json.dumps(log_data, ensure_ascii=False))
        else:
            # Compact format: ERROR [root] METHOD /path EXCEPTION (time)
            message = f"[root] {method} {path} {type(exception).__name__}: {exception} ({process_time:.3f}s)"
            self.logger.error(message)
            
            # Также записываем в файл через специальный логгер
            file_logger = logging.getLogger("middleware.http")
            file_logger.error(message)

    def _get_client_ip_from_scope(self, scope: Scope) -> str:
        """Extract client IP from ASGI scope."""
        # Check headers for forwarded IP
        headers = dict(scope.get("headers", []))
        
        forwarded_for = headers.get(b"x-forwarded-for")
        if forwarded_for:
            return forwarded_for.decode().split(",")[0].strip()
        
        real_ip = headers.get(b"x-real-ip")
        if real_ip:
            return real_ip.decode()
        
        # Fallback to client info
        client = scope.get("client")
        if client:
            return client[0]  # client is (host, port)
        
        return "unknown"

    def _mask_sensitive_data(self, data: Dict[bytes, bytes]) -> Dict[str, str]:
        """Mask sensitive headers."""
        result = {}
        for key_bytes, value_bytes in data.items():
            key = key_bytes.decode('latin1').lower()
            value = value_bytes.decode('latin1')
            
            if key in self.sensitive_headers:
                result[key] = "[MASKED]"
            else:
                result[key] = value
        
        return result


class LoggingMiddlewareAdapter(BaseHTTPMiddleware):
    """
    🔄 FastAPI-compatible adapter for LoggingMiddleware
    
    This adapter allows using our pure ASGI LoggingMiddleware with FastAPI's add_middleware()
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
        
        # Cache configuration
        self.enable_structured = settings.ENABLE_STRUCTURED_LOGGING
        self.include_headers = include_headers
        self.mask_sensitive = mask_sensitive_headers
        
        # Setup loggers
        self.logger = logging.getLogger()
        self.file_logger = logging.getLogger("middleware.http")
        
        # Exclude paths
        self.exclude_paths = [
            "/docs", "/openapi.json", "/favicon.ico", "/static"
        ]
        
        # Sensitive headers
        self.sensitive_headers = frozenset([
            "authorization", "x-api-key", "cookie", 
            "x-auth-token", "proxy-authorization"
        ])
        
        # Log initialization
        self.logger.info("✅ LoggingMiddlewareAdapter initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Adapter dispatch method."""
        # Check if path should be excluded
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate correlation ID and start timing
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log request
        client_ip = request.client.host if request.client else "unknown"
        await self._log_request(
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
            await self._log_response(
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
            await self._log_exception(
                request.method,
                request.url.path,
                exception,
                correlation_id,
                process_time
            )
            raise
    
    async def _log_request(self, method: str, path: str, client_ip: str, headers: Dict, correlation_id: str):
        """Log incoming request."""
        if self.enable_structured:
            # Structured logging for production
            log_data = {
                "event": "request_started",
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Add headers if enabled
            if self.include_headers:
                if self.mask_sensitive:
                    # Mask sensitive headers
                    headers = {
                        key: "[MASKED]" if key.lower() in self.sensitive_headers else value
                        for key, value in headers.items()
                    }
                log_data["headers"] = headers
            
            self.logger.info(json.dumps(log_data, ensure_ascii=False))
        else:
            # Compact format: INFO [root] METHOD /path - STARTED
            message = f"[root] {method} {path} - STARTED"
            self.logger.info(message)
            
            # Также записываем в файл через специальный логгер
            file_logger = logging.getLogger("middleware.http")
            file_logger.info(message)

    async def _log_response(self, method: str, path: str, status_code: int, process_time: float, correlation_id: str):
        """Log response."""
        if self.enable_structured:
            log_data = {
                "event": "request_completed",
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "process_time": round(process_time, 3),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.logger.info(json.dumps(log_data, ensure_ascii=False))
        else:
            # Compact format: INFO [root] METHOD /path STATUS TEXT (time)
            status_text = "OK" if status_code < 400 else "ERROR"
            message = f"[root] {method} {path} {status_code} {status_text} ({process_time:.3f}s)"
            self.logger.info(message)
            
            # Также записываем в файл через специальный логгер
            file_logger = logging.getLogger("middleware.http")
            file_logger.info(message)

    async def _log_exception(self, method: str, path: str, exception: Exception, correlation_id: str, process_time: float):
        """Log exception."""
        if self.enable_structured:
            log_data = {
                "event": "request_error",
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "error_type": type(exception).__name__,
                "error_message": str(exception),
                "process_time": round(process_time, 3),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.logger.error(json.dumps(log_data, ensure_ascii=False))
        else:
            # Compact format: ERROR [root] METHOD /path EXCEPTION (time)
            message = f"[root] {method} {path} {type(exception).__name__}: {exception} ({process_time:.3f}s)"
            self.logger.error(message)
            
            # Также записываем в файл через специальный логгер
            file_logger = logging.getLogger("middleware.http")
            file_logger.error(message)
    
    def _mask_sensitive_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive headers."""
        return {
            key: "[MASKED]" if key.lower() in self.sensitive_headers else value
            for key, value in data.items()
        } 