"""Cached materials repository with intelligent caching strategies.

Кеширующий репозиторий материалов с интеллектуальным кешированием и cache-aside pattern.
"""

import json
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import asyncio

from core.repositories.hybrid_materials import HybridMaterialsRepository
from core.database.adapters.redis_adapter import RedisDatabase
from core.database.exceptions import DatabaseError, CacheError
from core.schemas.materials import MaterialCreate, MaterialResponse, MaterialSearchRequest
from core.schemas.search import SearchResponse


logger = logging.getLogger(__name__)


class CachedMaterialsRepository:
    """Materials repository with intelligent Redis caching.
    
    Репозиторий материалов с интеллектуальным Redis кешированием и cache-aside pattern.
    """
    
    def __init__(
        self,
        hybrid_repository: HybridMaterialsRepository,
        cache_db: RedisDatabase,
        cache_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize cached repository.
        
        Args:
            hybrid_repository: Underlying hybrid repository
            cache_db: Redis cache database
            cache_config: Cache configuration
                - search_ttl: Search results TTL (default: 300s)
                - material_ttl: Material data TTL (default: 3600s)
                - health_ttl: Health check TTL (default: 60s)
                - batch_size: Batch processing size (default: 100)
                - enable_write_through: Enable write-through caching (default: False)
                - cache_miss_threshold: Cache miss threshold for warming (default: 0.3)
        """
        self.hybrid_repo = hybrid_repository
        self.cache_db = cache_db
        
        # Cache configuration
        config = cache_config or {}
        self.search_ttl = config.get("search_ttl", 300)  # 5 minutes
        self.material_ttl = config.get("material_ttl", 3600)  # 1 hour
        self.health_ttl = config.get("health_ttl", 60)  # 1 minute
        self.batch_size = config.get("batch_size", 100)
        self.enable_write_through = config.get("enable_write_through", False)
        self.cache_miss_threshold = config.get("cache_miss_threshold", 0.3)
        
        # Cache statistics
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_writes": 0,
            "cache_errors": 0,
            "last_reset": datetime.utcnow()
        }
        
        logger.info(f"Cached materials repository initialized with TTLs: search={self.search_ttl}s, material={self.material_ttl}s")
    
    # === Search operations with caching ===
    
    async def search_materials(
        self,
        request: MaterialSearchRequest,
        use_cache: bool = True
    ) -> SearchResponse:
        """Search materials with intelligent caching.
        
        Args:
            request: Search request
            use_cache: Whether to use cache
            
        Returns:
            Search response with cached or fresh results
            
        Raises:
            DatabaseError: If search fails
        """
        try:
            # Generate cache key from search parameters
            cache_key = self._generate_search_cache_key(request)
            
            # Try cache first if enabled
            if use_cache:
                cached_result = await self._get_cached_search(cache_key)
                if cached_result:
                    self.stats["cache_hits"] += 1
                    logger.debug(f"Cache hit for search: {cache_key}")
                    return cached_result
                
                self.stats["cache_misses"] += 1
                logger.debug(f"Cache miss for search: {cache_key}")
            
            # Perform actual search
            start_time = datetime.utcnow()
            result = await self.hybrid_repo.search_materials(request)
            search_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Cache the result if caching is enabled
            if use_cache and result.materials:
                await self._cache_search_result(cache_key, result, search_time)
                self.stats["cache_writes"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Search with caching failed: {e}")
            self.stats["cache_errors"] += 1
            raise DatabaseError(
                message="Search with caching failed",
                details=str(e)
            )
    
    async def vector_search(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        use_cache: bool = True
    ) -> List[MaterialResponse]:
        """Vector search with caching.
        
        Args:
            query: Search query
            limit: Maximum results
            threshold: Similarity threshold
            use_cache: Whether to use cache
            
        Returns:
            List of materials
        """
        try:
            # Generate cache key
            cache_key = f"vector_search:{self._hash_query(query)}:{limit}:{threshold}"
            
            # Try cache first
            if use_cache:
                cached_result = await self._get_cached_materials_list(cache_key)
                if cached_result is not None:
                    self.stats["cache_hits"] += 1
                    return cached_result
                
                self.stats["cache_misses"] += 1
            
            # Perform vector search
            result = await self.hybrid_repo.vector_search(query, limit, threshold)
            
            # Cache the result
            if use_cache and result:
                await self._cache_materials_list(cache_key, result, self.search_ttl)
                self.stats["cache_writes"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Vector search with caching failed: {e}")
            self.stats["cache_errors"] += 1
            raise DatabaseError(
                message="Vector search with caching failed",
                details=str(e)
            )
    
    async def sql_search(
        self,
        query: str,
        limit: int = 10,
        use_cache: bool = True
    ) -> List[MaterialResponse]:
        """SQL search with caching.
        
        Args:
            query: Search query
            limit: Maximum results
            use_cache: Whether to use cache
            
        Returns:
            List of materials
        """
        try:
            # Generate cache key
            cache_key = f"sql_search:{self._hash_query(query)}:{limit}"
            
            # Try cache first
            if use_cache:
                cached_result = await self._get_cached_materials_list(cache_key)
                if cached_result is not None:
                    self.stats["cache_hits"] += 1
                    return cached_result
                
                self.stats["cache_misses"] += 1
            
            # Perform SQL search
            result = await self.hybrid_repo.sql_search(query, limit)
            
            # Cache the result
            if use_cache and result:
                await self._cache_materials_list(cache_key, result, self.search_ttl)
                self.stats["cache_writes"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"SQL search with caching failed: {e}")
            self.stats["cache_errors"] += 1
            raise DatabaseError(
                message="SQL search with caching failed",
                details=str(e)
            )
    
    # === CRUD operations with caching ===
    
    async def create_material(
        self,
        material: MaterialCreate,
        generate_embedding: bool = True
    ) -> MaterialResponse:
        """Create material with cache invalidation.
        
        Args:
            material: Material to create
            generate_embedding: Whether to generate embedding
            
        Returns:
            Created material
        """
        try:
            # Create material
            result = await self.hybrid_repo.create_material(material, generate_embedding)
            
            # Cache the new material
            material_cache_key = f"material:{result.id}"
            await self._cache_material(material_cache_key, result, self.material_ttl)
            
            # Invalidate related search caches
            await self._invalidate_search_caches(material.name)
            
            self.stats["cache_writes"] += 1
            logger.debug(f"Created and cached material: {result.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Create material with caching failed: {e}")
            self.stats["cache_errors"] += 1
            raise DatabaseError(
                message="Create material with caching failed",
                details=str(e)
            )
    
    async def get_material(
        self,
        material_id: str,
        use_cache: bool = True
    ) -> Optional[MaterialResponse]:
        """Get material by ID with caching.
        
        Args:
            material_id: Material ID
            use_cache: Whether to use cache
            
        Returns:
            Material or None if not found
        """
        try:
            cache_key = f"material:{material_id}"
            
            # Try cache first
            if use_cache:
                cached_material = await self._get_cached_material(cache_key)
                if cached_material:
                    self.stats["cache_hits"] += 1
                    return cached_material
                
                self.stats["cache_misses"] += 1
            
            # Get from database
            result = await self.hybrid_repo.get_material(material_id)
            
            # Cache the result
            if use_cache and result:
                await self._cache_material(cache_key, result, self.material_ttl)
                self.stats["cache_writes"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Get material with caching failed: {e}")
            self.stats["cache_errors"] += 1
            raise DatabaseError(
                message="Get material with caching failed",
                details=str(e)
            )
    
    async def update_material(
        self,
        material_id: str,
        updates: Dict[str, Any],
        regenerate_embedding: bool = True
    ) -> Optional[MaterialResponse]:
        """Update material with cache invalidation.
        
        Args:
            material_id: Material ID
            updates: Fields to update
            regenerate_embedding: Whether to regenerate embedding
            
        Returns:
            Updated material or None if not found
        """
        try:
            # Update material
            result = await self.hybrid_repo.update_material(
                material_id, updates, regenerate_embedding
            )
            
            if result:
                # Update cache
                material_cache_key = f"material:{material_id}"
                await self._cache_material(material_cache_key, result, self.material_ttl)
                
                # Invalidate related search caches
                if "name" in updates:
                    await self._invalidate_search_caches(updates["name"])
                
                self.stats["cache_writes"] += 1
                logger.debug(f"Updated and cached material: {material_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Update material with caching failed: {e}")
            self.stats["cache_errors"] += 1
            raise DatabaseError(
                message="Update material with caching failed",
                details=str(e)
            )
    
    async def delete_material(self, material_id: str) -> bool:
        """Delete material with cache invalidation.
        
        Args:
            material_id: Material ID
            
        Returns:
            True if deleted
        """
        try:
            # Get material name for cache invalidation
            material = await self.get_material(material_id, use_cache=False)
            
            # Delete material
            result = await self.hybrid_repo.delete_material(material_id)
            
            if result:
                # Remove from cache
                material_cache_key = f"material:{material_id}"
                await self.cache_db.delete(material_cache_key)
                
                # Invalidate related search caches
                if material:
                    await self._invalidate_search_caches(material.name)
                
                logger.debug(f"Deleted and removed from cache: {material_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Delete material with caching failed: {e}")
            self.stats["cache_errors"] += 1
            raise DatabaseError(
                message="Delete material with caching failed",
                details=str(e)
            )
    
    # === Batch operations with caching ===
    
    async def batch_create_materials(
        self,
        materials: List[MaterialCreate],
        generate_embeddings: bool = True
    ) -> List[MaterialResponse]:
        """Batch create materials with caching.
        
        Args:
            materials: Materials to create
            generate_embeddings: Whether to generate embeddings
            
        Returns:
            List of created materials
        """
        try:
            # Create materials
            results = await self.hybrid_repo.batch_create_materials(
                materials, generate_embeddings
            )
            
            # Cache all created materials
            cache_tasks = []
            for result in results:
                cache_key = f"material:{result.id}"
                cache_tasks.append(
                    self._cache_material(cache_key, result, self.material_ttl)
                )
            
            if cache_tasks:
                await asyncio.gather(*cache_tasks, return_exceptions=True)
                self.stats["cache_writes"] += len(results)
            
            # Invalidate search caches
            await self._invalidate_all_search_caches()
            
            logger.info(f"Batch created and cached {len(results)} materials")
            return results
            
        except Exception as e:
            logger.error(f"Batch create materials with caching failed: {e}")
            self.stats["cache_errors"] += 1
            raise DatabaseError(
                message="Batch create materials with caching failed",
                details=str(e)
            )
    
    async def get_materials_batch(
        self,
        material_ids: List[str],
        use_cache: bool = True
    ) -> List[MaterialResponse]:
        """Get multiple materials with batch caching.
        
        Args:
            material_ids: List of material IDs
            use_cache: Whether to use cache
            
        Returns:
            List of materials (excluding not found)
        """
        try:
            if not use_cache:
                return await self.hybrid_repo.get_materials_batch(material_ids)
            
            # Try to get from cache first
            cache_keys = [f"material:{mid}" for mid in material_ids]
            cached_materials = await self.cache_db.mget(cache_keys)
            
            # Separate cached and missing materials
            results = []
            missing_ids = []
            
            for i, cached_data in enumerate(cached_materials):
                if cached_data:
                    try:
                        material = MaterialResponse(**cached_data)
                        results.append(material)
                        self.stats["cache_hits"] += 1
                    except Exception as e:
                        logger.warning(f"Failed to deserialize cached material {material_ids[i]}: {e}")
                        missing_ids.append(material_ids[i])
                        self.stats["cache_misses"] += 1
                else:
                    missing_ids.append(material_ids[i])
                    self.stats["cache_misses"] += 1
            
            # Fetch missing materials from database
            if missing_ids:
                missing_materials = await self.hybrid_repo.get_materials_batch(missing_ids)
                
                # Cache the missing materials
                cache_tasks = []
                for material in missing_materials:
                    cache_key = f"material:{material.id}"
                    cache_tasks.append(
                        self._cache_material(cache_key, material, self.material_ttl)
                    )
                    results.append(material)
                
                if cache_tasks:
                    await asyncio.gather(*cache_tasks, return_exceptions=True)
                    self.stats["cache_writes"] += len(missing_materials)
            
            logger.debug(f"Batch retrieved {len(results)} materials ({len(results) - len(missing_ids)} from cache)")
            return results
            
        except Exception as e:
            logger.error(f"Batch get materials with caching failed: {e}")
            self.stats["cache_errors"] += 1
            raise DatabaseError(
                message="Batch get materials with caching failed",
                details=str(e)
            )
    
    # === Cache management ===
    
    async def warm_cache(
        self,
        popular_queries: Optional[List[str]] = None,
        material_ids: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Warm cache with popular data.
        
        Args:
            popular_queries: List of popular search queries
            material_ids: List of popular material IDs
            
        Returns:
            Statistics about cache warming
        """
        try:
            stats = {"queries_cached": 0, "materials_cached": 0, "errors": 0}
            
            # Warm popular search queries
            if popular_queries:
                for query in popular_queries:
                    try:
                        # Create a basic search request
                        request = MaterialSearchRequest(
                            query=query,
                            limit=20,
                            search_type="hybrid"
                        )
                        
                        # Perform search (will cache automatically)
                        await self.search_materials(request, use_cache=True)
                        stats["queries_cached"] += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to warm cache for query '{query}': {e}")
                        stats["errors"] += 1
            
            # Warm popular materials
            if material_ids:
                try:
                    materials = await self.get_materials_batch(material_ids, use_cache=True)
                    stats["materials_cached"] = len(materials)
                    
                except Exception as e:
                    logger.warning(f"Failed to warm cache for materials: {e}")
                    stats["errors"] += 1
            
            logger.info(f"Cache warming completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            raise DatabaseError(
                message="Cache warming failed",
                details=str(e)
            )
    
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries.
        
        Args:
            pattern: Pattern to match (None for all)
            
        Returns:
            Number of deleted keys
        """
        try:
            if pattern:
                deleted = await self.cache_db.delete_pattern(pattern)
            else:
                deleted = await self.cache_db.clear_cache()
            
            logger.info(f"Cleared {deleted} cache entries")
            return deleted
            
        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")
            raise DatabaseError(
                message="Cache clearing failed",
                details=str(e)
            )
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics and performance metrics
        """
        try:
            # Calculate hit rate
            total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
            hit_rate = (self.stats["cache_hits"] / total_requests) if total_requests > 0 else 0.0
            
            # Get Redis stats
            redis_health = await self.cache_db.health_check()
            
            return {
                "cache_performance": {
                    "hit_rate": hit_rate,
                    "total_hits": self.stats["cache_hits"],
                    "total_misses": self.stats["cache_misses"],
                    "total_writes": self.stats["cache_writes"],
                    "total_errors": self.stats["cache_errors"],
                    "stats_since": self.stats["last_reset"].isoformat()
                },
                "cache_configuration": {
                    "search_ttl": self.search_ttl,
                    "material_ttl": self.material_ttl,
                    "health_ttl": self.health_ttl,
                    "batch_size": self.batch_size,
                    "write_through_enabled": self.enable_write_through
                },
                "redis_status": redis_health,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_writes": 0,
            "cache_errors": 0,
            "last_reset": datetime.utcnow()
        }
        logger.info("Cache statistics reset")
    
    # === Health check ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of cached repository.
        
        Returns:
            Health status information
        """
        try:
            # Check cache health
            cache_key = "health_check"
            cached_health = await self.cache_db.get(cache_key, default=None)
            
            if cached_health:
                return cached_health
            
            # Perform comprehensive health check
            start_time = datetime.utcnow()
            
            # Check hybrid repository
            hybrid_health = await self.hybrid_repo.health_check()
            
            # Check cache database
            cache_health = await self.cache_db.health_check()
            
            # Test cache operations
            test_key = f"health_test:{datetime.utcnow().timestamp()}"
            test_value = {"test": True, "timestamp": datetime.utcnow().isoformat()}
            
            await self.cache_db.set(test_key, test_value, ttl=60)
            retrieved_value = await self.cache_db.get(test_key)
            await self.cache_db.delete(test_key)
            
            cache_operations_ok = retrieved_value is not None
            
            total_time = (datetime.utcnow() - start_time).total_seconds()
            
            health_status = {
                "status": "healthy" if (
                    hybrid_health.get("status") == "healthy" and
                    cache_health.get("status") == "healthy" and
                    cache_operations_ok
                ) else "unhealthy",
                "repository_type": "CachedMaterialsRepository",
                "response_time_seconds": total_time,
                "components": {
                    "hybrid_repository": hybrid_health,
                    "cache_database": cache_health,
                    "cache_operations": {
                        "status": "healthy" if cache_operations_ok else "unhealthy",
                        "operations_tested": ["set", "get", "delete"]
                    }
                },
                "cache_stats": await self.get_cache_stats(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache the health check result
            await self.cache_db.set(cache_key, health_status, ttl=self.health_ttl)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "repository_type": "CachedMaterialsRepository",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # === Private helper methods ===
    
    def _generate_search_cache_key(self, request: MaterialSearchRequest) -> str:
        """Generate cache key for search request."""
        # Create a deterministic hash of search parameters
        key_data = {
            "query": request.query,
            "limit": request.limit,
            "search_type": request.search_type,
            "threshold": getattr(request, "threshold", None),
            "filters": getattr(request, "filters", None)
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"search:{key_hash}"
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query string."""
        return hashlib.md5(query.encode()).hexdigest()[:16]
    
    async def _get_cached_search(self, cache_key: str) -> Optional[SearchResponse]:
        """Get cached search result."""
        try:
            cached_data = await self.cache_db.get(cache_key, default=None)
            if cached_data:
                return SearchResponse(**cached_data)
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get cached search result: {e}")
            return None
    
    async def _cache_search_result(
        self,
        cache_key: str,
        result: SearchResponse,
        search_time: float
    ) -> None:
        """Cache search result."""
        try:
            # Add metadata to cached result
            cached_data = result.dict()
            cached_data["_cached_at"] = datetime.utcnow().isoformat()
            cached_data["_search_time"] = search_time
            
            await self.cache_db.set(cache_key, cached_data, ttl=self.search_ttl)
            
        except Exception as e:
            logger.warning(f"Failed to cache search result: {e}")
    
    async def _get_cached_material(self, cache_key: str) -> Optional[MaterialResponse]:
        """Get cached material."""
        try:
            cached_data = await self.cache_db.get(cache_key, default=None)
            if cached_data:
                return MaterialResponse(**cached_data)
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get cached material: {e}")
            return None
    
    async def _cache_material(
        self,
        cache_key: str,
        material: MaterialResponse,
        ttl: int
    ) -> None:
        """Cache material."""
        try:
            cached_data = material.dict()
            cached_data["_cached_at"] = datetime.utcnow().isoformat()
            
            await self.cache_db.set(cache_key, cached_data, ttl=ttl)
            
        except Exception as e:
            logger.warning(f"Failed to cache material: {e}")
    
    async def _get_cached_materials_list(self, cache_key: str) -> Optional[List[MaterialResponse]]:
        """Get cached materials list."""
        try:
            cached_data = await self.cache_db.get(cache_key, default=None)
            if cached_data and isinstance(cached_data, list):
                return [MaterialResponse(**item) for item in cached_data]
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get cached materials list: {e}")
            return None
    
    async def _cache_materials_list(
        self,
        cache_key: str,
        materials: List[MaterialResponse],
        ttl: int
    ) -> None:
        """Cache materials list."""
        try:
            cached_data = [material.dict() for material in materials]
            await self.cache_db.set(cache_key, cached_data, ttl=ttl)
            
        except Exception as e:
            logger.warning(f"Failed to cache materials list: {e}")
    
    async def _invalidate_search_caches(self, query_hint: str) -> None:
        """Invalidate search caches related to query."""
        try:
            # Invalidate search caches that might contain this material
            patterns = [
                "search:*",  # All search results
                f"vector_search:*{self._hash_query(query_hint)}*",
                f"sql_search:*{self._hash_query(query_hint)}*"
            ]
            
            for pattern in patterns:
                try:
                    await self.cache_db.delete_pattern(pattern)
                except Exception as e:
                    logger.warning(f"Failed to invalidate cache pattern '{pattern}': {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to invalidate search caches: {e}")
    
    async def _invalidate_all_search_caches(self) -> None:
        """Invalidate all search caches."""
        try:
            patterns = ["search:*", "vector_search:*", "sql_search:*"]
            
            for pattern in patterns:
                try:
                    await self.cache_db.delete_pattern(pattern)
                except Exception as e:
                    logger.warning(f"Failed to invalidate cache pattern '{pattern}': {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to invalidate all search caches: {e}") 