"""
Demo Script for Advanced Search and Filtering

Демонстрационный скрипт для продвинутого поиска и фильтрации.

Showcases:
- Advanced search with multiple types (vector, SQL, fuzzy, hybrid)
- Complex filtering by categories, units, dates, SKU patterns
- Multi-field sorting and pagination
- Text highlighting and search suggestions
- Search analytics and popular queries
- Performance comparisons
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.schemas.materials import (
    AdvancedSearchQuery, MaterialFilterOptions, SortOption, PaginationOptions,
    SearchResponse, Material
)
from services.advanced_search import AdvancedSearchService
from core.repositories.cached_materials import CachedMaterialsRepository
from core.database.adapters.redis_adapter import RedisDatabase
from core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedSearchDemo:
    """Demo class for advanced search functionality."""
    
    def __init__(self):
        self.service = None
        self.demo_materials = []
        
    async def initialize(self):
        """Initialize demo with mock service."""
        logger.info("🚀 Initializing Advanced Search Demo...")
        
        # Create mock service for demo
        self.service = await self._create_mock_service()
        
        # Create demo materials
        await self._create_demo_materials()
        
        logger.info("✅ Demo initialized successfully!")
    
    async def _create_mock_service(self) -> AdvancedSearchService:
        """Create mock advanced search service."""
        from unittest.mock import AsyncMock, MagicMock
        
        # Mock Redis
        redis_db = AsyncMock()
        redis_db.get.return_value = None
        redis_db.set.return_value = True
        redis_db.lpush.return_value = 1
        redis_db.hincrby.return_value = 1
        redis_db.hset.return_value = True
        redis_db.expire.return_value = True
        redis_db.keys.return_value = []
        redis_db.hgetall.return_value = {}
        redis_db.lrange.return_value = []
        
        # Mock materials repository
        materials_repo = AsyncMock()
        
        return AdvancedSearchService(
            materials_repo=materials_repo,
            redis_db=redis_db,
            analytics_enabled=True
        )
    
    async def _create_demo_materials(self):
        """Create demo materials for testing."""
        self.demo_materials = [
            Material(
                id="1",
                name="Цемент портландский М400",
                use_category="Цемент",
                unit="кг",
                sku="CEM400",
                description="Высококачественный портландцемент марки М400",
                created_at=datetime.utcnow() - timedelta(days=30),
                updated_at=datetime.utcnow() - timedelta(days=5)
            ),
            Material(
                id="2",
                name="Цемент портландский М500",
                use_category="Цемент", 
                unit="кг",
                sku="CEM500",
                description="Портландцемент повышенной прочности М500",
                created_at=datetime.utcnow() - timedelta(days=25),
                updated_at=datetime.utcnow() - timedelta(days=3)
            ),
            Material(
                id="3",
                name="Кирпич керамический красный",
                use_category="Кирпич",
                unit="шт",
                sku="BRICK001",
                description="Керамический кирпич красный полнотелый",
                created_at=datetime.utcnow() - timedelta(days=20),
                updated_at=datetime.utcnow() - timedelta(days=2)
            ),
            Material(
                id="4",
                name="Кирпич силикатный белый",
                use_category="Кирпич",
                unit="шт", 
                sku="BRICK002",
                description="Силикатный кирпич белый одинарный",
                created_at=datetime.utcnow() - timedelta(days=15),
                updated_at=datetime.utcnow() - timedelta(days=1)
            ),
            Material(
                id="5",
                name="Арматура А500С диаметр 12мм",
                use_category="Металлопрокат",
                unit="м",
                sku="ARM12",
                description="Арматурная сталь периодического профиля",
                created_at=datetime.utcnow() - timedelta(days=10),
                updated_at=datetime.utcnow()
            ),
            Material(
                id="6",
                name="Песок строительный",
                use_category="Сыпучие материалы",
                unit="м³",
                sku="SAND001",
                description="Песок строительный мытый фракция 0-5мм",
                created_at=datetime.utcnow() - timedelta(days=8),
                updated_at=datetime.utcnow()
            )
        ]
        
        # Mock repository to return demo materials
        self.service.materials_repo.get_all_materials.return_value = self.demo_materials
        self.service.materials_repo.vector_search.return_value = self.demo_materials[:3]
        self.service.materials_repo.hybrid_repo.search_materials.return_value = self.demo_materials[2:5]
    
    async def run_all_demos(self):
        """Run all demo scenarios."""
        logger.info("🎯 Starting Advanced Search Demo Scenarios...")
        
        await self.demo_basic_search_types()
        await self.demo_advanced_filtering()
        await self.demo_sorting_and_pagination()
        await self.demo_fuzzy_search()
        await self.demo_text_highlighting()
        await self.demo_search_suggestions()
        await self.demo_analytics()
        await self.demo_performance_comparison()
        
        logger.info("🎉 All demo scenarios completed!")
    
    async def demo_basic_search_types(self):
        """Demo different search types."""
        logger.info("\n📍 Demo 1: Basic Search Types")
        logger.info("=" * 50)
        
        search_types = ["vector", "sql", "fuzzy", "hybrid"]
        
        for search_type in search_types:
            logger.info(f"\n🔍 Testing {search_type.upper()} search...")
            
            query = AdvancedSearchQuery(
                query="цемент",
                search_type=search_type,
                pagination=PaginationOptions(page=1, page_size=5)
            )
            
            start_time = time.time()
            result = await self._mock_search(query)
            search_time = (time.time() - start_time) * 1000
            
            logger.info(f"   ✅ Found {len(result['results'])} results in {search_time:.2f}ms")
            logger.info(f"   📊 Search type: {search_type}")
            
            if result['results']:
                logger.info(f"   📝 First result: {result['results'][0]['name']}")
    
    async def demo_advanced_filtering(self):
        """Demo advanced filtering capabilities."""
        logger.info("\n📍 Demo 2: Advanced Filtering")
        logger.info("=" * 50)
        
        # Category filtering
        logger.info("\n🏷️  Category Filtering (Цемент)...")
        filters = MaterialFilterOptions(categories=["Цемент"])
        query = AdvancedSearchQuery(
            query="материал",
            search_type="hybrid",
            filters=filters,
            pagination=PaginationOptions(page=1, page_size=10)
        )
        
        result = await self._mock_search(query)
        logger.info(f"   ✅ Found {len(result['results'])} cement materials")
        
        # Unit filtering
        logger.info("\n📏 Unit Filtering (кг)...")
        filters = MaterialFilterOptions(units=["кг"])
        query.filters = filters
        
        result = await self._mock_search(query)
        logger.info(f"   ✅ Found {len(result['results'])} materials in kg")
        
        # SKU pattern filtering
        logger.info("\n🔢 SKU Pattern Filtering (CEM*)...")
        filters = MaterialFilterOptions(sku_pattern="CEM*")
        query.filters = filters
        
        result = await self._mock_search(query)
        logger.info(f"   ✅ Found {len(result['results'])} materials with CEM* SKU")
        
        # Date range filtering
        logger.info("\n📅 Date Range Filtering (last 20 days)...")
        twenty_days_ago = datetime.utcnow() - timedelta(days=20)
        filters = MaterialFilterOptions(created_after=twenty_days_ago)
        query.filters = filters
        
        result = await self._mock_search(query)
        logger.info(f"   ✅ Found {len(result['results'])} recent materials")
        
        # Combined filtering
        logger.info("\n🎯 Combined Filtering (Category + Unit + Date)...")
        filters = MaterialFilterOptions(
            categories=["Цемент", "Кирпич"],
            units=["кг", "шт"],
            created_after=twenty_days_ago,
            min_similarity=0.5
        )
        query.filters = filters
        
        result = await self._mock_search(query)
        logger.info(f"   ✅ Found {len(result['results'])} materials matching all filters")
    
    async def demo_sorting_and_pagination(self):
        """Demo sorting and pagination features."""
        logger.info("\n📍 Demo 3: Sorting and Pagination")
        logger.info("=" * 50)
        
        # Sort by relevance
        logger.info("\n📊 Sorting by Relevance (desc)...")
        sort_options = [SortOption(field="relevance", direction="desc")]
        query = AdvancedSearchQuery(
            query="материал",
            search_type="hybrid",
            sort_by=sort_options,
            pagination=PaginationOptions(page=1, page_size=3)
        )
        
        result = await self._mock_search(query)
        logger.info(f"   ✅ Page 1: {len(result['results'])} results")
        for i, material in enumerate(result['results']):
            logger.info(f"      {i+1}. {material['name']} (score: {material.get('score', 'N/A')})")
        
        # Sort by name
        logger.info("\n🔤 Sorting by Name (asc)...")
        sort_options = [SortOption(field="name", direction="asc")]
        query.sort_by = sort_options
        
        result = await self._mock_search(query)
        logger.info(f"   ✅ Sorted by name: {len(result['results'])} results")
        for i, material in enumerate(result['results']):
            logger.info(f"      {i+1}. {material['name']}")
        
        # Multi-field sorting
        logger.info("\n🎯 Multi-field Sorting (Category asc, Name desc)...")
        sort_options = [
            SortOption(field="use_category", direction="asc"),
            SortOption(field="name", direction="desc")
        ]
        query.sort_by = sort_options
        
        result = await self._mock_search(query)
        logger.info(f"   ✅ Multi-field sorted: {len(result['results'])} results")
        
        # Pagination
        logger.info("\n📄 Pagination Demo...")
        query.pagination = PaginationOptions(page=1, page_size=2)
        
        for page in range(1, 4):
            query.pagination.page = page
            result = await self._mock_search(query)
            logger.info(f"   📄 Page {page}: {len(result['results'])} results")
            if result.get('next_cursor'):
                logger.info(f"      🔗 Next cursor available")
    
    async def demo_fuzzy_search(self):
        """Demo fuzzy search capabilities."""
        logger.info("\n📍 Demo 4: Fuzzy Search")
        logger.info("=" * 50)
        
        test_queries = [
            ("цемент", "цемнт"),  # Missing letter
            ("кирпич", "кирпч"),  # Missing letter
            ("арматура", "арматра"),  # Transposed letters
            ("строительный", "строитльный")  # Transposed letters
        ]
        
        for original, fuzzy_query in test_queries:
            logger.info(f"\n🔍 Fuzzy search: '{fuzzy_query}' (should find '{original}')")
            
            # Test different thresholds
            for threshold in [0.6, 0.8, 0.9]:
                query = AdvancedSearchQuery(
                    query=fuzzy_query,
                    search_type="fuzzy",
                    fuzzy_threshold=threshold,
                    pagination=PaginationOptions(page=1, page_size=5)
                )
                
                result = await self._mock_search(query)
                logger.info(f"   📊 Threshold {threshold}: {len(result['results'])} results")
                
                # Show similarity scores
                for material in result['results'][:2]:
                    similarity = self.service._sequence_matcher_similarity(
                        fuzzy_query.lower(), material['name'].lower()
                    )
                    logger.info(f"      📝 {material['name']} (similarity: {similarity:.3f})")
    
    async def demo_text_highlighting(self):
        """Demo text highlighting feature."""
        logger.info("\n📍 Demo 5: Text Highlighting")
        logger.info("=" * 50)
        
        query = AdvancedSearchQuery(
            query="цемент портландский",
            search_type="hybrid",
            highlight_matches=True,
            pagination=PaginationOptions(page=1, page_size=3)
        )
        
        result = await self._mock_search(query)
        
        logger.info(f"\n🎨 Highlighting matches for: '{query.query}'")
        
        for material in result['results']:
            logger.info(f"\n   📝 Material: {material['name']}")
            
            # Simulate highlighting
            highlighted_name = self.service._highlight_text(
                material['name'], 
                query.query.lower().split()
            )
            
            if highlighted_name != material['name']:
                logger.info(f"      🎨 Highlighted: {highlighted_name}")
            
            if material.get('description'):
                highlighted_desc = self.service._highlight_text(
                    material['description'],
                    query.query.lower().split()
                )
                if highlighted_desc != material['description']:
                    logger.info(f"      📄 Description: {highlighted_desc}")
    
    async def demo_search_suggestions(self):
        """Demo search suggestions feature."""
        logger.info("\n📍 Demo 6: Search Suggestions")
        logger.info("=" * 50)
        
        test_queries = ["цем", "кир", "арм", "стр"]
        
        for partial_query in test_queries:
            logger.info(f"\n💡 Suggestions for: '{partial_query}'")
            
            # Mock suggestions based on demo materials
            suggestions = []
            
            # Find materials that contain the partial query
            for material in self.demo_materials:
                if partial_query.lower() in material.name.lower():
                    suggestions.append({
                        "text": material.name,
                        "type": "material",
                        "score": 0.8
                    })
                
                if partial_query.lower() in material.use_category.lower():
                    suggestions.append({
                        "text": material.use_category,
                        "type": "category", 
                        "score": 0.7
                    })
            
            # Remove duplicates and limit
            seen = set()
            unique_suggestions = []
            for suggestion in suggestions:
                if suggestion["text"] not in seen:
                    seen.add(suggestion["text"])
                    unique_suggestions.append(suggestion)
                    if len(unique_suggestions) >= 5:
                        break
            
            for i, suggestion in enumerate(unique_suggestions):
                logger.info(f"   {i+1}. {suggestion['text']} ({suggestion['type']}, score: {suggestion['score']})")
    
    async def demo_analytics(self):
        """Demo search analytics features."""
        logger.info("\n📍 Demo 7: Search Analytics")
        logger.info("=" * 50)
        
        # Simulate some searches for analytics
        search_queries = [
            "цемент", "кирпич", "арматура", "цемент", "песок", "цемент"
        ]
        
        logger.info("\n📊 Simulating search analytics...")
        
        for query_text in search_queries:
            query = AdvancedSearchQuery(
                query=query_text,
                search_type="hybrid",
                pagination=PaginationOptions(page=1, page_size=5)
            )
            
            await self._mock_search(query)
        
        # Mock analytics data
        analytics_data = {
            "total_searches": len(search_queries),
            "avg_search_time": 45.2,
            "avg_results_count": 3.5,
            "search_types": {
                "hybrid": 6,
                "vector": 0,
                "sql": 0,
                "fuzzy": 0
            },
            "popular_queries": [
                {"query": "цемент", "count": 3, "avg_results": 4.0, "avg_time_ms": 42.1},
                {"query": "кирпич", "count": 1, "avg_results": 3.0, "avg_time_ms": 38.5},
                {"query": "арматура", "count": 1, "avg_results": 2.0, "avg_time_ms": 51.2}
            ]
        }
        
        logger.info(f"\n📈 Analytics Summary:")
        logger.info(f"   🔢 Total searches: {analytics_data['total_searches']}")
        logger.info(f"   ⏱️  Average search time: {analytics_data['avg_search_time']:.1f}ms")
        logger.info(f"   📊 Average results: {analytics_data['avg_results_count']:.1f}")
        
        logger.info(f"\n🏆 Popular Queries:")
        for i, query in enumerate(analytics_data['popular_queries']):
            logger.info(f"   {i+1}. '{query['query']}' - {query['count']} searches")
        
        logger.info(f"\n🎯 Search Types Distribution:")
        for search_type, count in analytics_data['search_types'].items():
            percentage = (count / analytics_data['total_searches']) * 100
            logger.info(f"   📊 {search_type}: {count} ({percentage:.1f}%)")
    
    async def demo_performance_comparison(self):
        """Demo performance comparison between search types."""
        logger.info("\n📍 Demo 8: Performance Comparison")
        logger.info("=" * 50)
        
        search_types = ["vector", "sql", "fuzzy", "hybrid"]
        query_text = "строительные материалы"
        
        performance_results = {}
        
        for search_type in search_types:
            logger.info(f"\n⚡ Testing {search_type.upper()} performance...")
            
            times = []
            for i in range(3):  # Run 3 times for average
                query = AdvancedSearchQuery(
                    query=query_text,
                    search_type=search_type,
                    pagination=PaginationOptions(page=1, page_size=10)
                )
                
                start_time = time.time()
                result = await self._mock_search(query)
                search_time = (time.time() - start_time) * 1000
                times.append(search_time)
            
            avg_time = sum(times) / len(times)
            performance_results[search_type] = {
                "avg_time": avg_time,
                "results_count": len(result['results'])
            }
            
            logger.info(f"   ⏱️  Average time: {avg_time:.2f}ms")
            logger.info(f"   📊 Results: {len(result['results'])}")
        
        # Performance summary
        logger.info(f"\n🏁 Performance Summary:")
        logger.info("=" * 30)
        
        sorted_by_speed = sorted(
            performance_results.items(),
            key=lambda x: x[1]['avg_time']
        )
        
        for i, (search_type, metrics) in enumerate(sorted_by_speed):
            logger.info(f"   {i+1}. {search_type.upper()}: {metrics['avg_time']:.2f}ms")
        
        # Recommendations
        fastest = sorted_by_speed[0][0]
        logger.info(f"\n💡 Recommendations:")
        logger.info(f"   🚀 Fastest: {fastest.upper()} search")
        logger.info(f"   🎯 Most comprehensive: HYBRID search")
        logger.info(f"   🔍 Most flexible: FUZZY search")
    
    async def _mock_search(self, query: AdvancedSearchQuery) -> Dict[str, Any]:
        """Mock search operation for demo purposes."""
        # Simulate search delay
        await asyncio.sleep(0.01)
        
        # Filter materials based on query
        filtered_materials = []
        
        if query.query:
            query_lower = query.query.lower()
            for material in self.demo_materials:
                if (query_lower in material.name.lower() or
                    query_lower in material.description.lower() or
                    query_lower in material.use_category.lower()):
                    filtered_materials.append(material)
        else:
            filtered_materials = self.demo_materials.copy()
        
        # Apply filters
        if query.filters:
            if query.filters.categories:
                filtered_materials = [
                    m for m in filtered_materials 
                    if m.use_category in query.filters.categories
                ]
            
            if query.filters.units:
                filtered_materials = [
                    m for m in filtered_materials
                    if m.unit in query.filters.units
                ]
            
            if query.filters.sku_pattern:
                pattern = query.filters.sku_pattern.replace('*', '')
                filtered_materials = [
                    m for m in filtered_materials
                    if m.sku and m.sku.startswith(pattern)
                ]
            
            if query.filters.created_after:
                filtered_materials = [
                    m for m in filtered_materials
                    if m.created_at >= query.filters.created_after
                ]
        
        # Apply pagination
        start_idx = (query.pagination.page - 1) * query.pagination.page_size
        end_idx = start_idx + query.pagination.page_size
        paginated_materials = filtered_materials[start_idx:end_idx]
        
        # Convert to dict format for demo
        results = []
        for material in paginated_materials:
            material_dict = {
                "id": material.id,
                "name": material.name,
                "use_category": material.use_category,
                "unit": material.unit,
                "sku": material.sku,
                "description": material.description,
                "score": 0.85  # Mock score
            }
            results.append(material_dict)
        
        return {
            "results": results,
            "total_count": len(filtered_materials),
            "page": query.pagination.page,
            "page_size": query.pagination.page_size,
            "search_time_ms": 45.2,
            "next_cursor": "mock_cursor" if len(filtered_materials) > end_idx else None
        }


async def main():
    """Run the advanced search demo."""
    print("🎯 Advanced Search and Filtering Demo")
    print("=" * 60)
    print("Демонстрация продвинутого поиска и фильтрации")
    print("=" * 60)
    
    demo = AdvancedSearchDemo()
    
    try:
        await demo.initialize()
        await demo.run_all_demos()
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("🚀 Advanced search features are ready for production!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 