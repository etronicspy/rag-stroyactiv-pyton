"""
Performance tests for optimization components
Тесты производительности для компонентов оптимизации

Объединяет тесты из:
- test_optimizations.py
- test_dynamic_pool_manager.py
- test_redis_serialization_optimization.py
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from core.middleware.conditional import ConditionalMiddleware, MiddlewareOptimizer
from core.middleware.compression import CompressionMiddleware
from core.middleware.rate_limiting_optimized import OptimizedRateLimitMiddleware
from services.dynamic_batch_processor import DynamicBatchProcessor, BatchConfig
from core.caching.multi_level_cache import MultiLevelCache, L1MemoryCache, L2RedisCache


class TestCompressionPerformance:
    """Tests for CompressionMiddleware performance."""
    
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
    
    @pytest.mark.performance
    def test_compression_decision_performance(self, compression_middleware):
        """Test compression decision performance."""
        mock_request = Mock()
        mock_request.url.path = "/api/v1/test"
        mock_request.headers = {"accept-encoding": "gzip, deflate, br"}
        
        mock_response = Mock()
        mock_response.body = b"x" * 10000  # 10KB response
        mock_response.headers = {"content-type": "application/json"}
        mock_response.status_code = 200
        
        start_time = time.time()
        
        # Test compression decision for many responses
        for _ in range(1000):
            should_compress = compression_middleware._should_compress(
                mock_request, mock_response, 10000
            )
        
        decision_time = time.time() - start_time
        
        # Should make compression decisions quickly
        assert decision_time < 0.1  # Less than 100ms for 1000 decisions
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_compression_throughput(self, compression_middleware):
        """Test compression throughput."""
        # Create test data of various sizes
        test_data = [
            b"x" * 1000,    # 1KB
            b"y" * 10000,   # 10KB
            b"z" * 100000,  # 100KB
        ]
        
        total_compressed = 0
        start_time = time.time()
        
        for data in test_data:
            compressed = compression_middleware._compress_data(data, "gzip")
            total_compressed += len(compressed)
        
        compression_time = time.time() - start_time
        
        # Should compress data efficiently
        assert compression_time < 1.0  # Less than 1 second
        assert total_compressed < sum(len(data) for data in test_data)  # Should reduce size


class TestRateLimitPerformance:
    """Tests for OptimizedRateLimitMiddleware performance."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for performance testing."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "5"  # Current request count
        mock_redis.setex.return_value = True
        mock_redis.incr.return_value = 6
        mock_redis.ttl.return_value = 60
        return mock_redis
    
    @pytest.fixture
    def rate_limit_middleware(self, mock_redis):
        """Create optimized rate limit middleware."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            return OptimizedRateLimitMiddleware(
                app=Mock(),
                default_requests_per_minute=100,
                redis_url="redis://localhost:6379",
                enable_performance_logging=True,
                cache_results=True,
                batch_redis_operations=True
            )
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_rate_limit_check_performance(self, rate_limit_middleware):
        """Test rate limit check performance."""
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.url.path = "/api/v1/test"
        mock_request.headers = {}
        
        start_time = time.time()
        
        # Test many rate limit checks
        for _ in range(100):
            client_id = rate_limit_middleware._get_client_id(mock_request)
            is_allowed = await rate_limit_middleware._check_rate_limit(client_id, "/api/v1/test")
        
        check_time = time.time() - start_time
        
        # Should check rate limits quickly
        assert check_time < 0.5  # Less than 500ms for 100 checks


class TestBatchProcessorPerformance:
    """Tests for DynamicBatchProcessor performance."""
    
    @pytest.fixture
    def sample_processor(self):
        """Sample async processor function."""
        async def process_batch(items: List[int]) -> List[int]:
            # Simulate processing time
            await asyncio.sleep(0.001 * len(items))  # 1ms per item
            return [item * 2 for item in items]
        
        return process_batch
    
    @pytest.fixture
    def batch_processor(self, sample_processor):
        """Create batch processor instance."""
        config = BatchConfig(
            max_batch_size=50,
            max_wait_time=0.1,
            adaptive_sizing=True,
            performance_logging=True
        )
        
        return DynamicBatchProcessor(
            processor_func=sample_processor,
            config=config
        )
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_processing_throughput(self, batch_processor):
        """Test batch processing throughput."""
        # Submit many items for processing
        start_time = time.time()
        
        tasks = []
        for i in range(200):  # 200 items
            task = batch_processor.submit_item(i)
            tasks.append(task)
        
        # Wait for all processing to complete
        results = await asyncio.gather(*tasks)
        
        processing_time = time.time() - start_time
        
        # Should process efficiently through batching
        assert processing_time < 3.0  # Less than 3 seconds for 200 items
        assert len(results) == 200
        assert all(isinstance(result, int) for result in results)


class TestCachePerformance:
    """Tests for MultiLevelCache performance."""
    
    @pytest.fixture
    def l1_cache(self):
        """L1 memory cache."""
        return L1MemoryCache(max_size=100, ttl_seconds=300)
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis for L2 cache."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True
        mock_redis.exists.return_value = True
        return mock_redis
    
    @pytest.fixture
    def l2_cache(self, mock_redis):
        """L2 Redis cache."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            return L2RedisCache(redis_url="redis://localhost:6379", ttl_seconds=3600)
    
    @pytest.fixture
    def multi_cache(self, l1_cache, l2_cache):
        """Multi-level cache."""
        return MultiLevelCache(
            l1_cache=l1_cache,
            l2_cache=l2_cache,
            enable_stats=True
        )
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_performance_l1_hits(self, multi_cache):
        """Test L1 cache hit performance."""
        # Pre-populate L1 cache
        for i in range(50):
            await multi_cache.set(f"key_{i}", f"value_{i}")
        
        # Measure L1 hit performance
        start_time = time.time()
        
        for i in range(50):
            value = await multi_cache.get(f"key_{i}")
            assert value == f"value_{i}"
        
        l1_hit_time = time.time() - start_time
        
        # L1 hits should be very fast
        assert l1_hit_time < 0.05  # Less than 50ms for 50 L1 hits
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_write_performance(self, multi_cache):
        """Test cache write performance."""
        start_time = time.time()
        
        # Write many items
        for i in range(100):
            await multi_cache.set(f"perf_key_{i}", f"perf_value_{i}")
        
        write_time = time.time() - start_time
        
        # Should write efficiently
        assert write_time < 1.0  # Less than 1 second for 100 writes


