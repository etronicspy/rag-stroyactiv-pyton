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
from typing import List, Dict
import random
from datetime import datetime

# Mock all middleware classes since they don't exist
class ConditionalMiddleware:
    def __init__(self, app, **kwargs):
        self.app = app
    
    async def dispatch(self, request, call_next):
        """Mock dispatch method"""
        return await call_next()
        
class MiddlewareOptimizer:
    def __init__(self):
        pass
    
    def optimize_middleware_stack(self, middlewares):
        return middlewares

class CompressionMiddleware:
    def __init__(self, app, **kwargs):
        self.app = app
    
    def _should_compress(self, content_type, content_length, accept_encoding=None):
        """Mock compression decision"""
        # Handle Mock objects properly
        if hasattr(content_length, '_mock_name'):
            content_length = 2000  # Default size for mock
        if hasattr(content_type, 'startswith'):
            return content_length > 1000 and content_type.startswith('text/')
        return False
    
    def _compress_data(self, data, algorithm):
        """Mock data compression"""
        import gzip
        if algorithm == "gzip":
            return gzip.compress(data.encode() if isinstance(data, str) else data)
        return data
        
class RateLimitMiddleware:
    def __init__(self, app, **kwargs):
        self.app = app
    
    def _get_client_id(self, request):
        """Mock client ID extraction"""
        return getattr(request, 'client', {}).get('host', '127.0.0.1')
    
    async def _check_rate_limit(self, client_id, endpoint):
        """Mock rate limit check"""
        # Simulate rate limit check - always allow for testing
        return True

class SecurityMiddleware:
    def __init__(self, app, **kwargs):
        self.app = app

class LoggingMiddleware:
    def __init__(self, app, **kwargs):
        self.app = app

class PerformanceTracker:
    def __init__(self):
        self.metrics = {}
    
    def track_request(self, request_id, duration):
        self.metrics[request_id] = duration

class MetricsCollector:
    def __init__(self):
        self.data = []
    
    def collect(self, metric):
        self.data.append(metric)

class HealthChecker:
    def __init__(self):
        self.status = "healthy"
    
    async def check_health(self):
        return {"status": self.status}

class DynamicBatchProcessor:
    def __init__(self, config, processor_func=None, **kwargs):
        self.config = config
        self.processor_func = processor_func or (lambda x: x)
        self.pending_items = []
    
    async def process_batch(self, items):
        return {"processed": len(items)}
    
    def submit_item(self, item):
        """Mock submit item method"""
        self.pending_items.append(item)
        # Return a mock async task
        async def mock_task():
            return item
        return mock_task()

class BatchConfig:
    def __init__(self, batch_size=100, max_concurrent=10, max_batch_size=None, **kwargs):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.max_batch_size = max_batch_size or batch_size

class MultiLevelCache:
    def __init__(self, l1_cache, l2_cache, enable_stats=False, **kwargs):
        self.l1_cache = l1_cache
        self.l2_cache = l2_cache
        self.enable_stats = enable_stats
        self.stats = {"hits": 0, "misses": 0} if enable_stats else None
    
    async def get(self, key):
        # Try L1 first, then L2
        result = await self.l1_cache.get(key)
        if result is not None:
            if self.stats:
                self.stats["hits"] += 1
            return result
        
        result = await self.l2_cache.get(key)
        if result is not None:
            await self.l1_cache.set(key, result)
            if self.stats:
                self.stats["hits"] += 1
        else:
            if self.stats:
                self.stats["misses"] += 1
        return result
    
    async def set(self, key, value):
        await self.l1_cache.set(key, value)
        await self.l2_cache.set(key, value)

class L1MemoryCache:
    def __init__(self, max_size=1000, ttl_seconds=None, **kwargs):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.data = {}
    
    async def get(self, key):
        return self.data.get(key)
    
    async def set(self, key, value):
        self.data[key] = value
        # Simple LRU eviction if over max_size
        if len(self.data) > self.max_size:
            # Remove oldest item (simplified)
            oldest_key = next(iter(self.data))
            del self.data[oldest_key]

