"""
SSH Tunnel Manager for RAG Construction Materials API.

This module provides tunnel lifecycle management, monitoring, and recovery.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any

from .ssh_tunnel import SSHTunnel
from .tunnel_config import TunnelConfig
from .exceptions import SSHTunnelError

logger = logging.getLogger(__name__)


class TunnelManager:
    """SSH Tunnel Manager for lifecycle management.
    
    This class manages the lifecycle of SSH tunnels including:
    - Starting and stopping tunnels
    - Health monitoring
    - Automatic reconnection
    - Statistics and metrics collection
    """
    
    def __init__(self, config: TunnelConfig):
        """Initialize tunnel manager.
        
        Args:
            config: TunnelConfig instance
        """
        self.config = config
        self.tunnel: Optional[SSHTunnel] = None
        self.is_active: bool = False
        self.last_start_time: Optional[float] = None
        self.last_stop_time: Optional[float] = None
        self.restart_count: int = 0
        self.total_uptime: float = 0.0
        
        # Health monitoring
        self.health_check_count: int = 0
        self.health_check_failures: int = 0
        self.last_health_check_time: Optional[float] = None
        self.last_health_status: bool = False
        
        logger.info(f"Tunnel Manager initialized: {self.config.connection_string}")
    
    async def start_tunnel(self) -> bool:
        """Start SSH tunnel.
        
        Returns:
            True if tunnel started successfully, False otherwise
        """
        if self.is_active:
            logger.warning("Tunnel is already active")
            return True
        
        try:
            logger.info("Starting SSH tunnel")
            
            # Create new tunnel instance
            self.tunnel = SSHTunnel(self.config)
            
            # Attempt connection with retries
            for attempt in range(self.config.retry_attempts):
                try:
                    success = await self.tunnel.connect()
                    if success:
                        self.is_active = True
                        self.last_start_time = time.time()
                        logger.info(f"SSH tunnel started successfully on attempt {attempt + 1}")
                        return True
                    
                except SSHTunnelError as e:
                    logger.warning(f"Tunnel connection attempt {attempt + 1} failed: {e}")
                    
                    if attempt < self.config.retry_attempts - 1:
                        logger.info(f"Retrying in {self.config.retry_delay} seconds...")
                        await asyncio.sleep(self.config.retry_delay)
                    else:
                        logger.error("All tunnel connection attempts failed")
                        break
            
            # Cleanup on failure
            await self._cleanup_tunnel()
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error starting tunnel: {e}")
            await self._cleanup_tunnel()
            return False
    
    async def stop_tunnel(self) -> None:
        """Stop SSH tunnel."""
        if not self.is_active:
            logger.info("Tunnel is not active")
            return
        
        logger.info("Stopping SSH tunnel")
        
        # Update uptime
        if self.last_start_time:
            self.total_uptime += time.time() - self.last_start_time
        
        self.is_active = False
        self.last_stop_time = time.time()
        
        await self._cleanup_tunnel()
        logger.info("SSH tunnel stopped")
    
    async def restart_tunnel(self) -> bool:
        """Restart SSH tunnel.
        
        Returns:
            True if tunnel restarted successfully, False otherwise
        """
        logger.info("Restarting SSH tunnel")
        self.restart_count += 1
        
        await self.stop_tunnel()
        success = await self.start_tunnel()
        
        if success:
            logger.info("SSH tunnel restarted successfully")
        else:
            logger.error("Failed to restart SSH tunnel")
        
        return success
    
    async def health_check(self) -> bool:
        """Perform health check on SSH tunnel.
        
        Returns:
            True if tunnel is healthy, False otherwise
        """
        self.health_check_count += 1
        self.last_health_check_time = time.time()
        
        if not self.is_active or not self.tunnel:
            self.last_health_status = False
            self.health_check_failures += 1
            return False
        
        try:
            is_healthy = await self.tunnel.health_check()
            self.last_health_status = is_healthy
            
            if not is_healthy:
                self.health_check_failures += 1
                logger.warning("SSH tunnel health check failed")
            else:
                logger.debug("SSH tunnel health check passed")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            self.last_health_status = False
            self.health_check_failures += 1
            return False
    
    async def _cleanup_tunnel(self) -> None:
        """Cleanup tunnel resources."""
        if self.tunnel:
            try:
                await self.tunnel.disconnect()
            except Exception as e:
                logger.warning(f"Error during tunnel cleanup: {e}")
            finally:
                self.tunnel = None
    
    def is_tunnel_active(self) -> bool:
        """Check if tunnel is currently active.
        
        Returns:
            True if tunnel is active, False otherwise
        """
        return self.is_active and self.tunnel is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current tunnel status.
        
        Returns:
            Dictionary with tunnel status information
        """
        current_uptime = 0.0
        if self.is_active and self.last_start_time:
            current_uptime = time.time() - self.last_start_time
        
        total_uptime = self.total_uptime + current_uptime
        
        status = {
            "active": self.is_active,
            "config": self.config.connection_string,
            "last_start_time": self.last_start_time,
            "last_stop_time": self.last_stop_time,
            "current_uptime_seconds": current_uptime,
            "total_uptime_seconds": total_uptime,
            "restart_count": self.restart_count,
            "health_monitoring": {
                "last_check_time": self.last_health_check_time,
                "last_status": self.last_health_status,
                "total_checks": self.health_check_count,
                "total_failures": self.health_check_failures,
                "success_rate": self._calculate_health_success_rate()
            }
        }
        
        # Add tunnel-specific status if available
        if self.tunnel:
            status["tunnel_details"] = self.tunnel.get_status()
        
        return status
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get tunnel metrics and statistics.
        
        Returns:
            Dictionary with tunnel metrics
        """
        status = self.get_status()
        
        # Add additional metrics
        metrics = {
            "availability": {
                "uptime_percentage": self._calculate_uptime_percentage(),
                "health_success_rate": self._calculate_health_success_rate(),
                "restart_frequency": self._calculate_restart_frequency()
            },
            "performance": {
                "total_bytes_transferred": 0,
                "average_connection_time": 0,
                "connection_attempts": 0
            }
        }
        
        # Get tunnel-specific metrics
        if self.tunnel:
            tunnel_status = self.tunnel.get_status()
            if "statistics" in tunnel_status:
                stats = tunnel_status["statistics"]
                metrics["performance"].update({
                    "total_bytes_transferred": stats.get("total_bytes_transferred", 0),
                    "connection_attempts": stats.get("connection_attempts", 0),
                    "successful_connections": stats.get("successful_connections", 0),
                    "failed_connections": stats.get("failed_connections", 0)
                })
        
        return {**status, "metrics": metrics}
    
    def _calculate_health_success_rate(self) -> float:
        """Calculate health check success rate.
        
        Returns:
            Success rate as percentage (0.0 to 1.0)
        """
        if self.health_check_count == 0:
            return 1.0
        
        success_count = self.health_check_count - self.health_check_failures
        return success_count / self.health_check_count
    
    def _calculate_uptime_percentage(self) -> float:
        """Calculate uptime percentage.
        
        Returns:
            Uptime percentage (0.0 to 1.0)
        """
        if not self.last_start_time:
            return 0.0
        
        # Calculate total time since first start
        current_time = time.time()
        total_time = current_time - self.last_start_time
        
        # Calculate current session uptime
        current_uptime = 0.0
        if self.is_active:
            current_uptime = current_time - self.last_start_time
        
        total_uptime = self.total_uptime + current_uptime
        
        if total_time <= 0:
            return 1.0
        
        return min(total_uptime / total_time, 1.0)
    
    def _calculate_restart_frequency(self) -> float:
        """Calculate restart frequency (restarts per hour).
        
        Returns:
            Restart frequency as restarts per hour
        """
        if not self.last_start_time or self.restart_count == 0:
            return 0.0
        
        total_time_hours = (time.time() - self.last_start_time) / 3600
        if total_time_hours <= 0:
            return 0.0
        
        return self.restart_count / total_time_hours
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.is_active:
            try:
                # Schedule cleanup task
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self._cleanup_tunnel())
                    else:
                        loop.run_until_complete(self._cleanup_tunnel())
                except RuntimeError:
                    # Not in async context, will be cleaned up by tunnel destructor
                    pass
            except Exception:
                pass  # Ignore cleanup errors in destructor 