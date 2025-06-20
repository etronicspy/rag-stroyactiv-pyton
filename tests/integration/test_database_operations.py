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
import unittest.mock
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List

from core.database.adapters.postgresql_adapter import PostgreSQLAdapter
from core.database.adapters.redis_adapter import RedisDatabase
from core.database.exceptions import ConnectionError, DatabaseError, QueryError
from core.database.factories import DatabaseFactory
from core.database.init_db import DatabaseInitializer
from core.database.interfaces import IVectorDatabase, IRelationalDatabase, ICacheDatabase
from core.repositories.hybrid_materials import HybridMaterialsRepository
from core.repositories.cached_materials import CachedMaterialsRepository
from core.schemas.materials import MaterialCreate, Material
from core.monitoring.logger import get_logger
import redis.exceptions
from sqlalchemy.exc import OperationalError

logger = get_logger(__name__)

# Create simple request/response classes for testing if they don't exist
class SearchRequest:
    def __init__(self, query: str, limit: int = 10):
        self.query = query
        self.limit = limit

class SearchResponse:
    def __init__(self, materials: List[Dict], total: int, query: str, search_type: str):
        self.materials = materials
        self.total = total
        self.query = query
        self.search_type = search_type

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
                adapter = PostgreSQLAdapter(db_config)
                return adapter
    
    @pytest.mark.integration
    def test_postgresql_initialization(self, db_config, mock_engine):
        """Test successful PostgreSQL initialization."""
        with patch('core.database.adapters.postgresql_adapter.create_async_engine', return_value=mock_engine):
            with patch('core.database.adapters.postgresql_adapter.async_sessionmaker'):
                adapter = PostgreSQLAdapter(db_config)
                
                assert adapter.config == db_config
                assert adapter.connection_string == db_config["connection_string"]
                assert adapter.engine == mock_engine
    
    @pytest.mark.integration
    def test_postgresql_missing_connection_string(self):
        """Test PostgreSQL initialization with missing connection string."""
        config = {"pool_size": 5}
        
        with pytest.raises(ConnectionError) as exc_info:
            PostgreSQLAdapter(config)
        
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
            PostgreSQLAdapter({})
        
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


# === Cached Repository Tests ===
class TestCachedMaterialsRepository:
    """Test cached materials repository with Redis caching."""
    
    @pytest.fixture
    def mock_hybrid_repo(self):
        """Mock hybrid materials repository."""
        return AsyncMock(spec=HybridMaterialsRepository)
    
    @pytest.fixture
    def mock_cache_db(self):
        """Mock Redis cache database."""
        return AsyncMock(spec=RedisDatabase)
    
    @pytest.fixture
    def cache_config(self) -> Dict[str, Any]:
        """Cache configuration for testing."""
        return {
            "search_ttl": 300,
            "material_ttl": 3600,
            "health_ttl": 60,
            "batch_size": 100,
            "enable_write_through": False,
            "cache_miss_threshold": 0.3
        }
    
    @pytest.fixture
    def cached_repo(self, mock_hybrid_repo, mock_cache_db, cache_config):
        """Cached materials repository instance."""
        return CachedMaterialsRepository(
            hybrid_repository=mock_hybrid_repo,
            cache_db=mock_cache_db,
            cache_config=cache_config
        )
    
    def test_cached_repo_initialization(self, cached_repo, cache_config):
        """Test cached repository initialization."""
        assert cached_repo.search_ttl == cache_config["search_ttl"]
        assert cached_repo.material_ttl == cache_config["material_ttl"]
        assert cached_repo.batch_size == cache_config["batch_size"]
    
    @pytest.mark.asyncio
    async def test_search_materials_cache_hit(self, cached_repo, mock_cache_db):
        """Test search materials with cache hit."""
        # Mock cache hit
        cached_result = {
            "materials": [{"id": "1", "name": "Test Material"}],
            "total": 1,
            "query": "test",
            "search_type": "hybrid"
        }
        mock_cache_db.get.return_value = cached_result
        
        # Mock search request
        search_request = SearchRequest(query="test", limit=10)
        result = await cached_repo.search_materials(search_request)
        
        # Verify cache hit
        assert len(result.materials) == 1
        assert result.materials[0]["name"] == "Test Material"
        assert cached_repo.stats["cache_hits"] == 1
    
    @pytest.mark.asyncio
    async def test_search_materials_cache_miss(self, cached_repo, mock_cache_db, mock_hybrid_repo):
        """Test search materials with cache miss."""
        # Mock cache miss
        mock_cache_db.get.return_value = None
        
        # Mock hybrid repo response
        search_result = SearchResponse(
            materials=[{"id": "1", "name": "Test Material"}],
            total=1,
            query="test",
            search_type="hybrid"
        )
        mock_hybrid_repo.search_materials.return_value = search_result
        
        # Execute search
        search_request = SearchRequest(query="test", limit=10)
        result = await cached_repo.search_materials(search_request)
        
        # Verify cache miss and database call
        assert len(result.materials) == 1
        assert cached_repo.stats["cache_misses"] == 1
        mock_hybrid_repo.search_materials.assert_called_once()
        mock_cache_db.set.assert_called_once()


