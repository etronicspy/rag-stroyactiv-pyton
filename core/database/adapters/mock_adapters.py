"""
Mock adapters implementing database interfaces
Адаптеры-заглушки, реализующие интерфейсы БД
"""
from core.monitoring.logger import get_logger
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import asyncio

from core.database.interfaces import IRelationalDatabase, ICacheDatabase
from core.database.mocks import MockRedisClient, MockPostgreSQLAdapter

logger = get_logger(__name__)

class MockRelationalAdapter(IRelationalDatabase):
    """Mock adapter implementing IRelationalDatabase interface"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.mock_db = MockPostgreSQLAdapter()
        self.connected = False
        logger.info("🔧 MockRelationalAdapter initialized")
    
    async def connect(self) -> bool:
        """Mock connection"""
        self.connected = True
        await self.mock_db.connect()
        return True
    
    async def disconnect(self) -> bool:
        """Mock disconnection"""
        self.connected = False
        await self.mock_db.disconnect()
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check"""
        return await self.mock_db.health_check()
    
    async def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock material creation"""
        return await self.mock_db.create_material(material_data)
    
    async def get_materials(self, skip: int = 0, limit: int = 100, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Mock materials retrieval"""
        return await self.mock_db.get_materials(skip, limit, category)
    
    async def search_materials_sql(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Mock SQL search"""
        return await self.mock_db.search_materials_sql(query, limit)
    
    async def update_material(self, material_id: str, material_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock material update"""
        return {
            "id": material_id,
            "updated_at": datetime.utcnow(),
            **material_data
        }
    
    async def delete_material(self, material_id: str) -> bool:
        """Mock material deletion"""
        return True
    
    async def get_material_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        """Mock material retrieval by ID"""
        return {
            "id": material_id,
            "name": "Mock Material",
            "description": "Mock material description",
            "category": "Mock Category",
            "price": 100.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    # Required abstract methods from IRelationalDatabase
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return mock results"""
        return []
    
    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute SQL command and return mock affected rows"""
        return 1
    
    async def begin_transaction(self):
        """Begin mock transaction as async context manager"""
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def mock_transaction():
            try:
                yield "mock_transaction"
            finally:
                pass
        
        return mock_transaction()

class MockCacheAdapter(ICacheDatabase):
    """Mock adapter implementing ICacheDatabase interface"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.mock_redis = MockRedisClient()
        self.connected = False
        logger.info("🔧 MockCacheAdapter initialized")
    
    async def connect(self) -> bool:
        """Mock connection"""
        self.connected = True
        return True
    
    async def disconnect(self) -> bool:
        """Mock disconnection"""
        self.connected = False
        self.mock_redis.close()
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check"""
        return {
            "status": "healthy",
            "type": "mock_redis",
            "connected": True,
            "message": "Mock Redis adapter working"
        }
    
    async def get(self, key: str) -> Optional[str]:
        """Mock get operation"""
        return await self.mock_redis.get(key)
    
    async def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        """Mock set operation"""
        return await self.mock_redis.set(key, value, ex=expire_seconds)
    
    async def delete(self, key: str) -> bool:
        """Mock delete operation"""
        result = await self.mock_redis.delete(key)
        return result > 0
    
    async def exists(self, key: str) -> bool:
        """Mock exists check"""
        return await self.mock_redis.exists(key)
    
    # Additional methods for extended functionality (not in base interface)
    async def incr(self, key: str) -> int:
        """Mock increment"""
        return await self.mock_redis.incr(key)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Mock expire"""
        return await self.mock_redis.expire(key, seconds)
    
    async def ping(self) -> bool:
        """Mock ping"""
        return await self.mock_redis.ping()
    
    async def clear_cache(self, pattern: str = "*") -> int:
        """Mock cache clear"""
        # Simple implementation - clear all data
        cleared = len(self.mock_redis.data)
        self.mock_redis.data.clear()
        return cleared
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Mock cache statistics"""
        return {
            "total_keys": len(self.mock_redis.data),
            "used_memory": len(str(self.mock_redis.data)),
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0
        }

def create_mock_relational_adapter(config: Dict[str, Any] = None) -> MockRelationalAdapter:
    """Factory function for mock relational adapter"""
    return MockRelationalAdapter(config)

def create_mock_cache_adapter(config: Dict[str, Any] = None) -> MockCacheAdapter:
    """Factory function for mock cache adapter"""
    return MockCacheAdapter(config) 