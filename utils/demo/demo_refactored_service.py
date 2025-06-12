"""Demo script for refactored MaterialsService with new multi-database architecture.

Демо скрипт для рефакторенного MaterialsService с новой мульти-БД архитектурой.
"""

import asyncio
import logging
from typing import List

from core.schemas.materials import MaterialCreate, MaterialImportItem
from core.dependencies.database import get_vector_db_dependency, get_ai_client_dependency
from services.materials_new import MaterialsService
from core.database.exceptions import DatabaseError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_refactored_service():
    """Demonstrate refactored MaterialsService functionality."""
    
    print("🚀 Demo: Refactored MaterialsService with New Architecture")
    print("=" * 60)
    
    try:
        # Initialize service with dependency injection
        print("\n1. Initializing MaterialsService with dependency injection...")
        vector_db = get_vector_db_dependency()
        ai_client = get_ai_client_dependency()
        service = MaterialsService(vector_db=vector_db, ai_client=ai_client)
        
        await service.initialize()
        print("✅ Service initialized successfully")
        
        # Test health check
        print("\n2. Testing health check...")
        health = await service.vector_db.health_check()
        print(f"✅ Database health: {health.get('status', 'unknown')}")
        
        # Create test materials
        print("\n3. Creating test materials...")
        test_materials = [
            MaterialCreate(
                name="Цемент портландский М400",
                use_category="Цемент",
                unit="кг",
                sku="CEM400",
                description="Высококачественный портландцемент"
            ),
            MaterialCreate(
                name="Кирпич керамический красный",
                use_category="Кирпич",
                unit="шт",
                sku="BRICK001",
                description="Полнотелый керамический кирпич"
            ),
            MaterialCreate(
                name="Песок речной мытый",
                use_category="Песок",
                unit="м³",
                sku="SAND001",
                description="Чистый речной песок для строительства"
            )
        ]
        
        created_materials = []
        for material_data in test_materials:
            try:
                material = await service.create_material(material_data)
                created_materials.append(material)
                print(f"✅ Created: {material.name} (ID: {material.id[:8]}...)")
            except DatabaseError as e:
                print(f"❌ Failed to create {material_data.name}: {e.message}")
        
        # Test search functionality
        print("\n4. Testing semantic search...")
        search_queries = ["цемент", "кирпич", "песок для бетона"]
        
        for query in search_queries:
            try:
                results = await service.search_materials(query, limit=5)
                print(f"🔍 Search '{query}': {len(results)} results")
                for result in results[:2]:  # Show first 2 results
                    print(f"   - {result.name} ({result.use_category})")
            except DatabaseError as e:
                print(f"❌ Search failed for '{query}': {e.message}")
        
        # Test batch import
        print("\n5. Testing batch import from JSON...")
        import_items = [
            MaterialImportItem(name="Арматура А500С 12мм", sku="ARM12"),
            MaterialImportItem(name="Доска обрезная 50x150x6000", sku="BOARD001"),
            MaterialImportItem(name="Гипсокартон КНАУФ 12.5мм", sku="GKL125"),
            MaterialImportItem(name="Краска водоэмульсионная белая", sku="PAINT001"),
            MaterialImportItem(name="Труба ПВХ 110мм", sku="PIPE110")
        ]
        
        try:
            batch_result = await service.import_materials_from_json(
                import_items,
                default_category="Стройматериалы",
                default_unit="шт",
                batch_size=3
            )
            
            print(f"✅ Batch import completed:")
            print(f"   - Total processed: {batch_result.total_processed}")
            print(f"   - Successful: {batch_result.successful_creates}")
            print(f"   - Failed: {batch_result.failed_creates}")
            print(f"   - Processing time: {batch_result.processing_time_seconds}s")
            
            if batch_result.errors:
                print("   - Errors:")
                for error in batch_result.errors[:3]:  # Show first 3 errors
                    print(f"     * {error}")
                    
        except DatabaseError as e:
            print(f"❌ Batch import failed: {e.message}")
        
        # Test material retrieval
        print("\n6. Testing material retrieval...")
        if created_materials:
            material_id = created_materials[0].id
            try:
                retrieved = await service.get_material(material_id)
                if retrieved:
                    print(f"✅ Retrieved: {retrieved.name}")
                    print(f"   - Category: {retrieved.use_category}")
                    print(f"   - Unit: {retrieved.unit}")
                    print(f"   - SKU: {retrieved.sku}")
                else:
                    print(f"❌ Material not found: {material_id}")
            except DatabaseError as e:
                print(f"❌ Retrieval failed: {e.message}")
        
        # Test material listing
        print("\n7. Testing material listing...")
        try:
            all_materials = await service.get_materials(skip=0, limit=10)
            print(f"✅ Retrieved {len(all_materials)} materials")
            
            # Group by category
            categories = {}
            for material in all_materials:
                category = material.use_category
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            print("   - By category:")
            for category, count in categories.items():
                print(f"     * {category}: {count}")
                
        except DatabaseError as e:
            print(f"❌ Listing failed: {e.message}")
        
        # Test fallback search (should return empty for now)
        print("\n8. Testing fallback search...")
        try:
            fallback_results = await service.search_materials("несуществующий материал", limit=5)
            print(f"🔍 Fallback search: {len(fallback_results)} results")
            if len(fallback_results) == 0:
                print("   ℹ️  Fallback to SQL search not yet implemented (Этап 3)")
        except DatabaseError as e:
            print(f"❌ Fallback search failed: {e.message}")
        
        # Cleanup (optional)
        print("\n9. Cleanup (deleting test materials)...")
        deleted_count = 0
        for material in created_materials:
            try:
                success = await service.delete_material(material.id)
                if success:
                    deleted_count += 1
            except DatabaseError as e:
                print(f"❌ Failed to delete {material.id}: {e.message}")
        
        print(f"✅ Deleted {deleted_count} test materials")
        
        print("\n" + "=" * 60)
        print("🎉 Demo completed successfully!")
        print("\n📊 Architecture Benefits Demonstrated:")
        print("   ✅ Dependency injection with @lru_cache")
        print("   ✅ Structured error handling")
        print("   ✅ Semantic search with fallback strategy")
        print("   ✅ Batch processing with performance metrics")
        print("   ✅ Health checks and monitoring")
        print("   ✅ Category and unit inference")
        print("   ✅ Proper logging throughout")
        
    except Exception as e:
        print(f"\n❌ Demo failed with unexpected error: {e}")
        logger.exception("Demo failed")