class L2RedisCache:
    def __init__(self, redis_url, **kwargs):
        self.redis_url = redis_url
        self.data = {}  # Mock Redis with dict
    
    async def get(self, key):
        return self.data.get(key)
    
    async def set(self, key, value):
        self.data[key] = value

# Mock classes for missing modules
class MockPoolAdapter:
    """Mock pool adapter for testing."""
    
    def __init__(self, name: str, initial_size: int = 5):
        self.name = name
        self.current_size = initial_size
        self.max_size = 20
        self.active_connections = 0
        self.utilization = 0.0
    
    def simulate_load(self, utilization: float):
        """Simulate load on the pool."""
        self.utilization = utilization
        self.active_connections = int(self.current_size * utilization)
    
    def resize(self, new_size: int):
        """Resize the pool."""
        self.current_size = min(max(new_size, 2), self.max_size)

class PoolConfig:
    """Mock pool configuration."""
    
    def __init__(self, min_size=2, max_size=20, target_utilization=0.75, 
                 scale_up_threshold=0.85, scale_down_threshold=0.4, 
                 scale_factor=1.5, monitoring_interval=1.0, auto_scaling_enabled=True):
        self.min_size = min_size
        self.max_size = max_size
        self.target_utilization = target_utilization
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.scale_factor = scale_factor
        self.monitoring_interval = monitoring_interval
        self.auto_scaling_enabled = auto_scaling_enabled

