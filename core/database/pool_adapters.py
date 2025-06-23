"""
Pool adapters for integrating existing database pools with dynamic pool manager.

Адаптеры для интеграции существующих пулов соединений с динамическим менеджером.
"""

from core.logging import get_logger
from typing import Dict, Any
from datetime import datetime

from core.database.pool_manager import PoolProtocol

logger = get_logger(__name__)


class RedisPoolAdapter(PoolProtocol):
    """Adapter for Redis connection pool."""
    
    def __init__(self, redis_database):
        """Initialize adapter with Redis database instance."""
        self.redis_db = redis_database
        self.request_count = 0
        self.failed_count = 0
        self.last_metrics_update = datetime.utcnow()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get Redis pool metrics."""
        try:
            # Get connection pool stats
            pool = self.redis_db.pool
            
            pool_stats = {
                "max_connections": pool.max_connections,
                "created_connections": pool.created_connections,
                "available_connections": len(pool._available_connections),
                "in_use_connections": len(pool._in_use_connections)
            }
            
            current_size = pool_stats["created_connections"]
            active_connections = pool_stats["in_use_connections"]
            idle_connections = pool_stats["available_connections"]
            
            return {
                "current_size": current_size,
                "max_size": pool_stats["max_connections"],
                "active_connections": active_connections,
                "idle_connections": idle_connections,
                "total_requests": self.request_count,
                "failed_requests": self.failed_count,
                "pool_type": "Redis"
            }
            
        except Exception as e:
            logger.error(f"Failed to get Redis pool metrics: {e}")
            return {
                "current_size": 0,
                "max_size": 0,
                "active_connections": 0,
                "idle_connections": 0,
                "total_requests": self.request_count,
                "failed_requests": self.failed_count,
                "pool_type": "Redis",
                "error": str(e)
            }
    
    async def resize_pool(self, new_size: int) -> bool:
        """Resize Redis connection pool."""
        try:
            # Redis connection pools are typically not resizable at runtime
            # We'll create a new pool with the new size
            logger.info(f"Redis pool resize requested to {new_size} connections")
            
            # For Redis, we can't dynamically resize the existing pool
            # But we can log the recommendation for manual adjustment
            logger.warning(f"Redis pool cannot be dynamically resized. "
                         f"Consider updating REDIS_MAX_CONNECTIONS to {new_size} in configuration")
            
            return False  # Cannot resize Redis pool at runtime
            
        except Exception as e:
            logger.error(f"Failed to resize Redis pool: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check Redis pool health."""
        try:
            # Test basic connectivity
            result = await self.redis_db.ping()
            if result:
                return True
            else:
                logger.warning("Redis ping failed")
                return False
                
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            self.failed_count += 1
            return False
    
    def record_request(self, success: bool = True):
        """Record a request for metrics tracking."""
        self.request_count += 1
        if not success:
            self.failed_count += 1


class PostgreSQLPoolAdapter(PoolProtocol):
    """Adapter for PostgreSQL connection pool."""
    
    def __init__(self, postgresql_database):
        """Initialize adapter with PostgreSQL database instance."""
        self.pg_db = postgresql_database
        self.request_count = 0
        self.failed_count = 0
        self.last_metrics_update = datetime.utcnow()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get PostgreSQL pool metrics."""
        try:
            engine = self.pg_db.engine
            pool = engine.pool
            
            # Get pool statistics
            current_size = pool.size()
            checked_in = pool.checkedin()
            checked_out = pool.checkedout()
            overflow = pool.overflow()
            
            return {
                "current_size": current_size,
                "max_size": current_size + overflow,
                "active_connections": checked_out,
                "idle_connections": checked_in,
                "overflow_connections": overflow,
                "total_requests": self.request_count,
                "failed_requests": self.failed_count,
                "pool_type": "PostgreSQL"
            }
            
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL pool metrics: {e}")
            return {
                "current_size": 0,
                "max_size": 0,
                "active_connections": 0,
                "idle_connections": 0,
                "total_requests": self.request_count,
                "failed_requests": self.failed_count,
                "pool_type": "PostgreSQL",
                "error": str(e)
            }
    
    async def resize_pool(self, new_size: int) -> bool:
        """Resize PostgreSQL connection pool."""
        try:
            # SQLAlchemy pools can't be resized at runtime
            # But we can log recommendations
            current_metrics = await self.get_metrics()
            current_size = current_metrics.get("current_size", 0)
            
            logger.info(f"PostgreSQL pool resize requested from {current_size} to {new_size}")
            logger.warning(f"PostgreSQL pool cannot be dynamically resized. "
                         f"Consider updating POSTGRESQL_POOL_SIZE to {new_size} in configuration")
            
            return False  # Cannot resize PostgreSQL pool at runtime
            
        except Exception as e:
            logger.error(f"Failed to resize PostgreSQL pool: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check PostgreSQL pool health."""
        try:
            # Test connection with a simple query
            async with self.pg_db.get_session() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                row = result.fetchone()
                return row is not None
                
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            self.failed_count += 1
            return False
    
    def record_request(self, success: bool = True):
        """Record a request for metrics tracking."""
        self.request_count += 1
        if not success:
            self.failed_count += 1


