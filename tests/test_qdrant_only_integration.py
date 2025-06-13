"""
Integration tests for Qdrant-only mode without middleware
Интеграционные тесты для режима только с Qdrant без проблем middleware
"""
import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.config import get_settings
from core.database.factories import DatabaseFactory
from core.database.adapters.mock_adapters import MockRelationalAdapter, MockCacheAdapter


@pytest.fixture
def minimal_app():
    """Minimal FastAPI app without middleware for testing"""
    app = FastAPI(title="Test API")
    
    # Simple test endpoint
    @app.get("/test/health")
    async def test_health():
        return {"status": "ok"}
    
    @app.get("/test/db-status")
    async def test_db_status():
        """Test database status"""
        try:
            # Test relational database
            rel_db = DatabaseFactory.create_relational_database()
            rel_health = await rel_db.health_check()
            
            # Test cache database
            cache_db = DatabaseFactory.create_cache_database()
            cache_health = await cache_db.health_check()
            
            return {
                "relational_db": rel_health,
                "cache_db": cache_health
            }
        except Exception as e:
            return {"error": str(e)}
    
    return app


@pytest.fixture
def qdrant_only_settings():
    """Settings for Qdrant-only mode"""
    with patch('core.config.get_settings') as mock_get_settings:
        settings = get_settings()
        # Override specific attributes
        settings.QDRANT_ONLY_MODE = True
        settings.ENABLE_FALLBACK_DATABASES = True
        settings.DISABLE_REDIS_CONNECTION = True
        settings.DISABLE_POSTGRESQL_CONNECTION = True
        mock_get_settings.return_value = settings
        yield settings


class TestQdrantOnlyIntegration:
    """Integration tests for Qdrant-only mode"""
    
    def test_minimal_app_works(self, minimal_app):
        """Test that minimal app works"""
        client = TestClient(minimal_app)
        response = client.get("/test/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_database_factories_return_mocks(self, qdrant_only_settings, minimal_app):
        """Test that database factories return mock adapters in Qdrant-only mode"""
        client = TestClient(minimal_app)
        
        response = client.get("/test/db-status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check that relational DB is mock
        assert "relational_db" in data
        assert data["relational_db"]["status"] == "healthy"
        assert data["relational_db"]["type"] == "mock_postgresql"
        
        # Check that cache DB is mock
        assert "cache_db" in data
        assert data["cache_db"]["status"] == "healthy"
        assert data["cache_db"]["type"] == "mock_redis"
    
    def test_direct_database_creation(self, qdrant_only_settings):
        """Test direct database creation returns mock adapters"""
        # Clear any cached instances
        DatabaseFactory.clear_cache()
        
        # Test relational database
        rel_db = DatabaseFactory.create_relational_database()
        assert isinstance(rel_db, MockRelationalAdapter)
        assert hasattr(rel_db, 'mock_db')
        
        # Test cache database
        cache_db = DatabaseFactory.create_cache_database()
        assert isinstance(cache_db, MockCacheAdapter)
        assert hasattr(cache_db, 'mock_redis')
    
    @pytest.mark.asyncio
    async def test_mock_database_operations(self, qdrant_only_settings):
        """Test mock database operations work correctly"""
        # Clear any cached instances
        DatabaseFactory.clear_cache()
        
        # Test relational database operations
        rel_db = DatabaseFactory.create_relational_database()
        
        # Test connection
        connected = await rel_db.connect()
        assert connected is True
        
        # Test health check
        health = await rel_db.health_check()
        assert health['status'] == 'healthy'
        assert health['type'] == 'mock_postgresql'
        
        # Test basic operations
        query_result = await rel_db.execute_query("SELECT 1")
        assert isinstance(query_result, list)
        
        command_result = await rel_db.execute_command("INSERT INTO test VALUES (1)")
        assert isinstance(command_result, int)
        
        # Test cache database operations
        cache_db = DatabaseFactory.create_cache_database()
        
        # Test connection
        cache_connected = await cache_db.connect()
        assert cache_connected is True
        
        # Test health check
        cache_health = await cache_db.health_check()
        assert cache_health['status'] == 'healthy'
        assert cache_health['type'] == 'mock_redis'
        
        # Test cache operations
        set_result = await cache_db.set("test_key", "test_value")
        assert set_result is True
        
        get_result = await cache_db.get("test_key")
        assert get_result == "test_value"
        
        exists_result = await cache_db.exists("test_key")
        assert exists_result is True
        
        delete_result = await cache_db.delete("test_key")
        assert delete_result is True
    
    def test_settings_are_applied(self, qdrant_only_settings):
        """Test that Qdrant-only settings are properly applied"""
        settings = qdrant_only_settings
        
        assert settings.QDRANT_ONLY_MODE is True
        assert settings.ENABLE_FALLBACK_DATABASES is True
        assert settings.DISABLE_REDIS_CONNECTION is True
        assert settings.DISABLE_POSTGRESQL_CONNECTION is True
    
    @pytest.mark.asyncio
    async def test_concurrent_database_access(self, qdrant_only_settings):
        """Test concurrent access to mock databases"""
        DatabaseFactory.clear_cache()
        
        async def test_rel_db():
            rel_db = DatabaseFactory.create_relational_database()
            health = await rel_db.health_check()
            return health['status']
        
        async def test_cache_db():
            cache_db = DatabaseFactory.create_cache_database()
            health = await cache_db.health_check()
            return health['status']
        
        # Run concurrent operations
        rel_results = await asyncio.gather(*[test_rel_db() for _ in range(5)])
        cache_results = await asyncio.gather(*[test_cache_db() for _ in range(5)])
        
        # All should return healthy
        assert all(result == 'healthy' for result in rel_results)
        assert all(result == 'healthy' for result in cache_results)
    
    def test_factory_caching_works(self, qdrant_only_settings):
        """Test that factory caching works properly with mocks"""
        DatabaseFactory.clear_cache()
        
        # Create instances
        rel_db1 = DatabaseFactory.create_relational_database()
        rel_db2 = DatabaseFactory.create_relational_database()
        
        cache_db1 = DatabaseFactory.create_cache_database()
        cache_db2 = DatabaseFactory.create_cache_database()
        
        # Should be the same instances due to caching
        assert rel_db1 is rel_db2
        assert cache_db1 is cache_db2
        
        # Clear cache and create new instances
        DatabaseFactory.clear_cache()
        
        rel_db3 = DatabaseFactory.create_relational_database()
        cache_db3 = DatabaseFactory.create_cache_database()
        
        # Should be different instances after cache clear
        assert rel_db1 is not rel_db3
        assert cache_db1 is not cache_db3 