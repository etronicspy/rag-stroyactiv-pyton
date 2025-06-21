"""
Dynamic Connection Pool Manager for optimal database performance.

Автоматическое управление connection pools с мониторингом и динамическим масштабированием.
"""

import asyncio
import time
from functools import lru_cache
from core.logging import get_logger
import threading
from typing import Dict, Any, Optional, Protocol, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import psutil

logger = get_logger(__name__)


@dataclass
class PoolMetrics:
    """Connection pool metrics for monitoring."""
    pool_name: str
    current_size: int = 0
    max_size: int = 10
    active_connections: int = 0
    idle_connections: int = 0
    utilization_percentage: float = 0.0
    average_wait_time: float = 0.0
    peak_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def update_utilization(self):
        """Update utilization percentage."""
        if self.max_size > 0:
            self.utilization_percentage = (self.active_connections / self.max_size) * 100
        else:
            self.utilization_percentage = 0.0
        
        if self.active_connections > self.peak_connections:
            self.peak_connections = self.active_connections
        
        self.last_updated = datetime.utcnow()


@dataclass
class PoolConfig:
    """Dynamic pool configuration."""
    min_size: int = 2
    max_size: int = 50
    target_utilization: float = 0.75  # 75% utilization target
    scale_up_threshold: float = 0.85   # Scale up at 85% utilization
    scale_down_threshold: float = 0.4  # Scale down at 40% utilization
    scale_factor: float = 1.5          # Multiplier for scaling
    monitoring_interval: float = 30.0  # Seconds between monitoring checks
    auto_scaling_enabled: bool = True
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0        # 5 minutes


