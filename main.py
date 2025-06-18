import asyncio
import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.config import get_settings
from core.database.init_db import initialize_database_on_startup
from core.database.pool_manager import initialize_pool_manager, shutdown_pool_manager, PoolConfig
from core.middleware.factory import setup_middleware
from core.monitoring import setup_structured_logging, get_metrics_collector
from docs.api_description import get_fastapi_config
from api.routes import reference, health, materials, prices, search, advanced_search, tunnel
from services.ssh_tunnel_service import initialize_tunnel_service, shutdown_tunnel_service

# Initialize settings
settings = get_settings()

# Setup logging BEFORE creating the app and middleware
setup_structured_logging(
    log_level=settings.LOG_LEVEL,
    enable_structured=settings.ENABLE_STRUCTURED_LOGGING,
    log_file=settings.LOG_FILE,
    enable_colors=settings.LOG_COLORS,
    third_party_level=settings.LOG_THIRD_PARTY_LEVEL
)

# Initialize logger after setup
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup
    logger.info("🚀 Starting Construction Materials API...")
    
    # Initialize metrics collector
    metrics_collector = get_metrics_collector()
    metrics_collector._start_time = time.time()
    
    try:
        # Initialize SSH tunnel service FIRST (must be before database)
        tunnel_service = await initialize_tunnel_service()
        if tunnel_service:
            logger.info("✅ SSH tunnel service initialized")
        else:
            logger.info("ℹ️ SSH tunnel service is disabled or not available")
        
        # Initialize database on startup (after tunnel is ready)
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
    
    # Shutdown SSH tunnel service
    try:
        await shutdown_tunnel_service()
        logger.info("✅ SSH tunnel service shutdown completed")
    except Exception as e:
        logger.error(f"❌ SSH tunnel service shutdown failed: {e}")
    
    # Shutdown pool manager
    try:
        await shutdown_pool_manager()
        logger.info("✅ Pool manager shutdown completed")
    except Exception as e:
        logger.error(f"❌ Pool manager shutdown failed: {e}")
    
    # Log final metrics
    final_metrics = metrics_collector.get_metrics_summary()
    logger.info(f"📊 Final application metrics: {final_metrics}")


# 🔧 REFACTORED: Use centralized API configuration
app = FastAPI(
    lifespan=lifespan,
    **get_fastapi_config(settings)
)

# Custom JSON response class to ensure UTF-8 encoding
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

# Set default response class
app.default_response_class = UTF8JSONResponse

# 🔧 REFACTORED: Use middleware factory for clean setup
logger.info("🔧 Setting up middleware stack...")
setup_middleware(app, settings)
logger.info("✅ Middleware stack setup completed")

# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(reference.router, prefix="/api/v1/reference", tags=["reference"])
app.include_router(materials.router, prefix="/api/v1/materials", tags=["materials"])
app.include_router(prices.router, prefix="/api/v1/prices", tags=["prices"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(advanced_search.router)
app.include_router(tunnel.router, prefix="/api/v1", tags=["tunnel"])

# Test endpoints (только для development)
if settings.ENVIRONMENT == "development":
    pass  # Test endpoints removed

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs_url": "/docs"
    } 