"""
Unified logging middleware using core monitoring system.
Eliminates code duplication by leveraging core/monitoring/logger.py components.

ARCHITECTURE: Integrated with core.monitoring.logger for consistency
"""

import time
import uuid
from typing import Optional, Dict, Any, List, Callable

# 🔧 CLEANED: Removed unused imports (Request, Response, BaseHTTPMiddleware)
from starlette.types import ASGIApp, Receive, Scope, Send, Message

from core.config import get_settings
from core.monitoring.unified_manager import get_unified_logging_manager
from core.monitoring.context import CorrelationContext, set_correlation_id

# 🔧 CONSTANTS: Moved hardcoded values to constants
EXCLUDE_PATHS = ["/docs", "/openapi.json", "/favicon.ico", "/static"]


# 🔧 ELIMINATED: BaseLoggingHandler removed - using core.monitoring.logger.RequestLogger instead

def should_exclude_path(path: str) -> bool:
    """Fast path exclusion check."""
    return any(path.startswith(exclude_path) for exclude_path in EXCLUDE_PATHS)


class LoggingMiddleware:
    """
    🚀 Unified ASGI HTTP Request/Response Logging Middleware
    
    Features:
    - Pure ASGI implementation (compatible with BodyCacheMiddleware)
    - Integrated with core.monitoring.logger.RequestLogger
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
        
        # 🔧 UNIFIED: Use UnifiedLoggingManager for complete integration
        self.unified_manager = get_unified_logging_manager()
        self.request_logger = self.unified_manager.get_request_logger()
        self.app_logger = self.unified_manager.get_logger("middleware.asgi")
        
        # Override exclude paths if provided
        self.exclude_paths = exclude_paths or EXCLUDE_PATHS
        
        # Log initialization
        if self.enable_request_logging:
            self.app_logger.info("✅ LoggingMiddleware initialized with ASGI implementation")
        else:
            self.app_logger.info("⚠️ LoggingMiddleware initialized but REQUEST LOGGING DISABLED")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pure ASGI middleware entry point."""
        if scope["type"] != "http" or not self.enable_request_logging:
            await self.app(scope, receive, send)
            return
            
        # Fast path exclusion check
        path = scope.get("path", "")
        if should_exclude_path(path):
            await self.app(scope, receive, send)
            return
        
        # Generate correlation ID and extract request info
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        method = scope.get("method", "GET")
        client_ip = self._get_client_ip_from_scope(scope)
        
        # 🎯 ЭТАП 3.1: Установить correlation ID в контекст для всего запроса
        set_correlation_id(correlation_id)
        
        # Set request metadata in context
        request_metadata = {
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "user_agent": scope.get("headers", {}).get("user-agent", "unknown")
        }
        CorrelationContext.set_request_metadata(request_metadata)
        
        # 🔧 UNIFIED: Simple start logging
        self.app_logger.info(f"[{correlation_id}] {method} {path} - Started from {client_ip}")
        
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
                    duration_ms = (time.time() - start_time) * 1000
                    # 🔧 UNIFIED: Use UnifiedLoggingManager for logging + metrics
                    self.unified_manager.log_http_request(
                        method=method,
                        path=path,
                        status_code=status_code,
                        duration_ms=duration_ms,
                        request_id=correlation_id,
                        ip_address=client_ip
                    )
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exception:
            # Log exception
            duration_ms = (time.time() - start_time) * 1000
            self.app_logger.error(
                f"[{correlation_id}] {method} {path} - ERROR: {type(exception).__name__}: {str(exception)} ({duration_ms:.2f}ms)",
                exc_info=exception
            )
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


# 🔧 ELIMINATED: LoggingMiddlewareAdapter removed - single unified LoggingMiddleware only
# FastAPI can use ASGI middleware directly without adapter pattern 