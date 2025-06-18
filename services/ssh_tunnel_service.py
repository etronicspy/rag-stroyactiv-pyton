"""
SSH Tunnel Service for RAG Construction Materials API.

This module provides the main SSH tunnel service that manages tunnel lifecycle,
monitoring, and automatic reconnection.
"""

import asyncio
from core.monitoring.logger import get_logger
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from core.config import get_settings
from .tunnel.ssh_tunnel import SSHTunnel
from .tunnel.tunnel_config import TunnelConfig
from .tunnel.tunnel_manager import TunnelManager
from .tunnel.exceptions import SSHTunnelError

logger = get_logger(__name__)


class SSHTunnelService:
    """Main SSH Tunnel Service.
    
    This service manages the lifecycle of SSH tunnels, including:
    - Automatic startup and shutdown
    - Health monitoring and automatic reconnection
    - Status reporting and metrics
    - Integration with FastAPI lifecycle
    """
    
    def __init__(self, config: Optional[TunnelConfig] = None):
        """Initialize SSH tunnel service.
        
        Args:
            config: Optional TunnelConfig. If None, will be loaded from settings.
        """
        self.settings = get_settings()
        self.config = config or TunnelConfig.from_settings(self.settings)
        self.tunnel_manager: Optional[TunnelManager] = None
        self.is_running: bool = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        logger.info(f"SSH Tunnel Service initialized: enabled={self.config.enabled}")
    
    async def start_service(self) -> bool:
        """Start the SSH tunnel service.
        
        Returns:
            True if service started successfully, False otherwise
        """
        if not self.config.enabled:
            logger.info("SSH tunnel service is disabled")
            return False
        
        if self.is_running:
            logger.warning("SSH tunnel service is already running")
            return True
        
        try:
            logger.info("Starting SSH tunnel service")
            
            # Create tunnel manager
            self.tunnel_manager = TunnelManager(self.config)
            
            # Start tunnel
            success = await self.tunnel_manager.start_tunnel()
            if not success:
                logger.error("Failed to start SSH tunnel")
                return False
            
            # Start monitoring
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.is_running = True
            logger.info("SSH tunnel service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start SSH tunnel service: {e}")
            await self.stop_service()
            return False
    
    async def stop_service(self) -> None:
        """Stop the SSH tunnel service."""
        logger.info("Stopping SSH tunnel service")
        
        self.is_running = False
        
        # Cancel monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        
        # Stop tunnel manager
        if self.tunnel_manager:
            await self.tunnel_manager.stop_tunnel()
            self.tunnel_manager = None
        
        logger.info("SSH tunnel service stopped")
    
    async def restart_service(self) -> bool:
        """Restart the SSH tunnel service.
        
        Returns:
            True if service restarted successfully, False otherwise
        """
        logger.info("Restarting SSH tunnel service")
        await self.stop_service()
        return await self.start_service()
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for tunnel health checks."""
        logger.info("SSH tunnel monitoring loop started")
        
        while self.is_running:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                
                if not self.is_running:
                    break
                
                # Perform health check
                if self.tunnel_manager:
                    is_healthy = await self.tunnel_manager.health_check()
                    
                    if not is_healthy and self.config.auto_restart:
                        logger.warning("SSH tunnel unhealthy, attempting restart")
                        success = await self.tunnel_manager.restart_tunnel()
                        if success:
                            logger.info("SSH tunnel restarted successfully")
                        else:
                            logger.error("Failed to restart SSH tunnel")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
        
        logger.info("SSH tunnel monitoring loop stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status.
        
        Returns:
            Dictionary with service status information
        """
        status = {
            "service_running": self.is_running,
            "config_enabled": self.config.enabled,
            "tunnel_manager": None
        }
        
        if self.tunnel_manager:
            status["tunnel_manager"] = self.tunnel_manager.get_status()
        
        return status
    
    def is_tunnel_active(self) -> bool:
        """Check if tunnel is currently active.
        
        Returns:
            True if tunnel is active, False otherwise
        """
        if not self.is_running or not self.tunnel_manager:
            return False
        
        return self.tunnel_manager.is_tunnel_active()
    
    async def get_tunnel_metrics(self) -> Dict[str, Any]:
        """Get tunnel metrics and statistics.
        
        Returns:
            Dictionary with tunnel metrics
        """
        if not self.tunnel_manager:
            return {"error": "Tunnel manager not available"}
        
        return await self.tunnel_manager.get_metrics()


# Global service instance
_tunnel_service: Optional[SSHTunnelService] = None


def get_tunnel_service() -> Optional[SSHTunnelService]:
    """Get the global SSH tunnel service instance.
    
    Returns:
        SSHTunnelService instance or None if not initialized
    """
    return _tunnel_service


async def initialize_tunnel_service() -> Optional[SSHTunnelService]:
    """Initialize the global SSH tunnel service.
    
    Returns:
        SSHTunnelService instance or None if disabled
    """
    global _tunnel_service
    
    if _tunnel_service is not None:
        return _tunnel_service
    
    settings = get_settings()
    if not settings.ENABLE_SSH_TUNNEL:
        logger.info("SSH tunnel service is disabled in configuration")
        return None
    
    _tunnel_service = SSHTunnelService()
    success = await _tunnel_service.start_service()
    
    if not success:
        logger.error("Failed to initialize SSH tunnel service")
        _tunnel_service = None
        return None
    
    logger.info("SSH tunnel service initialized successfully")
    return _tunnel_service


async def shutdown_tunnel_service() -> None:
    """Shutdown the global SSH tunnel service."""
    global _tunnel_service
    
    if _tunnel_service:
        await _tunnel_service.stop_service()
        _tunnel_service = None
        logger.info("SSH tunnel service shutdown completed")


@asynccontextmanager
async def tunnel_service_lifespan():
    """Context manager for SSH tunnel service lifecycle.
    
    Usage:
        async with tunnel_service_lifespan():
            # Service is running
            pass
        # Service is stopped
    """
    service = await initialize_tunnel_service()
    try:
        yield service
    finally:
        await shutdown_tunnel_service() 