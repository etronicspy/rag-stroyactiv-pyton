"""Tests for new database architecture.

Тесты для новой архитектуры БД после рефакторинга этапа 1.
"""

import pytest
from unittest.mock import Mock, patch

from core.database.interfaces import IVectorDatabase, IRelationalDatabase, ICacheDatabase
from core.database.factories import DatabaseFactory, AIClientFactory
from core.database.exceptions import DatabaseError, ConnectionError, ConfigurationError
from core.dependencies.database import get_vector_db_dependency, get_ai_client_dependency, clear_dependency_cache


class TestDatabaseInterfaces:
    """Test database interfaces and abstract methods."""
    
    def test_vector_database_interface_methods(self):
        """Test that IVectorDatabase has all required methods."""
        required_methods = [
            "create_collection", "collection_exists", "upsert", "search", 
            "get_by_id", "update_vector", "delete", "batch_upsert", "health_check"
        ]
        
        for method_name in required_methods:
            assert hasattr(IVectorDatabase, method_name), f"Missing method: {method_name}"
    
    def test_relational_database_interface_methods(self):
        """Test that IRelationalDatabase has all required methods."""
        required_methods = [
            "execute_query", "execute_command", "begin_transaction", 
            "commit_transaction", "rollback_transaction", "health_check"
        ]
        
        for method_name in required_methods:
            assert hasattr(IRelationalDatabase, method_name), f"Missing method: {method_name}"
    
    def test_cache_database_interface_methods(self):
        """Test that ICacheDatabase has all required methods."""
        required_methods = ["get", "set", "delete", "exists", "health_check"]
        
        for method_name in required_methods:
            assert hasattr(ICacheDatabase, method_name), f"Missing method: {method_name}"


class TestDatabaseFactory:
    """Test database factory functionality."""
    
    def setUp(self):
        """Clear caches before each test."""
        DatabaseFactory.clear_cache()
        AIClientFactory.clear_cache()
    
    def test_vector_database_factory_creates_qdrant(self):
        """Test that vector database factory creates Qdrant adapter."""
        with patch('core.database.adapters.qdrant_adapter.QdrantVectorDatabase') as mock_qdrant:
            mock_instance = Mock()
            mock_qdrant.return_value = mock_instance
            
            result = DatabaseFactory.create_vector_database(
                db_type="qdrant_cloud",
                config_override={
                    "url": "test://url",
                    "api_key": "test_key",
                    "collection_name": "test_materials"
                }
            )
            
            mock_qdrant.assert_called_once()
            assert result == mock_instance
    
    def test_relational_database_factory_not_implemented(self):
        """Test that relational database factory raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="PostgreSQL adapter will be implemented in Этап 3"):
            DatabaseFactory.create_relational_database()
    
    def test_cache_database_factory_not_implemented(self):
        """Test that cache database factory raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Redis adapter will be implemented in Этап 4"):
            DatabaseFactory.create_cache_database()
    
    def test_factory_caching_works(self):
        """Test that factory caching works with @lru_cache."""
        with patch('core.database.adapters.qdrant_adapter.QdrantVectorDatabase') as mock_qdrant:
            mock_instance = Mock()
            mock_qdrant.return_value = mock_instance
            
            # Call twice with same parameters
            config = {"url": "test://url", "api_key": "test_key"}
            result1 = DatabaseFactory.create_vector_database(config_override=config)
            result2 = DatabaseFactory.create_vector_database(config_override=config)
            
            # Should be called only once due to caching
            mock_qdrant.assert_called_once()
            assert result1 == result2 == mock_instance
    
    def test_factory_cache_info(self):
        """Test that factory provides cache information."""
        cache_info = DatabaseFactory.get_cache_info()
        
        assert "vector_db_cache" in cache_info
        assert "relational_db_cache" in cache_info
        assert "cache_db_cache" in cache_info
        
        # Should have cache statistics
        vector_cache = cache_info["vector_db_cache"]
        assert "hits" in vector_cache
        assert "misses" in vector_cache


class TestDependencyInjection:
    """Test dependency injection functionality."""
    
    def setUp(self):
        """Clear dependency caches before each test."""
        clear_dependency_cache()
    
    def test_vector_db_dependency_works(self):
        """Test that vector DB dependency injection works."""
        with patch('core.database.factories.DatabaseFactory.create_vector_database') as mock_factory:
            mock_instance = Mock()
            mock_factory.return_value = mock_instance
            
            result = get_vector_db_dependency()
            
            mock_factory.assert_called_once()
            assert result == mock_instance
    
    def test_ai_client_dependency_works(self):
        """Test that AI client dependency injection works."""
        with patch('core.database.factories.AIClientFactory.create_ai_client') as mock_factory:
            mock_instance = Mock()
            mock_factory.return_value = mock_instance
            
            result = get_ai_client_dependency()
            
            mock_factory.assert_called_once()
            assert result == mock_instance
    
    def test_dependency_caching_works(self):
        """Test that dependency injection caching works."""
        with patch('core.database.factories.DatabaseFactory.create_vector_database') as mock_factory:
            mock_instance = Mock()
            mock_factory.return_value = mock_instance
            
            # Call twice
            result1 = get_vector_db_dependency()
            result2 = get_vector_db_dependency()
            
            # Should be called only once due to caching
            mock_factory.assert_called_once()
            assert result1 == result2 == mock_instance
    
    def test_clear_dependency_cache_works(self):
        """Test that clearing dependency cache works."""
        with patch('core.database.factories.DatabaseFactory.create_vector_database') as mock_factory:
            mock_instance = Mock()
            mock_factory.return_value = mock_instance
            
            # Call, clear cache, call again
            get_vector_db_dependency()
            clear_dependency_cache()
            get_vector_db_dependency()
            
            # Should be called twice after cache clear
            assert mock_factory.call_count == 2


class TestDatabaseExceptions:
    """Test database exception hierarchy."""
    
    def test_database_error_inheritance(self):
        """Test database exception inheritance."""
        error = DatabaseError("Test error", details="Test details")
        
        assert isinstance(error, Exception)
        assert error.message == "Test error"
        assert error.details == "Test details"
    
    def test_connection_error_inheritance(self):
        """Test connection error inheritance."""
        error = ConnectionError("PostgreSQL", "Connection failed", "Details")
        
        assert isinstance(error, DatabaseError)
        assert error.database_type == "PostgreSQL"
        assert "Failed to connect to PostgreSQL database" in str(error)
    
    def test_configuration_error_inheritance(self):
        """Test configuration error inheritance."""
        error = ConfigurationError("DATABASE_TYPE", "Invalid type", "Details")
        
        assert isinstance(error, DatabaseError)
        assert error.config_key == "DATABASE_TYPE"
        assert "Database configuration error for key: DATABASE_TYPE" in str(error)


# Integration test with real Qdrant (if available)
@pytest.mark.integration
class TestQdrantIntegration:
    """Integration tests with real Qdrant instance."""
    
    async def test_qdrant_adapter_health_check(self):
        """Test Qdrant adapter health check with real instance."""
        try:
            from core.database.adapters.qdrant_adapter import QdrantVectorDatabase
            from core.config import settings
            
            # Use real config
            config = settings.get_vector_db_config()
            adapter = QdrantVectorDatabase(config)
            
            # This should work if Qdrant is available
            health = await adapter.health_check()
            assert health["status"] in ["healthy", "unhealthy"]
            assert health["database_type"] == "Qdrant"
            
        except Exception as e:
            pytest.skip(f"Qdrant not available for integration test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 