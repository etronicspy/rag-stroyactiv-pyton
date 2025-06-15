"""
Logging middleware for comprehensive request/response monitoring.
Provides structured logging with performance metrics and security monitoring.
"""

import time
import uuid
import json
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

from core.config import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive logging middleware for FastAPI.
    
    Features:
    - Request/response logging with correlation IDs
    - Performance monitoring (response times, status codes)
    - Security event logging (failed authentications, rate limits)
    - Structured JSON logging for production environments
    - Request body logging (with size limits)
    - Error tracking and alerting
    """
    
    def __init__(
        self,
        app,
        log_level: str = "INFO",
        log_request_body: bool = True,
        log_response_body: bool = False,
        max_body_size: int = 64 * 1024,  # 64KB
        exclude_paths: Optional[list] = None,
        include_headers: bool = True,
        mask_sensitive_headers: bool = True,
    ):
        super().__init__(app)
        self.logger = logging.getLogger("middleware.logging")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.include_headers = include_headers
        self.mask_sensitive = mask_sensitive_headers
        
        # Paths to exclude from detailed logging (health checks, etc.)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/api/v1/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ]
        
        # Sensitive headers to mask in logs
        self.sensitive_headers = {
            "authorization",
            "x-api-key", 
            "cookie",
            "x-auth-token",
            "authorization",
            "proxy-authorization",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method."""
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        start_time = time.time()
        
        # Skip detailed logging for excluded paths
        should_log_details = not any(
            request.url.path.startswith(path) for path in self.exclude_paths
        )
        
        # Log request
        if should_log_details:
            await self._log_request(request, correlation_id)
        
        try:
            # Capture request body if needed
            if self.log_request_body and should_log_details:
                await self._capture_request_body(request)
            
            # Process request
            response = await call_next(request)
            
            # Calculate metrics
            process_time = time.time() - start_time
            
            # Log response
            if should_log_details:
                await self._log_response(request, response, process_time, correlation_id)
            else:
                # Minimal logging for excluded paths
                self.logger.debug(
                    f"{request.method} {request.url.path} -> {response.status_code} "
                    f"({process_time:.3f}s) [{correlation_id}]"
                )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            # Log exceptions
            process_time = time.time() - start_time
            await self._log_exception(request, e, process_time, correlation_id)
            raise

    async def _log_request(self, request: Request, correlation_id: str):
        """Log incoming request details."""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")
        
        log_data = {
            "event": "request_started",
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent,
        }
        
        # Add headers if enabled
        if self.include_headers:
            headers = dict(request.headers)
            if self.mask_sensitive:
                headers = self._mask_sensitive_data(headers)
            log_data["headers"] = headers
        
        # Log request size
        content_length = request.headers.get("content-length")
        if content_length:
            log_data["content_length"] = int(content_length)
        
        self.logger.info(f"Request: {json.dumps(log_data)}")

    async def _capture_request_body(self, request: Request):
        """Capture request body for logging using cached body (with size limits)."""
        try:
            content_type = request.headers.get("content-type", "")
            
            # Only capture text-based content types
            if not any(ct in content_type.lower() for ct in [
                "application/json", "application/xml", "text/", "application/x-www-form-urlencoded"
            ]):
                return
            
            # Используем кешированный body из BodyCacheMiddleware
            from core.middleware.body_cache import get_cached_body_str, get_cached_body_bytes
            
            body_str = get_cached_body_str(request)
            if body_str:
                if len(body_str) > self.max_body_size:
                    request.state.request_body = f"[Body too large: {len(body_str)} bytes]"
                else:
                    request.state.request_body = body_str
            elif hasattr(request.state, 'body_cache_available'):
                if request.state.body_cache_available:
                    # Кеш доступен, но body пустой
                    request.state.request_body = ""
                else:
                    # Кеш недоступен
                    request.state.request_body = "[Body cache not available]"
            else:
                # BodyCacheMiddleware не был выполнен
                request.state.request_body = "[Body cache middleware not configured]"
                    
        except Exception as e:
            self.logger.warning(f"Failed to capture request body: {e}")
            request.state.request_body = "[Failed to capture]"

    async def _log_response(
        self, 
        request: Request, 
        response: Response, 
        process_time: float, 
        correlation_id: str
    ):
        """Log response details and performance metrics."""
        client_ip = self._get_client_ip(request)
        
        log_data = {
            "event": "request_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_seconds": round(process_time, 3),
            "client_ip": client_ip,
        }
        
        # Add request body if captured
        if hasattr(request.state, "request_body"):
            log_data["request_body"] = request.state.request_body
        
        # Add response headers
        if self.include_headers:
            headers = dict(response.headers)
            log_data["response_headers"] = headers
        
        # Add response size
        content_length = response.headers.get("content-length")
        if content_length:
            log_data["response_size"] = int(content_length)
        
        # Log level based on status code
        if response.status_code >= 500:
            self.logger.error(f"Response 5xx: {json.dumps(log_data)}")
        elif response.status_code >= 400:
            self.logger.warning(f"Response 4xx: {json.dumps(log_data)}")
        elif process_time > 5.0:  # Slow requests
            self.logger.warning(f"Slow request: {json.dumps(log_data)}")
        else:
            self.logger.info(f"Response: {json.dumps(log_data)}")
        
        # Log performance metrics separately for monitoring
        self._log_performance_metrics(request, response, process_time)

    async def _log_exception(
        self, 
        request: Request, 
        exception: Exception, 
        process_time: float, 
        correlation_id: str
    ):
        """Log unhandled exceptions."""
        client_ip = self._get_client_ip(request)
        
        log_data = {
            "event": "request_exception",
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "client_ip": client_ip,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "process_time_seconds": round(process_time, 3),
        }
        
        # Add request body if captured
        if hasattr(request.state, "request_body"):
            log_data["request_body"] = request.state.request_body
        
        self.logger.error(f"Exception: {json.dumps(log_data)}", exc_info=True)

    def _log_performance_metrics(
        self, 
        request: Request, 
        response: Response, 
        process_time: float
    ):
        """Log performance metrics for monitoring."""
        # This could be sent to metrics collection system (Prometheus, etc.)
        metrics_data = {
            "metric": "http_request_duration",
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_seconds": process_time,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Log to metrics logger (could be separate handler)
        metrics_logger = logging.getLogger("metrics")
        metrics_logger.info(json.dumps(metrics_data))

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers."""
        # Try various headers for real IP (reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"

    def _mask_sensitive_data(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive information in headers."""
        masked_headers = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                # Mask sensitive headers
                if len(value) > 8:
                    masked_headers[key] = value[:4] + "..." + value[-4:]
                else:
                    masked_headers[key] = "***"
            else:
                masked_headers[key] = value
        return masked_headers

    def configure_structured_logging(self):
        """Configure structured JSON logging for production."""
        if settings.ENVIRONMENT == "production":
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": %(message)s}'
            )
            
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            
            self.logger.handlers = [handler]
            self.logger.propagate = False 