"""
Logging middleware for comprehensive request/response monitoring.
Provides structured logging with performance metrics and security monitoring.

OPTIMIZED: High-performance implementation with unified logger strategy
"""

import time
import uuid
import json
import logging
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_settings


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    🚀 Optimized HTTP Request/Response Logging Middleware
    
    Features:
    - High-performance unified logger strategy
    - Optimized body reading with lazy evaluation
    - Correlation ID tracking
    - Configurable formatting (simple/structured)
    - Smart path exclusion
    """
    
    def __init__(
        self,
        app,
        log_level: Optional[str] = None,
        log_request_body: Optional[bool] = None,
        log_response_body: Optional[bool] = None,
        max_body_size: int = 64 * 1024,  # 64KB
        exclude_paths: Optional[List[str]] = None,
        include_headers: bool = True,
        mask_sensitive_headers: bool = True,
    ):
        super().__init__(app)
        
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
        self.logger.info("✅ LoggingMiddleware initialized with optimized configuration")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Optimized main middleware dispatch method."""
        # Fast path exclusion check
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate correlation ID once
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log request
        await self._log_request(request, correlation_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers["x-correlation-id"] = correlation_id
            
            # Log response with timing
            process_time = time.time() - start_time
            await self._log_response(request, response.status_code, process_time, correlation_id)
            
            return response
            
        except Exception as exception:
            # Log exception with timing
            process_time = time.time() - start_time
            await self._log_exception(request, exception, correlation_id, process_time)
            raise

    async def _log_request(self, request: Request, correlation_id: str):
        """Optimized request logging."""
        # 🔧 FIX: Явно устанавливаем уровень в async контексте
        self.logger.setLevel(logging.DEBUG)
        # 🔧 FIX: Также устанавливаем уровень для всех handlers (включая file handler)
        for handler in self.logger.handlers:
            handler.setLevel(logging.DEBUG)
        
        client_ip = self._get_client_ip(request)
        
        if self.enable_structured:
            # Structured logging for production
            log_data = {
                "event": "request_started",
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Add headers if enabled (optimized)
            if self.include_headers:
                headers = dict(request.headers)
                if self.mask_sensitive:
                    headers = self._mask_sensitive_data(headers)
                log_data["headers"] = headers
            
            # Add request body if enabled (lazy evaluation)
            if self.log_request_body and request.method in {"POST", "PUT", "PATCH"}:
                log_data["body"] = await self._get_request_body(request)
            
            self.logger.info(json.dumps(log_data, ensure_ascii=False))
        else:
            # Simple format for development
            message = f"{request.method} {request.url.path} from {client_ip}"
            self.logger.info(message)  # В терминал
            self.file_logger.info(message)  # В файл

    async def _log_response(self, request: Request, status_code: int, process_time: float, correlation_id: str):
        """Optimized response logging."""
        # 🔧 FIX: Явно устанавливаем уровень в async контексте
        self.logger.setLevel(logging.DEBUG)
        # 🔧 FIX: Также устанавливаем уровень для всех handlers (включая file handler)
        for handler in self.logger.handlers:
            handler.setLevel(logging.DEBUG)
        
        if self.enable_structured:
            log_data = {
                "event": "request_completed",
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "process_time": round(process_time, 3),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.logger.info(json.dumps(log_data, ensure_ascii=False))
        else:
            # Beautiful simple format
            status_text = "OK" if status_code < 400 else "ERROR"
            message = f"{request.method} {request.url.path} {status_code} {status_text} ({process_time:.3f}s)"
            self.logger.info(message)  # В терминал
            self.file_logger.info(message)  # В файл

    async def _log_exception(self, request: Request, exception: Exception, correlation_id: str, process_time: float):
        """Optimized exception logging."""
        # 🔧 FIX: Явно устанавливаем уровень в async контексте
        self.logger.setLevel(logging.DEBUG)
        
        if self.enable_structured:
            log_data = {
                "event": "request_error",
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "error_type": type(exception).__name__,
                "error_message": str(exception),
                "process_time": round(process_time, 3),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.logger.error(json.dumps(log_data, ensure_ascii=False))
        else:
            self.logger.error(f"❌ {type(exception).__name__}: {exception} - {request.method} {request.url.path} ({process_time:.3f}s)")

    async def _get_request_body(self, request: Request) -> str:
        """Optimized request body reading with size limits."""
        try:
            body = await request.body()
            if not body:
                return ""
            
            body_str = body.decode('utf-8')
            if len(body_str) > self.max_body_size:
                return f"[Body too large: {len(body_str)} bytes, max: {self.max_body_size}]"
            
            return body_str
        except Exception as e:
            return f"[Error reading body: {e}]"

    def _get_client_ip(self, request: Request) -> str:
        """Optimized client IP extraction."""
        # Fast path for most common cases
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        # Fallback to headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.headers.get("x-real-ip", "unknown")

    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimized sensitive data masking with frozenset lookup."""
        return {
            key: "[MASKED]" if key.lower() in self.sensitive_headers else value
            for key, value in data.items()
        } 