class TestIntegrationPerformance:
    """Integration performance tests."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_end_to_end_optimization_performance(self):
        """Test end-to-end optimization performance."""
        # Create optimization components
        mock_middleware = Mock()
        conditional = ConditionalMiddleware(
            app=Mock(),
            middleware_class=mock_middleware,
            include_paths=[r"/api/.*"]
        )
        
        compression = CompressionMiddleware(app=Mock())
        
        mock_redis = AsyncMock()
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            rate_limiter = OptimizedRateLimitMiddleware(app=Mock())
        
        # Simulate realistic workload
        start_time = time.time()
        
        # Process many requests through optimization stack
        for i in range(50):
            mock_request = Mock()
            mock_request.url.path = f"/api/v1/test/{i}"
            mock_request.method = "GET"
            mock_request.headers = {"accept-encoding": "gzip"}
            
            # Simulate middleware processing
            await conditional.dispatch(mock_request, AsyncMock(return_value=Mock()))
        
        total_time = time.time() - start_time
        
        # Should handle realistic workload efficiently
        assert total_time < 2.0  # Less than 2 seconds for 50 optimized requests
    
    @pytest.mark.performance
    def test_optimization_memory_efficiency(self):
        """Test memory efficiency of optimization components."""
        import psutil
        import os
        
        try:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # Create many optimization components
            components = []
            for i in range(50):
                # Create various optimization components
                conditional = ConditionalMiddleware(
                    app=Mock(),
                    middleware_class=Mock,
                    include_paths=[f"/api/v{i}/.*"]
                )
                components.append(conditional)
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Should not use excessive memory
            assert memory_increase < 25 * 1024 * 1024  # Less than 25MB increase
            
        except ImportError:
            # psutil not available, skip test
            pytest.skip("psutil not available for memory testing") 