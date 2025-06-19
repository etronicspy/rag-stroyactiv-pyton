import asyncio
import time
from core.monitoring.logger import get_logger
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
from core.monitoring.context import with_correlation_context, CorrelationContext

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
logger = get_logger(__name__)

async def startup_with_correlation():
    """Startup routine with correlation context."""
    with CorrelationContext.with_correlation_id() as startup_correlation_id:
        logger.info(f"🚀 Starting Construction Materials API... (startup_id: {startup_correlation_id})")
        
        # Initialize SSH tunnel service
        try:
            await initialize_tunnel_service()
            logger.info("✅ SSH tunnel service initialized")
        except Exception as e:
            logger.info("ℹ️ SSH tunnel service is disabled or not available")
        
        # Initialize databases
        try:
            init_results = await initialize_database_on_startup()
            logger.info(f"✅ Database initialization: {init_results}")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
        
        # Initialize pool manager
        try:
            pool_config = PoolConfig()
            await initialize_pool_manager(pool_config)
            logger.info("✅ Dynamic pool manager initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

async def shutdown_with_correlation():
    """Shutdown routine with correlation context."""  
    with CorrelationContext.with_correlation_id() as shutdown_correlation_id:
        logger.info(f"🛑 Shutting down Construction Materials API... (shutdown_id: {shutdown_correlation_id})")
        
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
        
        # Get final metrics
        metrics_collector = get_metrics_collector()
        final_metrics = metrics_collector.get_summary()
        logger.info(f"📊 Final application metrics: {final_metrics}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with correlation context."""
    await startup_with_correlation()
    yield
    await shutdown_with_correlation()

def setup_middleware_with_correlation(app: FastAPI):
    """Setup middleware with correlation context."""
    with CorrelationContext.with_correlation_id() as middleware_correlation_id:
        logger.info(f"🔧 Setting up middleware stack... (middleware_id: {middleware_correlation_id})")
        setup_middleware(app, settings)
        logger.info("✅ Middleware stack setup completed")

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
setup_middleware_with_correlation(app)

# Middleware setup completed - no additional middleware needed

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