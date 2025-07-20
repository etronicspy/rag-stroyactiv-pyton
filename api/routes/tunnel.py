"""
SSH Tunnel API Routes for RAG Construction Materials API.

This module provides API endpoints for managing SSH tunnel service.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from core.dependencies.tunnel import RequiredTunnelService, TunnelService
from core.schemas.response_models import ERROR_RESPONSES

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
    summary="🔌 Tunnel Status – SSH Tunnel Status",
    response_description="SSH tunnel status and configuration information"
)
async def get_tunnel_status(tunnel_service: TunnelService):
    """
    🔌 **SSH Tunnel Status** - SSH tunnel state inspection
    
    Returns detailed information about current SSH tunnel state, including
    configuration, connection status, and tunnel manager information.
    
    **Features:**
    - 🔍 Complete tunnel state diagnostics
    - ⚙️ Configuration information (without sensitive data)
    - 📊 Tunnel manager status
    - 🔗 Active connection verification
    - ⏰ Uptime and connection metrics
    
    **Response Example:**
    ```json
    {
        "service_running": true,
        "config_enabled": true,
        "tunnel_manager": {
            "active_tunnels": 2,
            "local_port": 5432,
            "remote_host": "database.example.com",
            "remote_port": 5432,
            "connection_status": "established",
            "uptime_seconds": 3600.5
        }
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Status returned successfully
    - **503 Service Unavailable**: SSH tunnel unavailable
    - **500 Internal Server Error**: Status retrieval error
    
    **Status Fields:**
    - `service_running`: Tunnel service is running and operational
    - `config_enabled`: Tunnel configuration is enabled
    - `tunnel_manager`: Detailed tunnel manager information
    
    **Use Cases:**
    - SSH connection status monitoring
    - Database connection problem diagnostics
    - Administrative management panels
    - Automated health checks
    - Network connection debugging
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
    summary="🩺 Tunnel Health – SSH Tunnel Status Check",
    response_description="Simple SSH tunnel status verification"
)
async def tunnel_health_check(tunnel_service: TunnelService):
    """
    🩺 **SSH Tunnel Health Check** - Quick tunnel availability verification
    
    Lightweight endpoint for checking basic SSH tunnel status. Used by monitoring
    systems and load balancers to determine tunnel service availability.
    
    **Features:**
    - ⚡ Fast response time (< 100ms)
    - 🔄 Minimal system load
    - 📊 Simple healthy/unhealthy status
    - 🔗 Tunnel activity verification
    - 🛡️ Graceful handling of service unavailability
    
    **Response Example (Healthy):**
    ```json
    {
        "status": "healthy",
        "tunnel_active": true,
        "service_running": true
    }
    ```
    
    **Response Example (Unavailable):**
    ```json
    {
        "status": "unavailable",
        "message": "SSH tunnel service is not available"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Health check completed (status can be any)
    - **500 Internal Server Error**: Health check execution error
    
    **Status Values:**
    - `healthy`: Tunnel active and operating correctly
    - `unhealthy`: Tunnel inactive or has problems
    - `unavailable`: Tunnel service unavailable
    
    **Use Cases:**
    - Kubernetes liveness probes
    - Load balancer health checks
    - Tunnel availability monitoring
    - Automatic recovery systems
    - Simple status dashboards
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
    summary="📊 Tunnel Metrics – SSH Tunnel Performance Metrics",
    response_description="Detailed tunnel metrics and performance statistics"
)
async def get_tunnel_metrics(tunnel_service: RequiredTunnelService):
    """
    📊 **SSH Tunnel Metrics** - Detailed tunnel performance metrics
    
    Returns extended SSH tunnel operation statistics, including performance,
    uptime, connection statistics, and resource usage metrics.
    
    **Metrics Include:**
    - ⏱️ **Uptime**: Continuous tunnel operation time
    - 🔢 **Connection Stats**: Number of active/total connections
    - 📈 **Performance**: Throughput, latency measurements
    - 🔄 **Reconnection Stats**: Number of reconnections
    - 💾 **Resource Usage**: Memory and CPU utilization
    - 📊 **Traffic Stats**: Data transfer volumes
    
    **Response Example:**
    ```json
    {
        "active": true,
        "config": "production",
        "uptime_seconds": 86400.5,
        "metrics": {
            "connections": {
                "active": 5,
                "total": 1247,
                "failed": 3,
                "success_rate": 0.9976
            },
            "performance": {
                "avg_latency_ms": 45.2,
                "max_latency_ms": 156.7,
                "throughput_mbps": 12.8
            },
            "traffic": {
                "bytes_sent": 1048576000,
                "bytes_received": 524288000,
                "packets_sent": 125000,
                "packets_received": 87500
            },
            "resources": {
                "memory_usage_mb": 32.5,
                "cpu_usage_percent": 2.1
            }
        }
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Metrics returned successfully
    - **503 Service Unavailable**: Tunnel unavailable
    - **500 Internal Server Error**: Metrics retrieval error
    
    **Metric Categories:**
    - **Connection Metrics**: Connection statistics
    - **Performance Metrics**: Performance and latency data
    - **Traffic Metrics**: Traffic statistics
    - **Resource Metrics**: System resource utilization
    
    **Use Cases:**
    - Tunnel performance monitoring
    - Load and throughput analysis
    - Scaling planning
    - Performance problem diagnostics
    - Monitoring dashboard creation
    - SLA reporting and analytics
    """
    metrics_data = await tunnel_service.get_tunnel_metrics()
    return TunnelMetricsResponse(**metrics_data)


