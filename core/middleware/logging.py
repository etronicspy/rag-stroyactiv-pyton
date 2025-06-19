"""
Unified logging middleware using core monitoring system.
Eliminates code duplication by leveraging core/monitoring/logger.py components.

ARCHITECTURE: Integrated with core.monitoring.logger for consistency
"""

import time
import uuid
from typing import Optional, Dict, Any, List, Callable

from starlette.types import ASGIApp, Receive, Scope, Send, Message
from starlette.requests import Request

from core.config import get_settings, Settings
from core.monitoring.unified_manager import get_unified_logging_manager
from core.monitoring.context import CorrelationContext, set_correlation_id
from core.monitoring.performance_optimizer import get_performance_optimizer
from core.monitoring.logger import get_logger

def should_exclude_path(path: str) -> bool:
    """
    Smart path exclusion with support for:
    - Exact matches: /health
    - Prefix patterns: /docs*  
    - Suffix patterns: */health
    - Wildcard patterns: /api/*/health/*
    - Path segments: health (matches any path containing 'health')
    """
    from core.config import get_settings
    import fnmatch
    
    settings = get_settings()
    exclude_paths = getattr(settings, 'LOG_EXCLUDE_PATHS', [])
    
    for exclude_pattern in exclude_paths:
        # 1. Exact match
        if path == exclude_pattern:
            return True
            
        # 2. Simple prefix match (legacy support)
        if exclude_pattern.endswith('*'):
            if path.startswith(exclude_pattern[:-1]):
                return True
        elif path.startswith(exclude_pattern):
            return True
            
        # 3. Suffix match  
        if exclude_pattern.startswith('*'):
            if path.endswith(exclude_pattern[1:]):
                return True
                
        # 4. Wildcard pattern matching (advanced)
        if '*' in exclude_pattern:
            if fnmatch.fnmatch(path, exclude_pattern):
                return True
                
        # 5. Path segment matching (contains)
        if '/' not in exclude_pattern and exclude_pattern in path:
            return True
    
    return False


