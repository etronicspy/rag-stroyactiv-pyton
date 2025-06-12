"""Demo script for PostgreSQL adapter and hybrid search capabilities.

Демо скрипт для показа возможностей PostgreSQL адаптера и гибридного поиска.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.database.adapters.postgresql_adapter import PostgreSQLDatabase
from core.database.adapters.qdrant_adapter import QdrantVectorDatabase
from core.repositories.hybrid_materials import HybridMaterialsRepository
from core.database.factories import DatabaseFactory, AIClientFactory
from core.schemas.materials import MaterialCreate
from core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgreSQLHybridDemo:
    """Demo class for PostgreSQL and hybrid search capabilities."""
    
    def __init__(self):
        """Initialize demo with database connections."""
        self.postgresql_db = None
        self.vector_db = None
        self.hybrid_repo = None
        self.ai_client = None
    
    async def setup(self):
        """Setup database connections and repositories."""
        try:
            logger.info("🔧 Setting up PostgreSQL and hybrid search demo...")
            
            # Create database clients
            self.postgresql_db = DatabaseFactory.create_relational_database()
            self.vector_db = DatabaseFactory.create_vector_database()
            self.ai_client = AIClientFactory.create_ai_client()
            
            # Create hybrid repository
            self.hybrid_repo = HybridMaterialsRepository(
                vector_db=self.vector_db,
                relational_db=self.postgresql_db,
                ai_client=self.ai_client
            )
            
            # Create PostgreSQL tables
            await self.postgresql_db.create_tables()
            
            # Ensure vector collection exists
            await self.vector_db.create_collection(
                collection_name="materials",
                vector_size=1536,
                distance="cosine"
            )
            
            logger.info("✅ Setup completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise
    
    async def demo_postgresql_features(self):
        """Demonstrate PostgreSQL adapter features."""
        logger.info("\n🐘 === PostgreSQL Adapter Features Demo ===")
        
        try:
            # 1. Health check
            logger.info("1️⃣ Testing PostgreSQL health check...")
            health = await self.postgresql_db.health_check()
            logger.info(f"   Health status: {health['status']}")
            logger.info(f"   Connection pool: {health.get('connection_pool', {})}")
            logger.info(f"   Statistics: {health.get('statistics', {})}")
            
            # 2. Create test materials directly in PostgreSQL
            logger.info("\n2️⃣ Creating materials directly in PostgreSQL...")
            
            test_materials = [
                {
                    "name": "Портландцемент М500",
                    "use_category": "Цемент",
                    "unit": "мешок",
                    "sku": "CEM500",
                    "description": "Высококачественный портландцемент марки М500 для строительных работ",
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5] * 307 + [0.1]  # 1536 dimensions
                },
                {
                    "name": "Кирпич керамический красный",
                    "use_category": "Кирпич",
                    "unit": "шт",
                    "sku": "BRICK001",
                    "description": "Керамический кирпич красного цвета для кладки стен",
                    "embedding": [0.2, 0.3, 0.4, 0.5, 0.6] * 307 + [0.2]  # 1536 dimensions
                },
                {
                    "name": "Арматура стальная А500С",
                    "use_category": "Арматура",
                    "unit": "м",
                    "sku": "ARM500",
                    "description": "Стальная арматура класса А500С для железобетонных конструкций",
                    "embedding": [0.3, 0.4, 0.5, 0.6, 0.7] * 307 + [0.3]  # 1536 dimensions
                }
            ]
            
            created_materials = []
            for material_data in test_materials:
                created = await self.postgresql_db.create_material(material_data)
                created_materials.append(created)
                logger.info(f"   ✅ Created: {created['name']} (ID: {created['id'][:8]}...)")
            
            # 3. Test hybrid search in PostgreSQL
            logger.info("\n3️⃣ Testing PostgreSQL hybrid search...")
            
            search_queries = ["цемент", "кирпич", "арматура", "строительный материал"]
            
            for query in search_queries:
                results = await self.postgresql_db.search_materials_hybrid(query, limit=5)
                logger.info(f"   🔍 Query: '{query}' → {len(results)} results")
                
                for result in results[:2]:  # Show top 2 results
                    similarity = result.get('similarity_score', 0)
                    logger.info(f"      • {result['name']} (similarity: {similarity:.3f})")
            
            # 4. Test pagination
            logger.info("\n4️⃣ Testing pagination...")
            
            all_materials = await self.postgresql_db.get_materials(skip=0, limit=10)
            logger.info(f"   📄 Retrieved {len(all_materials)} materials with pagination")
            
            # Filter by category
            cement_materials = await self.postgresql_db.get_materials(skip=0, limit=10, category="Цемент")
            logger.info(f"   🏷️ Found {len(cement_materials)} materials in 'Цемент' category")
            
            # 5. Test raw SQL queries
            logger.info("\n5️⃣ Testing raw SQL queries...")
            
            # Count materials by category
            category_stats = await self.postgresql_db.execute_query("""
                SELECT use_category, COUNT(*) as count 
                FROM materials 
                GROUP BY use_category 
                ORDER BY count DESC
            """)
            
            logger.info("   📊 Materials by category:")
            for stat in category_stats:
                logger.info(f"      • {stat['use_category']}: {stat['count']}")
            
            # 6. Test transactions
            logger.info("\n6️⃣ Testing transactions...")
            
            transaction = await self.postgresql_db.begin_transaction()
            try:
                # This would be a real transaction in production
                await self.postgresql_db.commit_transaction(transaction)
                logger.info("   ✅ Transaction committed successfully")
            except Exception as e:
                await self.postgresql_db.rollback_transaction(transaction)
                logger.error(f"   ❌ Transaction rolled back: {e}")
            
            return created_materials
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL demo failed: {e}")
            raise
    
    async def demo_hybrid_repository(self, existing_materials: List[Dict[str, Any]]):
        """Demonstrate hybrid repository capabilities."""
        logger.info("\n🔄 === Hybrid Repository Demo ===")
        
        try:
            # 1. Create materials using hybrid repository
            logger.info("1️⃣ Creating materials using hybrid repository...")
            
            hybrid_materials = [
                MaterialCreate(
                    name="Бетон М300",
                    use_category="Бетон",
                    unit="м³",
                    sku="BET300",
                    description="Товарный бетон марки М300 для фундаментов и перекрытий"
                ),
                MaterialCreate(
                    name="Песок речной",
                    use_category="Песок",
                    unit="м³",
                    sku="SAND001",
                    description="Речной песок средней фракции для строительных работ"
                )
            ]
            
            created_hybrid = []
            for material in hybrid_materials:
                created = await self.hybrid_repo.create_material(material)
                created_hybrid.append(created)
                logger.info(f"   ✅ Created in both DBs: {created.name} (ID: {created.id[:8]}...)")
            
            # 2. Test hybrid search with fallback strategy
            logger.info("\n2️⃣ Testing hybrid search with fallback strategy...")
            
            search_tests = [
                ("цемент портландский", "Should find in vector DB"),
                ("строительный материал", "Should combine vector + SQL results"),
                ("редкий материал xyz", "Should fallback to SQL search"),
                ("бетон", "Should find newly created materials")
            ]
            
            for query, description in search_tests:
                logger.info(f"   🔍 Testing: {query} ({description})")
                
                # Test regular search (with fallback)
                results = await self.hybrid_repo.search_materials(query, limit=5)
                logger.info(f"      Regular search: {len(results)} results")
                
                # Test advanced hybrid search
                hybrid_results = await self.hybrid_repo.search_materials_hybrid(
                    query, 
                    limit=5,
                    vector_weight=0.7,
                    sql_weight=0.3
                )
                logger.info(f"      Hybrid search: {len(hybrid_results)} results")
                
                # Show top result
                if results:
                    top_result = results[0]
                    logger.info(f"      Top result: {top_result.name}")
            
            # 3. Test CRUD operations
            logger.info("\n3️⃣ Testing CRUD operations...")
            
            if created_hybrid:
                test_material = created_hybrid[0]
                
                # Read
                retrieved = await self.hybrid_repo.get_material_by_id(test_material.id)
                logger.info(f"   📖 Retrieved: {retrieved.name if retrieved else 'Not found'}")
                
                # Update
                from core.schemas.materials import MaterialUpdate
                update_data = MaterialUpdate(
                    description="Обновленное описание товарного бетона М300"
                )
                updated = await self.hybrid_repo.update_material(test_material.id, update_data)
                logger.info(f"   ✏️ Updated: {updated.name if updated else 'Not found'}")
                
                # List with pagination
                all_materials = await self.hybrid_repo.get_materials(skip=0, limit=10)
                logger.info(f"   📋 Listed: {len(all_materials)} materials")
            
            # 4. Test health check
            logger.info("\n4️⃣ Testing hybrid repository health check...")
            
            health = await self.hybrid_repo.health_check()
            logger.info(f"   🏥 Overall status: {health['status']}")
            logger.info(f"   🔍 Vector DB: {health['vector_database']['status']}")
            logger.info(f"   🐘 PostgreSQL: {health['relational_database']['status']}")
            
            # 5. Performance comparison
            logger.info("\n5️⃣ Performance comparison...")
            
            import time
            
            # Vector search timing
            start_time = time.time()
            vector_results = await self.hybrid_repo._search_vector_db("цемент", 10)
            vector_time = time.time() - start_time
            
            # SQL search timing
            start_time = time.time()
            sql_results = await self.hybrid_repo._search_relational_db("цемент", 10)
            sql_time = time.time() - start_time
            
            # Hybrid search timing
            start_time = time.time()
            hybrid_results = await self.hybrid_repo.search_materials_hybrid("цемент", 10)
            hybrid_time = time.time() - start_time
            
            logger.info(f"   ⚡ Vector search: {vector_time:.3f}s ({len(vector_results)} results)")
            logger.info(f"   ⚡ SQL search: {sql_time:.3f}s ({len(sql_results)} results)")
            logger.info(f"   ⚡ Hybrid search: {hybrid_time:.3f}s ({len(hybrid_results)} results)")
            
        except Exception as e:
            logger.error(f"❌ Hybrid repository demo failed: {e}")
            raise
    
    async def demo_advanced_features(self):
        """Demonstrate advanced PostgreSQL and hybrid features."""
        logger.info("\n🚀 === Advanced Features Demo ===")
        
        try:
            # 1. Full-text search with trigram similarity
            logger.info("1️⃣ Testing trigram similarity search...")
            
            # Test fuzzy matching
            fuzzy_queries = [
                "цемнт",  # Typo in "цемент"
                "кирпч",  # Typo in "кирпич"
                "арматр"  # Partial word
            ]
            
            for query in fuzzy_queries:
                results = await self.postgresql_db.search_materials_hybrid(
                    query, 
                    limit=3, 
                    similarity_threshold=0.2  # Lower threshold for fuzzy matching
                )
                logger.info(f"   🔤 Fuzzy query '{query}': {len(results)} results")
                
                for result in results[:1]:  # Show top result
                    similarity = result.get('similarity_score', 0)
                    logger.info(f"      • {result['name']} (similarity: {similarity:.3f})")
            
            # 2. Complex SQL queries with aggregations
            logger.info("\n2️⃣ Testing complex SQL aggregations...")
            
            # Materials statistics
            stats_query = """
                SELECT 
                    use_category,
                    COUNT(*) as total_materials,
                    COUNT(DISTINCT unit) as unique_units,
                    AVG(array_length(embedding, 1)) as avg_embedding_size
                FROM materials 
                WHERE embedding IS NOT NULL
                GROUP BY use_category
                ORDER BY total_materials DESC
            """
            
            stats = await self.postgresql_db.execute_query(stats_query)
            logger.info("   📈 Materials statistics:")
            for stat in stats:
                logger.info(
                    f"      • {stat['use_category']}: "
                    f"{stat['total_materials']} materials, "
                    f"{stat['unique_units']} units, "
                    f"avg embedding size: {stat['avg_embedding_size']:.0f}"
                )
            
            # 3. Concurrent operations test
            logger.info("\n3️⃣ Testing concurrent operations...")
            
            async def create_test_material(index: int):
                material = MaterialCreate(
                    name=f"Тестовый материал {index}",
                    use_category="Тест",
                    unit="шт",
                    sku=f"TEST{index:03d}",
                    description=f"Описание тестового материала номер {index}"
                )
                return await self.hybrid_repo.create_material(material)
            
            # Create 5 materials concurrently
            start_time = time.time()
            concurrent_tasks = [create_test_material(i) for i in range(5)]
            concurrent_results = await asyncio.gather(*concurrent_tasks)
            concurrent_time = time.time() - start_time
            
            logger.info(f"   ⚡ Created {len(concurrent_results)} materials concurrently in {concurrent_time:.3f}s")
            
            # 4. Database size and performance metrics
            logger.info("\n4️⃣ Database metrics...")
            
            # PostgreSQL metrics
            pg_health = await self.postgresql_db.health_check()
            pg_stats = pg_health.get('statistics', {})
            
            logger.info("   🐘 PostgreSQL metrics:")
            logger.info(f"      • Materials count: {pg_stats.get('materials_count', 0)}")
            logger.info(f"      • Raw products count: {pg_stats.get('raw_products_count', 0)}")
            logger.info(f"      • Database size: {pg_stats.get('database_size_mb', 0)} MB")
            
            # Vector DB metrics
            vector_health = await self.vector_db.health_check()
            logger.info("   🔍 Vector DB metrics:")
            logger.info(f"      • Status: {vector_health.get('status', 'unknown')}")
            logger.info(f"      • Collections: {vector_health.get('collections_count', 0)}")
            
        except Exception as e:
            logger.error(f"❌ Advanced features demo failed: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup demo data and close connections."""
        logger.info("\n🧹 Cleaning up demo data...")
        
        try:
            # Delete test materials
            test_materials = await self.postgresql_db.execute_query(
                "SELECT id FROM materials WHERE sku LIKE 'TEST%' OR use_category = 'Тест'"
            )
            
            for material in test_materials:
                await self.hybrid_repo.delete_material(material['id'])
            
            logger.info(f"   🗑️ Deleted {len(test_materials)} test materials")
            
            # Close connections
            if self.postgresql_db:
                await self.postgresql_db.close()
            
            logger.info("   ✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    async def run_full_demo(self):
        """Run the complete demo."""
        logger.info("🎬 Starting PostgreSQL and Hybrid Search Demo")
        logger.info("=" * 60)
        
        try:
            # Setup
            await self.setup()
            
            # Run demos
            created_materials = await self.demo_postgresql_features()
            await self.demo_hybrid_repository(created_materials)
            await self.demo_advanced_features()
            
            logger.info("\n🎉 Demo completed successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
        finally:
            # Always cleanup
            await self.cleanup()


async def main():
    """Main demo function."""
    demo = PostgreSQLHybridDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = ["POSTGRESQL_URL", "QDRANT_URL", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("Please set the following environment variables:")
        logger.info("  POSTGRESQL_URL=postgresql+asyncpg://user:password@localhost:5432/dbname")
        logger.info("  QDRANT_URL=https://your-cluster.qdrant.io")
        logger.info("  OPENAI_API_KEY=your-openai-api-key")
        sys.exit(1)
    
    # Run demo
    asyncio.run(main()) 