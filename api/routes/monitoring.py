"""
Monitoring endpoints for system health and performance metrics.

Эндпоинты мониторинга для системы здоровья и метрик производительности.
"""

import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
import time

from core.database.pool_manager import get_pool_manager
from core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", summary="🔍 System Health Check - Комплексная проверка здоровья системы")
async def health_check():
    """
    🏥 **System Health Check** - Комплексная проверка состояния системы
    
    Выполняет всестороннюю проверку здоровья всех компонентов системы, включая 
    все подключения к базам данных и внешним сервисам.
    
    **Возможности:**
    - 🔄 Проверка всех пулов подключений к БД
    - ⏱️ Мониторинг времени отклика каждого сервиса
    - 🚨 Детальная диагностика проблем
    - 📊 Статистика производительности
    - 🎯 Мультистатусные ответы для частичной деградации
    
    **Статусы системы:**
    - `healthy` - Все сервисы работают нормально
    - `degraded` - Некоторые сервисы недоступны, но основная функциональность работает
    - `unhealthy` - Критические сервисы недоступны
    - `error` - Системная ошибка при проверке
    
    **Response Status Codes:**
    - **200 OK**: Все системы работают нормально
    - **207 Multi-Status**: Частичная деградация (некоторые сервисы недоступны)
    - **503 Service Unavailable**: Критические сервисы недоступены
    
    **Example Response (Healthy):**
    ```json
    {
        "status": "healthy",
        "timestamp": "2025-06-16T19:08:36.074112Z",
        "version": "1.0.0",
        "environment": "production",
        "checks": {
            "qdrant_pool": {
                "status": "healthy",
                "response_time_ms": 45
            },
            "postgresql_pool": {
                "status": "healthy", 
                "response_time_ms": 12
            },
            "redis_pool": {
                "status": "healthy",
                "response_time_ms": 8
            }
        }
    }
    ```
    
    **Example Response (Degraded):**
    ```json
    {
        "status": "degraded",
        "timestamp": "2025-06-16T19:08:36.074112Z",
        "version": "1.0.0",
        "environment": "production",
        "checks": {
            "qdrant_pool": {
                "status": "healthy",
                "response_time_ms": 45
            },
            "postgresql_pool": {
                "status": "timeout",
                "error": "Health check timed out"
            },
            "redis_pool": {
                "status": "error",
                "error": "Connection refused"
            }
        }
    }
    ```
    
    **Практические применения:**
    - 🏗️ Мониторинг инфраструктуры в production
    - 🔧 Диагностика проблем подключений
    - 📈 Отслеживание производительности БД
    - 🚨 Настройка алертов и уведомлений
    - ⚖️ Load balancer health checks
    - 🐳 Kubernetes liveness/readiness probes
    - 📊 Интеграция с системами мониторинга (Prometheus, Grafana)
    
    **Рекомендации по использованию:**
    - Вызывайте каждые 30-60 секунд для мониторинга
    - Настройте алерты на статусы `degraded` и `unhealthy`
    - Используйте для автоматического переключения трафика
    - Анализируйте `response_time_ms` для оптимизации производительности
    """
    settings = get_settings()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }
    
    pool_manager = get_pool_manager()
    
    try:
        # Check all registered pools
        for pool_name in pool_manager.pools.keys():
            pool = pool_manager.pools[pool_name]
            try:
                start_time = time.time()
                is_healthy = await asyncio.wait_for(pool.health_check(), timeout=5.0)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                health_status["checks"][pool_name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "response_time_ms": response_time
                }
                
                if not is_healthy:
                    health_status["status"] = "degraded"
                    
            except asyncio.TimeoutError:
                health_status["checks"][pool_name] = {
                    "status": "timeout",
                    "error": "Health check timed out",
                    "response_time_ms": 5000  # Timeout threshold
                }
                health_status["status"] = "degraded"
                
            except Exception as e:
                health_status["checks"][pool_name] = {
                    "status": "error",
                    "error": str(e),
                    "response_time_ms": None
                }
                health_status["status"] = "unhealthy"
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status["status"] = "error"
        health_status["error"] = str(e)
    
    # Return appropriate HTTP status
    status_code = 200
    if health_status["status"] == "degraded":
        status_code = 207  # Multi-status
    elif health_status["status"] in ["unhealthy", "error"]:
        status_code = 503  # Service unavailable
    
    return JSONResponse(content=health_status, status_code=status_code) 