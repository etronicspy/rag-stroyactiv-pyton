"""
RAG Construction Materials API

Main FastAPI application module for construction materials API with AI-powered semantic search.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse

# Import logging
from core.logging import get_logger
from core.logging.base.loggers import setup_structured_logging
from core.logging.metrics.collectors import get_metrics_collector
from core.logging.context import CorrelationContext, with_correlation_context

# Import routers and middleware
from api.routes import (
    health_router, search_router, materials_router, prices_router, reference_router,
    advanced_search_router, tunnel_router
)

# Import configuration
from core.config import get_settings
from core.middleware.factory import setup_middleware

# Import English API documentation
from docs.api_description import get_fastapi_config

# Initialize logging and configuration
logger = get_logger(__name__)
settings = get_settings()

# Get English API configuration
api_config = get_fastapi_config(settings)

# Create FastAPI application with English documentation
app = FastAPI(
    title=api_config["title"],
    version=api_config["version"],
    description=api_config["description"],
    contact=api_config["contact"],
    license_info=api_config["license_info"],
    servers=api_config["servers"],
    openapi_tags=api_config["openapi_tags"],
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
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
app.include_router(health_router, prefix=f"{settings.API_V1_STR}/health", tags=["health"])
app.include_router(search_router, prefix=settings.API_V1_STR, tags=["search"])
app.include_router(materials_router, prefix=f"{settings.API_V1_STR}/materials", tags=["materials"])
app.include_router(prices_router, prefix=f"{settings.API_V1_STR}/prices", tags=["prices"])
app.include_router(reference_router, prefix=f"{settings.API_V1_STR}/reference", tags=["reference"])
app.include_router(advanced_search_router, prefix="", tags=["advanced-search"])
app.include_router(tunnel_router, prefix=settings.API_V1_STR, tags=["tunnel"])

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


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request) -> HTMLResponse:
    """Custom Swagger UI page with English documentation."""
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title="RAG Construction Materials API - Interactive Documentation",
        oauth2_redirect_url=f"{settings.API_V1_STR}/docs/oauth2-redirect",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        swagger_ui_parameters={
            "deepLinking": True,
            "displayRequestDuration": True,
            "docExpansion": "none",
            "operationsSorter": "method",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "tryItOutEnabled": True
        }
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html() -> HTMLResponse:
    """Alternative ReDoc documentation."""
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>RAG Construction Materials API - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {{ margin: 0; padding: 0; }}
        </style>
    </head>
    <body>
        <redoc spec-url='{settings.API_V1_STR}/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """)


@app.get(f"{settings.API_V1_STR}/openapi.json", include_in_schema=False)
@with_correlation_context
async def get_openapi_endpoint():
    """OpenAPI schema endpoint with English documentation."""
    with CorrelationContext.with_correlation_id():
        return JSONResponse(
            get_openapi(
                title=api_config["title"],
                version=api_config["version"],
                description=api_config["description"],
                contact=api_config["contact"],
                license_info=api_config["license_info"],
                servers=api_config["servers"],
                tags=api_config["openapi_tags"],
                routes=app.routes,
            )
        )


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