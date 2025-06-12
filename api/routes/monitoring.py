"""
Monitoring endpoints for system health and performance metrics.

Эндпоинты мониторинга для системы здоровья и метрик производительности.
"""

import asyncio
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
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
    
    Комплексная проверка здоровья системы включая все подключения к БД.
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


@router.get("/pools", summary="Connection pool metrics")
async def get_pool_metrics(
    pool_name: str = Query(None, description="Specific pool name to get metrics for")
):
    """
    Get connection pool metrics for monitoring and optimization.
    
    Получить метрики пулов подключений для мониторинга и оптимизации.
    """
    try:
        pool_manager = get_pool_manager()
        metrics = pool_manager.get_pool_metrics(pool_name)
        
        if not metrics:
            raise HTTPException(
                status_code=404, 
                detail=f"Pool '{pool_name}' not found" if pool_name else "No pools registered"
            )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "pools": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get pool metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pools/history", summary="Pool adjustment history")
async def get_pool_history(
    pool_name: str = Query(None, description="Specific pool name"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records")
):
    """
    Get pool adjustment history for analysis.
    
    Получить историю корректировок пулов для анализа.
    """
    try:
        pool_manager = get_pool_manager()
        history = pool_manager.get_adjustment_history(pool_name, limit)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "pool_name": pool_name,
            "total_adjustments": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Failed to get pool history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pools/recommendations", summary="Pool optimization recommendations")
async def get_pool_recommendations():
    """
    Get optimization recommendations based on current pool metrics.
    
    Получить рекомендации по оптимизации на основе текущих метрик пулов.
    """
    try:
        pool_manager = get_pool_manager()
        recommendations = pool_manager.get_recommendations()
        
        # Categorize recommendations by priority
        categorized = {
            "high": [r for r in recommendations if r.get("priority") == "high"],
            "medium": [r for r in recommendations if r.get("priority") == "medium"],
            "low": [r for r in recommendations if r.get("priority") == "low"]
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_recommendations": len(recommendations),
            "recommendations": categorized,
            "summary": {
                "high_priority": len(categorized["high"]),
                "medium_priority": len(categorized["medium"]),
                "low_priority": len(categorized["low"])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pools/{pool_name}/resize", summary="Manually resize pool")
async def resize_pool(
    pool_name: str,
    new_size: int = Query(..., ge=1, le=100, description="New pool size"),
    reason: str = Query("Manual resize via API", description="Reason for resize")
):
    """
    Manually resize a connection pool.
    
    Ручное изменение размера пула подключений.
    """
    try:
        pool_manager = get_pool_manager()
        success = await pool_manager.force_pool_resize(pool_name, new_size, reason)
        
        if success:
            return {
                "status": "success",
                "message": f"Pool '{pool_name}' resized to {new_size}",
                "pool_name": pool_name,
                "new_size": new_size,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to resize pool '{pool_name}'"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resize pool {pool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pools/stats", summary="Pool statistics summary")
async def get_pool_statistics():
    """
    Get comprehensive pool statistics summary.
    
    Получить сводную статистику пулов подключений.
    """
    try:
        pool_manager = get_pool_manager()
        all_metrics = pool_manager.get_pool_metrics()
        
        if not all_metrics:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_pools": 0,
                "summary": {
                    "total_connections": 0,
                    "active_connections": 0,
                    "idle_connections": 0,
                    "average_utilization": 0.0
                }
            }
        
        # Calculate summary statistics
        total_connections = sum(metrics.get("current_size", 0) for metrics in all_metrics.values())
        active_connections = sum(metrics.get("active_connections", 0) for metrics in all_metrics.values())
        idle_connections = sum(metrics.get("idle_connections", 0) for metrics in all_metrics.values())
        
        # Calculate average utilization
        utilizations = [metrics.get("utilization", 0) for metrics in all_metrics.values()]
        avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0.0
        
        # Find pools with high/low utilization
        high_utilization_pools = [
            name for name, metrics in all_metrics.items() 
            if metrics.get("utilization", 0) > 80
        ]
        low_utilization_pools = [
            name for name, metrics in all_metrics.items() 
            if metrics.get("utilization", 0) < 20
        ]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_pools": len(all_metrics),
            "summary": {
                "total_connections": total_connections,
                "active_connections": active_connections,
                "idle_connections": idle_connections,
                "average_utilization": round(avg_utilization, 2)
            },
            "alerts": {
                "high_utilization_pools": high_utilization_pools,
                "low_utilization_pools": low_utilization_pools
            },
            "pools": all_metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get pool statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 