import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database.init_db import initialize_database_on_startup
from core.middleware import RateLimitMiddleware, LoggingMiddleware, SecurityMiddleware
from api.routes import reference, health, materials, prices, search

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup
    logger.info("🚀 Starting Construction Materials API...")
    
    try:
        # Initialize database on startup
        init_results = await initialize_database_on_startup(
            run_migrations=settings.AUTO_MIGRATE,
            seed_data=settings.AUTO_SEED,
            verify_health=True
        )
        logger.info(f"✅ Database initialization: {init_results}")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Continue startup even if DB init fails
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Construction Materials API...")


app = FastAPI(lifespan=lifespan)

# Custom JSON response class to ensure UTF-8 encoding
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

# Set default response class
app.default_response_class = UTF8JSONResponse

# Initialize security middleware to get CORS settings
security_middleware = SecurityMiddleware(app)
cors_settings = security_middleware.get_cors_settings()

# Add middleware in correct order (LIFO - Last In First Out)
# 1. Security middleware (first to process, last to respond)
app.add_middleware(SecurityMiddleware,
    max_request_size=settings.MAX_REQUEST_SIZE_MB * 1024 * 1024,
    enable_security_headers=True,
    enable_input_validation=True,
    enable_xss_protection=True,
    enable_sql_injection_protection=True,
    enable_path_traversal_protection=True,
)

# 2. Rate limiting middleware  
if settings.ENABLE_RATE_LIMITING:
    app.add_middleware(RateLimitMiddleware,
        redis_url=settings.REDIS_URL,
        default_requests_per_minute=settings.RATE_LIMIT_RPM,
        default_requests_per_hour=settings.RATE_LIMIT_RPH,
        default_burst_size=settings.RATE_LIMIT_BURST,
        enable_burst_protection=True,
        rate_limit_headers=True,
    )

# 3. Logging middleware
app.add_middleware(LoggingMiddleware,
    log_level=settings.LOG_LEVEL,
    log_request_body=settings.LOG_REQUEST_BODY,
    log_response_body=settings.LOG_RESPONSE_BODY,
    max_body_size=64 * 1024,  # 64KB
    include_headers=True,
    mask_sensitive_headers=True,
)

# 4. CORS middleware (last, closest to app)
app.add_middleware(CORSMiddleware, **cors_settings)

# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
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