class PoolProtocol(Protocol):
    """Protocol for connection pools that can be managed."""
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current pool metrics."""
        ...
    
    async def resize_pool(self, new_size: int) -> bool:
        """Resize the pool to new size."""
        ...
    
    async def health_check(self) -> bool:
        """Check pool health."""
        ...


class DynamicPoolManager:
    """
    Dynamic connection pool manager with auto-scaling and monitoring.
    
    Автоматически масштабирует connection pools на основе нагрузки и метрик.
    """
    
    def __init__(self, config: Optional[PoolConfig] = None):
        """Initialize pool manager."""
        self.config = config or PoolConfig()
        self.pools: Dict[str, PoolProtocol] = {}
        self.metrics: Dict[str, PoolMetrics] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        self.lock = threading.Lock()
        
        # Performance tracking
        self.adjustment_history: List[Dict[str, Any]] = []
        self.last_adjustment_time = {}
        
        logger.info(f"Dynamic Pool Manager initialized with config: {self.config}")
    
    def register_pool(
        self, 
        name: str, 
        pool: PoolProtocol, 
        initial_size: int = 10,
        max_size: int = 50
    ) -> None:
        """Register a pool for management."""
        with self.lock:
            self.pools[name] = pool
            self.metrics[name] = PoolMetrics(
                pool_name=name,
                current_size=initial_size,
                max_size=max_size
            )
            self.last_adjustment_time[name] = time.time()
            
        logger.info(f"Registered pool '{name}' with initial size {initial_size}")
    
    def unregister_pool(self, name: str) -> None:
        """Unregister a pool from management."""
        with self.lock:
            self.pools.pop(name, None)
            self.metrics.pop(name, None)
            self.last_adjustment_time.pop(name, None)
            
        logger.info(f"Unregistered pool '{name}'")
    
    async def start_monitoring(self) -> None:
        """Start pool monitoring and auto-scaling."""
        if self.is_monitoring:
            logger.warning("Pool monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started pool monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop pool monitoring."""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped pool monitoring")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._collect_metrics()
                await self._analyze_and_adjust_pools()
                await asyncio.sleep(self.config.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.config.monitoring_interval)
    
    async def _collect_metrics(self) -> None:
        """Collect metrics from all registered pools."""
        for pool_name, pool in self.pools.items():
            try:
                pool_metrics = await pool.get_metrics()
                
                with self.lock:
                    metrics = self.metrics[pool_name]
                    
                    # Update metrics from pool
                    metrics.current_size = pool_metrics.get('current_size', metrics.current_size)
                    metrics.active_connections = pool_metrics.get('active_connections', 0)
                    metrics.idle_connections = pool_metrics.get('idle_connections', 0)
                    metrics.total_requests = pool_metrics.get('total_requests', metrics.total_requests)
                    metrics.failed_requests = pool_metrics.get('failed_requests', metrics.failed_requests)
                    
                    # Update utilization
                    metrics.update_utilization()
                    
            except Exception as e:
                logger.error(f"Failed to collect metrics for pool '{pool_name}': {e}")
    
    async def _analyze_and_adjust_pools(self) -> None:
        """Analyze metrics and adjust pool sizes if needed."""
        if not self.config.auto_scaling_enabled:
            return
        
        for pool_name, metrics in self.metrics.items():
            try:
                await self._adjust_pool_if_needed(pool_name, metrics)
            except Exception as e:
                logger.error(f"Failed to adjust pool '{pool_name}': {e}")
    
    async def _adjust_pool_if_needed(self, pool_name: str, metrics: PoolMetrics) -> None:
        """Adjust individual pool size based on metrics."""
        current_time = time.time()
        last_adjustment = self.last_adjustment_time.get(pool_name, 0)
        
        # Prevent too frequent adjustments (min 60 seconds between adjustments)
        if current_time - last_adjustment < 60:
            return
        
        utilization = metrics.utilization_percentage / 100.0
        current_size = metrics.current_size
        
        # Determine if scaling is needed
        new_size = None
        reason = ""
        
        if utilization > self.config.scale_up_threshold and current_size < self.config.max_size:
            # Scale up
            new_size = min(
                self.config.max_size,
                max(current_size + 1, int(current_size * self.config.scale_factor))
            )
            reason = f"High utilization ({utilization:.1%})"
            
        elif utilization < self.config.scale_down_threshold and current_size > self.config.min_size:
            # Scale down
            new_size = max(
                self.config.min_size,
                int(current_size / self.config.scale_factor)
            )
            reason = f"Low utilization ({utilization:.1%})"
        
        # Apply scaling if needed
        if new_size and new_size != current_size:
            pool = self.pools[pool_name]
            
            # Check system resources before scaling up
            if new_size > current_size:
                if not self._check_system_resources():
                    logger.warning(f"Skipping scale up for '{pool_name}' due to system resource constraints")
                    return
            
            success = await pool.resize_pool(new_size)
            
            if success:
                metrics.current_size = new_size
                metrics.max_size = max(metrics.max_size, new_size)
                self.last_adjustment_time[pool_name] = current_time
                
                # Record adjustment
                adjustment = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "pool_name": pool_name,
                    "old_size": current_size,
                    "new_size": new_size,
                    "reason": reason,
                    "utilization": utilization
                }
                self.adjustment_history.append(adjustment)
                
                # Keep only last 100 adjustments
                if len(self.adjustment_history) > 100:
                    self.adjustment_history = self.adjustment_history[-100:]
                
                logger.info(f"Scaled pool '{pool_name}' from {current_size} to {new_size} ({reason})")
            else:
                logger.warning(f"Failed to resize pool '{pool_name}' to {new_size}")
    
    def _check_system_resources(self) -> bool:
        """Check if system has enough resources for scaling up."""
        try:
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 85:  # More than 85% memory used
                logger.warning(f"High memory usage ({memory.percent:.1f}%), skipping scale up")
                return False
            
            # Check CPU usage (average over last minute)
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:  # More than 90% CPU used
                logger.warning(f"High CPU usage ({cpu_percent:.1f}%), skipping scale up")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to check system resources: {e}")
            return True  # Allow scaling if we can't check resources
    
    def get_pool_metrics(self, pool_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for specific pool or all pools."""
        with self.lock:
            if pool_name:
                if pool_name in self.metrics:
                    return {
                        pool_name: {
                            "current_size": self.metrics[pool_name].current_size,
                            "utilization": self.metrics[pool_name].utilization_percentage,
                            "active_connections": self.metrics[pool_name].active_connections,
                            "idle_connections": self.metrics[pool_name].idle_connections,
                            "peak_connections": self.metrics[pool_name].peak_connections,
                            "total_requests": self.metrics[pool_name].total_requests,
                            "failed_requests": self.metrics[pool_name].failed_requests,
                            "last_updated": self.metrics[pool_name].last_updated.isoformat()
                        }
                    }
                else:
                    return {}
            else:
                return {
                    name: {
                        "current_size": metrics.current_size,
                        "utilization": metrics.utilization_percentage,
                        "active_connections": metrics.active_connections,
                        "idle_connections": metrics.idle_connections,
                        "peak_connections": metrics.peak_connections,
                        "total_requests": metrics.total_requests,
                        "failed_requests": metrics.failed_requests,
                        "last_updated": metrics.last_updated.isoformat()
                    }
                    for name, metrics in self.metrics.items()
                }
    
    def get_adjustment_history(self, pool_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pool adjustment history."""
        history = self.adjustment_history[-limit:]
        
        if pool_name:
            return [adj for adj in history if adj["pool_name"] == pool_name]
        else:
            return history
    
    async def force_pool_resize(self, pool_name: str, new_size: int, reason: str = "Manual adjustment") -> bool:
        """Manually force pool resize."""
        if pool_name not in self.pools:
            logger.error(f"Pool '{pool_name}' not found")
            return False
        
        # Validate size bounds
        if new_size < self.config.min_size or new_size > self.config.max_size:
            logger.error(f"New size {new_size} out of bounds [{self.config.min_size}, {self.config.max_size}]")
            return False
        
        pool = self.pools[pool_name]
        current_size = self.metrics[pool_name].current_size
        
        success = await pool.resize_pool(new_size)
        
        if success:
            self.metrics[pool_name].current_size = new_size
            self.last_adjustment_time[pool_name] = time.time()
            
            adjustment = {
                "timestamp": datetime.utcnow().isoformat(),
                "pool_name": pool_name,
                "old_size": current_size,
                "new_size": new_size,
                "reason": reason,
                "manual": True
            }
            self.adjustment_history.append(adjustment)
            
            logger.info(f"Manually resized pool '{pool_name}' from {current_size} to {new_size} ({reason})")
        
        return success
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on current metrics."""
        recommendations = []
        
        with self.lock:
            for pool_name, metrics in self.metrics.items():
                utilization = metrics.utilization_percentage / 100.0
                
                # High utilization recommendation
                if utilization > 0.9 and metrics.current_size < self.config.max_size:
                    recommendations.append({
                        "pool_name": pool_name,
                        "type": "scale_up",
                        "priority": "high",
                        "current_utilization": f"{utilization:.1%}",
                        "recommended_size": min(self.config.max_size, int(metrics.current_size * 1.5)),
                        "reason": "High utilization may cause performance degradation"
                    })
                
                # Low utilization recommendation
                elif utilization < 0.2 and metrics.current_size > self.config.min_size:
                    recommendations.append({
                        "pool_name": pool_name,
                        "type": "scale_down",
                        "priority": "medium",
                        "current_utilization": f"{utilization:.1%}",
                        "recommended_size": max(self.config.min_size, int(metrics.current_size * 0.7)),
                        "reason": "Low utilization indicates over-provisioning"
                    })
                
                # High failure rate recommendation
                failure_rate = 0
                if metrics.total_requests > 0:
                    failure_rate = metrics.failed_requests / metrics.total_requests
                
                if failure_rate > 0.05:  # More than 5% failures
                    recommendations.append({
                        "pool_name": pool_name,
                        "type": "investigate",
                        "priority": "high",
                        "failure_rate": f"{failure_rate:.1%}",
                        "reason": "High failure rate may indicate connection issues"
                    })
        
        return recommendations


# Global pool manager instance
_pool_manager: Optional[DynamicPoolManager] = None


def get_pool_manager() -> DynamicPoolManager:
    """Get global pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = DynamicPoolManager()
    return _pool_manager


async def initialize_pool_manager(config: Optional[PoolConfig] = None) -> DynamicPoolManager:
    """Initialize and start the global pool manager."""
    global _pool_manager
    
    if _pool_manager is not None:
        await _pool_manager.stop_monitoring()
    
    _pool_manager = DynamicPoolManager(config)
    await _pool_manager.start_monitoring()
    
    logger.info("Pool manager initialized and monitoring started")
    return _pool_manager


async def shutdown_pool_manager() -> None:
    """Shutdown the global pool manager."""
    global _pool_manager
    if _pool_manager is not None:
        await _pool_manager.stop_monitoring()
        _pool_manager = None
        logger.info("Pool manager shutdown completed") 