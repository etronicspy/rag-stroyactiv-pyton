"""
Integration tests for vector search operations
Интеграционные тесты для операций векторного поиска

Объединяет тесты из:
- test_qdrant_only_integration.py
- test_qdrant_only_mode.py
"""
import pytest
import asyncio
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.config import get_settings
from core.database.factories import DatabaseFactory
from core.database.adapters.mock_adapters import MockRelationalAdapter, MockCacheAdapter


@pytest.fixture
def minimal_app():
    """Minimal FastAPI app without middleware for testing"""
    app = FastAPI(title="Test API")
    
    @app.get("/test/health")
    async def test_health():
        return {"status": "ok"}
    
    @app.get("/test/db-status")
    async def test_db_status():
        """Test database status"""
        try:
            rel_db = DatabaseFactory.create_relational_database()
            rel_health = await rel_db.health_check()
            
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
        settings.QDRANT_ONLY_MODE = True
        settings.ENABLE_FALLBACK_DATABASES = True
        settings.DISABLE_REDIS_CONNECTION = True
        settings.DISABLE_POSTGRESQL_CONNECTION = True
        mock_get_settings.return_value = settings
        yield settings


class TestQdrantOnlyIntegration:
    """Integration tests for Qdrant-only mode"""
    
    @pytest.mark.integration
    def test_minimal_app_works(self, minimal_app):
        """Test that minimal app works"""
        client = TestClient(minimal_app)
        response = client.get("/test/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    @pytest.mark.integration
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
    
    @pytest.mark.integration
    def test_direct_database_creation(self, qdrant_only_settings):
        """Test direct database creation returns mock adapters"""
        DatabaseFactory.clear_cache()
        
        rel_db = DatabaseFactory.create_relational_database()
        assert isinstance(rel_db, MockRelationalAdapter)
        assert hasattr(rel_db, 'mock_db')
        
        cache_db = DatabaseFactory.create_cache_database()
        assert isinstance(cache_db, MockCacheAdapter)
        assert hasattr(cache_db, 'mock_redis')
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mock_database_operations(self, qdrant_only_settings):
        """Test mock database operations work correctly"""
        DatabaseFactory.clear_cache()
        
        # Test relational database operations
        rel_db = DatabaseFactory.create_relational_database()
        
        connected = await rel_db.connect()
        assert connected is True
        
        health = await rel_db.health_check()
        assert health['status'] == 'healthy'
        assert health['type'] == 'mock_postgresql'
        
        query_result = await rel_db.execute_query("SELECT 1")
        assert isinstance(query_result, list)
        
        command_result = await rel_db.execute_command("INSERT INTO test VALUES (1)")
        assert isinstance(command_result, int)
        
        # Test cache database operations
        cache_db = DatabaseFactory.create_cache_database()
        
        cache_connected = await cache_db.connect()
        assert cache_connected is True
        
        cache_health = await cache_db.health_check()
        assert cache_health['status'] == 'healthy'
        assert cache_health['type'] == 'mock_redis'
        
        set_result = await cache_db.set("test_key", "test_value")
        assert set_result is True
        
        get_result = await cache_db.get("test_key")
        assert get_result == "test_value"
        
        exists_result = await cache_db.exists("test_key")
        assert exists_result is True
        
        delete_result = await cache_db.delete("test_key")
        assert delete_result is True
    
    @pytest.mark.integration
    def test_settings_are_applied(self, qdrant_only_settings):
        """Test that Qdrant-only settings are properly applied"""
        settings = qdrant_only_settings
        
        assert settings.QDRANT_ONLY_MODE is True
        assert settings.ENABLE_FALLBACK_DATABASES is True
        assert settings.DISABLE_REDIS_CONNECTION is True
        assert settings.DISABLE_POSTGRESQL_CONNECTION is True
    
    @pytest.mark.integration
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
    
    @pytest.mark.integration
    def test_factory_caching_works(self, qdrant_only_settings):
        """Test that factory caching works properly with mocks"""
        DatabaseFactory.clear_cache()
        
        rel_db1 = DatabaseFactory.create_relational_database()
        rel_db2 = DatabaseFactory.create_relational_database()
        
        cache_db1 = DatabaseFactory.create_cache_database()
        cache_db2 = DatabaseFactory.create_cache_database()
        
        # Should be the same instances due to caching
        assert rel_db1 is rel_db2
        assert cache_db1 is cache_db2


class TestQdrantModeConfiguration:
    """Тесты конфигурации Qdrant режима"""
    
    @pytest.mark.integration
    def test_qdrant_mode_settings_override(self):
        """Test Qdrant mode settings override"""
        with patch('core.config.get_settings') as mock_get_settings:
            settings = get_settings()
            
            # Override for Qdrant-only mode
            settings.QDRANT_ONLY_MODE = True
            settings.VECTOR_DB_TYPE = "qdrant"
            settings.ENABLE_VECTOR_SEARCH = True
            settings.DISABLE_RELATIONAL_FALLBACK = True
            
            mock_get_settings.return_value = settings
            
            # Test settings are applied
            current_settings = get_settings()
            assert current_settings.QDRANT_ONLY_MODE is True
            assert current_settings.VECTOR_DB_TYPE == "qdrant"
            assert current_settings.ENABLE_VECTOR_SEARCH is True
    
    @pytest.mark.integration 
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_qdrant_mode_performance(self, qdrant_only_settings):
        """Test performance in Qdrant-only mode"""
        DatabaseFactory.clear_cache()
        
        # Measure database creation time
        import time
        start_time = time.time()
        
        rel_db = DatabaseFactory.create_relational_database()
        cache_db = DatabaseFactory.create_cache_database()
        
        creation_time = time.time() - start_time
        
        # Should be fast with mock adapters
        assert creation_time < 1.0  # Less than 1 second
        
        # Test health check performance
        health_start = time.time()
        
        rel_health = await rel_db.health_check()
        cache_health = await cache_db.health_check()
        
        health_time = time.time() - health_start
        
        # Health checks should be very fast with mocks
        assert health_time < 0.5  # Less than 500ms
        
        # Verify mock responses
        assert rel_health['status'] == 'healthy'
        assert cache_health['status'] == 'healthy'
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_qdrant_mode_error_handling(self, qdrant_only_settings):
        """Test error handling in Qdrant-only mode"""
        DatabaseFactory.clear_cache()
        
        # Even with mock adapters, error handling should work
        rel_db = DatabaseFactory.create_relational_database()
        cache_db = DatabaseFactory.create_cache_database()
        
        # Test that operations don't raise unexpected exceptions
        try:
            await rel_db.health_check()
            await cache_db.health_check()
            await rel_db.execute_query("SELECT 1")
            await cache_db.set("test", "value")
            await cache_db.get("test")
        except Exception as e:
            # Should not raise exceptions with proper mock adapters
            pytest.fail(f"Unexpected exception in Qdrant-only mode: {e}")


class TestVectorSearchIntegration:
    """Интеграционные тесты векторного поиска"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_vector_search_fallback_chain(self):
        """Test vector search fallback chain"""
        # This would test the actual vector search workflow
        # but since we're in integration test mode, we focus
        # on testing the integration points
        
        DatabaseFactory.clear_cache()
        
        # Test that vector search components can be created
        try:
            # In a real scenario, this would test vector DB connection
            # For now, we test the factory pattern works
            rel_db = DatabaseFactory.create_relational_database()
            cache_db = DatabaseFactory.create_cache_database()
            
            # Verify adapters are created successfully
            assert rel_db is not None
            assert cache_db is not None
            
            # Test basic operations work
            rel_health = await rel_db.health_check()
            cache_health = await cache_db.health_check()
            
            assert rel_health['status'] in ['healthy', 'mock']
            assert cache_health['status'] in ['healthy', 'mock']
            
        except Exception as e:
            # Integration tests may fail due to missing dependencies
            # This is acceptable for vector search tests
            if "vector" in str(e).lower() or "embedding" in str(e).lower():
                pytest.skip(f"Vector search dependencies not available: {e}")
            else:
                raise
    
    @pytest.mark.integration
    def test_vector_db_configuration_validation(self):
        """Test vector database configuration validation"""
        # Test that vector DB settings are properly validated
        with patch('core.config.get_settings') as mock_get_settings:
            settings = get_settings()
            
            # Test different vector DB configurations
            vector_configs = [
                {"VECTOR_DB_TYPE": "qdrant", "QDRANT_URL": "http://localhost:6333"},
                {"VECTOR_DB_TYPE": "weaviate", "WEAVIATE_URL": "http://localhost:8080"},
                {"VECTOR_DB_TYPE": "pinecone", "PINECONE_API_KEY": "test-key"},
            ]
            
            for config in vector_configs:
                for key, value in config.items():
                    setattr(settings, key, value)
                
                mock_get_settings.return_value = settings
                
                # Test that configuration is accepted
                current_settings = get_settings()
                assert hasattr(current_settings, 'VECTOR_DB_TYPE')
                assert current_settings.VECTOR_DB_TYPE in ["qdrant", "weaviate", "pinecone"]
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_vector_search_performance_benchmark(self):
        """Test vector search performance benchmark"""
        DatabaseFactory.clear_cache()
        
        # This is a placeholder for vector search performance testing
        # In a real implementation, this would:
        # 1. Create test embeddings
        # 2. Perform vector searches
        # 3. Measure response times
        # 4. Validate search quality
        
        import time
        
        # Simulate vector search operations
        start_time = time.time()
        
        # Test database factory performance
        rel_db = DatabaseFactory.create_relational_database()
        cache_db = DatabaseFactory.create_cache_database()
        
        # Test health checks
        await rel_db.health_check()
        await cache_db.health_check()
        
        # Simulate vector operations
        for i in range(10):
            await rel_db.execute_query(f"SELECT {i}")
            await cache_db.set(f"vector_{i}", f"embedding_{i}")
            await cache_db.get(f"vector_{i}")
        
        total_time = time.time() - start_time
        
        # Performance should be reasonable even with multiple operations
        assert total_time < 5.0  # Less than 5 seconds for 10 operations
        
        # Average operation time should be fast
        avg_time = total_time / 30  # 10 queries + 10 sets + 10 gets
        assert avg_time < 0.2  # Less than 200ms per operation 