"""
Request logging handler.

Provides specialized logging for HTTP requests with correlation tracking.
Extracted and refactored from core/monitoring/logger.py.
"""

import logging
from typing import Optional

from ..context.correlation import get_correlation_id


class RequestLogger:
    """Logger for HTTP requests with correlation tracking."""
    
    def __init__(self):
        """Initialize request logger."""
        from ..base.loggers import get_logger
        self.logger = get_logger('requests')
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """
        Log HTTP request with structured data.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            user_id: User identifier
            request_id: Request identifier
            request_size: Request body size in bytes
            response_size: Response body size in bytes
            user_agent: User agent string
            ip_address: Client IP address
        """
        level = logging.INFO if status_code < 400 else logging.WARNING
        if status_code >= 500:
            level = logging.ERROR
            
        message = f"{method} {path} - {status_code} - {duration_ms:.2f}ms"
        
        # Build extra fields
        extra = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2)
        }
        
        # Add optional fields
        if user_id:
            extra["user_id"] = user_id
        if request_id:
            extra["request_id"] = request_id
        if request_size is not None:
            extra["request_size"] = request_size
        if response_size is not None:
            extra["response_size"] = response_size
        if user_agent:
            extra["user_agent"] = user_agent
        if ip_address:
            extra["ip_address"] = ip_address
            
        # Add correlation ID from context
        correlation_id = get_correlation_id()
        if correlation_id:
            extra["correlation_id"] = correlation_id
        
        # Use LoggerAdapter to add extra fields
        adapter = logging.LoggerAdapter(self.logger, extra)
        adapter.log(level, message, extra=extra) 