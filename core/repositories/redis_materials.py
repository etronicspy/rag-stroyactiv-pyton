"""Redis materials repository implementation.

Реализация репозитория материалов с использованием Redis.
"""

import json
from core.logging import get_logger
from typing import List, Optional, Dict, Any
from datetime import timedelta

from core.repositories.interfaces import IMaterialsRepository
from core.schemas.materials import Material, MaterialCreate, MaterialUpdate
from core.database.interfaces import ICacheDatabase
from core.database.exceptions import DatabaseError

logger = get_logger(__name__)


class RedisMaterialsRepository(IMaterialsRepository):
    """Redis repository for materials caching and session management.
    
    Provides caching layer for materials with TTL support and session management.
    This repository is primarily used for caching frequently accessed materials
    and storing temporary search results.
    """
    
    def __init__(self, cache_db: ICacheDatabase, default_ttl: int = 3600):
        """Initialize Redis materials repository.
        
        Args:
            cache_db: Redis cache database client
            default_ttl: Default TTL for cached materials (in seconds)
        """
        self.cache_db = cache_db
        self.default_ttl = default_ttl
        self.key_prefix = "material:"
        self.search_prefix = "search:"
        self.batch_prefix = "batch:"
    
    async def create(self, material: MaterialCreate) -> Material:
        """Create a new material in cache.
        
        Note: This is primarily for caching. For persistent storage,
        use PostgreSQL or vector database repository.
        
        Args:
            material: Material creation data
            
        Returns:
            Created material
        """
        try:
            # Generate ID for the material
            material_id = f"{material.name}_{hash(material.description)}"
            
            # Create Material object
            material_obj = Material(
                id=material_id,
                name=material.name,
                description=material.description,
                category=material.category,
                unit=material.unit,
                price=material.price,
                metadata=material.metadata or {}
            )
            
            # Cache the material
            cache_key = f"{self.key_prefix}{material_id}"
            await self.cache_db.set(
                key=cache_key,
                value=material_obj.model_dump_json(),
                ttl=self.default_ttl
            )
            
            logger.info(f"Material cached: {material_id}")
            return material_obj
            
        except Exception as e:
            logger.error(f"Failed to create material in cache: {e}")
            raise DatabaseError(f"Failed to cache material: {e}")
    
    async def upsert(self, material: MaterialCreate) -> Material:
        """Insert or update material in cache.
        
        Args:
            material: Material data for upsert
            
        Returns:
            Created or updated material
        """
        return await self.create(material)  # Same as create for cache
    
    async def get_by_id(self, material_id: str) -> Optional[Material]:
        """Get material by ID from cache.
        
        Args:
            material_id: Material identifier
            
        Returns:
            Material or None if not found
        """
        try:
            cache_key = f"{self.key_prefix}{material_id}"
            cached_data = await self.cache_db.get(cache_key)
            
            if cached_data:
                material_dict = json.loads(cached_data)
                return Material(**material_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get material from cache: {e}")
            return None
    
    async def update(self, material_id: str, material_update: MaterialUpdate) -> Optional[Material]:
        """Update material in cache.
        
        Args:
            material_id: Material identifier
            material_update: Material update data
            
        Returns:
            Updated material or None if not found
        """
        try:
            # Get existing material
            existing_material = await self.get_by_id(material_id)
            if not existing_material:
                return None
            
            # Update fields
            update_data = material_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(existing_material, field, value)
            
            # Cache updated material
            cache_key = f"{self.key_prefix}{material_id}"
            await self.cache_db.set(
                key=cache_key,
                value=existing_material.model_dump_json(),
                ttl=self.default_ttl
            )
            
            logger.info(f"Material updated in cache: {material_id}")
            return existing_material
            
        except Exception as e:
            logger.error(f"Failed to update material in cache: {e}")
            return None
    
    async def delete(self, material_id: str) -> bool:
        """Delete material from cache.
        
        Args:
            material_id: Material identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            cache_key = f"{self.key_prefix}{material_id}"
            deleted = await self.cache_db.delete(cache_key)
            
            if deleted:
                logger.info(f"Material deleted from cache: {material_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete material from cache: {e}")
            return False
    
    async def list(self, skip: int = 0, limit: int = 100, 
                  category: Optional[str] = None) -> List[Material]:
        """List materials from cache.
        
        Note: This method scans Redis keys, which can be expensive.
        Consider using for small datasets or implement pagination in source.
        
        Args:
            skip: Number of materials to skip
            limit: Maximum number of materials to return
            category: Optional category filter
            
        Returns:
            List of materials
        """
        try:
            # Get all material keys
            pattern = f"{self.key_prefix}*"
            keys = await self.cache_db.scan_keys(pattern)
            
            materials = []
            for key in keys[skip:skip + limit]:
                cached_data = await self.cache_db.get(key)
                if cached_data:
                    material_dict = json.loads(cached_data)
                    material = Material(**material_dict)
                    
                    # Apply category filter
                    if category is None or material.category == category:
                        materials.append(material)
            
            return materials
            
        except Exception as e:
            logger.error(f"Failed to list materials from cache: {e}")
            return []
    
    async def search_semantic(self, query: str, limit: int = 10) -> List[Material]:
        """Search materials using cached semantic results.
        
        Note: This method looks for cached search results, not performing actual semantic search.
        Actual semantic search should be done by vector database repository.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching materials from cache
        """
        try:
            # Try to get cached search results
            search_key = f"{self.search_prefix}semantic:{hash(query)}"
            cached_results = await self.cache_db.get(search_key)
            
            if cached_results:
                material_ids = json.loads(cached_results)
                materials = []
                
                for material_id in material_ids[:limit]:
                    material = await self.get_by_id(material_id)
                    if material:
                        materials.append(material)
                
                logger.info(f"Returned {len(materials)} cached search results for: {query}")
                return materials
            
            logger.info(f"No cached semantic search results for: {query}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to search materials in cache: {e}")
            return []
    
    async def search_text(self, query: str, limit: int = 10) -> List[Material]:
        """Search materials using cached text search results.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching materials from cache
        """
        try:
            # Try to get cached search results
            search_key = f"{self.search_prefix}text:{hash(query)}"
            cached_results = await self.cache_db.get(search_key)
            
            if cached_results:
                material_ids = json.loads(cached_results)
                materials = []
                
                for material_id in material_ids[:limit]:
                    material = await self.get_by_id(material_id)
                    if material:
                        materials.append(material)
                
                logger.info(f"Returned {len(materials)} cached text search results for: {query}")
                return materials
            
            logger.info(f"No cached text search results for: {query}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to search materials in cache: {e}")
            return []
    
    async def create_batch(self, materials: List[MaterialCreate], 
                          batch_size: int = 100) -> Dict[str, Any]:
        """Create multiple materials in batches (cache).
        
        Args:
            materials: List of materials to create
            batch_size: Size of processing batches
            
        Returns:
            Batch operation results
        """
        try:
            total_materials = len(materials)
            created_count = 0
            failed_count = 0
            
            # Process in batches
            for i in range(0, total_materials, batch_size):
                batch = materials[i:i + batch_size]
                
                for material in batch:
                    try:
                        await self.create(material)
                        created_count += 1
                    except Exception as e:
                        logger.error(f"Failed to create material in batch: {e}")
                        failed_count += 1
            
            result = {
                "total_processed": total_materials,
                "created": created_count,
                "failed": failed_count,
                "success_rate": created_count / total_materials if total_materials > 0 else 0
            }
            
            logger.info(f"Batch create completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Batch create failed: {e}")
            raise DatabaseError(f"Batch create failed: {e}")
    
    async def batch_upsert(self, materials: List[MaterialCreate], 
                          batch_size: int = 100) -> Dict[str, Any]:
        """Upsert multiple materials in batches (cache).
        
        Args:
            materials: List of materials to upsert
            batch_size: Size of processing batches
            
        Returns:
            Batch operation results with created/updated counts
        """
        try:
            total_materials = len(materials)
            upserted_count = 0
            failed_count = 0
            
            # Process in batches
            for i in range(0, total_materials, batch_size):
                batch = materials[i:i + batch_size]
                
                for material in batch:
                    try:
                        await self.upsert(material)
                        upserted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to upsert material in batch: {e}")
                        failed_count += 1
            
            result = {
                "total_processed": total_materials,
                "upserted": upserted_count,
                "failed": failed_count,
                "success_rate": upserted_count / total_materials if total_materials > 0 else 0
            }
            
            logger.info(f"Batch upsert completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            raise DatabaseError(f"Batch upsert failed: {e}")
    
    # Дополнительные методы для кеширования
    async def cache_search_results(self, query: str, search_type: str, 
                                  material_ids: List[str], ttl: int = None) -> bool:
        """Cache search results for future use.
        
        Args:
            query: Search query
            search_type: Type of search ('semantic' or 'text')
            material_ids: List of material IDs from search results
            ttl: Time to live for cached results
            
        Returns:
            True if cached successfully
        """
        try:
            search_key = f"{self.search_prefix}{search_type}:{hash(query)}"
            ttl = ttl or self.default_ttl
            
            await self.cache_db.set(
                key=search_key,
                value=json.dumps(material_ids),
                ttl=ttl
            )
            
            logger.info(f"Cached {search_type} search results for query: {query}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache search results: {e}")
            return False
    
    async def clear_cache(self, pattern: str = None) -> int:
        """Clear cached materials.
        
        Args:
            pattern: Optional pattern to match keys (default: all materials)
            
        Returns:
            Number of deleted keys
        """
        try:
            pattern = pattern or f"{self.key_prefix}*"
            keys = await self.cache_db.scan_keys(pattern)
            
            deleted_count = 0
            for key in keys:
                if await self.cache_db.delete(key):
                    deleted_count += 1
            
            logger.info(f"Cleared {deleted_count} cached materials")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0 