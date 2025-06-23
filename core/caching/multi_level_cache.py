"""
Multi-level caching system for optimized data access.

Многоуровневая система кэширования для оптимизированного доступа к данным.
"""

import time
from core.logging import get_logger
from typing import Any, Optional, Dict, List, TypeVar
from dataclasses import dataclass, field
from enum import Enum
import pickle
from abc import ABC, abstractmethod

logger = get_logger(__name__)

T = TypeVar('T')


class CacheLevel(Enum):
    """Cache level enumeration."""
    L1_MEMORY = "L1_MEMORY"
    L2_REDIS = "L2_REDIS" 
    L3_DATABASE = "L3_DATABASE"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0
    level: CacheLevel = CacheLevel.L1_MEMORY


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    average_access_time: float = 0.0


class CacheBackend(ABC):
    """Abstract cache backend interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: float = 3600) -> bool:
        """Set value with TTL."""
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value by key."""
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cached values."""
    
    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""


class L1MemoryCache(CacheBackend):
    """L1 Memory cache with LRU eviction."""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.stats = CacheStats()
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from L1 cache."""
        if key in self.cache:
            entry = self.cache[key]
            
            # Check TTL
            if time.time() - entry.timestamp > entry.ttl:
                await self.delete(key)
                self.stats.misses += 1
                return None
            
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = time.time()
            
            # Move to end of access order (LRU)
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            self.stats.hits += 1
            return entry.value
        
        self.stats.misses += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: float = 3600) -> bool:
        """Set value in L1 cache."""
        try:
            # Estimate size
            size_bytes = self._estimate_size(value)
            
            # Check memory limits
            if size_bytes > self.max_memory_bytes:
                logger.warning(f"Value too large for L1 cache: {size_bytes} bytes")
                return False
            
            # Evict if necessary
            await self._evict_if_needed(size_bytes)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl,
                size_bytes=size_bytes,
                level=CacheLevel.L1_MEMORY
            )
            
            # Remove old entry if exists
            if key in self.cache:
                old_entry = self.cache[key]
                self.stats.size_bytes -= old_entry.size_bytes
                if key in self.access_order:
                    self.access_order.remove(key)
            
            # Add new entry
            self.cache[key] = entry
            self.access_order.append(key)
            self.stats.size_bytes += size_bytes
            self.stats.entry_count = len(self.cache)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set L1 cache entry: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from L1 cache."""
        if key in self.cache:
            entry = self.cache[key]
            self.stats.size_bytes -= entry.size_bytes
            del self.cache[key]
            
            if key in self.access_order:
                self.access_order.remove(key)
            
            self.stats.entry_count = len(self.cache)
            return True
        return False
    
    async def clear(self) -> bool:
        """Clear L1 cache."""
        self.cache.clear()
        self.access_order.clear()
        self.stats.size_bytes = 0
        self.stats.entry_count = 0
        return True
    
    async def _evict_if_needed(self, new_size: int):
        """Evict entries if needed for new entry."""
        # Check size limit
        while (len(self.cache) >= self.max_size or 
               self.stats.size_bytes + new_size > self.max_memory_bytes):
            
            if not self.access_order:
                break
                
            # Evict least recently used
            lru_key = self.access_order[0]
            await self.delete(lru_key)
            self.stats.evictions += 1
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value."""
        try:
            if isinstance(value, (str, bytes)):
                return len(value)
            elif isinstance(value, (int, float, bool)):
                return 8
            elif isinstance(value, (list, tuple)):
                return sum(self._estimate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(
                    self._estimate_size(k) + self._estimate_size(v)
                    for k, v in value.items()
                )
            else:
                # Fallback to pickle size
                return len(pickle.dumps(value))
        except Exception:
            return 1000  # Default estimate
    
    def get_stats(self) -> CacheStats:
        """Get L1 cache statistics."""
        total_requests = self.stats.hits + self.stats.misses
        self.stats.hit_rate = (
            self.stats.hits / total_requests if total_requests > 0 else 0.0
        )
        return self.stats


class L2RedisCache(CacheBackend):
    """L2 Redis cache backend."""
    
    def __init__(self, redis_client, prefix: str = "cache:"):
        self.redis = redis_client
        self.prefix = prefix
        self.stats = CacheStats()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            cache_key = f"{self.prefix}{key}"
            data = await self.redis.get(cache_key)
            
            if data is not None:
                self.stats.hits += 1
                return data
            
            self.stats.misses += 1
            return None
            
        except Exception as e:
            logger.error(f"Redis cache get failed: {e}")
            self.stats.misses += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: float = 3600) -> bool:
        """Set value in Redis cache."""
        try:
            cache_key = f"{self.prefix}{key}"
            await self.redis.setex(cache_key, int(ttl), value)
            return True
            
        except Exception as e:
            logger.error(f"Redis cache set failed: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        try:
            cache_key = f"{self.prefix}{key}"
            result = await self.redis.delete(cache_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis cache delete failed: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear Redis cache with prefix."""
        try:
            pattern = f"{self.prefix}*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return True
            
        except Exception as e:
            logger.error(f"Redis cache clear failed: {e}")
            return False
    
    def get_stats(self) -> CacheStats:
        """Get Redis cache statistics."""
        total_requests = self.stats.hits + self.stats.misses
        self.stats.hit_rate = (
            self.stats.hits / total_requests if total_requests > 0 else 0.0
        )
        return self.stats


class L3DatabaseCache(CacheBackend):
    """L3 Database cache backend (placeholder)."""
    
    def __init__(self, db_client):
        self.db = db_client
        self.stats = CacheStats()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from database cache."""
        # Placeholder - would implement database-based caching
        self.stats.misses += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: float = 3600) -> bool:
        """Set value in database cache."""
        # Placeholder - would implement database-based caching
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from database cache."""
        return True
    
    async def clear(self) -> bool:
        """Clear database cache."""
        return True
    
    def get_stats(self) -> CacheStats:
        """Get database cache statistics."""
        return self.stats


class MultiLevelCache:
    """
    Multi-level cache with intelligent data promotion and eviction.
    
    Features:
    - L1: Fast in-memory cache with LRU eviction
    - L2: Redis-based distributed cache
    - L3: Database-backed persistent cache
    - Automatic data promotion between levels
    - Smart prefetching and invalidation
    - Comprehensive performance monitoring
    """
    
    def __init__(
        self,
        l1_cache: Optional[L1MemoryCache] = None,
        l2_cache: Optional[L2RedisCache] = None,
        l3_cache: Optional[L3DatabaseCache] = None,
        enable_promotion: bool = True,
        enable_prefetching: bool = True,
        promotion_threshold: int = 3,  # Promote after 3 accesses
    ):
        self.l1_cache = l1_cache
        self.l2_cache = l2_cache
        self.l3_cache = l3_cache
        self.enable_promotion = enable_promotion
        self.enable_prefetching = enable_prefetching
        self.promotion_threshold = promotion_threshold
        
        # Statistics tracking
        self.global_stats = {
            'total_requests': 0,
            'l1_hits': 0,
            'l2_hits': 0,
            'l3_hits': 0,
            'cache_misses': 0,
            'promotions': 0,
            'prefetches': 0
        }
        
        # Access pattern tracking for prefetching
        self.access_patterns: Dict[str, List[float]] = {}
        self.prefetch_candidates: Dict[str, float] = {}
        
        logger.info(
            f"✅ MultiLevelCache initialized: "
            f"L1={'enabled' if l1_cache else 'disabled'}, "
            f"L2={'enabled' if l2_cache else 'disabled'}, "
            f"L3={'enabled' if l3_cache else 'disabled'}"
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache."""
        start_time = time.time()
        self.global_stats['total_requests'] += 1
        
        try:
            # Try L1 cache first
            if self.l1_cache:
                value = await self.l1_cache.get(key)
                if value is not None:
                    self.global_stats['l1_hits'] += 1
                    await self._track_access_pattern(key)
                    return value
            
            # Try L2 cache
            if self.l2_cache:
                value = await self.l2_cache.get(key)
                if value is not None:
                    self.global_stats['l2_hits'] += 1
                    
                    # Promote to L1 if enabled
                    if self.enable_promotion and self.l1_cache:
                        await self._promote_to_l1(key, value)
                    
                    await self._track_access_pattern(key)
                    return value
            
            # Try L3 cache
            if self.l3_cache:
                value = await self.l3_cache.get(key)
                if value is not None:
                    self.global_stats['l3_hits'] += 1
                    
                    # Promote to higher levels if enabled
                    if self.enable_promotion:
                        if self.l2_cache:
                            await self._promote_to_l2(key, value)
                        if self.l1_cache:
                            await self._promote_to_l1(key, value)
                    
                    await self._track_access_pattern(key)
                    return value
            
            # Cache miss
            self.global_stats['cache_misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Multi-level cache get failed: {e}")
            return None
        finally:
            # Track access time for performance monitoring
            access_time = time.time() - start_time
            logger.debug(f"Cache access for '{key}': {access_time*1000:.2f}ms")
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: float = 3600, 
        levels: Optional[List[CacheLevel]] = None
    ) -> bool:
        """Set value in specified cache levels."""
        if levels is None:
            levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]
        
        success = True
        
        try:
            # Set in L1 if requested
            if CacheLevel.L1_MEMORY in levels and self.l1_cache:
                l1_success = await self.l1_cache.set(key, value, ttl)
                success = success and l1_success
            
            # Set in L2 if requested
            if CacheLevel.L2_REDIS in levels and self.l2_cache:
                l2_success = await self.l2_cache.set(key, value, ttl)
                success = success and l2_success
            
            # Set in L3 if requested
            if CacheLevel.L3_DATABASE in levels and self.l3_cache:
                l3_success = await self.l3_cache.set(key, value, ttl)
                success = success and l3_success
            
            return success
            
        except Exception as e:
            logger.error(f"Multi-level cache set failed: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from all cache levels."""
        success = True
        
        try:
            # Delete from all levels
            if self.l1_cache:
                l1_success = await self.l1_cache.delete(key)
                success = success and l1_success
            
            if self.l2_cache:
                l2_success = await self.l2_cache.delete(key)
                success = success and l2_success
            
            if self.l3_cache:
                l3_success = await self.l3_cache.delete(key)
                success = success and l3_success
            
            # Clean up access patterns
            if key in self.access_patterns:
                del self.access_patterns[key]
            if key in self.prefetch_candidates:
                del self.prefetch_candidates[key]
            
            return success
            
        except Exception as e:
            logger.error(f"Multi-level cache delete failed: {e}")
            return False
    
    async def clear(self, levels: Optional[List[CacheLevel]] = None) -> bool:
        """Clear specified cache levels."""
        if levels is None:
            levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS, CacheLevel.L3_DATABASE]
        
        success = True
        
        try:
            if CacheLevel.L1_MEMORY in levels and self.l1_cache:
                l1_success = await self.l1_cache.clear()
                success = success and l1_success
            
            if CacheLevel.L2_REDIS in levels and self.l2_cache:
                l2_success = await self.l2_cache.clear()
                success = success and l2_success
            
            if CacheLevel.L3_DATABASE in levels and self.l3_cache:
                l3_success = await self.l3_cache.clear()
                success = success and l3_success
            
            # Clear tracking data
            self.access_patterns.clear()
            self.prefetch_candidates.clear()
            
            return success
            
        except Exception as e:
            logger.error(f"Multi-level cache clear failed: {e}")
            return False
    
    async def _promote_to_l1(self, key: str, value: Any):
        """Promote value to L1 cache."""
        if self.l1_cache:
            success = await self.l1_cache.set(key, value)
            if success:
                self.global_stats['promotions'] += 1
                logger.debug(f"Promoted '{key}' to L1 cache")
    
    async def _promote_to_l2(self, key: str, value: Any):
        """Promote value to L2 cache."""
        if self.l2_cache:
            success = await self.l2_cache.set(key, value)
            if success:
                self.global_stats['promotions'] += 1
                logger.debug(f"Promoted '{key}' to L2 cache")
    
    async def _track_access_pattern(self, key: str):
        """Track access patterns for prefetching."""
        if not self.enable_prefetching:
            return
        
        current_time = time.time()
        
        if key not in self.access_patterns:
            self.access_patterns[key] = []
        
        self.access_patterns[key].append(current_time)
        
        # Keep only recent accesses (last hour)
        cutoff_time = current_time - 3600
        self.access_patterns[key] = [
            t for t in self.access_patterns[key] if t > cutoff_time
        ]
        
        # Update prefetch candidates based on access frequency
        access_count = len(self.access_patterns[key])
        if access_count >= self.promotion_threshold:
            self.prefetch_candidates[key] = current_time
    
    async def prefetch_popular_items(self, limit: int = 10):
        """Prefetch popular items to higher cache levels."""
        if not self.enable_prefetching:
            return
        
        # Sort by access frequency and recency
        candidates = sorted(
            self.prefetch_candidates.items(),
            key=lambda x: len(self.access_patterns.get(x[0], [])),
            reverse=True
        )
        
        prefetched = 0
        for key, _ in candidates[:limit]:
            try:
                # Check if already in L1
                if self.l1_cache:
                    l1_value = await self.l1_cache.get(key)
                    if l1_value is not None:
                        continue
                
                # Try to get from L2 and promote to L1
                if self.l2_cache:
                    l2_value = await self.l2_cache.get(key)
                    if l2_value is not None:
                        await self._promote_to_l1(key, l2_value)
                        prefetched += 1
                        self.global_stats['prefetches'] += 1
                        continue
                
                # Try to get from L3 and promote
                if self.l3_cache:
                    l3_value = await self.l3_cache.get(key)
                    if l3_value is not None:
                        if self.l2_cache:
                            await self._promote_to_l2(key, l3_value)
                        if self.l1_cache:
                            await self._promote_to_l1(key, l3_value)
                        prefetched += 1
                        self.global_stats['prefetches'] += 1
                
            except Exception as e:
                logger.error(f"Prefetch failed for '{key}': {e}")
        
        if prefetched > 0:
            logger.debug(f"Prefetched {prefetched} items to higher cache levels")
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = self.global_stats['total_requests']
        cache_hits = (
            self.global_stats['l1_hits'] + 
            self.global_stats['l2_hits'] + 
            self.global_stats['l3_hits']
        )
        
        overall_hit_rate = cache_hits / total_requests if total_requests > 0 else 0.0
        
        stats = {
            'global_stats': {
                'total_requests': total_requests,
                'overall_hit_rate': overall_hit_rate,
                'cache_hits': cache_hits,
                'cache_misses': self.global_stats['cache_misses'],
                'promotions': self.global_stats['promotions'],
                'prefetches': self.global_stats['prefetches']
            },
            'level_breakdown': {
                'l1_hit_rate': self.global_stats['l1_hits'] / total_requests if total_requests > 0 else 0.0,
                'l2_hit_rate': self.global_stats['l2_hits'] / total_requests if total_requests > 0 else 0.0,
                'l3_hit_rate': self.global_stats['l3_hits'] / total_requests if total_requests > 0 else 0.0,
            },
            'cache_levels': {}
        }
        
        # Add individual level stats
        if self.l1_cache:
            stats['cache_levels']['L1'] = self.l1_cache.get_stats().__dict__
        if self.l2_cache:
            stats['cache_levels']['L2'] = self.l2_cache.get_stats().__dict__
        if self.l3_cache:
            stats['cache_levels']['L3'] = self.l3_cache.get_stats().__dict__
        
        # Add prefetching stats
        stats['prefetching'] = {
            'access_patterns_tracked': len(self.access_patterns),
            'prefetch_candidates': len(self.prefetch_candidates),
            'enabled': self.enable_prefetching
        }
        
        return stats 
