"""Redis cache database adapter implementation.

Адаптер для работы с Redis кеш БД с поддержкой async/await и connection pooling.
"""

import json
import pickle
from core.monitoring.logger import get_logger
import zlib
from typing import Any, Dict, List, Optional, Union, Set
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

# Try to import msgpack for optimized serialization
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False
    get_logger(__name__).warning("msgpack not available, falling back to JSON+pickle serialization")

from core.database.interfaces import ICacheDatabase
from core.database.exceptions import ConnectionError, DatabaseError, QueryError


logger = get_logger(__name__)


class RedisDatabase(ICacheDatabase):
    """Redis cache database adapter with async/await support.
    
    Адаптер для работы с Redis с поддержкой async/await, connection pooling и advanced кеширования.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Redis client with connection pooling.
        
        Args:
            config: Redis configuration dictionary
                - redis_url: Redis connection URL
                - max_connections: Maximum connections in pool (default: 10)
                - retry_on_timeout: Whether to retry on timeout (default: True)
                - socket_timeout: Socket timeout in seconds (default: 30)
                - socket_connect_timeout: Connection timeout (default: 30)
                - decode_responses: Decode responses to strings (default: True)
                - health_check_interval: Health check interval (default: 30)
            
        Raises:
            ConnectionError: If connection fails
        """
        self.config = config
        self.redis_url = config.get("redis_url")
        
        if not self.redis_url:
            raise ConnectionError(
                message="Redis URL is required",
                details="Missing 'redis_url' in config"
            )
        
        # Connection pool configuration
        pool_kwargs = {
            "max_connections": config.get("max_connections", 10),
            "retry_on_timeout": config.get("retry_on_timeout", True),
            "socket_timeout": config.get("socket_timeout", 30),
            "socket_connect_timeout": config.get("socket_connect_timeout", 30),
            "decode_responses": config.get("decode_responses", True),
            "health_check_interval": config.get("health_check_interval", 30)
        }
        
        try:
            # Create connection pool
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                **pool_kwargs
            )
            
            # Create Redis client
            self.redis = redis.Redis(connection_pool=self.pool)
            
            # Cache configuration
            self.default_ttl = config.get("default_ttl", 3600)  # 1 hour
            self.key_prefix = config.get("key_prefix", "rag_materials:")
            
            logger.info(f"Redis adapter initialized with max_connections={pool_kwargs['max_connections']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis adapter: {e}")
            raise ConnectionError(
                message="Failed to initialize Redis connection",
                details=str(e)
            )
    
    async def ping(self) -> bool:
        """Test Redis connection.
        
        Returns:
            True if connection is healthy
            
        Raises:
            ConnectionError: If ping fails
        """
        try:
            result = await self.redis.ping()
            return result
        except RedisError as e:
            logger.error(f"Redis ping failed: {e}")
            raise ConnectionError(
                message="Redis ping failed",
                details=str(e)
            )
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for default)
            serialize: Whether to serialize value (JSON or pickle)
            
        Returns:
            True if successful
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            ttl = ttl or self.default_ttl
            
            # Serialize value
            if serialize:
                serialized_value = self._serialize_value(value)
            else:
                serialized_value = value
            
            # Set with TTL
            result = await self.redis.setex(full_key, ttl, serialized_value)
            
            logger.debug(f"Cached key '{key}' with TTL {ttl}s")
            return result
            
        except RedisError as e:
            logger.error(f"Failed to set cache key '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to set cache key '{key}'",
                details=str(e)
            )
    
    async def get(
        self, 
        key: str, 
        deserialize: bool = True,
        default: Any = None
    ) -> Any:
        """Get value from cache.
        
        Args:
            key: Cache key
            deserialize: Whether to deserialize value
            default: Default value if key not found
            
        Returns:
            Cached value or default
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            value = await self.redis.get(full_key)
            
            if value is None:
                logger.debug(f"Cache miss for key '{key}'")
                return default
            
            # Deserialize value
            if deserialize:
                deserialized_value = self._deserialize_value(value)
                logger.debug(f"Cache hit for key '{key}'")
                return deserialized_value
            else:
                return value
                
        except RedisError as e:
            logger.error(f"Failed to get cache key '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to get cache key '{key}'",
                details=str(e)
            )
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            result = await self.redis.delete(full_key)
            
            logger.debug(f"Deleted cache key '{key}': {bool(result)}")
            return bool(result)
            
        except RedisError as e:
            logger.error(f"Failed to delete cache key '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to delete cache key '{key}'",
                details=str(e)
            )
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            result = await self.redis.exists(full_key)
            return bool(result)
            
        except RedisError as e:
            logger.error(f"Failed to check cache key '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to check cache key '{key}'",
                details=str(e)
            )
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if TTL was set
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            result = await self.redis.expire(full_key, ttl)
            
            logger.debug(f"Set TTL {ttl}s for key '{key}': {bool(result)}")
            return bool(result)
            
        except RedisError as e:
            logger.error(f"Failed to set TTL for key '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to set TTL for key '{key}'",
                details=str(e)
            )
    
    async def ttl(self, key: str) -> int:
        """Get TTL for key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds (-1 if no TTL, -2 if key doesn't exist)
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            result = await self.redis.ttl(full_key)
            return result
            
        except RedisError as e:
            logger.error(f"Failed to get TTL for key '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to get TTL for key '{key}'",
                details=str(e)
            )
    
    # === Hash operations ===
    
    async def hset(self, key: str, field: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set hash field.
        
        Args:
            key: Hash key
            field: Field name
            value: Field value
            ttl: TTL for the hash key
            
        Returns:
            True if field was set
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            serialized_value = self._serialize_value(value)
            
            result = await self.redis.hset(full_key, field, serialized_value)
            
            # Set TTL if provided
            if ttl:
                await self.redis.expire(full_key, ttl)
            
            logger.debug(f"Set hash field '{field}' in key '{key}'")
            return bool(result)
            
        except RedisError as e:
            logger.error(f"Failed to set hash field '{field}' in key '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to set hash field '{field}' in key '{key}'",
                details=str(e)
            )
    
    async def hget(self, key: str, field: str, default: Any = None) -> Any:
        """Get hash field.
        
        Args:
            key: Hash key
            field: Field name
            default: Default value if field not found
            
        Returns:
            Field value or default
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            value = await self.redis.hget(full_key, field)
            
            if value is None:
                return default
            
            return self._deserialize_value(value)
            
        except RedisError as e:
            logger.error(f"Failed to get hash field '{field}' from key '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to get hash field '{field}' from key '{key}'",
                details=str(e)
            )
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields.
        
        Args:
            key: Hash key
            
        Returns:
            Dictionary of all fields and values
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            result = await self.redis.hgetall(full_key)
            
            # Deserialize all values
            deserialized = {}
            for field, value in result.items():
                deserialized[field] = self._deserialize_value(value)
            
            return deserialized
            
        except RedisError as e:
            logger.error(f"Failed to get all hash fields from key '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to get all hash fields from key '{key}'",
                details=str(e)
            )
    
    async def hdel(self, key: str, field: str) -> bool:
        """Delete hash field.
        
        Args:
            key: Hash key
            field: Field name to delete
            
        Returns:
            True if field was deleted
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            result = await self.redis.hdel(full_key, field)
            
            logger.debug(f"Deleted hash field '{field}' from key '{key}': {bool(result)}")
            return bool(result)
            
        except RedisError as e:
            logger.error(f"Failed to delete hash field '{field}' from key '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to delete hash field '{field}' from key '{key}'",
                details=str(e)
            )
    
    # === List operations ===
    
    async def lpush(self, key: str, *values: Any, ttl: Optional[int] = None) -> int:
        """Push values to left of list.
        
        Args:
            key: List key
            values: Values to push
            ttl: TTL for the list key
            
        Returns:
            New length of list
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            serialized_values = [self._serialize_value(v) for v in values]
            
            result = await self.redis.lpush(full_key, *serialized_values)
            
            # Set TTL if provided
            if ttl:
                await self.redis.expire(full_key, ttl)
            
            logger.debug(f"Pushed {len(values)} values to list '{key}'")
            return result
            
        except RedisError as e:
            logger.error(f"Failed to push to list '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to push to list '{key}'",
                details=str(e)
            )
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get range of list elements.
        
        Args:
            key: List key
            start: Start index
            end: End index (-1 for end of list)
            
        Returns:
            List of elements
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            result = await self.redis.lrange(full_key, start, end)
            
            # Deserialize all values
            return [self._deserialize_value(v) for v in result]
            
        except RedisError as e:
            logger.error(f"Failed to get range from list '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to get range from list '{key}'",
                details=str(e)
            )
    
    # === Set operations ===
    
    async def sadd(self, key: str, *values: Any, ttl: Optional[int] = None) -> int:
        """Add values to set.
        
        Args:
            key: Set key
            values: Values to add
            ttl: TTL for the set key
            
        Returns:
            Number of new elements added
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            serialized_values = [self._serialize_value(v) for v in values]
            
            result = await self.redis.sadd(full_key, *serialized_values)
            
            # Set TTL if provided
            if ttl:
                await self.redis.expire(full_key, ttl)
            
            logger.debug(f"Added {result} new values to set '{key}'")
            return result
            
        except RedisError as e:
            logger.error(f"Failed to add to set '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to add to set '{key}'",
                details=str(e)
            )
    
    async def smembers(self, key: str) -> Set[Any]:
        """Get all set members.
        
        Args:
            key: Set key
            
        Returns:
            Set of all members
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_key = self._build_key(key)
            result = await self.redis.smembers(full_key)
            
            # Deserialize all values
            return {self._deserialize_value(v) for v in result}
            
        except RedisError as e:
            logger.error(f"Failed to get set members from '{key}': {e}")
            raise DatabaseError(
                message=f"Failed to get set members from '{key}'",
                details=str(e)
            )
    
    # === Batch operations ===
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple keys.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: TTL for all keys
            
        Returns:
            True if successful
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            # Build full keys and serialize values
            full_mapping = {}
            for key, value in mapping.items():
                full_key = self._build_key(key)
                serialized_value = self._serialize_value(value)
                full_mapping[full_key] = serialized_value
            
            result = await self.redis.mset(full_mapping)
            
            # Set TTL for all keys if provided
            if ttl:
                keys = list(full_mapping.keys())
                pipeline = self.redis.pipeline()
                for key in keys:
                    pipeline.expire(key, ttl)
                await pipeline.execute()
            
            logger.debug(f"Set {len(mapping)} keys with batch operation")
            return result
            
        except RedisError as e:
            logger.error(f"Failed to set multiple keys: {e}")
            raise DatabaseError(
                message="Failed to set multiple keys",
                details=str(e)
            )
    
    async def mget(self, keys: List[str]) -> List[Any]:
        """Get multiple keys.
        
        Args:
            keys: List of cache keys
            
        Returns:
            List of values (None for missing keys)
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_keys = [self._build_key(key) for key in keys]
            result = await self.redis.mget(full_keys)
            
            # Deserialize all values
            deserialized = []
            for value in result:
                if value is None:
                    deserialized.append(None)
                else:
                    deserialized.append(self._deserialize_value(value))
            
            logger.debug(f"Retrieved {len(keys)} keys with batch operation")
            return deserialized
            
        except RedisError as e:
            logger.error(f"Failed to get multiple keys: {e}")
            raise DatabaseError(
                message="Failed to get multiple keys",
                details=str(e)
            )
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
            
        Returns:
            Number of deleted keys
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            full_pattern = self._build_key(pattern)
            
            # Find matching keys
            keys = []
            async for key in self.redis.scan_iter(match=full_pattern):
                keys.append(key)
            
            if not keys:
                return 0
            
            # Delete in batches
            deleted = 0
            batch_size = 1000
            for i in range(0, len(keys), batch_size):
                batch = keys[i:i + batch_size]
                deleted += await self.redis.delete(*batch)
            
            logger.info(f"Deleted {deleted} keys matching pattern '{pattern}'")
            return deleted
            
        except RedisError as e:
            logger.error(f"Failed to delete keys matching pattern '{pattern}': {e}")
            raise DatabaseError(
                message=f"Failed to delete keys matching pattern '{pattern}'",
                details=str(e)
            )
    
    async def clear_cache(self) -> int:
        """Clear all cache keys with prefix.
        
        Returns:
            Number of deleted keys
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            pattern = f"{self.key_prefix}*"
            return await self.delete_pattern("*")  # Will use prefix automatically
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise DatabaseError(
                message="Failed to clear cache",
                details=str(e)
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health status.
        
        Returns:
            Health status information
        """
        try:
            # Test basic connectivity
            start_time = datetime.utcnow()
            await self.ping()
            ping_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Get Redis info
            info = await self.redis.info()
            
            # Get connection pool stats
            pool_stats = {
                "max_connections": self.pool.max_connections,
                "created_connections": self.pool.created_connections,
                "available_connections": len(self.pool._available_connections),
                "in_use_connections": len(self.pool._in_use_connections)
            }
            
            return {
                "status": "healthy",
                "database_type": "Redis",
                "ping_time_seconds": ping_time,
                "connection_pool": pool_stats,
                "redis_info": {
                    "version": info.get("redis_version"),
                    "mode": info.get("redis_mode", "standalone"),
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands_processed": info.get("total_commands_processed"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                    "uptime_in_seconds": info.get("uptime_in_seconds")
                },
                "cache_stats": await self._get_cache_stats(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "database_type": "Redis",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close(self) -> None:
        """Close Redis connections.
        
        Закрывает все соединения с Redis.
        """
        try:
            await self.redis.close()
            await self.pool.disconnect()
            logger.info("Redis connections closed")
            
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")
    
    # === Private helper methods ===
    
    def _build_key(self, key: str) -> str:
        """Build full cache key with prefix."""
        return f"{self.key_prefix}{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage with optimal performance.
        
        Uses msgpack if available (fastest), otherwise falls back to JSON+pickle.
        Automatically compresses large objects.
        """
        if MSGPACK_AVAILABLE:
            try:
                # Use msgpack for fastest serialization
                serialized = msgpack.packb(value, use_bin_type=True, strict_types=False)
                
                # Compress if larger than 1KB
                if len(serialized) > 1024:
                    compressed = zlib.compress(serialized, level=1)  # Fast compression
                    # Only use compression if it actually reduces size
                    if len(compressed) < len(serialized):
                        return b'ZLIB:' + compressed
                
                return b'MSGPACK:' + serialized
                
            except (TypeError, ValueError, msgpack.exceptions.PackException) as e:
                logger.debug(f"msgpack serialization failed, falling back to pickle: {e}")
                # Fallback to pickle for complex objects
                pickled = pickle.dumps(value)
                if len(pickled) > 1024:
                    compressed = zlib.compress(pickled, level=1)
                    if len(compressed) < len(pickled):
                        return b'ZLIB_PICKLE:' + compressed
                return b'PICKLE:' + pickled
        else:
            # Legacy JSON+pickle fallback
            try:
                json_str = json.dumps(value, default=str, ensure_ascii=False)
                json_bytes = json_str.encode('utf-8')
                
                if len(json_bytes) > 1024:
                    compressed = zlib.compress(json_bytes, level=1)
                    if len(compressed) < len(json_bytes):
                        return b'ZLIB_JSON:' + compressed
                
                return b'JSON:' + json_bytes
                
            except (TypeError, ValueError):
                # Fallback to pickle for complex objects
                pickled = pickle.dumps(value)
                if len(pickled) > 1024:
                    compressed = zlib.compress(pickled, level=1)
                    if len(compressed) < len(pickled):
                        return b'ZLIB_PICKLE:' + compressed
                return b'PICKLE:' + pickled
    
    def _deserialize_value(self, value: Union[str, bytes]) -> Any:
        """Deserialize value from storage with automatic format detection."""
        if isinstance(value, str):
            # Legacy string format (JSON or hex-encoded pickle)
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(bytes.fromhex(value))
                except (ValueError, pickle.PickleError):
                    return value
        
        if not isinstance(value, bytes):
            return value
            
        # New binary format with prefixes
        if value.startswith(b'ZLIB:'):
            # Compressed msgpack
            try:
                decompressed = zlib.decompress(value[5:])
                return msgpack.unpackb(decompressed, raw=False, strict_map_key=False)
            except Exception as e:
                logger.error(f"Failed to decompress/deserialize ZLIB msgpack: {e}")
                return None
                
        elif value.startswith(b'MSGPACK:'):
            # Uncompressed msgpack
            try:
                return msgpack.unpackb(value[8:], raw=False, strict_map_key=False)
            except Exception as e:
                logger.error(f"Failed to deserialize msgpack: {e}")
                return None
                
        elif value.startswith(b'ZLIB_PICKLE:'):
            # Compressed pickle
            try:
                decompressed = zlib.decompress(value[12:])
                return pickle.loads(decompressed)
            except Exception as e:
                logger.error(f"Failed to decompress/deserialize ZLIB pickle: {e}")
                return None
                
        elif value.startswith(b'PICKLE:'):
            # Uncompressed pickle
            try:
                return pickle.loads(value[7:])
            except Exception as e:
                logger.error(f"Failed to deserialize pickle: {e}")
                return None
                
        elif value.startswith(b'ZLIB_JSON:'):
            # Compressed JSON
            try:
                decompressed = zlib.decompress(value[10:])
                return json.loads(decompressed.decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to decompress/deserialize ZLIB JSON: {e}")
                return None
                
        elif value.startswith(b'JSON:'):
            # Uncompressed JSON
            try:
                return json.loads(value[5:].decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to deserialize JSON: {e}")
                return None
        
        # Unknown format, try to decode as string
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            logger.warning("Unknown serialization format, returning raw bytes")
            return value
    
    async def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            # Count keys with our prefix
            key_count = 0
            async for _ in self.redis.scan_iter(match=f"{self.key_prefix}*"):
                key_count += 1
            
            return {
                "total_keys": key_count,
                "key_prefix": self.key_prefix,
                "default_ttl": self.default_ttl
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "error": str(e)
            } 