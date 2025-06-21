"""
RAG Construction Materials API

Основной модуль FastAPI приложения для API строительных материалов с RAG.
"""

import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse

# Импорт логирования
from core.logging import get_logger
from core.logging.base.loggers import setup_structured_logging
from core.logging.metrics.collectors import get_metrics_collector
from core.logging.context import CorrelationContext, with_correlation_context

# Импорт роутеров и middleware
from api.routes import (
    health_router, search_router, materials_router, prices_router, reference_router,
    advanced_search_router, tunnel_router
)

# Импорт конфигурации
from core.config import get_settings
from core.middleware.factory import setup_middleware

# Инициализация логирования и конфигурации
logger = get_logger(__name__)
settings = get_settings()

# Создание приложения FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API для работы со строительными материалами с использованием RAG",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Настройка CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Применение middleware
setup_middleware(app, settings)

# Регистрация роутеров
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(search_router, prefix=settings.API_V1_STR, tags=["search"])
app.include_router(materials_router, prefix=f"{settings.API_V1_STR}/materials", tags=["materials"])
app.include_router(prices_router, prefix=settings.API_V1_STR, tags=["prices"])
app.include_router(reference_router, prefix=settings.API_V1_STR, tags=["reference"])
app.include_router(advanced_search_router, prefix=settings.API_V1_STR, tags=["advanced-search"])
app.include_router(tunnel_router, prefix=settings.API_V1_STR, tags=["tunnel"])

# Настройка структурированного логирования
if os.getenv("ENABLE_STRUCTURED_LOGGING", "").lower() in ("true", "1", "yes", "y"):
    setup_structured_logging()


@app.on_event("startup")
async def startup_event():
    """Действия при запуске приложения."""
    logger.info("🚀 Запуск API приложения")
    
    # Инициализация метрик
    metrics = get_metrics_collector()
    metrics.increment_counter("app_starts")
    
    # Инициализация SSH туннеля
    if settings.ENABLE_SSH_TUNNEL:
        try:
            from services.ssh_tunnel_service import initialize_tunnel_service

            tunnel_service = await initialize_tunnel_service()
            if tunnel_service:
                logger.info("SSH туннель успешно запущен")
            else:
                logger.warning("SSH туннель сервис отключён в конфигурации или не инициализирован")
        except Exception as e:
            logger.error(f"Ошибка при запуске SSH туннеля: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Действия при завершении работы приложения."""
    logger.info("🛑 Завершение работы API приложения")
    
    # Остановка SSH туннеля
    if settings.ENABLE_SSH_TUNNEL:
        try:
            from services.ssh_tunnel_service import shutdown_tunnel_service

            await shutdown_tunnel_service()
            logger.info("SSH туннель успешно остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке SSH туннеля: {e}")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request) -> HTMLResponse:
    """Кастомная страница Swagger UI."""
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        oauth2_redirect_url=f"{settings.API_V1_STR}/docs/oauth2-redirect",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


@app.get(f"{settings.API_V1_STR}/openapi.json", include_in_schema=False)
@with_correlation_context
async def get_openapi_endpoint():
    """Эндпоинт для OpenAPI схемы."""
    with CorrelationContext.with_correlation_id():
        return JSONResponse(
            get_openapi(
                title=settings.PROJECT_NAME,
                version=settings.VERSION,
                description="API для работы со строительными материалами с использованием RAG",
                routes=app.routes,
            )
        )


@app.get("/", include_in_schema=False)
async def root():
    """Корневой эндпоинт, перенаправляющий на документацию."""
    return HTMLResponse(
        """
        <html>
            <head>
                <title>RAG Construction Materials API</title>
                <meta http-equiv="refresh" content="0;url=/docs" />
            </head>
            <body>
                <p>Перенаправление на <a href="/docs">документацию</a>...</p>
            </body>
        </html>
        """
    ) 