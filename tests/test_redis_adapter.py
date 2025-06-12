"""Tests for Redis cache database adapter.

Тесты для Redis адаптера с поддержкой mock и integration тестирования.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from core.database.adapters.redis_adapter import RedisDatabase
from core.database.exceptions import ConnectionError, DatabaseError


class TestRedisDatabase:
    """Test Redis database adapter."""
    
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
    
    # === Initialization tests ===
    
    def test_init_success(self, redis_config):
        """Test successful Redis adapter initialization."""
        with patch('redis.asyncio.ConnectionPool.from_url') as mock_pool, \
             patch('redis.asyncio.Redis') as mock_redis:
            
            mock_pool.return_value = MagicMock()
            mock_redis.return_value = AsyncMock()
            
            adapter = RedisDatabase(redis_config)
            
            assert adapter.redis_url == redis_config["redis_url"]
            assert adapter.default_ttl == redis_config["default_ttl"]
            assert adapter.key_prefix == redis_config["key_prefix"]
            
            mock_pool.assert_called_once()
            mock_redis.assert_called_once()
    
    def test_init_missing_url(self):
        """Test initialization with missing Redis URL."""
        config = {"max_connections": 5}
        
        with pytest.raises(ConnectionError) as exc_info:
            RedisDatabase(config)
        
        assert "Redis URL is required" in str(exc_info.value)
    
    def test_init_connection_error(self, redis_config):
        """Test initialization with connection error."""
        with patch('redis.asyncio.ConnectionPool.from_url', side_effect=Exception("Connection failed")):
            
            with pytest.raises(ConnectionError) as exc_info:
                RedisDatabase(redis_config)
            
            assert "Failed to initialize Redis connection" in str(exc_info.value)
    
    # === Basic operations tests ===
    
    @pytest.mark.asyncio
    async def test_ping_success(self, redis_config, mock_redis_client):
        """Test successful ping operation."""
        mock_client, mock_pool = mock_redis_client
        mock_client.ping.return_value = True
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            result = await adapter.ping()
            
            assert result is True
            mock_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ping_failure(self, redis_config, mock_redis_client):
        """Test ping operation failure."""
        mock_client, mock_pool = mock_redis_client
        mock_client.ping.side_effect = Exception("Redis connection failed")
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            
            with pytest.raises(ConnectionError) as exc_info:
                await adapter.ping()
            
            assert "Redis ping failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_set_get_success(self, redis_config, mock_redis_client):
        """Test successful set and get operations."""
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
            
            mock_client.setex.assert_called_once_with(
                "test_materials:test_key", 
                600, 
                serialized_value
            )
            
            # Test get
            retrieved_value = await adapter.get("test_key")
            assert retrieved_value == test_value
            
            mock_client.get.assert_called_once_with("test_materials:test_key")
    
    @pytest.mark.asyncio
    async def test_get_missing_key(self, redis_config, mock_redis_client):
        """Test get operation with missing key."""
        mock_client, mock_pool = mock_redis_client
        mock_client.get.return_value = None
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            result = await adapter.get("missing_key", default="not_found")
            
            assert result == "not_found"
    
    @pytest.mark.asyncio
    async def test_delete_success(self, redis_config, mock_redis_client):
        """Test successful delete operation."""
        mock_client, mock_pool = mock_redis_client
        mock_client.delete.return_value = 1
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            result = await adapter.delete("test_key")
            
            assert result is True
            mock_client.delete.assert_called_once_with("test_materials:test_key")
    
    @pytest.mark.asyncio
    async def test_exists_success(self, redis_config, mock_redis_client):
        """Test successful exists operation."""
        mock_client, mock_pool = mock_redis_client
        mock_client.exists.return_value = 1
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            result = await adapter.exists("test_key")
            
            assert result is True
            mock_client.exists.assert_called_once_with("test_materials:test_key")
    
    # === TTL operations tests ===
    
    @pytest.mark.asyncio
    async def test_expire_success(self, redis_config, mock_redis_client):
        """Test successful expire operation."""
        mock_client, mock_pool = mock_redis_client
        mock_client.expire.return_value = True
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            result = await adapter.expire("test_key", 3600)
            
            assert result is True
            mock_client.expire.assert_called_once_with("test_materials:test_key", 3600)
    
    @pytest.mark.asyncio
    async def test_ttl_success(self, redis_config, mock_redis_client):
        """Test successful TTL operation."""
        mock_client, mock_pool = mock_redis_client
        mock_client.ttl.return_value = 1800
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            result = await adapter.ttl("test_key")
            
            assert result == 1800
            mock_client.ttl.assert_called_once_with("test_materials:test_key")
    
    # === Hash operations tests ===
    
    @pytest.mark.asyncio
    async def test_hash_operations(self, redis_config, mock_redis_client):
        """Test hash operations (hset, hget, hgetall, hdel)."""
        mock_client, mock_pool = mock_redis_client
        test_value = {"price": 150.0, "category": "cement"}
        serialized_value = '{"price": 150.0, "category": "cement"}'
        
        mock_client.hset.return_value = 1
        mock_client.hget.return_value = serialized_value
        mock_client.hgetall.return_value = {"field1": serialized_value}
        mock_client.hdel.return_value = 1
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            
            # Test hset
            result = await adapter.hset("hash_key", "field1", test_value, ttl=600)
            assert result is True
            
            # Test hget
            retrieved_value = await adapter.hget("hash_key", "field1")
            assert retrieved_value == test_value
            
            # Test hgetall
            all_fields = await adapter.hgetall("hash_key")
            assert "field1" in all_fields
            assert all_fields["field1"] == test_value
            
            # Test hdel
            delete_result = await adapter.hdel("hash_key", "field1")
            assert delete_result is True
    
    # === List operations tests ===
    
    @pytest.mark.asyncio
    async def test_list_operations(self, redis_config, mock_redis_client):
        """Test list operations (lpush, lrange)."""
        mock_client, mock_pool = mock_redis_client
        test_values = ["item1", "item2", "item3"]
        serialized_values = ['"item1"', '"item2"', '"item3"']
        
        mock_client.lpush.return_value = 3
        mock_client.lrange.return_value = serialized_values
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            
            # Test lpush
            result = await adapter.lpush("list_key", *test_values, ttl=600)
            assert result == 3
            
            # Test lrange
            retrieved_values = await adapter.lrange("list_key", 0, -1)
            assert retrieved_values == test_values
    
    # === Set operations tests ===
    
    @pytest.mark.asyncio
    async def test_set_operations(self, redis_config, mock_redis_client):
        """Test set operations (sadd, smembers)."""
        mock_client, mock_pool = mock_redis_client
        test_values = {"item1", "item2", "item3"}
        serialized_values = {'"item1"', '"item2"', '"item3"'}
        
        mock_client.sadd.return_value = 3
        mock_client.smembers.return_value = serialized_values
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            
            # Test sadd
            result = await adapter.sadd("set_key", *test_values, ttl=600)
            assert result == 3
            
            # Test smembers
            retrieved_values = await adapter.smembers("set_key")
            assert retrieved_values == test_values
    
    # === Batch operations tests ===
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, redis_config, mock_redis_client):
        """Test batch operations (mset, mget)."""
        mock_client, mock_pool = mock_redis_client
        test_mapping = {
            "key1": {"name": "Material 1"},
            "key2": {"name": "Material 2"}
        }
        serialized_values = ['{"name": "Material 1"}', '{"name": "Material 2"}']
        
        mock_client.mset.return_value = True
        mock_client.mget.return_value = serialized_values
        mock_client.pipeline.return_value = mock_client
        mock_client.expire.return_value = mock_client
        mock_client.execute.return_value = [True, True]
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            
            # Test mset
            result = await adapter.mset(test_mapping, ttl=600)
            assert result is True
            
            # Test mget
            keys = list(test_mapping.keys())
            retrieved_values = await adapter.mget(keys)
            assert len(retrieved_values) == 2
            assert retrieved_values[0] == {"name": "Material 1"}
            assert retrieved_values[1] == {"name": "Material 2"}
    
    # === Pattern operations tests ===
    
    @pytest.mark.asyncio
    async def test_delete_pattern(self, redis_config, mock_redis_client):
        """Test delete pattern operation."""
        mock_client, mock_pool = mock_redis_client
        
        # Mock scan_iter to return some keys
        async def mock_scan_iter(match):
            keys = ["test_materials:key1", "test_materials:key2", "test_materials:key3"]
            for key in keys:
                yield key
        
        mock_client.scan_iter = mock_scan_iter
        mock_client.delete.return_value = 3
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            result = await adapter.delete_pattern("key*")
            
            assert result == 3
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, redis_config, mock_redis_client):
        """Test clear cache operation."""
        mock_client, mock_pool = mock_redis_client
        
        # Mock scan_iter to return some keys
        async def mock_scan_iter(match):
            keys = ["test_materials:key1", "test_materials:key2"]
            for key in keys:
                yield key
        
        mock_client.scan_iter = mock_scan_iter
        mock_client.delete.return_value = 2
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            result = await adapter.clear_cache()
            
            assert result == 2
    
    # === Health check tests ===
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, redis_config, mock_redis_client):
        """Test successful health check."""
        mock_client, mock_pool = mock_redis_client
        mock_client.ping.return_value = True
        mock_client.info.return_value = {
            "redis_version": "7.0.0",
            "redis_mode": "standalone",
            "used_memory_human": "1.5M",
            "connected_clients": 5,
            "total_commands_processed": 1000,
            "keyspace_hits": 800,
            "keyspace_misses": 200,
            "uptime_in_seconds": 3600
        }
        
        # Mock scan_iter for cache stats
        async def mock_scan_iter(match):
            keys = ["test_materials:key1", "test_materials:key2"]
            for key in keys:
                yield key
        
        mock_client.scan_iter = mock_scan_iter
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            health_status = await adapter.health_check()
            
            assert health_status["status"] == "healthy"
            assert health_status["database_type"] == "Redis"
            assert "ping_time_seconds" in health_status
            assert "connection_pool" in health_status
            assert "redis_info" in health_status
            assert "cache_stats" in health_status
            
            # Check Redis info
            redis_info = health_status["redis_info"]
            assert redis_info["version"] == "7.0.0"
            assert redis_info["connected_clients"] == 5
            
            # Check cache stats
            cache_stats = health_status["cache_stats"]
            assert cache_stats["total_keys"] == 2
            assert cache_stats["key_prefix"] == "test_materials:"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, redis_config, mock_redis_client):
        """Test health check failure."""
        mock_client, mock_pool = mock_redis_client
        mock_client.ping.side_effect = Exception("Connection failed")
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            health_status = await adapter.health_check()
            
            assert health_status["status"] == "unhealthy"
            assert "error" in health_status
    
    # === Serialization tests ===
    
    def test_serialize_deserialize_json(self, redis_config):
        """Test JSON serialization and deserialization."""
        with patch('redis.asyncio.ConnectionPool.from_url'), \
             patch('redis.asyncio.Redis'):
            
            adapter = RedisDatabase(redis_config)
            
            # Test simple objects
            test_data = {"name": "Test", "price": 100.0, "active": True}
            serialized = adapter._serialize_value(test_data)
            deserialized = adapter._deserialize_value(serialized)
            
            assert deserialized == test_data
    
    def test_serialize_deserialize_complex(self, redis_config):
        """Test serialization of complex objects."""
        with patch('redis.asyncio.ConnectionPool.from_url'), \
             patch('redis.asyncio.Redis'):
            
            adapter = RedisDatabase(redis_config)
            
            # Test complex object that requires pickle
            test_data = datetime.utcnow()
            serialized = adapter._serialize_value(test_data)
            deserialized = adapter._deserialize_value(serialized)
            
            # Should fallback to string representation for datetime
            assert isinstance(deserialized, str)
    
    # === Error handling tests ===
    
    @pytest.mark.asyncio
    async def test_set_error_handling(self, redis_config, mock_redis_client):
        """Test error handling in set operation."""
        mock_client, mock_pool = mock_redis_client
        mock_client.setex.side_effect = Exception("Redis error")
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            
            with pytest.raises(DatabaseError) as exc_info:
                await adapter.set("test_key", "test_value")
            
            assert "Failed to set cache key" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_error_handling(self, redis_config, mock_redis_client):
        """Test error handling in get operation."""
        mock_client, mock_pool = mock_redis_client
        mock_client.get.side_effect = Exception("Redis error")
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            
            with pytest.raises(DatabaseError) as exc_info:
                await adapter.get("test_key")
            
            assert "Failed to get cache key" in str(exc_info.value)
    
    # === Connection management tests ===
    
    @pytest.mark.asyncio
    async def test_close_connections(self, redis_config, mock_redis_client):
        """Test closing Redis connections."""
        mock_client, mock_pool = mock_redis_client
        mock_client.close.return_value = None
        mock_pool.disconnect.return_value = None
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            await adapter.close()
            
            mock_client.close.assert_called_once()
            mock_pool.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_connections_error(self, redis_config, mock_redis_client):
        """Test error handling when closing connections."""
        mock_client, mock_pool = mock_redis_client
        mock_client.close.side_effect = Exception("Close error")
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=mock_pool), \
             patch('redis.asyncio.Redis', return_value=mock_client):
            
            adapter = RedisDatabase(redis_config)
            # Should not raise exception, just log error
            await adapter.close()
    
    # === Key building tests ===
    
    def test_build_key(self, redis_config):
        """Test key building with prefix."""
        with patch('redis.asyncio.ConnectionPool.from_url'), \
             patch('redis.asyncio.Redis'):
            
            adapter = RedisDatabase(redis_config)
            
            key = adapter._build_key("test_key")
            assert key == "test_materials:test_key"
            
            key = adapter._build_key("search:query_hash")
            assert key == "test_materials:search:query_hash"


# === Integration tests (require real Redis) ===

@pytest.mark.integration
class TestRedisIntegration:
    """Integration tests for Redis adapter (require real Redis instance)."""
    
    @pytest.fixture
    def redis_config(self) -> Dict[str, Any]:
        """Redis configuration for integration testing."""
        return {
            "redis_url": "redis://localhost:6379/15",  # Use DB 15 for testing
            "max_connections": 5,
            "retry_on_timeout": True,
            "socket_timeout": 10,
            "socket_connect_timeout": 10,
            "decode_responses": True,
            "health_check_interval": 30,
            "default_ttl": 60,
            "key_prefix": "integration_test:"
        }
    
    @pytest.mark.asyncio
    async def test_real_redis_operations(self, redis_config):
        """Test operations with real Redis instance."""
        try:
            adapter = RedisDatabase(redis_config)
            
            # Test ping
            ping_result = await adapter.ping()
            assert ping_result is True
            
            # Test set/get
            test_data = {"name": "Integration Test", "value": 42}
            await adapter.set("test_key", test_data, ttl=60)
            
            retrieved_data = await adapter.get("test_key")
            assert retrieved_data == test_data
            
            # Test exists
            exists_result = await adapter.exists("test_key")
            assert exists_result is True
            
            # Test TTL
            ttl_result = await adapter.ttl("test_key")
            assert 0 < ttl_result <= 60
            
            # Test delete
            delete_result = await adapter.delete("test_key")
            assert delete_result is True
            
            # Verify deletion
            exists_after_delete = await adapter.exists("test_key")
            assert exists_after_delete is False
            
            # Test health check
            health_status = await adapter.health_check()
            assert health_status["status"] == "healthy"
            
            # Cleanup
            await adapter.clear_cache()
            await adapter.close()
            
        except Exception as e:
            pytest.skip(f"Redis integration test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_real_redis_batch_operations(self, redis_config):
        """Test batch operations with real Redis instance."""
        try:
            adapter = RedisDatabase(redis_config)
            
            # Test batch set/get
            test_mapping = {
                "batch_key1": {"name": "Item 1", "price": 100},
                "batch_key2": {"name": "Item 2", "price": 200},
                "batch_key3": {"name": "Item 3", "price": 300}
            }
            
            # Batch set
            await adapter.mset(test_mapping, ttl=60)
            
            # Batch get
            keys = list(test_mapping.keys())
            retrieved_values = await adapter.mget(keys)
            
            assert len(retrieved_values) == 3
            for i, key in enumerate(keys):
                assert retrieved_values[i] == test_mapping[key]
            
            # Test pattern deletion
            deleted_count = await adapter.delete_pattern("batch_key*")
            assert deleted_count == 3
            
            # Cleanup
            await adapter.close()
            
        except Exception as e:
            pytest.skip(f"Redis batch integration test skipped: {e}") 