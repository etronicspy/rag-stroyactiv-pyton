"""Tests for cached materials repository.

Тесты для кеширующего репозитория материалов с интеллектуальным кешированием.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from core.repositories.cached_materials import CachedMaterialsRepository
from core.repositories.hybrid_materials import HybridMaterialsRepository
from core.database.adapters.redis_adapter import RedisDatabase
from core.database.exceptions import DatabaseError
from core.schemas.materials import MaterialCreate, MaterialResponse, MaterialSearchRequest
from core.schemas.search import SearchResponse


class TestCachedMaterialsRepository:
    """Test cached materials repository."""
    
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
    def sample_material(self) -> MaterialResponse:
        """Sample material for testing."""
        return MaterialResponse(
            id="test-material-1",
            name="Test Cement",
            description="High quality cement for construction",
            category="cement",
            price=150.0,
            unit="bag",
            supplier="Test Supplier",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_search_request(self) -> MaterialSearchRequest:
        """Sample search request for testing."""
        return MaterialSearchRequest(
            query="cement",
            limit=10,
            search_type="hybrid"
        )
    
    @pytest.fixture
    def cached_repo(self, mock_hybrid_repo, mock_cache_db, cache_config):
        """Cached materials repository instance."""
        return CachedMaterialsRepository(
            hybrid_repository=mock_hybrid_repo,
            cache_db=mock_cache_db,
            cache_config=cache_config
        )
    
    # === Initialization tests ===
    
    def test_init_success(self, mock_hybrid_repo, mock_cache_db, cache_config):
        """Test successful initialization."""
        repo = CachedMaterialsRepository(
            hybrid_repository=mock_hybrid_repo,
            cache_db=mock_cache_db,
            cache_config=cache_config
        )
        
        assert repo.hybrid_repo == mock_hybrid_repo
        assert repo.cache_db == mock_cache_db
        assert repo.search_ttl == cache_config["search_ttl"]
        assert repo.material_ttl == cache_config["material_ttl"]
        assert repo.health_ttl == cache_config["health_ttl"]
        assert repo.batch_size == cache_config["batch_size"]
        assert repo.enable_write_through == cache_config["enable_write_through"]
        assert repo.cache_miss_threshold == cache_config["cache_miss_threshold"]
    
    def test_init_default_config(self, mock_hybrid_repo, mock_cache_db):
        """Test initialization with default configuration."""
        repo = CachedMaterialsRepository(
            hybrid_repository=mock_hybrid_repo,
            cache_db=mock_cache_db
        )
        
        assert repo.search_ttl == 300
        assert repo.material_ttl == 3600
        assert repo.health_ttl == 60
        assert repo.batch_size == 100
        assert repo.enable_write_through is False
        assert repo.cache_miss_threshold == 0.3
    
    # === Search operations tests ===
    
    @pytest.mark.asyncio
    async def test_search_materials_cache_hit(
        self, 
        cached_repo, 
        sample_search_request, 
        sample_material
    ):
        """Test search materials with cache hit."""
        # Setup cache hit
        cached_result = SearchResponse(
            materials=[sample_material],
            total=1,
            query=sample_search_request.query,
            search_type=sample_search_request.search_type,
            response_time_ms=50.0
        )
        
        cached_repo.cache_db.get.return_value = cached_result.dict()
        
        # Execute search
        result = await cached_repo.search_materials(sample_search_request)
        
        # Verify cache hit
        assert result.materials == [sample_material]
        assert result.total == 1
        assert cached_repo.stats["cache_hits"] == 1
        assert cached_repo.stats["cache_misses"] == 0
        
        # Verify hybrid repo was not called
        cached_repo.hybrid_repo.search_materials.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_search_materials_cache_miss(
        self, 
        cached_repo, 
        sample_search_request, 
        sample_material
    ):
        """Test search materials with cache miss."""
        # Setup cache miss
        cached_repo.cache_db.get.return_value = None
        
        # Setup hybrid repo response
        search_result = SearchResponse(
            materials=[sample_material],
            total=1,
            query=sample_search_request.query,
            search_type=sample_search_request.search_type,
            response_time_ms=100.0
        )
        cached_repo.hybrid_repo.search_materials.return_value = search_result
        
        # Execute search
        result = await cached_repo.search_materials(sample_search_request)
        
        # Verify cache miss and database call
        assert result.materials == [sample_material]
        assert result.total == 1
        assert cached_repo.stats["cache_hits"] == 0
        assert cached_repo.stats["cache_misses"] == 1
        assert cached_repo.stats["cache_writes"] == 1
        
        # Verify hybrid repo was called
        cached_repo.hybrid_repo.search_materials.assert_called_once_with(sample_search_request)
        
        # Verify cache was updated
        cached_repo.cache_db.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_materials_no_cache(
        self, 
        cached_repo, 
        sample_search_request, 
        sample_material
    ):
        """Test search materials with caching disabled."""
        # Setup hybrid repo response
        search_result = SearchResponse(
            materials=[sample_material],
            total=1,
            query=sample_search_request.query,
            search_type=sample_search_request.search_type,
            response_time_ms=100.0
        )
        cached_repo.hybrid_repo.search_materials.return_value = search_result
        
        # Execute search without cache
        result = await cached_repo.search_materials(sample_search_request, use_cache=False)
        
        # Verify no cache operations
        assert result.materials == [sample_material]
        assert cached_repo.stats["cache_hits"] == 0
        assert cached_repo.stats["cache_misses"] == 0
        
        # Verify hybrid repo was called
        cached_repo.hybrid_repo.search_materials.assert_called_once_with(sample_search_request)
        
        # Verify cache was not accessed
        cached_repo.cache_db.get.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_vector_search_with_cache(self, cached_repo, sample_material):
        """Test vector search with caching."""
        # Setup cache miss and hybrid repo response
        cached_repo.cache_db.get.return_value = None
        cached_repo.hybrid_repo.vector_search.return_value = [sample_material]
        
        # Execute vector search
        result = await cached_repo.vector_search("cement", limit=5, threshold=0.8)
        
        # Verify result and cache operations
        assert result == [sample_material]
        assert cached_repo.stats["cache_misses"] == 1
        assert cached_repo.stats["cache_writes"] == 1
        
        # Verify hybrid repo was called with correct parameters
        cached_repo.hybrid_repo.vector_search.assert_called_once_with("cement", 5, 0.8)
    
    @pytest.mark.asyncio
    async def test_sql_search_with_cache(self, cached_repo, sample_material):
        """Test SQL search with caching."""
        # Setup cache miss and hybrid repo response
        cached_repo.cache_db.get.return_value = None
        cached_repo.hybrid_repo.sql_search.return_value = [sample_material]
        
        # Execute SQL search
        result = await cached_repo.sql_search("cement", limit=15)
        
        # Verify result and cache operations
        assert result == [sample_material]
        assert cached_repo.stats["cache_misses"] == 1
        assert cached_repo.stats["cache_writes"] == 1
        
        # Verify hybrid repo was called with correct parameters
        cached_repo.hybrid_repo.sql_search.assert_called_once_with("cement", 15)
    
    # === CRUD operations tests ===
    
    @pytest.mark.asyncio
    async def test_create_material(self, cached_repo, sample_material):
        """Test create material with cache invalidation."""
        # Setup hybrid repo response
        material_create = MaterialCreate(
            name="New Cement",
            description="Brand new cement",
            category="cement",
            price=200.0,
            unit="bag",
            supplier="New Supplier"
        )
        cached_repo.hybrid_repo.create_material.return_value = sample_material
        
        # Execute create
        result = await cached_repo.create_material(material_create)
        
        # Verify result and cache operations
        assert result == sample_material
        assert cached_repo.stats["cache_writes"] == 1
        
        # Verify hybrid repo was called
        cached_repo.hybrid_repo.create_material.assert_called_once_with(material_create, True)
        
        # Verify cache operations
        cached_repo.cache_db.set.assert_called_once()
        cached_repo.cache_db.delete_pattern.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_material_cache_hit(self, cached_repo, sample_material):
        """Test get material with cache hit."""
        # Setup cache hit
        cached_repo.cache_db.get.return_value = sample_material.dict()
        
        # Execute get
        result = await cached_repo.get_material("test-material-1")
        
        # Verify cache hit
        assert result.id == sample_material.id
        assert result.name == sample_material.name
        assert cached_repo.stats["cache_hits"] == 1
        assert cached_repo.stats["cache_misses"] == 0
        
        # Verify hybrid repo was not called
        cached_repo.hybrid_repo.get_material.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_material_cache_miss(self, cached_repo, sample_material):
        """Test get material with cache miss."""
        # Setup cache miss
        cached_repo.cache_db.get.return_value = None
        cached_repo.hybrid_repo.get_material.return_value = sample_material
        
        # Execute get
        result = await cached_repo.get_material("test-material-1")
        
        # Verify cache miss and database call
        assert result == sample_material
        assert cached_repo.stats["cache_hits"] == 0
        assert cached_repo.stats["cache_misses"] == 1
        assert cached_repo.stats["cache_writes"] == 1
        
        # Verify hybrid repo was called
        cached_repo.hybrid_repo.get_material.assert_called_once_with("test-material-1")
    
    @pytest.mark.asyncio
    async def test_update_material(self, cached_repo, sample_material):
        """Test update material with cache invalidation."""
        # Setup hybrid repo response
        updates = {"price": 175.0, "name": "Updated Cement"}
        updated_material = MaterialResponse(**{**sample_material.dict(), **updates})
        cached_repo.hybrid_repo.update_material.return_value = updated_material
        
        # Execute update
        result = await cached_repo.update_material("test-material-1", updates)
        
        # Verify result and cache operations
        assert result == updated_material
        assert cached_repo.stats["cache_writes"] == 1
        
        # Verify hybrid repo was called
        cached_repo.hybrid_repo.update_material.assert_called_once_with(
            "test-material-1", updates, True
        )
        
        # Verify cache operations
        cached_repo.cache_db.set.assert_called_once()
        cached_repo.cache_db.delete_pattern.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_material(self, cached_repo, sample_material):
        """Test delete material with cache invalidation."""
        # Setup get material for cache invalidation
        cached_repo.get_material = AsyncMock(return_value=sample_material)
        cached_repo.hybrid_repo.delete_material.return_value = True
        
        # Execute delete
        result = await cached_repo.delete_material("test-material-1")
        
        # Verify result and cache operations
        assert result is True
        
        # Verify hybrid repo was called
        cached_repo.hybrid_repo.delete_material.assert_called_once_with("test-material-1")
        
        # Verify cache operations
        cached_repo.cache_db.delete.assert_called_once()
        cached_repo.cache_db.delete_pattern.assert_called()
    
    # === Batch operations tests ===
    
    @pytest.mark.asyncio
    async def test_batch_create_materials(self, cached_repo, sample_material):
        """Test batch create materials with caching."""
        # Setup materials to create
        materials_to_create = [
            MaterialCreate(name=f"Material {i}", description=f"Description {i}", 
                         category="cement", price=100.0 + i, unit="bag", supplier="Supplier")
            for i in range(3)
        ]
        
        # Setup hybrid repo response
        created_materials = [
            MaterialResponse(id=f"material-{i}", **material.dict(), 
                           created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            for i, material in enumerate(materials_to_create)
        ]
        cached_repo.hybrid_repo.batch_create_materials.return_value = created_materials
        
        # Execute batch create
        result = await cached_repo.batch_create_materials(materials_to_create)
        
        # Verify result and cache operations
        assert len(result) == 3
        assert cached_repo.stats["cache_writes"] == 3
        
        # Verify hybrid repo was called
        cached_repo.hybrid_repo.batch_create_materials.assert_called_once_with(
            materials_to_create, True
        )
        
        # Verify cache invalidation
        cached_repo.cache_db.delete_pattern.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_materials_batch_mixed_cache(self, cached_repo, sample_material):
        """Test batch get materials with mixed cache hits/misses."""
        # Setup material IDs
        material_ids = ["material-1", "material-2", "material-3"]
        
        # Setup cache responses (hit, miss, hit)
        cached_materials = [
            sample_material.dict(),  # Cache hit
            None,                    # Cache miss
            sample_material.dict()   # Cache hit
        ]
        cached_repo.cache_db.mget.return_value = cached_materials
        
        # Setup hybrid repo response for missing material
        missing_material = MaterialResponse(
            id="material-2", name="Missing Material", description="Was not cached",
            category="cement", price=200.0, unit="bag", supplier="Supplier",
            created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )
        cached_repo.hybrid_repo.get_materials_batch.return_value = [missing_material]
        
        # Execute batch get
        result = await cached_repo.get_materials_batch(material_ids)
        
        # Verify result and cache statistics
        assert len(result) == 3
        assert cached_repo.stats["cache_hits"] == 2
        assert cached_repo.stats["cache_misses"] == 1
        assert cached_repo.stats["cache_writes"] == 1
        
        # Verify hybrid repo was called for missing material
        cached_repo.hybrid_repo.get_materials_batch.assert_called_once_with(["material-2"])
    
    # === Cache management tests ===
    
    @pytest.mark.asyncio
    async def test_warm_cache(self, cached_repo, sample_material):
        """Test cache warming with popular queries and materials."""
        # Setup popular queries and materials
        popular_queries = ["cement", "concrete", "steel"]
        popular_material_ids = ["material-1", "material-2"]
        
        # Setup search responses
        search_response = SearchResponse(
            materials=[sample_material], total=1, query="test",
            search_type="hybrid", response_time_ms=50.0
        )
        cached_repo.search_materials = AsyncMock(return_value=search_response)
        cached_repo.get_materials_batch = AsyncMock(return_value=[sample_material])
        
        # Execute cache warming
        stats = await cached_repo.warm_cache(
            popular_queries=popular_queries,
            material_ids=popular_material_ids
        )
        
        # Verify warming statistics
        assert stats["queries_cached"] == 3
        assert stats["materials_cached"] == 1
        assert stats["errors"] == 0
        
        # Verify search was called for each query
        assert cached_repo.search_materials.call_count == 3
        
        # Verify materials batch get was called
        cached_repo.get_materials_batch.assert_called_once_with(popular_material_ids, use_cache=True)
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, cached_repo):
        """Test cache clearing."""
        # Setup cache clear response
        cached_repo.cache_db.delete_pattern.return_value = 50
        cached_repo.cache_db.clear_cache.return_value = 100
        
        # Test pattern-based clearing
        result = await cached_repo.clear_cache("search:*")
        assert result == 50
        cached_repo.cache_db.delete_pattern.assert_called_once_with("search:*")
        
        # Test full cache clearing
        result = await cached_repo.clear_cache()
        assert result == 100
        cached_repo.cache_db.clear_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, cached_repo):
        """Test cache statistics retrieval."""
        # Setup cache statistics
        cached_repo.stats["cache_hits"] = 100
        cached_repo.stats["cache_misses"] = 20
        cached_repo.stats["cache_writes"] = 50
        cached_repo.stats["cache_errors"] = 2
        
        # Setup Redis health check
        redis_health = {
            "status": "healthy",
            "database_type": "Redis",
            "ping_time_seconds": 0.001
        }
        cached_repo.cache_db.health_check.return_value = redis_health
        
        # Execute get cache stats
        stats = await cached_repo.get_cache_stats()
        
        # Verify statistics
        assert stats["cache_performance"]["hit_rate"] == 100 / 120  # 100 hits / 120 total
        assert stats["cache_performance"]["total_hits"] == 100
        assert stats["cache_performance"]["total_misses"] == 20
        assert stats["cache_performance"]["total_writes"] == 50
        assert stats["cache_performance"]["total_errors"] == 2
        
        assert stats["cache_configuration"]["search_ttl"] == 300
        assert stats["cache_configuration"]["material_ttl"] == 3600
        assert stats["redis_status"] == redis_health
    
    @pytest.mark.asyncio
    async def test_reset_stats(self, cached_repo):
        """Test cache statistics reset."""
        # Set some statistics
        cached_repo.stats["cache_hits"] = 100
        cached_repo.stats["cache_misses"] = 20
        
        # Reset statistics
        await cached_repo.reset_stats()
        
        # Verify reset
        assert cached_repo.stats["cache_hits"] == 0
        assert cached_repo.stats["cache_misses"] == 0
        assert cached_repo.stats["cache_writes"] == 0
        assert cached_repo.stats["cache_errors"] == 0
    
    # === Health check tests ===
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, cached_repo):
        """Test successful health check."""
        # Setup component health checks
        hybrid_health = {"status": "healthy", "database_type": "HybridMaterialsRepository"}
        cache_health = {"status": "healthy", "database_type": "Redis"}
        
        cached_repo.hybrid_repo.health_check.return_value = hybrid_health
        cached_repo.cache_db.health_check.return_value = cache_health
        cached_repo.cache_db.set.return_value = True
        cached_repo.cache_db.get.return_value = {"test": True}
        cached_repo.cache_db.delete.return_value = True
        
        # Mock get_cache_stats
        cached_repo.get_cache_stats = AsyncMock(return_value={"hit_rate": 0.8})
        
        # Execute health check
        health_status = await cached_repo.health_check()
        
        # Verify health status
        assert health_status["status"] == "healthy"
        assert health_status["repository_type"] == "CachedMaterialsRepository"
        assert "response_time_seconds" in health_status
        assert health_status["components"]["hybrid_repository"] == hybrid_health
        assert health_status["components"]["cache_database"] == cache_health
        assert health_status["components"]["cache_operations"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, cached_repo):
        """Test health check with component failure."""
        # Setup component health checks with failure
        hybrid_health = {"status": "unhealthy", "error": "Database connection failed"}
        cache_health = {"status": "healthy", "database_type": "Redis"}
        
        cached_repo.hybrid_repo.health_check.return_value = hybrid_health
        cached_repo.cache_db.health_check.return_value = cache_health
        cached_repo.cache_db.set.return_value = True
        cached_repo.cache_db.get.return_value = {"test": True}
        cached_repo.cache_db.delete.return_value = True
        
        # Mock get_cache_stats
        cached_repo.get_cache_stats = AsyncMock(return_value={"hit_rate": 0.8})
        
        # Execute health check
        health_status = await cached_repo.health_check()
        
        # Verify health status shows unhealthy due to hybrid repo failure
        assert health_status["status"] == "unhealthy"
        assert health_status["components"]["hybrid_repository"] == hybrid_health
    
    # === Error handling tests ===
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, cached_repo, sample_search_request):
        """Test error handling in search operations."""
        # Setup cache error
        cached_repo.cache_db.get.side_effect = Exception("Cache error")
        
        # Execute search
        with pytest.raises(DatabaseError) as exc_info:
            await cached_repo.search_materials(sample_search_request)
        
        assert "Search with caching failed" in str(exc_info.value)
        assert cached_repo.stats["cache_errors"] == 1
    
    @pytest.mark.asyncio
    async def test_create_error_handling(self, cached_repo):
        """Test error handling in create operations."""
        # Setup hybrid repo error
        material_create = MaterialCreate(
            name="Test", description="Test", category="cement",
            price=100.0, unit="bag", supplier="Supplier"
        )
        cached_repo.hybrid_repo.create_material.side_effect = Exception("Database error")
        
        # Execute create
        with pytest.raises(DatabaseError) as exc_info:
            await cached_repo.create_material(material_create)
        
        assert "Create material with caching failed" in str(exc_info.value)
        assert cached_repo.stats["cache_errors"] == 1
    
    # === Cache key generation tests ===
    
    def test_generate_search_cache_key(self, cached_repo, sample_search_request):
        """Test search cache key generation."""
        key1 = cached_repo._generate_search_cache_key(sample_search_request)
        key2 = cached_repo._generate_search_cache_key(sample_search_request)
        
        # Same request should generate same key
        assert key1 == key2
        assert key1.startswith("search:")
        
        # Different request should generate different key
        different_request = MaterialSearchRequest(
            query="steel",
            limit=20,
            search_type="vector"
        )
        key3 = cached_repo._generate_search_cache_key(different_request)
        assert key1 != key3
    
    def test_hash_query(self, cached_repo):
        """Test query hashing."""
        hash1 = cached_repo._hash_query("cement")
        hash2 = cached_repo._hash_query("cement")
        hash3 = cached_repo._hash_query("concrete")
        
        # Same query should generate same hash
        assert hash1 == hash2
        
        # Different query should generate different hash
        assert hash1 != hash3
        
        # Hash should be 16 characters
        assert len(hash1) == 16 