"""
RAG Construction Materials API

Main FastAPI application module for construction materials API with AI-powered semantic search.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Import logging
from core.logging import get_logger
from core.logging.base.loggers import setup_structured_logging
from core.logging.metrics.collectors import get_metrics_collector
from core.logging.context import CorrelationContext, with_correlation_context

# Import routers and middleware
from api.routes import (
    materials_router, prices_router, reference_router,
    tunnel_router, health_unified, search_unified, enhanced_processing
)

# Import configuration
from core.config import get_settings
from core.middleware.factory import setup_middleware

# Initialize logging and configuration
logger = get_logger(__name__)
settings = get_settings()

# Create FastAPI application with English documentation
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    contact=settings.CONTACT,
    license_info=settings.LICENSE_INFO,
    servers=settings.SERVERS,
    openapi_tags=settings.OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Setup CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Apply middleware
setup_middleware(app, settings)

# Register routers with English tags
# Removing duplicated health and search routers as they are included via their unified versions.
# app.include_router(health_router, prefix="", tags=["health"])
# app.include_router(search_router, prefix="", tags=["search"])
app.include_router(materials_router, prefix=f"{settings.API_V1_STR}/materials", tags=["materials"])
app.include_router(prices_router, prefix=f"{settings.API_V1_STR}/prices", tags=["prices"])
app.include_router(reference_router, prefix=f"{settings.API_V1_STR}/reference", tags=["reference"])
app.include_router(tunnel_router, prefix=settings.API_V1_STR, tags=["tunnel"])
app.include_router(health_unified.router, prefix=f"{settings.API_V1_STR}/health", tags=["health"])
app.include_router(search_unified.router, prefix=f"{settings.API_V1_STR}/search", tags=["search"])
app.include_router(enhanced_processing.router, prefix=f"{settings.API_V1_STR}/process-enhanced")

# Always initialize logging system according to configuration
setup_structured_logging()


@app.on_event("startup")
async def startup_event():
    """Actions on application startup."""
    logger.info("🚀 Starting RAG Construction Materials API")
    
    # Initialize metrics
    metrics = get_metrics_collector()
    metrics.increment_counter("app_starts")
    
    # Initialize SSH tunnel
    if settings.ENABLE_SSH_TUNNEL:
        try:
            from services.ssh_tunnel_service import initialize_tunnel_service

            tunnel_service = await initialize_tunnel_service()
            if tunnel_service:
                logger.info("SSH tunnel service started successfully")
            else:
                logger.warning("SSH tunnel service disabled in configuration or not initialized")
        except Exception as e:
            logger.error(f"Error starting SSH tunnel: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions on application shutdown."""
    logger.info("🛑 Shutting down RAG Construction Materials API")
    
    # Stop SSH tunnel
    if settings.ENABLE_SSH_TUNNEL:
        try:
            from services.ssh_tunnel_service import shutdown_tunnel_service

            await shutdown_tunnel_service()
            logger.info("SSH tunnel service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping SSH tunnel: {e}")


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirecting to documentation."""
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
            <head>
                <title>RAG Construction Materials API</title>
                <meta charset="utf-8"/>
                <meta http-equiv="refresh" content="0;url=/docs" />
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                        margin: 0;
                        padding: 40px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        text-align: center;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        flex-direction: column;
                    }
                    .container {
                        max-width: 600px;
                        padding: 40px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 20px;
                        backdrop-filter: blur(10px);
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    }
                    h1 {
                        font-size: 2.5em;
                        margin-bottom: 20px;
                        font-weight: 300;
                    }
                    p {
                        font-size: 1.2em;
                        margin-bottom: 30px;
                        opacity: 0.9;
                    }
                    a {
                        color: #ffd700;
                        text-decoration: none;
                        font-weight: 500;
                        padding: 12px 30px;
                        border: 2px solid #ffd700;
                        border-radius: 25px;
                        transition: all 0.3s ease;
                        display: inline-block;
                    }
                    a:hover {
                        background: #ffd700;
                        color: #333;
                        transform: translateY(-2px);
                        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
                    }
                    .emoji {
                        font-size: 3em;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="emoji">🏗️</div>
                    <h1>RAG Construction Materials API</h1>
                    <p>AI-Powered Semantic Search & Management System</p>
                    <p>Redirecting to <a href="/docs">interactive documentation</a>...</p>
                    <div style="margin-top: 30px; font-size: 0.9em; opacity: 0.7;">
                        <p>Alternative documentation: <a href="/redoc">ReDoc</a></p>
                    </div>
                </div>
            </body>
        </html>
        """
    )