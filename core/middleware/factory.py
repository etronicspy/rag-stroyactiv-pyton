"""
Middleware factory for creating and configuring middleware stack.

Provides centralized middleware configuration and eliminates duplication in main.py.
"""

from typing import List, Tuple, Dict, Any, Type
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import Settings
from core.middleware.logging import LoggingMiddleware
from core.middleware.security import SecurityMiddleware
from core.middleware.compression import CompressionMiddleware
from core.middleware.rate_limiting import RateLimitMiddleware
from core.middleware.body_cache import BodyCacheMiddleware


class MiddlewareConfig:
    """Configuration holder for middleware settings."""
    
    # 🔧 CONSTANTS: Centralized middleware configuration
    DEFAULT_EXCLUDE_PATHS = ["/docs", "/openapi.json", "/favicon.ico", "/static"]
    DEFAULT_HEALTH_PATHS = ["/health", "/ping", "/metrics"]
    
    @staticmethod
    def get_logging_config(settings: Settings) -> Dict[str, Any]:
        """Get logging middleware configuration."""
        return {
            "log_level": settings.LOG_LEVEL,
            "log_request_body": settings.LOG_REQUEST_BODY,
            "log_response_body": settings.LOG_RESPONSE_BODY,
            "max_body_size": 64 * 1024,  # 64KB
            "exclude_paths": MiddlewareConfig.DEFAULT_EXCLUDE_PATHS,
            "include_headers": True,
            "mask_sensitive_headers": True,
        }
    
    @staticmethod
    def get_body_cache_config(settings: Settings) -> Dict[str, Any]:
        """Get body cache middleware configuration."""
        return {
            "max_body_size": settings.MAX_REQUEST_SIZE_MB * 1024 * 1024,
            "methods_to_cache": ["POST", "PUT", "PATCH"],
        }
    
    @staticmethod
    def get_compression_config(settings: Settings) -> Dict[str, Any]:
        """Get compression middleware configuration."""
        return {
            "minimum_size": 2048,                    # 2KB minimum
            "maximum_size": 5 * 1024 * 1024,         # 5MB maximum
            "compression_level": 6,                  # Optimal compression
            "enable_brotli": True,                   # Brotli support (~20% better than gzip)
            "enable_streaming": True,                # Streaming for large files
            "exclude_paths": MiddlewareConfig.DEFAULT_HEALTH_PATHS,
            "enable_performance_logging": True,      # Performance metrics
        }
    
    @staticmethod
    def get_security_config(settings: Settings) -> Dict[str, Any]:
        """Get security middleware configuration."""
        return {
            "max_request_size": settings.MAX_REQUEST_SIZE_MB * 1024 * 1024,
            "enable_security_headers": True,
            "enable_input_validation": True,
            "enable_xss_protection": True,
            "enable_sql_injection_protection": True,
            "enable_path_traversal_protection": True,
        }
    
    @staticmethod
    def get_rate_limit_config(settings: Settings) -> Dict[str, Any]:
        """Get rate limiting middleware configuration."""
        return {
            "default_requests_per_minute": settings.RATE_LIMIT_RPM,
            "default_requests_per_hour": 1000,
            "enable_burst_protection": True,
            "rate_limit_headers": True,
        }
    
    @staticmethod
    def get_cors_config(security_middleware: SecurityMiddleware) -> Dict[str, Any]:
        """Get CORS middleware configuration."""
        return security_middleware.get_cors_settings()


class MiddlewareFactory:
    """
    🏭 Factory for creating and configuring middleware stack.
    
    Provides centralized middleware creation and eliminates code duplication.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config = MiddlewareConfig()
    
    def create_middleware_stack(self) -> List[Tuple[Type, Dict[str, Any]]]:
        """
        Create middleware stack configuration.
        
        Returns:
            List of (middleware_class, config) tuples in LIFO order
        """
        middleware_stack = []
        
        # 1. Logging middleware (executes first)
        middleware_stack.append((
            LoggingMiddleware,
            self.config.get_logging_config(self.settings)
        ))
        
        # 2. Body Cache middleware
        middleware_stack.append((
            BodyCacheMiddleware,
            self.config.get_body_cache_config(self.settings)
        ))
        
        # 3. Compression middleware
        middleware_stack.append((
            CompressionMiddleware,
            self.config.get_compression_config(self.settings)
        ))
        
        # 4. Security middleware
        middleware_stack.append((
            SecurityMiddleware,
            self.config.get_security_config(self.settings)
        ))
        
        # 5. Rate limiting middleware (optional)
        if self.settings.ENABLE_RATE_LIMITING:
            middleware_stack.append((
                RateLimitMiddleware,
                self.config.get_rate_limit_config(self.settings)
            ))
        
        return middleware_stack
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration from security middleware."""
        security_middleware = SecurityMiddleware(None)  # Temporary instance for config
        return self.config.get_cors_config(security_middleware)


def setup_middleware(app: FastAPI, settings: Settings) -> None:
    """
    🔧 Setup complete middleware stack for FastAPI application.
    
    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    factory = MiddlewareFactory(settings)
    
    # Get middleware stack configuration
    middleware_stack = factory.create_middleware_stack()
    
    # Add CORS middleware first (executes last)
    cors_config = factory.get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)
    
    # Add middleware stack in reverse order (LIFO)
    for middleware_class, middleware_config in reversed(middleware_stack):
        try:
            app.add_middleware(middleware_class, **middleware_config)
            # Log successful initialization
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"✅ {middleware_class.__name__} initialized")
        except Exception as e:
            # Log initialization failure but continue
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize {middleware_class.__name__}: {e}")


def create_development_middleware_stack(app: FastAPI, settings: Settings) -> None:
    """
    🚧 Create lightweight middleware stack for development.
    
    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    # Minimal middleware for development
    app.add_middleware(LoggingMiddleware,
        log_level=settings.LOG_LEVEL,
        exclude_paths=MiddlewareConfig.DEFAULT_EXCLUDE_PATHS,
    )
    
    # Security with minimal overhead
    app.add_middleware(SecurityMiddleware,
        max_request_size=settings.MAX_REQUEST_SIZE_MB * 1024 * 1024,
        enable_security_headers=False,  # Disable for development
    )


def create_production_middleware_stack(app: FastAPI, settings: Settings) -> None:
    """
    🚀 Create full middleware stack for production.
    
    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    # Use full middleware stack for production
    setup_middleware(app, settings) 