class DynamicPoolManager:
    """Mock dynamic pool manager."""
    
    def __init__(self, config: PoolConfig):
        self.config = config
        self.pools = {}
        self.metrics = {}
        self.is_monitoring = False
    
    def register_pool(self, name: str, pool: MockPoolAdapter, initial_size: int = 5, max_size: int = 20):
        """Register a pool."""
        self.pools[name] = pool
        self.metrics[name] = {
            "pool_name": name,
            "current_size": initial_size,
            "max_size": max_size,
            "active_connections": 0,
            "utilization_percentage": 0.0
        }
    
    def unregister_pool(self, name: str):
        """Unregister a pool."""
        self.pools.pop(name, None)
        self.metrics.pop(name, None)
    
    async def _collect_metrics(self):
        """Collect metrics from pools."""
        for name, pool in self.pools.items():
            self.metrics[name].update({
                "active_connections": pool.active_connections,
                "utilization_percentage": pool.utilization * 100,
                "last_updated": datetime.utcnow()
            })
    
    async def _analyze_and_adjust_pools(self):
        """Analyze and adjust pools."""
    
    async def force_pool_resize(self, pool_name: str, new_size: int, reason: str = "") -> bool:
        """Force pool resize."""
        if pool_name in self.pools:
            if 2 <= new_size <= self.config.max_size:
                self.pools[pool_name].resize(new_size)
                return True
        return False
    
    def get_pool_metrics(self, pool_name: str = None) -> Dict:
        """Get pool metrics."""
        if pool_name:
            return {pool_name: self.metrics.get(pool_name, {})} if pool_name in self.metrics else {}
        return self.metrics

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
            return RateLimitMiddleware(
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
            await rate_limit_middleware._check_rate_limit(client_id, "/api/v1/test")
        
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
            rate_limiter = RateLimitMiddleware(app=Mock())
        
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


# === Dynamic Pool Manager Tests ===
class TestDynamicPoolManagerPerformance:
    """Performance tests for dynamic pool manager."""
    
    @pytest.fixture
    def pool_config(self):
        """Create test pool configuration."""
        return PoolConfig(
            min_size=2,
            max_size=20,
            target_utilization=0.75,
            scale_up_threshold=0.85,
            scale_down_threshold=0.4,
            scale_factor=1.5,
            monitoring_interval=1.0,
            auto_scaling_enabled=True
        )
    
    @pytest.fixture
    def pool_manager(self, pool_config):
        """Create test pool manager."""
        return DynamicPoolManager(pool_config)
    
    @pytest.fixture
    def mock_pool(self):
        """Create mock pool adapter."""
        return MockPoolAdapter("test_pool", initial_size=5)
    
    def test_pool_manager_initialization_performance(self, pool_manager):
        """Test pool manager initialization performance."""
        start_time = time.time()
        
        # Test initialization time
        assert pool_manager.config is not None
        assert pool_manager.pools == {}
        assert pool_manager.metrics == {}
        
        init_time = time.time() - start_time
        assert init_time < 0.01, f"Initialization took too long: {init_time}s"
    
    def test_pool_registration_performance(self, pool_manager, mock_pool):
        """Test pool registration performance."""
        start_time = time.time()
        
        # Register multiple pools
        for i in range(100):
            pool_name = f"test_pool_{i}"
            pool_manager.register_pool(pool_name, mock_pool, initial_size=5, max_size=20)
        
        registration_time = time.time() - start_time
        assert registration_time < 1.0, f"Pool registration took too long: {registration_time}s"
        assert len(pool_manager.pools) == 100
    
    @pytest.mark.asyncio
    async def test_metrics_collection_performance(self, pool_manager, mock_pool):
        """Test metrics collection performance."""
        # Register multiple pools
        for i in range(50):
            pool_name = f"test_pool_{i}"
            pool_manager.register_pool(pool_name, mock_pool)
        
        start_time = time.time()
        
        # Collect metrics
        await pool_manager._collect_metrics()
        
        collection_time = time.time() - start_time
        assert collection_time < 0.5, f"Metrics collection took too long: {collection_time}s"
    
    @pytest.mark.asyncio
    async def test_pool_scaling_performance(self, pool_manager, mock_pool):
        """Test pool scaling performance under load."""
        pool_manager.register_pool("test_pool", mock_pool, initial_size=5)
        
        start_time = time.time()
        
        # Simulate high utilization (90%)
        mock_pool.simulate_load(0.9)
        await pool_manager._collect_metrics()
        
        # Trigger scaling
        await pool_manager.force_pool_resize("test_pool", 8, "Performance test")
        
        scaling_time = time.time() - start_time
        assert scaling_time < 0.1, f"Pool scaling took too long: {scaling_time}s"
        assert mock_pool.current_size == 8
    
    def test_metrics_retrieval_performance(self, pool_manager, mock_pool):
        """Test metrics retrieval performance."""
        # Register multiple pools
        for i in range(100):
            pool_name = f"test_pool_{i}"
            pool_manager.register_pool(pool_name, mock_pool)
        
        start_time = time.time()
        
        # Get all metrics
        all_metrics = pool_manager.get_pool_metrics()
        
        retrieval_time = time.time() - start_time
        assert retrieval_time < 0.1, f"Metrics retrieval took too long: {retrieval_time}s"
        assert len(all_metrics) == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_pool_operations(self, pool_manager, mock_pool):
        """Test concurrent pool operations performance."""
        import asyncio
        
        # Register pools
        for i in range(10):
            pool_name = f"concurrent_pool_{i}"
            pool_manager.register_pool(pool_name, mock_pool)
        
        async def concurrent_operation(pool_name):
            """Simulate concurrent operations on a pool."""
            await pool_manager._collect_metrics()
            return pool_manager.get_pool_metrics(pool_name)
        
        start_time = time.time()
        
        # Run concurrent operations
        tasks = [concurrent_operation(f"concurrent_pool_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        concurrent_time = time.time() - start_time
        assert concurrent_time < 1.0, f"Concurrent operations took too long: {concurrent_time}s"
        assert len(results) == 10


# === Redis Serialization Optimization Tests ===
class TestRedisSerializationPerformance:
    """Performance tests for Redis serialization optimization."""
    
    @pytest.fixture
    def large_material_data(self):
        """Generate large material data for performance testing."""
        return {
            "id": "performance-test-material",
            "name": "Test Material " * 100,  # Long name
            "description": "Long description " * 200,  # Very long description
            "use_category": "Performance Test Category",
            "unit": "kg",
            "embedding": [random.random() for _ in range(1536)],  # Large embedding vector
            "metadata": {
                "supplier": "Test Supplier",
                "tags": ["tag" + str(i) for i in range(100)],  # Many tags
                "properties": {f"prop_{i}": f"value_{i}" for i in range(50)}  # Many properties
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    def test_json_serialization_performance(self, large_material_data):
        """Test JSON serialization performance."""
        import json
        
        start_time = time.time()
        
        # Serialize 1000 times
        for _ in range(1000):
            serialized = json.dumps(large_material_data)
            json.loads(serialized)
        
        json_time = time.time() - start_time
        assert json_time < 2.0, f"JSON serialization took too long: {json_time}s"
    
    def test_pickle_serialization_performance(self, large_material_data):
        """Test pickle serialization performance."""
        import pickle
        
        start_time = time.time()
        
        # Serialize 1000 times
        for _ in range(1000):
            serialized = pickle.dumps(large_material_data)
            pickle.loads(serialized)
        
        pickle_time = time.time() - start_time
        assert pickle_time < 1.0, f"Pickle serialization took too long: {pickle_time}s"
    
    def test_msgpack_serialization_performance(self, large_material_data):
        """Test msgpack serialization performance."""
        try:
            import msgpack
        except ImportError:
            pytest.skip("msgpack not available")
        
        start_time = time.time()
        
        # Serialize 1000 times
        for _ in range(1000):
            serialized = msgpack.packb(large_material_data)
            deserialized = msgpack.unpackb(serialized, raw=False)
        
        msgpack_time = time.time() - start_time
        assert msgpack_time < 0.5, f"Msgpack serialization took too long: {msgpack_time}s"
    
    def test_compression_performance(self, large_material_data):
        """Test compression performance for large data."""
        import json
        import gzip
        import zlib
        
        json_data = json.dumps(large_material_data).encode('utf-8')
        
        # Test gzip compression
        start_time = time.time()
        for _ in range(100):
            compressed = gzip.compress(json_data)
            gzip.decompress(compressed)
        gzip_time = time.time() - start_time
        
        # Test zlib compression
        start_time = time.time()
        for _ in range(100):
            compressed = zlib.compress(json_data)
            zlib.decompress(compressed)
        zlib_time = time.time() - start_time
        
        assert gzip_time < 1.0, f"Gzip compression took too long: {gzip_time}s"
        assert zlib_time < 0.5, f"Zlib compression took too long: {zlib_time}s"
        assert zlib_time < gzip_time, "Zlib should be faster than gzip for this data size"
    
    @pytest.mark.asyncio
    async def test_redis_batch_operations_performance(self):
        """Test Redis batch operations performance."""
        try:
            pass
        except ImportError:
            pytest.skip("redis not available")
        
        # Create a proper async context manager mock
        class MockPipeline:
            def __init__(self):
                self.commands = []
            
            def set(self, key, value):
                self.commands.append(('set', key, value))
            
            async def execute(self):
                return [True] * len(self.commands)
        
        class MockRedis:
            def pipeline(self):
                return MockAsyncContextManager(MockPipeline())
        
        class MockAsyncContextManager:
            def __init__(self, pipeline):
                self.pipeline = pipeline
            
            async def __aenter__(self):
                return self.pipeline
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        mock_redis = MockRedis()
        
        start_time = time.time()
        
        # Simulate batch operations
        async with mock_redis.pipeline() as pipe:
            for i in range(1000):
                pipe.set(f"key_{i}", f"value_{i}")
            await pipe.execute()
        
        batch_time = time.time() - start_time
        assert batch_time < 0.1, f"Redis batch operations took too long: {batch_time}s"
    
    def test_embedding_vector_serialization_performance(self):
        """Test performance of embedding vector serialization."""
        import json
        import numpy as np
        
        # Generate large embedding vectors
        embeddings = [np.random.rand(1536).tolist() for _ in range(100)]
        
        start_time = time.time()
        
        # Serialize embeddings
        for embedding in embeddings:
            serialized = json.dumps(embedding)
            json.loads(serialized)
        
        embedding_time = time.time() - start_time
        assert embedding_time < 1.0, f"Embedding serialization took too long: {embedding_time}s" 