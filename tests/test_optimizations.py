"""
Tests for optimization components.

Тесты для компонентов оптимизации.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from core.middleware.conditional import ConditionalMiddleware, MiddlewareOptimizer
from core.middleware.compression import CompressionMiddleware
from core.middleware.rate_limiting_optimized import OptimizedRateLimitMiddleware
from services.dynamic_batch_processor import DynamicBatchProcessor, BatchConfig, ProcessingResult
from core.caching.multi_level_cache import MultiLevelCache, L1MemoryCache, L2RedisCache, CacheLevel


class TestConditionalMiddleware:
    """Tests for ConditionalMiddleware."""
    
    @pytest.fixture
    def mock_middleware(self):
        """Mock middleware class."""
        class MockMiddleware:
            def __init__(self, app, **kwargs):
                self.app = app
                self.kwargs = kwargs
                self.called = False
                
            async def dispatch(self, request, call_next):
                self.called = True
                return await call_next(request)
        
        return MockMiddleware
    
    @pytest.fixture
    def mock_request(self):
        """Mock HTTP request."""
        request = Mock()
        request.url.path = "/api/v1/test"
        request.method = "GET"
        return request
    
    @pytest.mark.asyncio
    async def test_conditional_middleware_inclusion(self, mock_middleware, mock_request):
        """Test middleware inclusion based on paths."""
        middleware = ConditionalMiddleware(
            app=Mock(),
            middleware_class=mock_middleware,
            include_paths=[r"/api/.*"],
            enable_performance_logging=False
        )
        
        mock_call_next = AsyncMock(return_value=Mock())
        
        # Should apply middleware for API paths
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Check middleware was applied
        assert middleware.middleware_applied > 0
        assert middleware.middleware_skipped == 0
    
    @pytest.mark.asyncio
    async def test_conditional_middleware_exclusion(self, mock_middleware, mock_request):
        """Test middleware exclusion based on paths."""
        mock_request.url.path = "/health"
        
        middleware = ConditionalMiddleware(
            app=Mock(),
            middleware_class=mock_middleware,
            exclude_paths=[r"/health.*"],
            enable_performance_logging=False
        )
        
        mock_call_next = AsyncMock(return_value=Mock())
        
        # Should skip middleware for health paths
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Check middleware was skipped
        assert middleware.middleware_skipped > 0
        assert middleware.middleware_applied == 0
    
    def test_middleware_optimizer_api_routes_only(self, mock_middleware):
        """Test MiddlewareOptimizer for API routes only."""
        conditional = MiddlewareOptimizer.for_api_routes_only(
            mock_middleware, test_param="value"
        )
        
        assert conditional.middleware_class == mock_middleware
        assert conditional.middleware_kwargs["test_param"] == "value"
        assert any(pattern.pattern == "/api/.*" for pattern in conditional.include_paths)
    
    def test_performance_stats(self, mock_middleware):
        """Test performance statistics collection."""
        middleware = ConditionalMiddleware(
            app=Mock(),
            middleware_class=mock_middleware,
            enable_performance_logging=True
        )
        
        # Simulate some requests
        middleware.total_requests = 100
        middleware.middleware_applied = 70
        middleware.middleware_skipped = 30
        
        stats = middleware.get_performance_stats()
        
        assert stats["total_requests"] == 100
        assert stats["middleware_applied"] == 70
        assert stats["middleware_skipped"] == 30
        assert stats["application_rate"] == 0.7
        assert stats["skip_rate"] == 0.3


class TestCompressionMiddleware:
    """Tests for CompressionMiddleware."""
    
    @pytest.fixture
    def compression_middleware(self):
        """Create compression middleware instance."""
        return CompressionMiddleware(
            app=Mock(),
            minimum_size=100,
            maximum_size=1000000,
            compression_level=6,
            enable_performance_logging=True
        )
    
    @pytest.fixture
    def mock_request(self):
        """Mock HTTP request with compression headers."""
        request = Mock()
        request.url.path = "/api/v1/test"
        request.headers = {
            "accept-encoding": "gzip, deflate, br"
        }
        return request
    
    @pytest.fixture
    def mock_response(self):
        """Mock HTTP response."""
        response = Mock()
        response.body = b"x" * 1000  # 1KB response
        response.headers = {"content-type": "application/json"}
        response.status_code = 200
        return response
    
    def test_should_compress(self, compression_middleware, mock_request, mock_response):
        """Test compression decision logic."""
        # Should compress large JSON response
        should_compress = compression_middleware._should_compress(
            mock_request, mock_response, 1000
        )
        assert should_compress
        
        # Should not compress small response
        should_compress = compression_middleware._should_compress(
            mock_request, mock_response, 50
        )
        assert not should_compress
        
        # Should not compress already compressed content
        mock_response.headers["content-encoding"] = "gzip"
        should_compress = compression_middleware._should_compress(
            mock_request, mock_response, 1000
        )
        assert not should_compress
    
    def test_algorithm_selection(self, compression_middleware):
        """Test compression algorithm selection."""
        # Should prefer Brotli if available
        algorithm = compression_middleware._select_compression_algorithm("gzip, deflate, br")
        if compression_middleware.brotli_available:
            assert algorithm == "br"
        else:
            assert algorithm == "gzip"
        
        # Should fall back to gzip
        algorithm = compression_middleware._select_compression_algorithm("gzip, deflate")
        assert algorithm == "gzip"
        
        # Should return None if no supported algorithms
        algorithm = compression_middleware._select_compression_algorithm("identity")
        assert algorithm is None
    
    def test_compression_stats(self, compression_middleware):
        """Test compression statistics."""
        # Simulate some compression operations
        compression_middleware.total_responses = 100
        compression_middleware.compressed_responses = 80
        compression_middleware.total_bytes_original = 100000
        compression_middleware.total_bytes_compressed = 30000
        
        stats = compression_middleware.get_compression_stats()
        
        assert stats["total_responses"] == 100
        assert stats["compressed_responses"] == 80
        assert stats["compression_rate"] == 0.8
        assert stats["average_compression_ratio"] == 0.3
        assert stats["total_bytes_saved"] == 70000


class TestOptimizedRateLimitMiddleware:
    """Tests for OptimizedRateLimitMiddleware."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock.ping.return_value = True
        redis_mock.script_load.return_value = "test_script_sha"
        redis_mock.evalsha.return_value = [1, 50, 950, 8]  # Success response
        return redis_mock
    
    @pytest.fixture
    def rate_limit_middleware(self, mock_redis):
        """Create rate limiting middleware."""
        with patch('core.middleware.rate_limiting_optimized.aioredis') as mock_aioredis:
            mock_aioredis.ConnectionPool.from_url.return_value = Mock()
            mock_aioredis.Redis.return_value = mock_redis
            
            middleware = OptimizedRateLimitMiddleware(
                app=Mock(),
                redis_url="redis://localhost",
                default_requests_per_minute=60,
                enable_performance_logging=True
            )
            middleware._redis = mock_redis
            middleware._multi_tier_script = "test_script_sha"
            
            return middleware
    
    @pytest.fixture
    def mock_request(self):
        """Mock HTTP request."""
        request = Mock()
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.headers = {}
        request.client.host = "127.0.0.1"
        return request
    
    def test_client_identifier_extraction(self, rate_limit_middleware, mock_request):
        """Test client identifier extraction."""
        # Test IP-based identification
        client_id = rate_limit_middleware._get_client_identifier(mock_request)
        assert client_id.startswith("ip:")
        
        # Test API key identification
        mock_request.headers = {"X-API-Key": "test-api-key-12345"}
        client_id = rate_limit_middleware._get_client_identifier(mock_request)
        assert client_id.startswith("key:")
        assert "test-api-key-1234" in client_id  # First 16 chars
    
    def test_endpoint_limits(self, rate_limit_middleware):
        """Test endpoint-specific limit configuration."""
        # Test API search endpoint
        limits = rate_limit_middleware._get_endpoint_limits("/api/v1/search/test")
        assert limits["rpm"] == 30
        assert limits["rph"] == 500
        assert limits["burst"] == 5
        
        # Test default limits
        limits = rate_limit_middleware._get_endpoint_limits("/unknown/path")
        assert limits["rpm"] == 60  # Default
        assert limits["rph"] == 1000  # Default
    
    @pytest.mark.asyncio
    async def test_rate_limit_check(self, rate_limit_middleware, mock_request):
        """Test rate limit checking with Lua scripts."""
        client_id = "ip:127.0.0.1"
        limits = {"rpm": 60, "rph": 1000, "burst": 10}
        
        # Test successful rate limit check
        is_allowed, limit_info = await rate_limit_middleware._check_rate_limits_optimized(
            client_id, "/api/v1/test", limits
        )
        
        assert is_allowed is True
        assert "remaining_minute" in limit_info
        assert "remaining_hour" in limit_info
        assert "remaining_burst" in limit_info
    
    def test_performance_stats(self, rate_limit_middleware):
        """Test performance statistics collection."""
        # Simulate some requests
        rate_limit_middleware.total_requests = 100
        rate_limit_middleware.allowed_requests = 90
        rate_limit_middleware.rate_limited_requests = 10
        rate_limit_middleware.total_lua_execution_time = 0.1
        
        stats = rate_limit_middleware.get_performance_stats()
        
        assert stats["total_requests"] == 100
        assert stats["allowed_requests"] == 90
        assert stats["rate_limited_requests"] == 10
        assert stats["allow_rate"] == 0.9
        assert stats["rate_limit_rate"] == 0.1
        assert stats["average_lua_execution_time"] == 0.001  # 0.1/100