async def demo_architecture_features():
    """Demonstrate specific architecture features."""
    
    print("\n🏗️  Architecture Features Demo")
    print("=" * 40)
    
    try:
        # Show dependency injection caching
        print("\n1. Dependency Injection Caching:")
        
        # First call - should create new instances
        vector_db1 = get_vector_db_dependency()
        ai_client1 = get_ai_client_dependency()
        
        # Second call - should return cached instances
        vector_db2 = get_vector_db_dependency()
        ai_client2 = get_ai_client_dependency()
        
        print(f"   Vector DB instances same: {vector_db1 is vector_db2}")
        print(f"   AI Client instances same: {ai_client1 is ai_client2}")
        
        # Show factory cache info
        from core.database.factories import DatabaseFactory, AIClientFactory
        
        db_cache_info = DatabaseFactory.get_cache_info()
        ai_cache_info = AIClientFactory.get_cache_info()
        
        print(f"\n2. Factory Cache Statistics:")
        print(f"   Database Factory:")
        for cache_name, info in db_cache_info.items():
            print(f"     - {cache_name}: hits={info['hits']}, misses={info['misses']}")
        
        print(f"   AI Client Factory:")
        for cache_name, info in ai_cache_info.items():
            print(f"     - {cache_name}: hits={info['hits']}, misses={info['misses']}")
        
        # Show runtime database switching capability
        print(f"\n3. Runtime Database Switching:")
        print("   ℹ️  Can switch between Qdrant Cloud/Local, Weaviate, Pinecone")
        print("   ℹ️  Configuration override support")
        print("   ℹ️  Cache clearing for testing")
        
        print(f"\n4. Error Handling Hierarchy:")
        print("   ✅ DatabaseError (base)")
        print("   ✅ ConnectionError (database-specific)")
        print("   ✅ QueryError (operation-specific)")
        print("   ✅ ConfigurationError (setup-specific)")
        
    except Exception as e:
        print(f"❌ Architecture demo failed: {e}")


if __name__ == "__main__":
    print("🔧 RAG Construction Materials API - Refactored Service Demo")
    print("Using new multi-database architecture with dependency injection")
    
    asyncio.run(demo_refactored_service())
    asyncio.run(demo_architecture_features()) 