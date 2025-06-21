"""Mock database clients and adapters for testing and fallback.

Мок-клиенты и адаптеры для тестирования и fallback стратегий.
"""
from core.logging import get_logger
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import asyncio

logger = get_logger(__name__)

class MockRedisClient:
    """Mock Redis client for when Redis is not available"""
    
    def __init__(self, *args, **kwargs):
        self.data = {}
        self.connected = False
        logger.info("🔧 MockRedisClient initialized (Redis fallback)")
    
    async def ping(self) -> bool:
        """Mock ping"""
        return True
    
    async def get(self, key: str) -> Optional[str]:
        """Mock get operation"""
        return self.data.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Mock set operation"""
        self.data[key] = value
        return True
    
    async def delete(self, *keys: str) -> int:
        """Mock delete operation"""
        deleted = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                deleted += 1
        return deleted
    
    async def exists(self, key: str) -> bool:
        """Mock exists check"""
        return key in self.data
    
    async def incr(self, key: str) -> int:
        """Mock increment"""
        current = int(self.data.get(key, 0))
        current += 1
        self.data[key] = str(current)
        return current
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Mock expire (no-op)"""
        return True
    
    def close(self):
        """Mock close"""
        self.connected = False
        logger.info("🔧 MockRedisClient closed")

class MockPostgreSQLSession:
    """Mock PostgreSQL session"""
    
    def __init__(self):
        self.data = {
            'materials': [],
            'categories': [],
            'units': [],
            'prices': []
        }
        logger.info("🔧 MockPostgreSQLSession initialized (PostgreSQL fallback)")
    
    async def execute(self, query, params=None):
        """Mock query execution"""
        # Simple mock that returns empty results
        class MockResult:
            def scalars(self):
                return MockScalars()
            
            def fetchall(self):
                return []
            
            def scalar(self):
                return 0
        
        class MockScalars:
            def all(self):
                return []
            
            def first(self):
                return None
        
        return MockResult()
    
    async def commit(self):
        """Mock commit"""
        pass
    
    async def rollback(self):
        """Mock rollback"""  
        pass
    
    async def close(self):
        """Mock close"""
        pass
    
    def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

class MockPostgreSQLAdapter:
    """Mock PostgreSQL database adapter"""
    
    def __init__(self, *args, **kwargs):
        self.connected = False
        logger.info("🔧 MockPostgreSQLAdapter initialized (PostgreSQL fallback)")
    
    async def connect(self):
        """Mock connection"""
        self.connected = True
        return True
    
    async def disconnect(self):
        """Mock disconnection"""
        self.connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check"""
        return {
            "status": "healthy",
            "type": "mock_postgresql",
            "connected": True,
            "message": "Mock PostgreSQL adapter working"
        }
    
    def async_session(self):
        """Return mock session"""
        return MockPostgreSQLSession()
    
    async def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock material creation"""
        material_id = f"mock-{len(self.async_session().data['materials'])}"
        material = {
            "id": material_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **material_data
        }
        return material
    
    async def get_materials(self, skip: int = 0, limit: int = 100, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Mock materials retrieval"""
        return []  # Return empty list for mock
    
    async def search_materials_sql(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Mock SQL search"""
        return []  # Return empty list for mock

class MockAIClient:
    """Mock AI client for when OpenAI/HuggingFace is not available"""
    
    def __init__(self, *args, **kwargs):
        self.model = "mock-embedding-model"
        logger.info("🔧 MockAIClient initialized (AI fallback)")
    
    async def get_embedding(self, text: str) -> List[float]:
        """Generate mock embedding based on text hash"""
        # Create a deterministic but varied embedding based on text
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert hash to 1536-dimensional vector (OpenAI embedding size)
        embedding = []
        for i in range(1536):
            # Use different parts of hash to create varied values
            byte_index = i % len(hash_hex)
            value = int(hash_hex[byte_index], 16) / 15.0 - 0.5  # Normalize to [-0.5, 0.5]
            embedding.append(value)
        
        return embedding
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate batch of mock embeddings"""
        return [await self.get_embedding(text) for text in texts]

def create_mock_redis_client(*args, **kwargs) -> MockRedisClient:
    """Factory function for mock Redis client"""
    return MockRedisClient(*args, **kwargs)

def create_mock_postgresql_database(*args, **kwargs) -> MockPostgreSQLAdapter:
    """Factory function for mock PostgreSQL database"""
    return MockPostgreSQLAdapter(*args, **kwargs)

def create_mock_ai_client(*args, **kwargs) -> MockAIClient:
    """Factory function for mock AI client"""
    return MockAIClient(*args, **kwargs) 