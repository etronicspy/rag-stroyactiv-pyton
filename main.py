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
from api.routes import reference, health, materials, prices, search, advanced_search, tunnel
from services.ssh_tunnel_service import initialize_tunnel_service, shutdown_tunnel_service

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


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    🏗️ **RAG Construction Materials API** - Система управления и семантического поиска строительных материалов

    ## 🚀 Возможности API

    ### 🔍 **Интеллектуальный поиск**
    - **Семантический поиск** с AI-эмбеддингами (OpenAI)
    - **Гибридный поиск** (векторный + SQL + нечеткий)
    - **Автодополнение** и предложения
    - **Фильтрация** по категориям и единицам измерения

    ### 📦 **Управление материалами**
    - CRUD операции с материалами
    - **Пакетная загрузка** и импорт из JSON
    - **Автоматическая векторизация** описаний
    - **Категоризация** и стандартизация единиц

    ### 💰 **Обработка прайс-листов**
    - **Загрузка CSV/Excel** прайс-листов
    - **Автоматическая обработка** и индексация
    - **Трекинг** статуса обработки продуктов
    - **Управление** несколькими поставщиками

    ### 🏥 **Мониторинг и диагностика**
    - **Полная диагностика** всех систем
    - **Статус баз данных** (Qdrant, PostgreSQL, Redis)
    - **Мониторинг пулов** подключений
    - **SSH туннель** для PostgreSQL

    ### 🔧 **Техническая архитектура**
    - **Multi-database**: Qdrant Cloud + PostgreSQL + Redis
    - **Fallback стратегия** при недоступности БД  
    - **Rate limiting** и безопасность
    - **Автоматическое масштабирование** пулов подключений

    ## 📚 **Документация**
    - **Interactive Docs**: `/docs` (Swagger UI)
    - **ReDoc**: `/redoc` 
    - **OpenAPI Schema**: `/openapi.json`

    ## 🎯 **Версионирование**
    - Текущая версия: **v1**
    - Базовый путь: `/api/v1/`
    - Стабильный API без устаревших эндпоинтов

    ---
    **Разработано с ❤️ для эффективного управления строительными материалами**
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "RAG Construction Materials API",
        "url": "https://github.com/your-repo/rag-construction-materials",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.construction-materials.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "health",
            "description": "🏥 **Health & Monitoring** - Проверка состояния системы, диагностика баз данных и мониторинг"
        },
        {
            "name": "materials",
            "description": "📦 **Materials Management** - CRUD операции с материалами, пакетная загрузка, импорт и векторизация"
        },
        {
            "name": "search",
            "description": "🔍 **Search & Discovery** - Семантический поиск, автодополнение, фильтрация по категориям"
        },
        {
            "name": "prices",
            "description": "💰 **Price Lists** - Загрузка и обработка прайс-листов, управление поставщиками"
        },
        {
            "name": "reference",
            "description": "📚 **Reference Data** - Управление справочниками категорий и единиц измерения"
        },
        {
            "name": "tunnel",
            "description": "🔌 **SSH Tunnel** - Управление SSH туннелем для безопасного подключения к PostgreSQL"
        }
    ]
)

# Custom JSON response class to ensure UTF-8 encoding
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

# Set default response class
app.default_response_class = UTF8JSONResponse

# Initialize security middleware to get CORS settings
security_middleware = SecurityMiddleware(app)
cors_settings = security_middleware.get_cors_settings()

# ✅ MIDDLEWARE STACK WITH CORRECT ORDER - Fixed hanging issue
# Order: LIFO (Last In First Out) - REVERSED execution order!
# Last added = First executed

# 5. CORS middleware (добавляем первым - выполнится последним, ближе к app)

# 4. Logging middleware (🔥 FULL FUNCTIONALITY RESTORED - использует кешированный body)
app.add_middleware(LoggingMiddleware,
    log_level=settings.LOG_LEVEL,
    log_request_body=True,      # 🔥 RESTORED: Полное логирование body через кеш
    log_response_body=True,     # 🔥 RESTORED: Full response body logging
    max_body_size=64*1024,      # 🔥 RESTORED: 64KB limit (was 1KB)
    include_headers=True,       # 🔥 RESTORED: Headers logging
    mask_sensitive_headers=True, # Keep security
)

# 3. Rate limiting middleware (🔥 FULL FUNCTIONALITY RESTORED)
if settings.ENABLE_RATE_LIMITING:
    try:
        app.add_middleware(RateLimitMiddleware,
            default_requests_per_minute=settings.RATE_LIMIT_RPM,  # Fixed: use correct parameter name
            default_requests_per_hour=1000,                       # Default hourly limit
            enable_burst_protection=True,                         # Enable burst protection
            rate_limit_headers=True,                              # Include rate limit headers
        )
        logger.info("✅ RateLimitMiddleware initialized with full functionality")
    except Exception as e:
        logger.warning(f"Failed to initialize RateLimitMiddleware: {e}")

# 2. Security middleware (🔥 FULL FUNCTIONALITY RESTORED - использует кешированный body)
app.add_middleware(SecurityMiddleware,
    max_request_size=settings.MAX_REQUEST_SIZE_MB * 1024 * 1024,
    enable_security_headers=True,
    enable_input_validation=True,   # 🔥 RESTORED: Полная валидация body через кеш
    enable_xss_protection=True,     # 🔥 RESTORED: XSS защита для body
    enable_sql_injection_protection=True,  # 🔥 RESTORED: SQL injection защита для body
    enable_path_traversal_protection=True,
)

# 1. Compression middleware (🔥 FULL FUNCTIONALITY RESTORED)
app.add_middleware(CompressionMiddleware,
    minimum_size=2048,                    # 2KB minimum
    maximum_size=5 * 1024 * 1024,         # 5MB maximum
    compression_level=6,                  # 🔥 RESTORED: Optimal compression (was 3)
    enable_brotli=True,                   # 🔥 RESTORED: Brotli support (~20% better than gzip)
    enable_streaming=True,                # 🔥 RESTORED: Streaming for large files
    exclude_paths=["/health", "/ping", "/metrics"],  # Reduced exclusions
    enable_performance_logging=True,      # 🔥 RESTORED: Performance metrics
)

# 0. Body Cache middleware (🔥 FIXED: добавляем ПОСЛЕДНИМ - выполнится ПЕРВЫМ!)
# Это middleware ДОЛЖЕН выполниться первым для чтения и кеширования body
from core.middleware.body_cache import BodyCacheMiddleware
app.add_middleware(BodyCacheMiddleware,
    max_body_size=settings.MAX_REQUEST_SIZE_MB * 1024 * 1024,  # Используем тот же лимит
    methods_to_cache=["POST", "PUT", "PATCH"],  # Методы с body
)

# CORS middleware (добавляем последним - выполнится после всех остальных)
app.add_middleware(CORSMiddleware, **cors_settings)

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