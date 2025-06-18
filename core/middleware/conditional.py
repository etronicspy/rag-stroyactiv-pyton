"""
Conditional middleware wrapper for optimized performance.
Allows middleware to be applied only to specific routes or conditions.
"""

from core.monitoring.logger import get_logger
import time
from typing import Callable, Optional, List, Union, Pattern
import re
from functools import lru_cache

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = get_logger(__name__)


class ConditionalMiddleware(BaseHTTPMiddleware):
    """
    Conditional middleware wrapper that applies middleware only when specific conditions are met.
    
    This optimization reduces overhead by skipping middleware execution for routes that don't need it.
    For example, static files, health checks, or specific API endpoints can bypass certain middleware.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        middleware_class: type,
        middleware_kwargs: dict = None,
        include_paths: Optional[List[Union[str, Pattern]]] = None,
        exclude_paths: Optional[List[Union[str, Pattern]]] = None,
        include_methods: Optional[List[str]] = None,
        exclude_methods: Optional[List[str]] = None,
        condition_func: Optional[Callable[[Request], bool]] = None,
        enable_performance_logging: bool = False,
    ):
        """
        Initialize conditional middleware.
        
        Args:
            app: ASGI application
            middleware_class: The middleware class to conditionally apply
            middleware_kwargs: Keyword arguments for middleware initialization
            include_paths: List of path patterns to include (if None, all paths included)
            exclude_paths: List of path patterns to exclude
            include_methods: List of HTTP methods to include (if None, all methods included)
            exclude_methods: List of HTTP methods to exclude
            condition_func: Custom condition function that takes Request and returns bool
            enable_performance_logging: Log performance metrics for middleware decisions
        """
        super().__init__(app)
        
        self.middleware_class = middleware_class
        self.middleware_kwargs = middleware_kwargs or {}
        self.include_paths = self._compile_patterns(include_paths or [])
        self.exclude_paths = self._compile_patterns(exclude_paths or [])
        self.include_methods = set(include_methods or [])
        self.exclude_methods = set(exclude_methods or [])
        self.condition_func = condition_func
        self.enable_performance_logging = enable_performance_logging
        
        # Performance tracking
        self.total_requests = 0
        self.middleware_applied = 0
        self.middleware_skipped = 0
        
        # Initialize the actual middleware instance
        self._middleware_instance = None
        
        logger.info(
            f"✅ ConditionalMiddleware initialized for {middleware_class.__name__} "
            f"with {len(self.include_paths)} include patterns, "
            f"{len(self.exclude_paths)} exclude patterns"
        )

    def _compile_patterns(self, patterns: List[Union[str, Pattern]]) -> List[Pattern]:
        """Compile string patterns to regex patterns for efficient matching."""
        compiled = []
        for pattern in patterns:
            if isinstance(pattern, str):
                # Convert glob-like patterns to regex
                regex_pattern = pattern.replace("*", ".*").replace("?", ".")
                compiled.append(re.compile(regex_pattern))
            else:
                compiled.append(pattern)
        return compiled

    @lru_cache(maxsize=1000)
    def _should_apply_middleware(self, path: str, method: str) -> bool:
        """
        Determine if middleware should be applied based on conditions.
        Uses LRU cache for frequently accessed paths.
        """
        # Check method filters
        if self.include_methods and method not in self.include_methods:
            return False
        if self.exclude_methods and method in self.exclude_methods:
            return False
        
        # Check exclude paths first (higher priority)
        for pattern in self.exclude_paths:
            if pattern.match(path):
                return False
        
        # Check include paths
        if self.include_paths:
            for pattern in self.include_paths:
                if pattern.match(path):
                    return True
            return False  # No include pattern matched
        
        return True  # No include patterns specified, so include by default

    async def _get_middleware_instance(self):
        """Lazy initialization of middleware instance."""
        if self._middleware_instance is None:
            # Create middleware instance with the current app
            self._middleware_instance = self.middleware_class(
                self.app, **self.middleware_kwargs
            )
        return self._middleware_instance

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main dispatch method with conditional middleware application."""
        start_time = time.time() if self.enable_performance_logging else 0
        self.total_requests += 1
        
        path = request.url.path
        method = request.method
        
        # Apply custom condition function if provided
        if self.condition_func and not self.condition_func(request):
            self.middleware_skipped += 1
            if self.enable_performance_logging:
                decision_time = time.time() - start_time
                logger.debug(
                    f"Middleware skipped (custom condition): {method} {path} "
                    f"({decision_time*1000:.2f}ms decision time)"
                )
            return await call_next(request)
        
        # Check path and method conditions
        should_apply = self._should_apply_middleware(path, method)
        
        if should_apply:
            # Apply middleware
            self.middleware_applied += 1
            
            if self.enable_performance_logging:
                decision_time = time.time() - start_time
                logger.debug(
                    f"Middleware applied: {method} {path} "
                    f"({decision_time*1000:.2f}ms decision time)"
                )
            
            # Get middleware instance and process request
            middleware_instance = await self._get_middleware_instance()
            return await middleware_instance.dispatch(request, call_next)
        else:
            # Skip middleware
            self.middleware_skipped += 1
            
            if self.enable_performance_logging:
                decision_time = time.time() - start_time
                logger.debug(
                    f"Middleware skipped: {method} {path} "
                    f"({decision_time*1000:.2f}ms decision time)"
                )
            
            return await call_next(request)

    def get_performance_stats(self) -> dict:
        """Get performance statistics for this conditional middleware."""
        if self.total_requests == 0:
            return {
                "total_requests": 0,
                "middleware_applied": 0,
                "middleware_skipped": 0,
                "application_rate": 0.0,
                "skip_rate": 0.0,
            }
        
        return {
            "middleware_class": self.middleware_class.__name__,
            "total_requests": self.total_requests,
            "middleware_applied": self.middleware_applied,
            "middleware_skipped": self.middleware_skipped,
            "application_rate": self.middleware_applied / self.total_requests,
            "skip_rate": self.middleware_skipped / self.total_requests,
        }


