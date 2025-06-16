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

from core.database.pool_manager import get_pool_manager
from core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", summary="System health check")
async def health_check():
    """
    Comprehensive system health check including all database connections.
    
    Parameters:
    - Returns: System health status with database connection checks
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
                is_healthy = await asyncio.wait_for(pool.health_check(), timeout=5.0)
                health_status["checks"][pool_name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "response_time_ms": 0  # Would need to implement timing
                }
                
                if not is_healthy:
                    health_status["status"] = "degraded"
                    
            except asyncio.TimeoutError:
                health_status["checks"][pool_name] = {
                    "status": "timeout",
                    "error": "Health check timed out"
                }
                health_status["status"] = "degraded"
                
            except Exception as e:
                health_status["checks"][pool_name] = {
                    "status": "error",
                    "error": str(e)
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