class LoggingMiddleware:
    """Enhanced ASGI logging middleware with performance optimization."""
    
    def __init__(self, app: ASGIApp):
        """Initialize logging middleware with FastAPI-compatible signature."""
        self.app = app
        self.settings = get_settings()
        
        # 🚀 ЭТАП 4.4: Performance Optimization Integration
        self.enable_performance_optimization = getattr(self.settings, 'ENABLE_PERFORMANCE_OPTIMIZATION', True)
        if self.enable_performance_optimization:
            self.performance_optimizer = get_performance_optimizer()
        
        # Use optimized manager
        self.unified_manager = get_unified_logging_manager()
        self.request_logger = self.unified_manager.get_request_logger()
        
        # Get optimized logger
        if self.enable_performance_optimization:
            self.app_logger = self.unified_manager.get_optimized_logger("middleware.asgi")
        else:
            self.app_logger = get_logger("middleware.asgi")
        
        # Performance settings
        self.enable_batching = getattr(self.settings, 'ENABLE_LOG_BATCHING', True)
        self.log_requests = getattr(self.settings, 'ENABLE_REQUEST_LOGGING', True)
        self.log_request_body = getattr(self.settings, 'LOG_REQUEST_BODY', False) 
        self.log_request_headers = getattr(self.settings, 'LOG_REQUEST_HEADERS', True)
        self.log_performance_metrics = getattr(self.settings, 'LOG_PERFORMANCE_METRICS', True)
        
        self.app_logger.info(
            f"✅ LoggingMiddleware initialized with performance optimization: "
            f"optimization={self.enable_performance_optimization}, "
            f"batching={self.enable_batching}"
        )
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process HTTP request with performance-optimized logging."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract request information
        request = Request(scope, receive)
        method = request.method
        path = str(request.url.path)
        query_params = str(request.url.query)
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 🔧 Check if path should be excluded from logging
        if should_exclude_path(path):
            # Debug log for excluded paths
            self.app_logger.info(f"🚫 Path excluded from logging: {path}")
            await self.app(scope, receive, send)
            return
        
        # 🎯 ЭТАП 3.1: Generate and set correlation ID in context
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # 🔧 DEBUG: Always log that middleware is processing request
        self.app_logger.info(f"🔄 Processing HTTP request: {method} {path} (correlation_id: {correlation_id})")
        
        # Set request metadata in context  
        request_metadata = {
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "user_agent": user_agent
        }
        CorrelationContext.set_request_metadata(request_metadata)
        
        # 🚀 ЭТАП 4.4: Performance-optimized logging with fallback
        if self.log_requests:
            if self.enable_performance_optimization and self.request_logger:
                # Use optimized batched logging
                self.request_logger.log_request_start(
                    correlation_id=correlation_id,
                    method=method,
                    path=path,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    query_params=query_params
                )
            else:
                # Traditional logging fallback
                self.app_logger.info(
                    f"[{correlation_id}] Request started: {method} {path}",
                    extra={
                        "method": method,
                        "path": path,
                        "correlation_id": correlation_id,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "query_params": query_params
                    }
                )
        
        # Process request
        start_time = time.time()
        response_status = 200
        
        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
            
        except Exception as e:
            response_status = 500
            duration_ms = (time.time() - start_time) * 1000
            
            # 🚀 ЭТАП 4.4: Performance-optimized error logging
            if self.enable_performance_optimization and self.request_logger:
                self.request_logger.log_request_error(
                    correlation_id=correlation_id,
                    method=method,
                    path=path,
                    status_code=response_status,
                    duration_ms=duration_ms,
                    error=str(e),
                    client_ip=client_ip
                )
            else:
                # Traditional error logging fallback
                self.app_logger.error(
                    f"[{correlation_id}] Request failed: {method} {path} - {str(e)} ({duration_ms:.2f}ms)",
                    extra={
                        "method": method,
                        "path": path,
                        "status_code": response_status,
                        "duration_ms": duration_ms,
                        "correlation_id": correlation_id,
                        "error": str(e),
                        "client_ip": client_ip
                    }
                )
            
            raise
        
        finally:
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000
            
            # 🚀 ЭТАП 4.4: Performance-optimized completion logging
            if self.log_requests:
                if self.enable_performance_optimization and self.request_logger:
                    # Use optimized batched logging
                    self.request_logger.log_request_completion(
                        correlation_id=correlation_id,
                        method=method,
                        path=path,
                        status_code=response_status,
                        duration_ms=duration_ms,
                        client_ip=client_ip,
                        user_agent=user_agent
                    )
                else:
                    # Traditional logging fallback
                    self.app_logger.info(
                        f"[{correlation_id}] Request completed: {method} {path} - {response_status} ({duration_ms:.2f}ms)",
                        extra={
                            "method": method,
                            "path": path,
                            "status_code": response_status,
                            "duration_ms": duration_ms,
                            "correlation_id": correlation_id,
                            "client_ip": client_ip,
                            "user_agent": user_agent
                        }
                    )
            
            # 🚀 ЭТАП 4.4: Record performance metrics with batching
            if self.log_performance_metrics and self.enable_performance_optimization:
                self.performance_optimizer.record_metric_with_batching(
                    metric_type="counter",
                    metric_name="http_requests_total",
                    value=1,
                    labels={
                        "method": method,
                        "status_code": str(response_status),
                        "path_pattern": self.unified_manager._get_path_pattern(path)
                    }
                )
                
                self.performance_optimizer.record_metric_with_batching(
                    metric_type="histogram", 
                    metric_name="http_request_duration_seconds",
                    value=duration_ms / 1000.0,
                    labels={
                        "method": method,
                        "path_pattern": self.unified_manager._get_path_pattern(path)
                    }
                )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from ASGI scope."""
        headers = dict(request.scope.get("headers", []))
        
        # Check forwarded headers
        forwarded_for = headers.get(b"x-forwarded-for")
        if forwarded_for:
            return forwarded_for.decode().split(",")[0].strip()
        
        real_ip = headers.get(b"x-real-ip")
        if real_ip:
            return real_ip.decode()
        
        # Fallback to client info
        client = request.scope.get("client")
        return client[0] if client else "unknown"


# 🔧 ELIMINATED: LoggingMiddlewareAdapter removed - single unified LoggingMiddleware only
# FastAPI can use ASGI middleware directly without adapter pattern 