"""
Tests for Qdrant-only mode with mock databases
Тесты для режима только с Qdrant и mock БД
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from core.config import get_settings
from core.database.factories import DatabaseFactory
from core.database.adapters.mock_adapters import MockRelationalAdapter, MockCacheAdapter
from core.dependencies import get_relational_db_dependency, get_cache_db_dependency


@pytest.fixture
def qdrant_only_settings():
    """Override settings for Qdrant-only mode"""
    with patch('core.config.get_settings') as mock_settings:
        settings = get_settings()
        settings.QDRANT_ONLY_MODE = True
        settings.ENABLE_FALLBACK_DATABASES = True
        settings.DISABLE_REDIS_CONNECTION = True
        settings.DISABLE_POSTGRESQL_CONNECTION = True
        mock_settings.return_value = settings
        yield settings


class TestQdrantOnlyMode:
    """Test Qdrant-only mode functionality"""
    
    def test_relational_database_returns_mock(self, qdrant_only_settings):
        """Test that relational database factory returns mock adapter"""
        db_client = DatabaseFactory.create_relational_database()
        
        assert isinstance(db_client, MockRelationalAdapter)
        assert hasattr(db_client, 'mock_db')
        
    def test_cache_database_returns_mock(self, qdrant_only_settings):
        """Test that cache database factory returns mock adapter"""
        cache_client = DatabaseFactory.create_cache_database()
        
        assert isinstance(cache_client, MockCacheAdapter)
        assert hasattr(cache_client, 'mock_redis')
    
    @pytest.mark.asyncio
    async def test_mock_relational_adapter_basic_operations(self, qdrant_only_settings):
        """Test basic operations on mock relational adapter"""
        db_client = DatabaseFactory.create_relational_database()
        
        # Test connection
        connected = await db_client.connect()
        assert connected is True
        
        # Test health check
        health = await db_client.health_check()
        assert health['status'] == 'healthy'
        assert health['type'] == 'mock_postgresql'
        
        # Test material operations
        material_data = {
            "name": "Test Material",
            "description": "Test description",
            "category": "Test Category",
            "price": 100.0
        }
        
        created_material = await db_client.create_material(material_data)
        assert created_material['name'] == material_data['name']
        assert 'id' in created_material
        
        # Test get materials
        materials = await db_client.get_materials()
        assert isinstance(materials, list)
        
        # Test search
        search_results = await db_client.search_materials_sql("test")
        assert isinstance(search_results, list)
        
        # Test disconnection
        disconnected = await db_client.disconnect()
        assert disconnected is True
    
    @pytest.mark.asyncio
    async def test_mock_cache_adapter_basic_operations(self, qdrant_only_settings):
        """Test basic operations on mock cache adapter"""
        cache_client = DatabaseFactory.create_cache_database()
        
        # Test connection
        connected = await cache_client.connect()
        assert connected is True
        
        # Test health check
        health = await cache_client.health_check()
        assert health['status'] == 'healthy'
        assert health['type'] == 'mock_redis'
        
        # Test cache operations
        key = "test_key"
        value = "test_value"
        
        # Test set
        set_result = await cache_client.set(key, value)
        assert set_result is True
        
        # Test get
        get_result = await cache_client.get(key)
        assert get_result == value
        
        # Test exists
        exists_result = await cache_client.exists(key)
        assert exists_result is True
        
        # Test delete
        delete_result = await cache_client.delete(key)
        assert delete_result == 1
        
        # Test ping
        ping_result = await cache_client.ping()
        assert ping_result is True
        
        # Test disconnection
        disconnected = await cache_client.disconnect()
        assert disconnected is True
    
    def test_dependency_injection_returns_mocks(self, qdrant_only_settings):
        """Test that dependency injection returns mock adapters"""
        # Clear caches first
        from core.dependencies import clear_dependency_cache
        clear_dependency_cache()
        
        # Test relational DB dependency
        rel_db = get_relational_db_dependency()
        assert isinstance(rel_db, MockRelationalAdapter)
        
        # Test cache DB dependency
        cache_db = get_cache_db_dependency()
        assert isinstance(cache_db, MockCacheAdapter)
    
    @pytest.mark.asyncio
    async def test_concurrent_mock_operations(self, qdrant_only_settings):
        """Test concurrent operations on mock adapters"""
        db_client = DatabaseFactory.create_relational_database()
        cache_client = DatabaseFactory.create_cache_database()
        
        # Test concurrent DB operations
        async def db_operation(i):
            material_data = {
                "name": f"Material {i}",
                "description": f"Description {i}",
                "category": f"Category {i}",
                "price": i * 10.0
            }
            return await db_client.create_material(material_data)
        
        # Test concurrent cache operations
        async def cache_operation(i):
            key = f"key_{i}"
            value = f"value_{i}"
            await cache_client.set(key, value)
            return await cache_client.get(key)
        
        # Run concurrent operations
        db_tasks = [db_operation(i) for i in range(5)]
        cache_tasks = [cache_operation(i) for i in range(5)]
        
        db_results = await asyncio.gather(*db_tasks)
        cache_results = await asyncio.gather(*cache_tasks)
        
        # Verify results
        assert len(db_results) == 5
        assert len(cache_results) == 5
        
        for i, result in enumerate(db_results):
            assert result['name'] == f"Material {i}"
        
        for i, result in enumerate(cache_results):
            assert result == f"value_{i}"
    
    @pytest.mark.asyncio
    async def test_mock_ai_embedding_generation(self, qdrant_only_settings):
        """Test mock AI client embedding generation"""
        from core.database.mocks import create_mock_ai_client
        
        ai_client = create_mock_ai_client()
        
        # Test single embedding
        text = "test material description"
        embedding = await ai_client.get_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # OpenAI embedding size
        assert all(isinstance(x, float) for x in embedding)
        
        # Test batch embeddings
        texts = ["material 1", "material 2", "material 3"]
        embeddings = await ai_client.get_embeddings_batch(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
        
        # Test deterministic generation (same input = same output)
        embedding1 = await ai_client.get_embedding(text)
        embedding2 = await ai_client.get_embedding(text)
        assert embedding1 == embedding2
    
    def test_settings_validation_qdrant_only_mode(self, qdrant_only_settings):
        """Test that settings are correctly configured for Qdrant-only mode"""
        settings = qdrant_only_settings
        
        assert settings.QDRANT_ONLY_MODE is True
        assert settings.ENABLE_FALLBACK_DATABASES is True
        assert settings.DISABLE_REDIS_CONNECTION is True
        assert settings.DISABLE_POSTGRESQL_CONNECTION is True
        
        # Verify required Qdrant settings are present
        assert hasattr(settings, 'QDRANT_URL')
        assert hasattr(settings, 'QDRANT_API_KEY')
        assert hasattr(settings, 'QDRANT_COLLECTION_NAME')
        
        # Verify OpenAI settings for embeddings
        assert hasattr(settings, 'OPENAI_API_KEY')
        assert hasattr(settings, 'OPENAI_MODEL') 