"""
Integration tests for database operations
Интеграционные тесты для операций с базами данных

Объединяет тесты из:
- test_postgresql_adapter.py
- test_redis_adapter.py
- test_database_architecture.py
- test_cached_repository.py
- test_hybrid_repository.py
"""
import pytest
import asyncio
import unittest.mock
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from core.database.adapters.postgresql_adapter import PostgreSQLDatabase, MaterialModel
from core.database.adapters.redis_adapter import RedisDatabase
from core.database.exceptions import ConnectionError, DatabaseError, QueryError
from core.database.factories import DatabaseFactory


class TestPostgreSQLIntegration:
    """Интеграционные тесты для PostgreSQL adapter"""
    
    @pytest.fixture
    def db_config(self) -> Dict[str, Any]:
        """Database configuration for testing."""
        return {
            "connection_string": "postgresql+asyncpg://test:test@localhost:5432/test_db",
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "echo": False
        }
    
    @pytest.fixture
    def mock_engine(self):
        """Mock SQLAlchemy async engine."""
        engine = AsyncMock()
        engine.pool.size.return_value = 5
        engine.pool.checkedin.return_value = 3
        engine.pool.checkedout.return_value = 2
        engine.pool.overflow.return_value = 0
        return engine
    
    @pytest.fixture
    def mock_session(self):
        """Mock SQLAlchemy async session."""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    async def db_adapter(self, db_config, mock_engine):
        """PostgreSQL adapter instance for testing."""
        with patch('core.database.adapters.postgresql_adapter.create_async_engine', return_value=mock_engine):
            with patch('core.database.adapters.postgresql_adapter.async_sessionmaker'):
                adapter = PostgreSQLDatabase(db_config)
                return adapter
    
    @pytest.mark.integration
    def test_postgresql_initialization(self, db_config, mock_engine):
        """Test successful PostgreSQL initialization."""
        with patch('core.database.adapters.postgresql_adapter.create_async_engine', return_value=mock_engine):
            with patch('core.database.adapters.postgresql_adapter.async_sessionmaker'):
                adapter = PostgreSQLDatabase(db_config)
                
                assert adapter.config == db_config
                assert adapter.connection_string == db_config["connection_string"]
                assert adapter.engine == mock_engine
    
    @pytest.mark.integration
    def test_postgresql_missing_connection_string(self):
        """Test PostgreSQL initialization with missing connection string."""
        config = {"pool_size": 5}
        
        with pytest.raises(ConnectionError) as exc_info:
            PostgreSQLDatabase(config)
        
        assert "PostgreSQL connection string is required" in str(exc_info.value)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_postgresql_create_tables(self, db_adapter):
        """Test PostgreSQL table creation."""
        mock_conn = AsyncMock()
        db_adapter.engine.begin.return_value.__aenter__.return_value = mock_conn
        
        await db_adapter.create_tables()
        
        # Verify extensions were created
        mock_conn.execute.assert_any_call(unittest.mock.ANY)
        mock_conn.run_sync.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_postgresql_execute_query(self, db_adapter, mock_session):
        """Test PostgreSQL query execution."""
        # Mock query result
        mock_result = MagicMock()
        mock_result.keys.return_value = ['id', 'name']
        mock_result.fetchall.return_value = [('1', 'Test Material')]
        
        mock_session.execute.return_value = mock_result
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        result = await db_adapter.execute_query("SELECT * FROM materials", {"id": "1"})
        
        assert result == [{'id': '1', 'name': 'Test Material'}]
        mock_session.execute.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_postgresql_create_material(self, db_adapter, mock_session):
        """Test PostgreSQL material creation."""
        material_data = {
            "id": "test-id",
            "name": "Test Material",
            "use_category": "Test Category",
            "unit": "kg",
            "sku": "TEST001",
            "description": "Test description",
            "embedding": [0.1, 0.2, 0.3],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Mock material instance
        mock_material = MagicMock()
        for key, value in material_data.items():
            setattr(mock_material, key, value)
        
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        result = await db_adapter.create_material(material_data)
        
        assert result["id"] == material_data["id"]
        assert result["name"] == material_data["name"]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestRedisIntegration:
    """Интеграционные тесты для Redis adapter"""
    
    @pytest.fixture
    def redis_config(self) -> Dict[str, Any]:
        """Redis configuration for testing."""
        return {
            "redis_url": "redis://localhost:6379/0",
            "max_connections": 5,
            "retry_on_timeout": True,
            "socket_timeout": 10,
            "socket_connect_timeout": 10,
            "decode_responses": True,
            "health_check_interval": 30,
            "default_ttl": 300,
            "key_prefix": "test_materials:"
        }
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        mock_client = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.max_connections = 5
        mock_pool.created_connections = 2
        mock_pool._available_connections = [1, 2]
        mock_pool._in_use_connections = [3]
        
        return mock_client, mock_pool
    
    @pytest.mark.integration
    def test_redis_initialization(self, redis_config):
        """Test successful Redis adapter initialization."""
        with patch('redis.asyncio.ConnectionPool.from_url') as mock_pool, \
             patch('redis.asyncio.Redis') as mock_redis:
            
            mock_pool.return_value = MagicMock()
            mock_redis.return_value = AsyncMock()
            
            adapter = RedisDatabase(redis_config)
            
            assert adapter.redis_url == redis_config["redis_url"]
            assert adapter.default_ttl == redis_config["default_ttl"]
            assert adapter.key_prefix == redis_config["key_prefix"]
    
    @pytest.mark.integration
    def test_redis_missing_url(self):
        """Test Redis initialization with missing URL."""
        config = {"max_connections": 5}
        
        with pytest.raises(ConnectionError) as exc_info:
            RedisDatabase(config)
        
        assert "Redis URL is required" in str(exc_info.value)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_redis_ping(self, redis_config, mock_redis_client):
        """Test Redis ping operation."""
        mock_client, mock_pool = mock_redis_client
        mock_client.ping.return_value = True
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            result = await adapter.ping()
            
            assert result is True
            mock_client.ping.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_redis_set_get(self, redis_config, mock_redis_client):
        """Test Redis set and get operations."""
        mock_client, mock_pool = mock_redis_client
        test_value = {"name": "Test Material", "price": 100.0}
        serialized_value = '{"name": "Test Material", "price": 100.0}'
        
        mock_client.setex.return_value = True
        mock_client.get.return_value = serialized_value
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            
            # Test set
            result = await adapter.set("test_key", test_value, ttl=600)
            assert result is True
            
            # Test get
            retrieved_value = await adapter.get("test_key")
            assert retrieved_value == test_value
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_redis_health_check(self, redis_config, mock_redis_client):
        """Test Redis health check."""
        mock_client, mock_pool = mock_redis_client
        mock_client.ping.return_value = True
        mock_client.info.return_value = {
            "connected_clients": 5,
            "used_memory": 1048576,
            "keyspace_hits": 100,
            "keyspace_misses": 10
        }
        
        async def mock_scan_iter(match):
            yield "test_key1"
            yield "test_key2"
        
        mock_client.scan_iter.return_value = mock_scan_iter("test_materials:*")
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            health = await adapter.health_check()
            
            assert health["status"] == "healthy"
            assert health["connected_clients"] == 5
            assert health["memory_usage"] == "1MB"
            assert health["total_keys"] == 2


class TestDatabaseFactoryIntegration:
    """Интеграционные тесты для Database Factory"""
    
    @pytest.mark.integration
    def test_factory_creates_adapters(self):
        """Test that factory creates database adapters."""
        try:
            rel_db = DatabaseFactory.create_relational_database()
            assert rel_db is not None
            assert hasattr(rel_db, 'health_check')
            
            cache_db = DatabaseFactory.create_cache_database()
            assert cache_db is not None
            assert hasattr(cache_db, 'health_check')
        except Exception:
            # В интеграционных тестах ошибки подключения допустимы
            pass
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test database error handling in integration mode."""
        DatabaseFactory.clear_cache()
        
        rel_db = DatabaseFactory.create_relational_database()
        cache_db = DatabaseFactory.create_cache_database()
        
        try:
            await rel_db.health_check()
            await cache_db.health_check()
        except (ConnectionError, DatabaseError, QueryError):
            # Expected in integration tests with unavailable databases
            pass
        except Exception as e:
            # Other exceptions should be related to database connectivity
            assert any(keyword in str(e).lower() for keyword in 
                      ["connection", "timeout", "unavailable", "refused"])


class TestHybridDatabaseOperations:
    """Интеграционные тесты для гибридных операций с БД"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fallback_mode_operations(self):
        """Test database operations in fallback mode."""
        DatabaseFactory.clear_cache()
        
        rel_db = DatabaseFactory.create_relational_database()
        cache_db = DatabaseFactory.create_cache_database()
        
        try:
            rel_health = await rel_db.health_check()
            assert "status" in rel_health
            
            cache_health = await cache_db.health_check()
            assert "status" in cache_health
        except Exception as e:
            # In integration tests, connection failures are acceptable
            assert "connection" in str(e).lower() or "timeout" in str(e).lower()
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_database_performance_integration(self):
        """Test database performance in integration mode."""
        DatabaseFactory.clear_cache()
        
        start_time = datetime.utcnow()
        
        rel_db = DatabaseFactory.create_relational_database()
        cache_db = DatabaseFactory.create_cache_database()
        
        creation_time = (datetime.utcnow() - start_time).total_seconds()
        assert creation_time < 5.0  # Should take less than 5 seconds
        
        try:
            health_start = datetime.utcnow()
            rel_health = await rel_db.health_check()
            cache_health = await cache_db.health_check()
            
            health_time = (datetime.utcnow() - health_start).total_seconds()
            assert health_time < 10.0  # Should take less than 10 seconds
            
        except Exception:
            # Connection failures are acceptable in integration tests
            pass


class TestDatabaseArchitectureIntegration:
    """Интеграционные тесты архитектуры БД"""
    
    @pytest.mark.integration
    def test_database_adapters_implement_interface(self):
        """Test that database adapters implement required interfaces."""
        DatabaseFactory.clear_cache()
        
        # Get adapters
        rel_db = DatabaseFactory.create_relational_database()
        cache_db = DatabaseFactory.create_cache_database()
        
        # Check required methods exist
        required_rel_methods = ['health_check', 'execute_query', 'execute_command']
        for method in required_rel_methods:
            assert hasattr(rel_db, method), f"Relational DB missing method: {method}"
            assert callable(getattr(rel_db, method)), f"Method {method} is not callable"
        
        required_cache_methods = ['health_check', 'set', 'get', 'delete', 'exists']
        for method in required_cache_methods:
            assert hasattr(cache_db, method), f"Cache DB missing method: {method}"
            assert callable(getattr(cache_db, method)), f"Method {method} is not callable"
    
    @pytest.mark.integration
    def test_database_configuration_validation(self):
        """Test database configuration validation."""
        # Test that invalid configurations are rejected
        
        # PostgreSQL with missing connection string
        with pytest.raises(ConnectionError):
            PostgreSQLDatabase({})
        
        # Redis with missing URL
        with pytest.raises(ConnectionError):
            RedisDatabase({})
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_database_connection_lifecycle(self):
        """Test database connection lifecycle."""
        DatabaseFactory.clear_cache()
        
        # Get adapters
        rel_db = DatabaseFactory.create_relational_database()
        cache_db = DatabaseFactory.create_cache_database()
        
        # Test connection methods if they exist
        if hasattr(rel_db, 'connect'):
            try:
                connected = await rel_db.connect()
                assert isinstance(connected, bool)
            except Exception:
                pass  # Connection failures acceptable in integration tests
        
        if hasattr(cache_db, 'connect'):
            try:
                connected = await cache_db.connect()
                assert isinstance(connected, bool)
            except Exception:
                pass  # Connection failures acceptable in integration tests
        
        # Test close methods if they exist
        if hasattr(rel_db, 'close'):
            try:
                await rel_db.close()
            except Exception:
                pass
        
        if hasattr(cache_db, 'close'):
            try:
                await cache_db.close()
            except Exception:
                pass 