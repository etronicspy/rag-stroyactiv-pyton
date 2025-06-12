"""Demo script for Redis caching functionality.

Демонстрация возможностей Redis кеширования с performance benchmarks.
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from core.database.adapters.redis_adapter import RedisDatabase
from core.repositories.cached_materials import CachedMaterialsRepository
from core.repositories.hybrid_materials import HybridMaterialsRepository
from core.database.adapters.qdrant_adapter import QdrantDatabase
from core.database.adapters.postgresql_adapter import PostgreSQLDatabase
from core.schemas.materials import MaterialCreate, MaterialResponse, MaterialSearchRequest
from core.schemas.search import SearchResponse
from core.config import settings


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisCachingDemo:
    """Demo class for Redis caching functionality."""
    
    def __init__(self):
        """Initialize demo with database connections."""
        self.redis_db = None
        self.cached_repo = None
        self.hybrid_repo = None
        
    async def setup(self):
        """Setup database connections and repositories."""
        try:
            logger.info("🚀 Setting up Redis caching demo...")
            
            # Initialize Redis database
            redis_config = settings.get_redis_config()
            self.redis_db = RedisDatabase(redis_config)
            
            # Test Redis connection
            await self.redis_db.ping()
            logger.info("✅ Redis connection established")
            
            # Initialize hybrid repository (mock for demo)
            self.hybrid_repo = MockHybridRepository()
            
            # Initialize cached repository
            cache_config = {
                "search_ttl": 300,      # 5 minutes
                "material_ttl": 3600,   # 1 hour
                "health_ttl": 60,       # 1 minute
                "batch_size": 100,
                "enable_write_through": False,
                "cache_miss_threshold": 0.3
            }
            
            self.cached_repo = CachedMaterialsRepository(
                hybrid_repository=self.hybrid_repo,
                cache_db=self.redis_db,
                cache_config=cache_config
            )
            
            logger.info("✅ Cached repository initialized")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise
    
    async def demo_basic_redis_operations(self):
        """Demonstrate basic Redis operations."""
        logger.info("\n" + "="*60)
        logger.info("🔧 BASIC REDIS OPERATIONS DEMO")
        logger.info("="*60)
        
        try:
            # Test basic set/get operations
            test_data = {
                "name": "Premium Cement",
                "price": 250.0,
                "category": "cement",
                "supplier": "Best Materials Co.",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Set with TTL
            start_time = time.time()
            await self.redis_db.set("demo:material:1", test_data, ttl=600)
            set_time = (time.time() - start_time) * 1000
            
            # Get data
            start_time = time.time()
            retrieved_data = await self.redis_db.get("demo:material:1")
            get_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Set operation: {set_time:.2f}ms")
            logger.info(f"✅ Get operation: {get_time:.2f}ms")
            logger.info(f"✅ Data integrity: {retrieved_data == test_data}")
            
            # Test TTL operations
            ttl_value = await self.redis_db.ttl("demo:material:1")
            logger.info(f"✅ TTL: {ttl_value} seconds")
            
            # Test exists operation
            exists = await self.redis_db.exists("demo:material:1")
            logger.info(f"✅ Key exists: {exists}")
            
            # Test hash operations
            await self.redis_db.hset("demo:hash", "field1", {"value": 100}, ttl=300)
            hash_value = await self.redis_db.hget("demo:hash", "field1")
            logger.info(f"✅ Hash operation: {hash_value}")
            
        except Exception as e:
            logger.error(f"❌ Basic operations demo failed: {e}")
    
    async def demo_batch_operations(self):
        """Demonstrate batch Redis operations."""
        logger.info("\n" + "="*60)
        logger.info("📦 BATCH OPERATIONS DEMO")
        logger.info("="*60)
        
        try:
            # Prepare batch data
            batch_data = {}
            for i in range(10):
                batch_data[f"batch:material:{i}"] = {
                    "id": f"material-{i}",
                    "name": f"Material {i}",
                    "price": 100.0 + i * 10,
                    "category": "cement" if i % 2 == 0 else "concrete"
                }
            
            # Batch set operation
            start_time = time.time()
            await self.redis_db.mset(batch_data, ttl=600)
            batch_set_time = (time.time() - start_time) * 1000
            
            # Batch get operation
            keys = list(batch_data.keys())
            start_time = time.time()
            retrieved_values = await self.redis_db.mget(keys)
            batch_get_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Batch set ({len(batch_data)} items): {batch_set_time:.2f}ms")
            logger.info(f"✅ Batch get ({len(keys)} items): {batch_get_time:.2f}ms")
            logger.info(f"✅ Data integrity: {len([v for v in retrieved_values if v is not None])} items retrieved")
            
            # Test pattern deletion
            start_time = time.time()
            deleted_count = await self.redis_db.delete_pattern("batch:material:*")
            delete_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Pattern deletion: {deleted_count} keys deleted in {delete_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"❌ Batch operations demo failed: {e}")
    
    async def demo_cached_repository(self):
        """Demonstrate cached repository functionality."""
        logger.info("\n" + "="*60)
        logger.info("🏪 CACHED REPOSITORY DEMO")
        logger.info("="*60)
        
        try:
            # Create sample materials
            materials_to_create = [
                MaterialCreate(
                    name=f"Cached Material {i}",
                    description=f"High quality material {i} for construction",
                    category="cement" if i % 2 == 0 else "concrete",
                    price=150.0 + i * 25,
                    unit="bag",
                    supplier=f"Supplier {i % 3 + 1}"
                )
                for i in range(5)
            ]
            
            # Test create operations
            logger.info("Creating materials...")
            created_materials = []
            for material in materials_to_create:
                start_time = time.time()
                created = await self.cached_repo.create_material(material)
                create_time = (time.time() - start_time) * 1000
                created_materials.append(created)
                logger.info(f"✅ Created material '{created.name}' in {create_time:.2f}ms")
            
            # Test get operations (should hit cache)
            logger.info("\nTesting get operations...")
            for material in created_materials:
                # First get (cache miss)
                start_time = time.time()
                retrieved1 = await self.cached_repo.get_material(material.id)
                miss_time = (time.time() - start_time) * 1000
                
                # Second get (cache hit)
                start_time = time.time()
                retrieved2 = await self.cached_repo.get_material(material.id)
                hit_time = (time.time() - start_time) * 1000
                
                logger.info(f"✅ Get '{material.name}': miss={miss_time:.2f}ms, hit={hit_time:.2f}ms")
            
            # Test search operations
            logger.info("\nTesting search operations...")
            search_queries = ["cement", "concrete", "material", "quality"]
            
            for query in search_queries:
                search_request = MaterialSearchRequest(
                    query=query,
                    limit=10,
                    search_type="hybrid"
                )
                
                # First search (cache miss)
                start_time = time.time()
                result1 = await self.cached_repo.search_materials(search_request)
                miss_time = (time.time() - start_time) * 1000
                
                # Second search (cache hit)
                start_time = time.time()
                result2 = await self.cached_repo.search_materials(search_request)
                hit_time = (time.time() - start_time) * 1000
                
                logger.info(f"✅ Search '{query}': {len(result1.materials)} results, miss={miss_time:.2f}ms, hit={hit_time:.2f}ms")
            
            # Test batch operations
            logger.info("\nTesting batch operations...")
            material_ids = [m.id for m in created_materials]
            
            start_time = time.time()
            batch_materials = await self.cached_repo.get_materials_batch(material_ids)
            batch_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Batch get: {len(batch_materials)} materials in {batch_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"❌ Cached repository demo failed: {e}")
    
    async def demo_cache_management(self):
        """Demonstrate cache management features."""
        logger.info("\n" + "="*60)
        logger.info("⚙️ CACHE MANAGEMENT DEMO")
        logger.info("="*60)
        
        try:
            # Get cache statistics
            stats = await self.cached_repo.get_cache_stats()
            logger.info("📊 Cache Statistics:")
            logger.info(f"   Hit Rate: {stats['cache_performance']['hit_rate']:.2%}")
            logger.info(f"   Total Hits: {stats['cache_performance']['total_hits']}")
            logger.info(f"   Total Misses: {stats['cache_performance']['total_misses']}")
            logger.info(f"   Total Writes: {stats['cache_performance']['total_writes']}")
            logger.info(f"   Total Errors: {stats['cache_performance']['total_errors']}")
            
            # Test cache warming
            logger.info("\n🔥 Testing cache warming...")
            popular_queries = ["cement", "concrete", "steel", "brick"]
            popular_materials = ["material-1", "material-2", "material-3"]
            
            start_time = time.time()
            warming_stats = await self.cached_repo.warm_cache(
                popular_queries=popular_queries,
                material_ids=popular_materials
            )
            warming_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Cache warming completed in {warming_time:.2f}ms:")
            logger.info(f"   Queries cached: {warming_stats['queries_cached']}")
            logger.info(f"   Materials cached: {warming_stats['materials_cached']}")
            logger.info(f"   Errors: {warming_stats['errors']}")
            
            # Test cache clearing
            logger.info("\n🧹 Testing cache clearing...")
            
            # Clear specific pattern
            start_time = time.time()
            cleared_search = await self.cached_repo.clear_cache("search:*")
            clear_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Cleared search cache: {cleared_search} keys in {clear_time:.2f}ms")
            
            # Get updated statistics
            updated_stats = await self.cached_repo.get_cache_stats()
            logger.info(f"📊 Updated hit rate: {updated_stats['cache_performance']['hit_rate']:.2%}")
            
        except Exception as e:
            logger.error(f"❌ Cache management demo failed: {e}")
    
    async def demo_performance_comparison(self):
        """Demonstrate performance comparison between cached and non-cached operations."""
        logger.info("\n" + "="*60)
        logger.info("🏁 PERFORMANCE COMPARISON DEMO")
        logger.info("="*60)
        
        try:
            # Reset cache statistics
            await self.cached_repo.reset_stats()
            
            # Test search performance
            search_request = MaterialSearchRequest(
                query="high quality cement",
                limit=20,
                search_type="hybrid"
            )
            
            # Warm up cache
            await self.cached_repo.search_materials(search_request)
            
            # Performance test parameters
            num_iterations = 5
            
            # Test cached search performance
            logger.info(f"🔄 Testing cached search performance ({num_iterations} iterations)...")
            
            cached_times = []
            for i in range(num_iterations):
                start_time = time.time()
                result = await self.cached_repo.search_materials(search_request, use_cache=True)
                cached_times.append((time.time() - start_time) * 1000)
            
            # Test non-cached search performance
            logger.info(f"🔄 Testing non-cached search performance ({num_iterations} iterations)...")
            
            non_cached_times = []
            for i in range(num_iterations):
                start_time = time.time()
                result = await self.cached_repo.search_materials(search_request, use_cache=False)
                non_cached_times.append((time.time() - start_time) * 1000)
            
            # Calculate statistics
            avg_cached = sum(cached_times) / len(cached_times)
            avg_non_cached = sum(non_cached_times) / len(non_cached_times)
            speedup = avg_non_cached / avg_cached
            
            logger.info(f"📊 Performance Results:")
            logger.info(f"   Cached search average: {avg_cached:.2f}ms")
            logger.info(f"   Non-cached search average: {avg_non_cached:.2f}ms")
            logger.info(f"   Speedup: {speedup:.2f}x faster with cache")
            
        except Exception as e:
            logger.error(f"❌ Performance comparison demo failed: {e}")
    
    async def demo_health_monitoring(self):
        """Demonstrate health monitoring capabilities."""
        logger.info("\n" + "="*60)
        logger.info("🏥 HEALTH MONITORING DEMO")
        logger.info("="*60)
        
        try:
            # Redis health check
            redis_health = await self.redis_db.health_check()
            logger.info("🔍 Redis Health Check:")
            logger.info(f"   Status: {redis_health['status']}")
            logger.info(f"   Ping Time: {redis_health['ping_time_seconds']:.3f}s")
            
            if 'redis_info' in redis_health:
                logger.info(f"   Redis Version: {redis_health['redis_info'].get('version', 'N/A')}")
                logger.info(f"   Connected Clients: {redis_health['redis_info'].get('connected_clients', 'N/A')}")
                logger.info(f"   Used Memory: {redis_health['redis_info'].get('used_memory_human', 'N/A')}")
            
            if 'cache_stats' in redis_health:
                logger.info(f"   Cache Keys: {redis_health['cache_stats'].get('total_keys', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ Health monitoring demo failed: {e}")
    
    async def cleanup(self):
        """Cleanup demo resources."""
        logger.info("\n" + "="*60)
        logger.info("🧹 CLEANUP")
        logger.info("="*60)
        
        try:
            # Clear all demo data
            if self.redis_db:
                deleted_count = await self.redis_db.clear_cache()
                logger.info(f"✅ Cleared {deleted_count} cache keys")
                
                # Close Redis connections
                await self.redis_db.close()
                logger.info("✅ Redis connections closed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    async def run_full_demo(self):
        """Run the complete Redis caching demo."""
        try:
            await self.setup()
            await self.demo_basic_redis_operations()
            await self.demo_batch_operations()
            await self.demo_cached_repository()
            await self.demo_cache_management()
            await self.demo_performance_comparison()
            await self.demo_health_monitoring()
            
            logger.info("\n" + "="*60)
            logger.info("🎉 REDIS CACHING DEMO COMPLETED SUCCESSFULLY!")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
        finally:
            await self.cleanup()


class MockHybridRepository:
    """Mock hybrid repository for demo purposes."""
    
    def __init__(self):
        self.materials = {}
        self.search_delay = 0.1  # Simulate database latency
    
    async def create_material(self, material: MaterialCreate, generate_embedding: bool = True) -> MaterialResponse:
        """Mock create material."""
        await asyncio.sleep(self.search_delay)
        
        material_id = f"material-{len(self.materials) + 1}"
        created_material = MaterialResponse(
            id=material_id,
            **material.dict(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.materials[material_id] = created_material
        return created_material
    
    async def get_material(self, material_id: str) -> MaterialResponse:
        """Mock get material."""
        await asyncio.sleep(self.search_delay)
        return self.materials.get(material_id)
    
    async def search_materials(self, request: MaterialSearchRequest) -> SearchResponse:
        """Mock search materials."""
        await asyncio.sleep(self.search_delay)
        
        # Simple mock search
        matching_materials = [
            MaterialResponse(
                id=f"material-{i}",
                name=f"Mock Material {i}",
                description=f"Mock description for {request.query}",
                category="cement",
                price=100.0 + i * 10,
                unit="bag",
                supplier="Mock Supplier",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for i in range(min(request.limit, 5))
        ]
        
        return SearchResponse(
            materials=matching_materials,
            total=len(matching_materials),
            query=request.query,
            search_type=request.search_type,
            response_time_ms=self.search_delay * 1000
        )
    
    async def get_materials_batch(self, material_ids: List[str]) -> List[MaterialResponse]:
        """Mock batch get materials."""
        await asyncio.sleep(self.search_delay)
        return [self.materials[mid] for mid in material_ids if mid in self.materials]
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        return {
            "status": "healthy",
            "database_type": "MockHybridRepository",
            "response_time_seconds": 0.001
        }


async def main():
    """Main demo function."""
    demo = RedisCachingDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main()) 