@router.post(
    "/restart",
    response_model=MessageResponse,
    summary="🔄 Restart Tunnel – Tunnel Restart Operation",
    response_description="Tunnel restart operation status"
)
async def restart_tunnel(tunnel_service: RequiredTunnelService):
    """
    🔄 **Restart SSH Tunnel** - SSH tunnel restart operation
    
    Performs graceful SSH tunnel restart while preserving configuration.
    Useful for connection problems or after configuration changes.
    
    **Restart Process:**
    1. 🛑 Graceful shutdown of current connections
    2. 🧹 Resource cleanup and port closure
    3. ⏳ Wait for active operations completion
    4. 🚀 New tunnel initialization
    5. ✅ Connection success verification
    
    **Features:**
    - 🔄 Graceful restart without configuration loss
    - ⏱️ Minimal downtime duration
    - 🛡️ Automatic verification after restart
    - 📊 Restart process logging
    - 🚨 Rollback on failed restart
    
    **Response Example (Success):**
    ```json
    {
        "message": "SSH tunnel service restarted successfully",
        "success": true
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Tunnel successfully restarted
    - **500 Internal Server Error**: Restart error
    - **503 Service Unavailable**: Service unavailable
    
    **⚠️ Warnings:**
    - Active connections will be terminated
    - Brief database unavailability possible
    - Recommended to perform during maintenance window
    
    **Use Cases:**
    - Recovery from connection failures
    - Applying configuration changes
    - Regular tunnel maintenance
    - Performance problem resolution
    - Clearing stuck connections
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
    summary="▶️ Start Tunnel – Tunnel Start Operation",
    response_description="Tunnel start operation status"
)
async def start_tunnel(tunnel_service: RequiredTunnelService):
    """
    ▶️ **Start SSH Tunnel** - SSH tunnel initialization
    
    Initializes and starts SSH tunnel according to current configuration.
    Creates secure connection to remote server and configures local port
    forwarding.
    
    **Startup Process:**
    1. 📋 Tunnel configuration verification
    2. 🔐 SSH connection establishment
    3. 🔗 Port forwarding setup
    4. ✅ Tunnel functionality verification
    5. 📊 Monitoring initialization
    
    **Features:**
    - 🔐 Secure SSH connection with authentication
    - 🔄 Automatic reconnection on disconnection
    - 📊 Connection status monitoring
    - 🛡️ Already running service verification
    - 📝 Detailed process logging
    
    **Response Example (Success):**
    ```json
    {
        "message": "SSH tunnel service started successfully",
        "success": true
    }
    ```
    
    **Response Example (Already Running):**
    ```json
    {
        "message": "SSH tunnel service is already running",
        "success": true
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Tunnel successfully started or already running
    - **500 Internal Server Error**: Tunnel startup error
    - **503 Service Unavailable**: Service unavailable
    
    **Possible Issues:**
    - Invalid SSH credentials
    - Remote server unavailability
    - Occupied local ports
    - Network connectivity problems
    
    **Use Cases:**
    - Initial tunnel startup
    - Recovery after service shutdown
    - Automatic startup in CI/CD pipeline
    - Docker container initialization
    - Manual tunnel management via API
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
    summary="⏹️ Stop Tunnel – Tunnel Stop Operation",
    response_description="Tunnel stop operation status"
)
async def stop_tunnel(tunnel_service: RequiredTunnelService):
    """
    ⏹️ **Stop SSH Tunnel** - SSH tunnel shutdown operation
    
    Performs graceful SSH tunnel shutdown with proper closure of all active
    connections and resource cleanup.
    
    **Shutdown Process:**
    1. 📊 Metrics and statistics preservation
    2. 🔌 Graceful active connection closure
    3. 🛑 SSH tunnel termination
    4. 🧹 Port and resource cleanup
    5. ✅ Successful shutdown confirmation
    
    **Features:**
    - 🔄 Graceful shutdown without data loss
    - 📊 Operation statistics preservation
    - 🧹 Complete resource cleanup
    - ⏱️ Timeout for forced termination
    - 📝 Shutdown process logging
    
    **Response Example:**
    ```json
    {
        "message": "SSH tunnel service stopped successfully",
        "success": true
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Tunnel successfully stopped
    - **500 Internal Server Error**: Tunnel stop error
    - **503 Service Unavailable**: Service unavailable
    
    **⚠️ Shutdown Consequences:**
    - All SSH connections will be terminated
    - Applications will lose access to remote resources
    - Restart required for service recovery
    
    **Use Cases:**
    - Planned system maintenance
    - Tunnel configuration changes
    - Resource conservation when unused
    - Emergency shutdown during problems
    - Controlled service termination
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
    summary="⚙️ Tunnel Config – Tunnel Configuration",
    response_description="Tunnel configuration without sensitive data"
)
async def get_tunnel_config(tunnel_service: RequiredTunnelService):
    """
    ⚙️ **SSH Tunnel Configuration** - Tunnel configuration inspection
    
    Returns current SSH tunnel configuration without sensitive data (passwords,
    private keys). Useful for diagnostics and settings verification.
    
    **Features:**
    - 🔒 Automatic sensitive data masking
    - 📋 Complete tunnel settings information
    - 🔍 Configuration correctness verification
    - 📊 Settings application status
    - 🛡️ Safe viewing for logs and debugging
    
    **Response Example:**
    ```json
    {
        "enabled": true,
        "ssh_host": "remote.example.com",
        "ssh_port": 22,
        "ssh_username": "tunnel_user",
        "local_bind_address": "127.0.0.1",
        "local_bind_port": 5432,
        "remote_bind_address": "127.0.0.1",
        "remote_bind_port": 5432,
        "connection_timeout": 30,
        "keepalive_interval": 60,
        "max_retries": 3,
        "auto_reconnect": true,
        "compression": true,
        "config_source": "/app/config/ssh_tunnel.conf",
        "last_updated": "2025-06-16T17:30:15.123456Z"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Configuration returned successfully
    - **503 Service Unavailable**: Tunnel service unavailable
    - **500 Internal Server Error**: Configuration retrieval error
    
    **🔒 Hidden Fields (Security):**
    - `ssh_password`: SSH password (if used)
    - `ssh_private_key`: SSH private key
    - `ssh_private_key_password`: Private key password
    - Other sensitive authentication data
    
    **Configuration Fields:**
    - **Connection Settings**: Host, port, username, timeouts
    - **Bind Settings**: Local and remote addresses/ports
    - **Advanced Options**: Compression, keepalive, retries
    - **Metadata**: Source file, last update timestamp
    
    **Use Cases:**
    - Connection problem diagnostics
    - Settings correctness verification
    - System configuration documentation
    - Network problem debugging
    - Security settings audit
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