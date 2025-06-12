import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database.init_db import initialize_database_on_startup
from core.database.pool_manager import initialize_pool_manager, shutdown_pool_manager, PoolConfig
from core.middleware import (
    RateLimitMiddleware, 
    LoggingMiddleware, 
    SecurityMiddleware,
    ConditionalMiddleware,
    CompressionMiddleware,
    MiddlewareOptimizer
)
from core.middleware.rate_limiting_optimized import OptimizedRateLimitMiddleware
from core.monitoring import setup_structured_logging, get_metrics_collector
from api.routes import reference, health, materials, prices, search, monitoring

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup
    logger.info("🚀 Starting Construction Materials API...")
    
    # Setup monitoring and logging
    setup_structured_logging(
        log_level=settings.LOG_LEVEL,
        enable_structured=settings.ENABLE_STRUCTURED_LOGGING
    )
    
    # Initialize metrics collector
    metrics_collector = get_metrics_collector()
    metrics_collector._start_time = time.time()
    
    try:
        # Initialize database on startup
        init_results = await initialize_database_on_startup(
            run_migrations=settings.AUTO_MIGRATE,
            seed_data=settings.AUTO_SEED,
            verify_health=True
        )
        logger.info(f"✅ Database initialization: {init_results}")
        
        # Initialize dynamic pool manager
        pool_config = PoolConfig(
            min_size=2,
            max_size=50,
            target_utilization=0.75,
            scale_up_threshold=0.85,
            scale_down_threshold=0.4,
            monitoring_interval=30.0,
            auto_scaling_enabled=True
        )
        
        pool_manager = await initialize_pool_manager(pool_config)
        logger.info("✅ Dynamic pool manager initialized")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Continue startup even if DB init fails
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Construction Materials API...")
    
    # Shutdown pool manager
    try:
        await shutdown_pool_manager()
        logger.info("✅ Pool manager shutdown completed")
    except Exception as e:
        logger.error(f"❌ Pool manager shutdown failed: {e}")
    
    # Log final metrics
    final_metrics = metrics_collector.get_metrics_summary()
    logger.info(f"📊 Final application metrics: {final_metrics}")


app = FastAPI(lifespan=lifespan)

# Custom JSON response class to ensure UTF-8 encoding
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

# Set default response class
app.default_response_class = UTF8JSONResponse

# Initialize security middleware to get CORS settings
security_middleware = SecurityMiddleware(app)
cors_settings = security_middleware.get_cors_settings()

# Add optimized middleware in correct order (LIFO - Last In First Out)
# 1. Compression middleware (first to process responses)
app.add_middleware(CompressionMiddleware,
    minimum_size=1024,  # 1KB minimum
    maximum_size=10 * 1024 * 1024,  # 10MB maximum
    compression_level=6,  # Balanced compression
    enable_brotli=True,
    enable_streaming=True,
    exclude_paths=["/health", "/ping", "/metrics"],
    enable_performance_logging=settings.DEBUG,
)

# 2. Conditional Security middleware (only for API routes)
security_middleware = MiddlewareOptimizer.exclude_static_and_health(
    SecurityMiddleware,
    max_request_size=settings.MAX_REQUEST_SIZE_MB * 1024 * 1024,
    enable_security_headers=True,
    enable_input_validation=True,
    enable_xss_protection=True,
    enable_sql_injection_protection=True,
    enable_path_traversal_protection=True,
)
app.add_middleware(ConditionalMiddleware, 
    middleware_class=SecurityMiddleware,
    middleware_kwargs={
        "max_request_size": settings.MAX_REQUEST_SIZE_MB * 1024 * 1024,
        "enable_security_headers": True,
        "enable_input_validation": True,
        "enable_xss_protection": True,
        "enable_sql_injection_protection": True,
        "enable_path_traversal_protection": True,
    },
    exclude_paths=[r"/health.*", r"/ping", r"/metrics", r"/docs.*", r"/redoc.*"],
    enable_performance_logging=settings.DEBUG,
)

# 3. Optimized Rate limiting middleware (only for API routes)
if settings.ENABLE_RATE_LIMITING:
    app.add_middleware(ConditionalMiddleware,
        middleware_class=OptimizedRateLimitMiddleware,
        middleware_kwargs={
            "redis_url": settings.REDIS_URL,
            "default_requests_per_minute": settings.RATE_LIMIT_RPM,
            "default_requests_per_hour": settings.RATE_LIMIT_RPH,
            "default_burst_size": settings.RATE_LIMIT_BURST,
            "enable_burst_protection": True,
            "rate_limit_headers": True,
            "enable_performance_logging": settings.DEBUG,
        },
        include_paths=[r"/api/.*"],
        exclude_paths=[r"/api/v1/health/.*"],
        enable_performance_logging=settings.DEBUG,
    )

# 4. Conditional Logging middleware (exclude health checks for performance)
app.add_middleware(ConditionalMiddleware,
    middleware_class=LoggingMiddleware,
    middleware_kwargs={
        "log_level": settings.LOG_LEVEL,
        "log_request_body": settings.LOG_REQUEST_BODY,
        "log_response_body": settings.LOG_RESPONSE_BODY,
        "max_body_size": 64 * 1024,  # 64KB
        "include_headers": True,
        "mask_sensitive_headers": True,
    },
    exclude_paths=[r"/health", r"/ping", r"/metrics"],
    enable_performance_logging=settings.DEBUG,
)

# 5. CORS middleware (last, closest to app)
app.add_middleware(CORSMiddleware, **cors_settings)

# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(reference.router, prefix="/api/v1/reference", tags=["reference"])
app.include_router(materials.router, prefix="/api/v1/materials", tags=["materials"])
app.include_router(prices.router, prefix="/api/v1/prices", tags=["prices"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Construction Materials API",
        "version": settings.VERSION,
        "docs_url": "/docs"
    } 