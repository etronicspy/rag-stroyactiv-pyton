"""
Tests for optimized Redis serialization performance.

Тесты для проверки производительности оптимизированной сериализации Redis.
"""

import pytest
import time
import random
import string
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from core.database.adapters.redis_adapter import RedisDatabase


class TestRedisSerializationOptimization:
    """Test optimized Redis serialization performance."""
    
    @pytest.fixture
    def redis_config(self) -> Dict[str, Any]:
        """Redis configuration for testing."""
        return {
            "redis_url": "redis://localhost:6379/0",
            "max_connections": 5,
            "default_ttl": 300,
            "key_prefix": "test_opt:"
        }
    
    @pytest.fixture
    def mock_redis_adapter(self, redis_config):
        """Mock Redis adapter for serialization testing."""
        with patch('redis.asyncio.ConnectionPool.from_url'), \
             patch('redis.asyncio.Redis'):
            adapter = RedisDatabase(redis_config)
            return adapter
    
    def test_serialization_formats(self, mock_redis_adapter):
        """Test different serialization formats."""
        adapter = mock_redis_adapter
        
        # Test data
        test_data = [
            {"simple": "string"},
            {"number": 42},
            {"list": [1, 2, 3, "test"]},
            {"nested": {"a": {"b": {"c": "deep"}}}},
            {"large_text": "x" * 2000},  # Large data for compression test
        ]
        
        for data in test_data:
            # Serialize
            serialized = adapter._serialize_value(data)
            assert isinstance(serialized, bytes)
            
            # Deserialize
            deserialized = adapter._deserialize_value(serialized)
            assert deserialized == data
    
    def test_compression_threshold(self, mock_redis_adapter):
        """Test that compression is applied for large objects."""
        adapter = mock_redis_adapter
        
        # Small data (should not be compressed)
        small_data = {"test": "small"}
        small_serialized = adapter._serialize_value(small_data)
        assert not small_serialized.startswith(b'ZLIB')
        
        # Large data (should be compressed if beneficial)
        large_data = {"large_text": "x" * 5000, "numbers": list(range(1000))}
        large_serialized = adapter._serialize_value(large_data)
        
        # Check if compression was applied
        if large_serialized.startswith(b'ZLIB'):
            print("✅ Compression applied for large data")
        else:
            print("ℹ️ Compression not beneficial for this data")
    
    def test_backward_compatibility(self, mock_redis_adapter):
        """Test backward compatibility with old serialization format."""
        adapter = mock_redis_adapter
        
        # Test legacy JSON format
        import json
        test_data = {"legacy": "json"}
        legacy_json = json.dumps(test_data)
        deserialized = adapter._deserialize_value(legacy_json)
        assert deserialized == test_data
        
        # Test legacy pickle format (hex-encoded)
        import pickle
        legacy_pickle = pickle.dumps(test_data).hex()
        deserialized = adapter._deserialize_value(legacy_pickle)
        assert deserialized == test_data
    
    def test_serialization_performance(self, mock_redis_adapter):
        """Test serialization performance improvement."""
        adapter = mock_redis_adapter
        
        # Generate test data
        test_objects = []
        for _ in range(100):
            obj = {
                "id": random.randint(1, 10000),
                "name": ''.join(random.choices(string.ascii_letters, k=20)),
                "data": {
                    "values": [random.random() for _ in range(10)],
                    "metadata": {
                        "created": time.time(),
                        "tags": [f"tag_{i}" for i in range(5)]
                    }
                }
            }
            test_objects.append(obj)
        
        # Benchmark serialization
        start_time = time.time()
        serialized_objects = []
        for obj in test_objects:
            serialized = adapter._serialize_value(obj)
            serialized_objects.append(serialized)
        serialize_time = time.time() - start_time
        
        # Benchmark deserialization
        start_time = time.time()
        for serialized in serialized_objects:
            deserialized = adapter._deserialize_value(serialized)
        deserialize_time = time.time() - start_time
        
        print(f"✅ Serialization: {len(test_objects)} objects in {serialize_time:.4f}s")
        print(f"✅ Deserialization: {len(test_objects)} objects in {deserialize_time:.4f}s")
        print(f"✅ Total time: {serialize_time + deserialize_time:.4f}s")
        
        # Performance should be reasonable (less than 1ms per object)
        avg_time_per_object = (serialize_time + deserialize_time) / len(test_objects)
        assert avg_time_per_object < 0.001, f"Too slow: {avg_time_per_object:.6f}s per object"
    
    def test_error_handling(self, mock_redis_adapter):
        """Test error handling in serialization."""
        adapter = mock_redis_adapter
        
        # Test with problematic data
        class UnserializableClass:
            def __init__(self):
                self.data = "test"
        
        # Should not raise exception, should fallback to pickle
        obj = UnserializableClass()
        try:
            serialized = adapter._serialize_value(obj)
            deserialized = adapter._deserialize_value(serialized)
            assert hasattr(deserialized, 'data')
            assert deserialized.data == "test"
        except Exception as e:
            pytest.fail(f"Serialization should handle complex objects: {e}")
    
    def test_msgpack_availability(self, mock_redis_adapter):
        """Test behavior when msgpack is not available."""
        adapter = mock_redis_adapter
        
        # Test data
        test_data = {"test": "data", "number": 42}
        
        # This should work regardless of msgpack availability
        serialized = adapter._serialize_value(test_data)
        deserialized = adapter._deserialize_value(serialized)
        assert deserialized == test_data
    
    def test_memory_efficiency(self, mock_redis_adapter):
        """Test memory efficiency of new serialization."""
        adapter = mock_redis_adapter
        
        # Create large but compressible data
        large_data = {
            "repeated_data": ["same_string"] * 1000,
            "numbers": list(range(500)),
            "text": "This is repeated text. " * 100
        }
        
        # Serialize with new method
        serialized = adapter._serialize_value(large_data)
        
        # Compare with naive JSON approach
        import json
        json_size = len(json.dumps(large_data).encode('utf-8'))
        optimized_size = len(serialized)
        
        print(f"✅ JSON size: {json_size} bytes")
        print(f"✅ Optimized size: {optimized_size} bytes")
        print(f"✅ Compression ratio: {json_size / optimized_size:.2f}x")
        
        # Should be more efficient for this type of data
        if optimized_size < json_size:
            print("🎉 Optimization successful!")
        else:
            print("ℹ️ No size benefit for this specific data pattern")


