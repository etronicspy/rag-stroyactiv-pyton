"""
SSH Tunnel API Routes for RAG Construction Materials API.

This module provides API endpoints for managing SSH tunnel service.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.schemas.response_models import ERROR_RESPONSES

from core.dependencies.tunnel import (
    TunnelService,
    RequiredTunnelService
)

router = APIRouter(prefix="/tunnel", tags=["tunnel"], responses=ERROR_RESPONSES)


class TunnelStatusResponse(BaseModel):
    """Response model for tunnel status."""
    service_running: bool
    config_enabled: bool
    tunnel_manager: Optional[Dict[str, Any]] = None


class TunnelMetricsResponse(BaseModel):
    """Response model for tunnel metrics."""
    active: bool
    config: str
    uptime_seconds: Optional[float]
    metrics: Dict[str, Any]


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool


@router.get(
    "/status",
    response_model=TunnelStatusResponse,
    summary="🔌 Tunnel Status – Статус SSH туннеля",
    response_description="Информация о состоянии SSH туннеля"
)
async def get_tunnel_status(tunnel_service: TunnelService):
    """Get SSH tunnel service status.
    
    Returns:
        Current status of SSH tunnel service including configuration and tunnel manager status
    """
    if tunnel_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SSH tunnel service is not available"
        )
    
    status_data = tunnel_service.get_status()
    return TunnelStatusResponse(**status_data)


@router.get(
    "/health",
    summary="🩺 Tunnel Health – Проверка здоровья SSH туннеля",
    response_description="Простая проверка состояния туннеля"
)
async def tunnel_health_check(tunnel_service: TunnelService):
    """Health check endpoint for SSH tunnel.
    
    Returns:
        Simple health status of the tunnel service
    """
    if tunnel_service is None:
        return {
            "status": "unavailable",
            "message": "SSH tunnel service is not available"
        }
    
    is_active = tunnel_service.is_tunnel_active()
    
    return {
        "status": "healthy" if is_active else "unhealthy",
        "tunnel_active": is_active,
        "service_running": tunnel_service.is_running
    }


@router.get(
    "/metrics",
    response_model=TunnelMetricsResponse,
    summary="📊 Tunnel Metrics – Метрики SSH туннеля",
    response_description="Детальные метрики и статистика туннеля"
)
async def get_tunnel_metrics(tunnel_service: RequiredTunnelService):
    """Get detailed SSH tunnel metrics and statistics.
    
    Returns:
        Detailed metrics including uptime, performance stats, and availability information
    """
    metrics_data = await tunnel_service.get_tunnel_metrics()
    return TunnelMetricsResponse(**metrics_data)


@router.post(
    "/restart",
    response_model=MessageResponse,
    summary="🔄 Restart Tunnel – Перезагрузка туннеля",
    response_description="Статус перезапуска туннеля"
)
async def restart_tunnel(tunnel_service: RequiredTunnelService):
    """Restart SSH tunnel service.
    
    Returns:
        Success message and status
    """
    try:
        success = await tunnel_service.restart_service()
        
        if success:
            return MessageResponse(
                message="SSH tunnel service restarted successfully",
                success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restart SSH tunnel service"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restarting tunnel service: {str(e)}"
        )


@router.post(
    "/start",
    response_model=MessageResponse,
    summary="▶️ Start Tunnel – Запуск туннеля",
    response_description="Статус запуска туннеля"
)
async def start_tunnel(tunnel_service: RequiredTunnelService):
    """Start SSH tunnel service.
    
    Returns:
        Success message and status
    """
    try:
        if tunnel_service.is_running:
            return MessageResponse(
                message="SSH tunnel service is already running",
                success=True
            )
        
        success = await tunnel_service.start_service()
        
        if success:
            return MessageResponse(
                message="SSH tunnel service started successfully",
                success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start SSH tunnel service"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting tunnel service: {str(e)}"
        )


@router.post(
    "/stop",
    response_model=MessageResponse,
    summary="⏹️ Stop Tunnel – Остановка туннеля",
    response_description="Статус остановки туннеля"
)
async def stop_tunnel(tunnel_service: RequiredTunnelService):
    """Stop SSH tunnel service.
    
    Returns:
        Success message and status
    """
    try:
        await tunnel_service.stop_service()
        return MessageResponse(
            message="SSH tunnel service stopped successfully",
            success=True
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping tunnel service: {str(e)}"
        )


@router.get(
    "/config",
    summary="⚙️ Tunnel Config – Конфигурация туннеля",
    response_description="Конфигурация туннеля без чувствительных данных"
)
async def get_tunnel_config(tunnel_service: RequiredTunnelService):
    """Get SSH tunnel configuration (without sensitive data).
    
    Returns:
        Tunnel configuration excluding sensitive information like SSH keys
    """
    config = tunnel_service.config
    
    # Return config without sensitive data
    safe_config = {
        "enabled": config.enabled,
        "local_port": config.local_port,
        "remote_host": config.remote_host,
        "remote_user": config.remote_user,
        "remote_port": config.remote_port,
        "timeout": config.timeout,
        "retry_attempts": config.retry_attempts,
        "retry_delay": config.retry_delay,
        "heartbeat_interval": config.heartbeat_interval,
        "auto_restart": config.auto_restart,
        "connection_string": config.connection_string,
        # Note: key_path is excluded for security
    }
    
    return {
        "config": safe_config,
        "status": "Configuration retrieved successfully"
    } 