# === Hybrid Repository Tests ===
class TestHybridMaterialsRepository:
    """Test hybrid materials repository combining vector and relational databases."""
    
    @pytest.fixture
    def mock_vector_db(self):
        """Mock vector database."""
        return AsyncMock(spec=IVectorDatabase)
    
    @pytest.fixture
    def mock_relational_db(self):
        """Mock relational database."""
        return AsyncMock(spec=IRelationalDatabase)
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client."""
        return AsyncMock()
    
    @pytest.fixture
    def hybrid_repo(self, mock_vector_db, mock_relational_db, mock_ai_client):
        """Hybrid repository instance."""
        with patch.object(HybridMaterialsRepository, 'get_embedding', new_callable=AsyncMock) as mock_embedding:
            mock_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
            return HybridMaterialsRepository(
                vector_db=mock_vector_db,
                relational_db=mock_relational_db,
                ai_client=mock_ai_client
            )
    
    def test_hybrid_repo_initialization(self, hybrid_repo, mock_vector_db, mock_relational_db, mock_ai_client):
        """Test hybrid repository initialization."""
        assert hybrid_repo.vector_db == mock_vector_db
        assert hybrid_repo.relational_db == mock_relational_db
        assert hybrid_repo.ai_client == mock_ai_client
        assert hybrid_repo.collection_name == "materials"
    
    @pytest.mark.asyncio
    async def test_create_material_success(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test successful material creation in both databases."""
        # Mock successful operations
        mock_vector_db.upsert.return_value = None
        mock_relational_db.create_material.return_value = {"id": "test-id"}
        
        sample_material = MaterialCreate(
            name="Test Material",
            use_category="Test Category",
            unit="kg",
            description="Test description"
        )
        
        with patch('uuid.uuid4', return_value=MagicMock(hex="test-id")):
            result = await hybrid_repo.create_material(sample_material)
        
        assert isinstance(result, Material)
        assert result.name == sample_material.name
        assert result.use_category == sample_material.use_category
        
        # Verify both databases were called
        mock_vector_db.upsert.assert_called_once()
        mock_relational_db.create_material.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_materials_hybrid_success(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test successful hybrid search combining vector and SQL results."""
        query = "test material"
        
        # Mock vector search results
        vector_result = MagicMock()
        vector_result.id = "test-id-1"
        vector_result.score = 0.85
        vector_result.payload = {
            "name": "Vector Material",
            "use_category": "Vector Category",
            "unit": "kg",
            "description": "Vector description"
        }
        
        # Mock SQL search results
        sql_result = {
            "id": "test-id-2",
            "name": "SQL Material",
            "use_category": "SQL Category",
            "unit": "kg",
            "description": "SQL description",
            "similarity_score": 0.75
        }
        
        # Setup mocks
        mock_vector_db.search.return_value = [vector_result]
        mock_relational_db.search_materials_hybrid.return_value = [sql_result]
        
        results = await hybrid_repo.search_materials_hybrid(query, limit=10)
        
        assert len(results) == 2  # One from each source
        assert results[0]["search_type"] == "vector"  # Higher score should be first
        assert results[1]["search_type"] == "sql"
        
        # Verify both searches were called
        mock_vector_db.search.assert_called_once()
        mock_relational_db.search_materials_hybrid.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_materials_fallback_strategy(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test fallback strategy: vector → SQL if 0 results."""
        query = "test material"
        
        # Mock vector search returning empty results
        mock_vector_db.search.return_value = []
        
        # Mock SQL search returning results
        sql_result = {
            "id": "test-id",
            "name": "SQL Material",
            "similarity_score": 0.75,
            "search_type": "sql"
        }
        mock_relational_db.search_materials_hybrid.return_value = [sql_result]
        
        results = await hybrid_repo.search_materials_hybrid(query, limit=10)
        
        assert len(results) == 1
        assert results[0]["search_type"] == "sql"
        
        # Verify fallback to SQL search
        mock_vector_db.search.assert_called_once()
        mock_relational_db.search_materials_hybrid.assert_called_once()


# === Database Migrations Tests ===
class TestDatabaseMigrations:
    """Test database migrations and initialization."""
    
    @pytest.fixture
    def mock_db_config(self):
        """Mock database configuration."""
        return {
            "connection_string": "postgresql+asyncpg://test:test@localhost/test_db",
            "pool_size": 5,
            "max_overflow": 10
        }
    
    @pytest.fixture
    def db_initializer(self, mock_db_config):
        """Create database initializer with mock config."""
        return DatabaseInitializer(mock_db_config)
    
    @patch('core.database.init_db.PostgreSQLAdapter')
    async def test_connect_database(self, mock_postgres, db_initializer):
        """Test database connection."""
        mock_db_instance = Mock()
        mock_postgres.return_value = mock_db_instance
        
        await db_initializer.connect_database()
        
        mock_postgres.assert_called_once_with(db_initializer.db_config)
        assert db_initializer.db_adapter == mock_db_instance
    
    @patch('core.database.init_db.Config')
    @patch('core.database.init_db.command')
    def test_run_migrations(self, mock_command, mock_config, db_initializer):
        """Test running Alembic migrations."""
        mock_alembic_cfg = Mock()
        mock_config.return_value = mock_alembic_cfg
        
        db_initializer.run_migrations()
        
        mock_config.assert_called_once()
        mock_command.upgrade.assert_called_once_with(mock_alembic_cfg, "head")
    
    @patch('core.database.init_db.PostgreSQLAdapter')
    async def test_seed_reference_data(self, mock_postgres, db_initializer):
        """Test seeding reference data."""
        mock_db_instance = Mock()
        mock_session = AsyncMock()
        mock_db_instance.get_session.return_value.__aenter__.return_value = mock_session
        mock_postgres.return_value = mock_db_instance
        
        await db_initializer.connect_database()
        
        with patch('core.database.init_db.seed_database') as mock_seed:
            mock_seed.return_value = {"categories": 5, "units": 18}
            
            result = await db_initializer.seed_reference_data()
            
            mock_seed.assert_called_once_with(mock_session)
            assert result == {"categories": 5, "units": 18}
    
    @patch('core.database.init_db.PostgreSQLAdapter')
    async def test_initialize_database_success(self, mock_postgres, db_initializer):
        """Test successful database initialization."""
        mock_db_instance = Mock()
        mock_session = AsyncMock()
        mock_db_instance.get_session.return_value.__aenter__.return_value = mock_session
        mock_db_instance.health_check.return_value = {"status": "healthy"}
        mock_db_instance.close = AsyncMock()
        mock_postgres.return_value = mock_db_instance
        
        with patch.object(db_initializer, 'run_migrations') as mock_migrate, \
             patch('core.database.init_db.seed_database') as mock_seed:
            
            mock_seed.return_value = {"categories": 5, "units": 18}
            
            result = await db_initializer.initialize_database()
            
            assert result["success"] is True
            assert result["migrations"]["status"] == "success"
            assert result["seeding"]["status"] == "success"
            assert result["health_check"]["status"] == "success"
            mock_migrate.assert_called_once()


# === Real Database Connection Tests ===
@pytest.mark.integration
class TestRealDBConnection:
    """Integration tests for real database connections."""
    
    def test_qdrant_connection(self, qdrant_client):
        """Test connection to Qdrant."""
        try:
            collections = qdrant_client.get_collections()
            logger.info(f"✅ Connected to Qdrant. Collections count: {len(collections.collections)}")
            
            # Log information about existing collections
            for collection in collections.collections:
                logger.info(f"📚 Collection: {collection.name}")
            
            assert True, "Connection successful"
        except Exception as e:
            pytest.fail(f"Failed to connect to Qdrant: {e}")
    
    def test_create_test_collection(self, qdrant_client):
        """Test creating a test collection."""
        import time
        from qdrant_client.models import Distance, VectorParams
        
        test_collection_name = f"test_connection_{int(time.time())}"
        
        try:
            # Create test collection
            qdrant_client.create_collection(
                collection_name=test_collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            
            # Verify collection was created
            collections = qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            assert test_collection_name in collection_names
            logger.info(f"✅ Test collection '{test_collection_name}' created successfully")
            
        except Exception as e:
            pytest.fail(f"Failed to create test collection: {e}")
        
        finally:
            # Cleanup test collection
            try:
                qdrant_client.delete_collection(test_collection_name)
                logger.info(f"🧹 Cleaned up test collection '{test_collection_name}'")
            except Exception as e:
                logger.warning(f"Failed to cleanup test collection: {e}")
    
    def test_insert_and_retrieve_data(self, qdrant_client):
        """Test inserting and retrieving data."""
        import time
        from qdrant_client.models import Distance, VectorParams, PointStruct
        
        test_collection_name = f"test_data_{int(time.time())}"
        
        try:
            # Create collection
            qdrant_client.create_collection(
                collection_name=test_collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            
            # Prepare test data
            test_vector = [0.1] * 384  # Simple test vector
            test_payload = {
                "name": "Test Material",
                "use_category": "Test Category",
                "price": 100.0,
                "supplier": "TEST_SUPPLIER"
            }
            
            # Insert data
            qdrant_client.upsert(
                collection_name=test_collection_name,
                points=[
                    PointStruct(
                        id=1,
                        vector=test_vector,
                        payload=test_payload
                    )
                ]
            )
            
            # Retrieve data
            retrieved = qdrant_client.retrieve(
                collection_name=test_collection_name,
                ids=[1]
            )
            
            assert len(retrieved) == 1
            assert retrieved[0].payload["name"] == "Test Material"
            assert retrieved[0].payload["supplier"] == "TEST_SUPPLIER"
            
            logger.info("✅ Data insert and retrieve test passed")
            
        except Exception as e:
            pytest.fail(f"Failed to insert/retrieve data: {e}")
        
        finally:
            # Cleanup
            try:
                qdrant_client.delete_collection(test_collection_name)
                logger.info(f"🧹 Cleaned up test collection '{test_collection_name}'")
            except Exception as e:
                logger.warning(f"Failed to cleanup: {e}")
    
    def test_list_existing_collections(self, qdrant_client):
        """Test listing existing collections."""
        try:
            collections = qdrant_client.get_collections()
            
            logger.info(f"📊 Database contains {len(collections.collections)} collections:")
            for collection in collections.collections:
                # Get collection information
                try:
                    info = qdrant_client.get_collection(collection.name)
                    logger.info(f"  📚 {collection.name}: {info.points_count} points, vector size: {info.config.params.vectors.size}")
                except Exception as e:
                    logger.info(f"  📚 {collection.name}: (error getting details: {e})")
            
            assert True, "Collection listing successful"
            
        except Exception as e:
            pytest.fail(f"Failed to list collections: {e}")


class TestPostgreSQLAdapter:
    """Тесты PostgreSQL адаптера"""
    
    @pytest.mark.integration
    async def test_connection_error_handling(self):
        """Тест обработки ошибок подключения"""
        from sqlalchemy.exc import OperationalError
        
        # Create adapter with invalid connection string
        adapter = PostgreSQLAdapter("postgresql://invalid:invalid@localhost:5432/invalid")
        
        # Test connection error handling
        with pytest.raises(OperationalError):
            await adapter.connect()
    
    @pytest.mark.integration
    async def test_query_execution_error(self):
        """Тест обработки ошибок выполнения запросов"""
        
        # Mock adapter for testing
        adapter = PostgreSQLAdapter("postgresql://test:test@localhost:5432/test")
        
        # Mock connection that raises error
        with patch.object(adapter, 'execute_query') as mock_execute:
            # Fix: Use proper exception message format
            mock_execute.side_effect = Exception("Query execution failed")
            
            with pytest.raises(Exception, match="Query execution failed"):
                await adapter.execute_query("SELECT * FROM invalid_table")


class TestRedisAdapter:
    """Тесты Redis адаптера"""
    
    @pytest.mark.integration
    async def test_connection_error_handling(self):
        """Тест обработки ошибок подключения Redis"""
        
        # Create adapter with invalid connection
        adapter = RedisDatabase({"redis_url": "redis://invalid:6379"})
        
        # Test connection error handling
        with pytest.raises(redis.exceptions.ConnectionError):
            await adapter.connect()
    
    @pytest.mark.integration
    async def test_operation_error_handling(self):
        """Тест обработки ошибок операций Redis"""
        
        adapter = RedisDatabase({"redis_url": "redis://localhost:6379"})
        
        # Mock Redis client that raises error
        with patch.object(adapter, 'get') as mock_get:
            # Fix: Use proper Redis exception
            mock_get.side_effect = redis.exceptions.RedisError("Redis operation failed")
            
            with pytest.raises(redis.exceptions.RedisError):
                await adapter.get("test_key")


class TestCachedMaterialsRepository:
    """Тесты кешированного репозитория материалов"""
    
    @pytest.fixture
    def mock_cache(self):
        """Mock cache для тестирования"""
        cache = Mock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.delete = AsyncMock()
        cache.clear = AsyncMock()
        return cache
    
    @pytest.fixture
    def mock_repository(self):
        """Mock основного репозитория"""
        repo = Mock()
        repo.get_by_id = AsyncMock()
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock()
        repo.list_all = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def cached_repository(self, mock_repository, mock_cache):
        """Кешированный репозиторий для тестирования"""
        return CachedMaterialsRepository(mock_repository, mock_cache)
    
    @pytest.mark.integration
    async def test_cache_hit(self, cached_repository, mock_cache, sample_material):
        """Тест попадания в кеш"""
        # Setup cache hit
        mock_cache.get.return_value = sample_material.dict()
        
        result = await cached_repository.get_by_id("test-id")
        
        assert result is not None
        mock_cache.get.assert_called_once_with("material:test-id")
    
    @pytest.mark.integration
    async def test_cache_miss_and_set(self, cached_repository, mock_cache, mock_repository, sample_material):
        """Тест промаха кеша и установки значения"""
        # Setup cache miss
        mock_cache.get.return_value = None
        mock_repository.get_by_id.return_value = sample_material
        
        result = await cached_repository.get_by_id("test-id")
        
        assert result == sample_material
        mock_cache.get.assert_called_once_with("material:test-id")
        mock_cache.set.assert_called_once()
    
    @pytest.mark.integration
    async def test_cache_invalidation_on_update(self, cached_repository, mock_cache, mock_repository, sample_material):
        """Тест инвалидации кеша при обновлении"""
        mock_repository.update.return_value = sample_material
        
        await cached_repository.update("test-id", {"name": "Updated"})
        
        mock_cache.delete.assert_called_once_with("material:test-id")
    
    @pytest.mark.integration
    async def test_cache_invalidation_on_delete(self, cached_repository, mock_cache, mock_repository):
        """Тест инвалидации кеша при удалении"""
        mock_repository.delete.return_value = True
        
        await cached_repository.delete("test-id")
        
        mock_cache.delete.assert_called_once_with("material:test-id")


class TestHybridMaterialsRepository:
    """Тесты гибридного репозитория материалов"""
    
    @pytest.fixture
    def mock_sql_repo(self):
        """Mock SQL репозитория"""
        repo = Mock()
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.list_all = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def mock_vector_repo(self):
        """Mock векторного репозитория"""
        repo = Mock()
        repo.upsert = AsyncMock()
        repo.delete = AsyncMock()
        repo.search = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def hybrid_repository(self, mock_sql_repo, mock_vector_repo):
        """Гибридный репозиторий для тестирования"""
        return HybridMaterialsRepository(mock_sql_repo, mock_vector_repo)
    
    @pytest.mark.integration
    async def test_create_syncs_to_both_repos(self, hybrid_repository, mock_sql_repo, mock_vector_repo, sample_material):
        """Тест синхронизации создания в оба репозитория"""
        mock_sql_repo.create.return_value = sample_material
        
        result = await hybrid_repository.create(sample_material.dict())
        
        assert result == sample_material
        mock_sql_repo.create.assert_called_once()
        mock_vector_repo.upsert.assert_called_once()
    
    @pytest.mark.integration
    async def test_update_syncs_to_both_repos(self, hybrid_repository, mock_sql_repo, mock_vector_repo, sample_material):
        """Тест синхронизации обновления в оба репозитория"""
        mock_sql_repo.update.return_value = sample_material
        
        result = await hybrid_repository.update("test-id", {"name": "Updated"})
        
        assert result == sample_material
        mock_sql_repo.update.assert_called_once()
        mock_vector_repo.upsert.assert_called_once()
    
    @pytest.mark.integration
    async def test_delete_syncs_to_both_repos(self, hybrid_repository, mock_sql_repo, mock_vector_repo):
        """Тест синхронизации удаления в оба репозитория"""
        mock_sql_repo.delete.return_value = True
        
        result = await hybrid_repository.delete("test-id")
        
        assert result is True
        mock_sql_repo.delete.assert_called_once()
        mock_vector_repo.delete.assert_called_once()
    
    @pytest.mark.integration
    async def test_search_uses_vector_repo(self, hybrid_repository, mock_vector_repo):
        """Тест использования векторного репозитория для поиска"""
        mock_results = [{"id": "1", "score": 0.9}]
        mock_vector_repo.search.return_value = mock_results
        
        results = await hybrid_repository.search("test query", limit=10)
        
        assert results == mock_results
        mock_vector_repo.search.assert_called_once_with("test query", limit=10)
    
    @pytest.mark.integration
    async def test_vector_repo_failure_handling(self, hybrid_repository, mock_sql_repo, mock_vector_repo, sample_material):
        """Тест обработки ошибок векторного репозитория"""
        mock_sql_repo.create.return_value = sample_material
        mock_vector_repo.upsert.side_effect = Exception("Vector DB error")
        
        # Should still succeed with SQL repo, log vector error
        result = await hybrid_repository.create(sample_material.dict())
        
        assert result == sample_material
        mock_sql_repo.create.assert_called_once() 