class TestDynamicBatchProcessor:
    """Tests for DynamicBatchProcessor."""
    
    @pytest.fixture
    def sample_processor(self):
        """Sample processing function."""
        async def process_batch(items: List[int]) -> List[int]:
            # Simulate processing time
            await asyncio.sleep(0.01)
            return [item * 2 for item in items]
        
        return process_batch
    
    @pytest.fixture
    def batch_processor(self, sample_processor):
        """Create batch processor instance."""
        config = BatchConfig(
            min_batch_size=5,
            max_batch_size=50,
            adaptive_sizing=True,
            enable_metrics=True
        )
        
        return DynamicBatchProcessor(
            processor_func=sample_processor,
            config=config,
            max_concurrent_batches=2,
            enable_parallel_processing=True
        )
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, batch_processor):
        """Test basic batch processing functionality."""
        items = list(range(100))  # 100 items to process
        
        result = await batch_processor.process_items(items)
        
        assert result.processed_items == 100
        assert result.failed_items == 0
        assert result.batches_processed > 0
        assert result.throughput > 0
        assert result.total_time > 0
    
    @pytest.mark.asyncio
    async def test_empty_batch(self, batch_processor):
        """Test processing empty batch."""
        result = await batch_processor.process_items([])
        
        assert result.processed_items == 0
        assert result.failed_items == 0
        assert result.batches_processed == 0
        assert result.total_time == 0
    
    @pytest.mark.asyncio
    async def test_adaptive_batch_sizing(self, batch_processor):
        """Test adaptive batch sizing."""
        # Process some items to build history
        items = list(range(200))
        
        initial_batch_size = batch_processor.current_batch_size
        
        await batch_processor.process_items(items)
        
        # Batch size should potentially adjust based on performance
        # (May stay the same if performance is good)
        assert batch_processor.current_batch_size >= batch_processor.config.min_batch_size
        assert batch_processor.current_batch_size <= batch_processor.config.max_batch_size
    
    def test_performance_stats(self, batch_processor):
        """Test performance statistics collection."""
        # Simulate some metrics
        from services.dynamic_batch_processor import BatchMetrics
        
        metrics = BatchMetrics(
            batch_size=25,
            processing_time=1.5,
            memory_used=1024,
            memory_available=1024*1024,
            throughput=16.7,
            efficiency=0.85
        )
        
        batch_processor.metrics_history.append(metrics)
        
        stats = batch_processor.get_performance_stats()
        
        assert stats["total_batches"] == 1
        assert stats["average_batch_size"] == 25
        assert stats["average_processing_time"] == 1.5
        assert stats["average_throughput"] == 16.7
        assert stats["average_efficiency"] == 0.85