class QdrantPoolAdapter(PoolProtocol):
    """Adapter for Qdrant connection pool."""
    
    def __init__(self, qdrant_database):
        """Initialize adapter with Qdrant database instance."""
        self.qdrant_db = qdrant_database
        self.request_count = 0
        self.failed_count = 0
        self.last_metrics_update = datetime.utcnow()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get Qdrant pool metrics."""
        try:
            # Qdrant client doesn't expose detailed pool metrics
            # We'll provide basic information
            return {
                "current_size": 1,  # Qdrant typically uses single connection
                "max_size": 1,
                "active_connections": 1 if hasattr(self.qdrant_db, 'client') else 0,
                "idle_connections": 0,
                "total_requests": self.request_count,
                "failed_requests": self.failed_count,
                "pool_type": "Qdrant"
            }
            
        except Exception as e:
            logger.error(f"Failed to get Qdrant pool metrics: {e}")
            return {
                "current_size": 0,
                "max_size": 1,
                "active_connections": 0,
                "idle_connections": 0,
                "total_requests": self.request_count,
                "failed_requests": self.failed_count,
                "pool_type": "Qdrant",
                "error": str(e)
            }
    
    async def resize_pool(self, new_size: int) -> bool:
        """Resize Qdrant connection pool."""
        try:
            # Qdrant doesn't use traditional connection pools
            logger.info(f"Qdrant doesn't support connection pool resizing")
            return True  # No-op for Qdrant
            
        except Exception as e:
            logger.error(f"Failed to resize Qdrant pool: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check Qdrant health."""
        try:
            # Test basic connectivity
            if hasattr(self.qdrant_db, 'client'):
                await self.qdrant_db.client.get_collections()
                return True
            return False
                
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            self.failed_count += 1
            return False
    
    def record_request(self, success: bool = True):
        """Record a request for metrics tracking."""
        self.request_count += 1
        if not success:
            self.failed_count += 1


# Mock pool adapter for testing
class MockPoolAdapter(PoolProtocol):
    """Mock pool adapter for testing dynamic pool management."""
    
    def __init__(self, name: str, initial_size: int = 5):
        """Initialize mock pool."""
        self.name = name
        self.current_size = initial_size
        self.max_size = 50
        self.active_connections = 0
        self.request_count = 0
        self.failed_count = 0
        self.utilization_factor = 0.5  # Simulate 50% utilization by default
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get mock pool metrics."""
        # Simulate some load
        self.active_connections = int(self.current_size * self.utilization_factor)
        idle_connections = self.current_size - self.active_connections
        
        return {
            "current_size": self.current_size,
            "max_size": self.max_size,
            "active_connections": self.active_connections,
            "idle_connections": idle_connections,
            "total_requests": self.request_count,
            "failed_requests": self.failed_count,
            "pool_type": "Mock"
        }
    
    async def resize_pool(self, new_size: int) -> bool:
        """Resize mock pool."""
        if 1 <= new_size <= self.max_size:
            old_size = self.current_size
            self.current_size = new_size
            logger.info(f"Mock pool '{self.name}' resized from {old_size} to {new_size}")
            return True
        return False
    
    async def health_check(self) -> bool:
        """Check mock pool health."""
        return True
    
    def simulate_load(self, utilization: float):
        """Simulate different load levels for testing."""
        self.utilization_factor = max(0.0, min(1.0, utilization))
        self.request_count += 10  # Simulate some requests
    
    def record_request(self, success: bool = True):
        """Record a request for metrics tracking."""
        self.request_count += 1
        if not success:
            self.failed_count += 1 