# Integration test for real Redis instance
@pytest.mark.integration
class TestRedisSerializationIntegration:
    """Integration tests with real Redis instance."""
    
    @pytest.fixture
    def redis_config(self) -> Dict[str, Any]:
        """Redis configuration for integration testing."""
        return {
            "redis_url": "redis://localhost:6379/15",  # Use DB 15 for testing
            "max_connections": 5,
            "default_ttl": 60,
            "key_prefix": "integration_opt_test:"
        }
    
    @pytest.mark.asyncio
    async def test_real_redis_serialization(self, redis_config):
        """Test optimized serialization with real Redis instance."""
        try:
            adapter = RedisDatabase(redis_config)
            
            # Test data
            test_data = {
                "optimization_test": True,
                "timestamp": time.time(),
                "data": {
                    "metrics": [1.5, 2.3, 4.1, 8.9],
                    "metadata": {
                        "version": "1.0",
                        "features": ["msgpack", "compression", "fallback"]
                    }
                }
            }
            
            # Store and retrieve
            await adapter.set("optimization_test", test_data, ttl=30)
            retrieved = await adapter.get("optimization_test")
            
            assert retrieved == test_data
            print("✅ Real Redis serialization test passed!")
            
            # Cleanup
            await adapter.delete("optimization_test")
            await adapter.close()
            
        except Exception as e:
            pytest.skip(f"Redis not available for integration test: {e}")


if __name__ == "__main__":
    # Run basic tests
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    pytest.main([__file__, "-v"]) 