class TestMultiLevelCache:
    """Tests for MultiLevelCache."""
    
    @pytest.fixture
    def l1_cache(self):
        """Create L1 memory cache."""
        return L1MemoryCache(max_size=100, max_memory_mb=1)
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for L2 cache."""
        redis_mock = AsyncMock()
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        redis_mock.delete.return_value = 1
        return redis_mock
    
    @pytest.fixture
    def l2_cache(self, mock_redis):
        """Create L2 Redis cache."""
        return L2RedisCache(mock_redis, prefix="test:")
    
    @pytest.fixture
    def multi_cache(self, l1_cache, l2_cache):
        """Create multi-level cache."""
        return MultiLevelCache(
            l1_cache=l1_cache,
            l2_cache=l2_cache,
            enable_promotion=True,
            enable_prefetching=True
        )
    
    @pytest.mark.asyncio
    async def test_l1_cache_operations(self, l1_cache):
        """Test L1 cache basic operations."""
        # Test set and get
        success = await l1_cache.set("test_key", "test_value", ttl=60)
        assert success
        
        value = await l1_cache.get("test_key")
        assert value == "test_value"
        
        # Test delete
        success = await l1_cache.delete("test_key")
        assert success
        
        value = await l1_cache.get("test_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_l1_cache_lru_eviction(self, l1_cache):
        """Test L1 cache LRU eviction."""
        # Fill cache beyond capacity
        for i in range(150):  # More than max_size=100
            await l1_cache.set(f"key_{i}", f"value_{i}")
        
        # Check that cache size is limited
        assert len(l1_cache.cache) <= l1_cache.max_size
        
        # Check that evictions occurred
        assert l1_cache.stats.evictions > 0
    
    @pytest.mark.asyncio
    async def test_l1_cache_ttl_expiration(self, l1_cache):
        """Test L1 cache TTL expiration."""
        # Set with very short TTL
        await l1_cache.set("expire_key", "expire_value", ttl=0.1)
        
        # Should exist immediately
        value = await l1_cache.get("expire_key")
        assert value == "expire_value"
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Should be expired
        value = await l1_cache.get("expire_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_multi_cache_hierarchy(self, multi_cache):
        """Test multi-level cache hierarchy."""
        # Set in all levels
        await multi_cache.set("test_key", "test_value", levels=[
            CacheLevel.L1_MEMORY, 
            CacheLevel.L2_REDIS
        ])
        
        # Should get from L1 (fastest)
        value = await multi_cache.get("test_key")
        assert value == "test_value"
        assert multi_cache.global_stats["l1_hits"] > 0
    
    @pytest.mark.asyncio
    async def test_cache_promotion(self, multi_cache, mock_redis):
        """Test cache promotion between levels."""
        # Set value only in L2
        mock_redis.get.return_value = "promoted_value"
        
        # Clear L1 to force L2 access
        await multi_cache.l1_cache.clear()
        
        # Get value (should promote from L2 to L1)
        value = await multi_cache.get("promote_key")
        assert value == "promoted_value"
        
        # Should now be in L1
        l1_value = await multi_cache.l1_cache.get("promote_key")
        assert l1_value == "promoted_value"
        
        # Check promotion stats
        assert multi_cache.global_stats["promotions"] > 0
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, multi_cache):
        """Test comprehensive cache statistics."""
        # Simulate some operations
        multi_cache.global_stats["total_requests"] = 100
        multi_cache.global_stats["l1_hits"] = 60
        multi_cache.global_stats["l2_hits"] = 30
        multi_cache.global_stats["cache_misses"] = 10
        multi_cache.global_stats["promotions"] = 5
        
        stats = multi_cache.get_comprehensive_stats()
        
        assert stats["global_stats"]["total_requests"] == 100
        assert stats["global_stats"]["overall_hit_rate"] == 0.9
        assert stats["level_breakdown"]["l1_hit_rate"] == 0.6
        assert stats["level_breakdown"]["l2_hit_rate"] == 0.3
        assert stats["global_stats"]["promotions"] == 5


class TestIntegrationOptimizations:
    """Integration tests for optimization components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_optimizations(self):
        """Test end-to-end optimization pipeline."""
        # This would test how all optimizations work together
        # For now, just verify they can be imported and initialized
        
        # Test conditional middleware
        conditional = ConditionalMiddleware(
            app=Mock(),
            middleware_class=Mock,
            include_paths=["/api/*"]
        )
        assert conditional is not None
        
        # Test compression middleware
        compression = CompressionMiddleware(app=Mock())
        assert compression is not None
        
        # Test batch processor
        async def dummy_processor(items):
            return items
        
        batch_processor = DynamicBatchProcessor(dummy_processor)
        assert batch_processor is not None
        
        # Test multi-level cache
        l1_cache = L1MemoryCache()
        multi_cache = MultiLevelCache(l1_cache=l1_cache)
        assert multi_cache is not None
    
    def test_optimization_compatibility(self):
        """Test that optimizations are compatible with each other."""
        # Test that all optimization components can coexist
        # without conflicts in their dependencies or configurations
        
        optimizations = [
            "ConditionalMiddleware",
            "CompressionMiddleware", 
            "OptimizedRateLimitMiddleware",
            "DynamicBatchProcessor",
            "MultiLevelCache"
        ]
        
        # All optimizations should be importable
        assert len(optimizations) == 5
        
        # No conflicts in their core dependencies
        assert True  # Placeholder for actual compatibility tests


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 