class MiddlewareOptimizer:
    """
    Utility class for creating optimized conditional middleware configurations.
    """
    
    @staticmethod
    def for_api_routes_only(middleware_class: type, **kwargs) -> ConditionalMiddleware:
        """Create conditional middleware that only applies to API routes."""
        return ConditionalMiddleware(
            app=None,  # Will be set by FastAPI
            middleware_class=middleware_class,
            middleware_kwargs=kwargs,
            include_paths=[r"/api/.*"],
            exclude_paths=[r"/docs.*", r"/redoc.*", r"/openapi\.json"],
        )
    
    @staticmethod
    def exclude_static_and_health(middleware_class: type, **kwargs) -> ConditionalMiddleware:
        """Create conditional middleware that excludes static files and health checks."""
        return ConditionalMiddleware(
            app=None,  # Will be set by FastAPI
            middleware_class=middleware_class,
            middleware_kwargs=kwargs,
            exclude_paths=[
                r"/static/.*",
                r"/favicon\.ico",
                r"/health.*",
                r"/ping",
                r"/metrics",
            ],
        )
    
    @staticmethod
    def for_authenticated_routes_only(middleware_class: type, **kwargs) -> ConditionalMiddleware:
        """Create conditional middleware that only applies to routes requiring authentication."""
        def requires_auth(request: Request) -> bool:
            # Check if request has authentication headers or is to protected endpoint
            has_auth_header = bool(
                request.headers.get("Authorization") or 
                request.headers.get("X-API-Key")
            )
            protected_patterns = ["/api/v1/materials", "/api/v1/prices"]
            is_protected_endpoint = any(
                request.url.path.startswith(pattern) for pattern in protected_patterns
            )
            return has_auth_header or is_protected_endpoint
        
        return ConditionalMiddleware(
            app=None,  # Will be set by FastAPI
            middleware_class=middleware_class,
            middleware_kwargs=kwargs,
            condition_func=requires_auth,
        )
    
    @staticmethod
    def for_write_operations_only(middleware_class: type, **kwargs) -> ConditionalMiddleware:
        """Create conditional middleware that only applies to write operations (POST, PUT, DELETE)."""
        return ConditionalMiddleware(
            app=None,  # Will be set by FastAPI
            middleware_class=middleware_class,
            middleware_kwargs=kwargs,
            include_methods=["POST", "PUT", "PATCH", "DELETE"],
        ) 