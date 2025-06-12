"""
Advanced Search API Routes

Продвинутые API роуты для поиска материалов с расширенными возможностями:
- Комплексная фильтрация и сортировка
- Fuzzy search и гибридный поиск
- Автодополнение и предложения
- Аналитика поиска
- Cursor-based пагинация
"""

from datetime import datetime, timedelta
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from core.schemas.materials import (
    AdvancedSearchQuery, SearchResponse, SearchSuggestion, 
    PopularQuery, Material
)
from services.advanced_search import AdvancedSearchService
from core.repositories.cached_materials import CachedMaterialsRepository
from core.database.adapters.redis_adapter import RedisDatabase
from core.config import get_settings
from core.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/search", tags=["Advanced Search"])

# Dependency injection
async def get_advanced_search_service() -> AdvancedSearchService:
    """Get advanced search service with dependencies."""
    settings = get_settings()
    
    # Initialize Redis
    redis_db = RedisDatabase(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        db=settings.redis_db
    )
    await redis_db.connect()
    
    # Initialize cached materials repository
    # Note: This would need proper dependency injection in production
    from core.repositories.hybrid_materials import HybridMaterialsRepository
    from core.database.adapters.qdrant_adapter import QdrantDatabase
    from core.database.adapters.postgresql_adapter import PostgreSQLDatabase
    
    # Initialize databases
    vector_db = QdrantDatabase(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key
    )
    
    relational_db = PostgreSQLDatabase(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        username=settings.postgres_user,
        password=settings.postgres_password
    )
    
    # Initialize hybrid repository
    hybrid_repo = HybridMaterialsRepository(
        vector_db=vector_db,
        relational_db=relational_db,
        collection_name="materials"
    )
    
    # Initialize cached repository
    cached_repo = CachedMaterialsRepository(
        hybrid_repo=hybrid_repo,
        redis_db=redis_db
    )
    
    return AdvancedSearchService(
        materials_repo=cached_repo,
        redis_db=redis_db,
        analytics_enabled=True
    )


@router.post("/advanced", response_model=SearchResponse)
async def advanced_search(
    query: AdvancedSearchQuery,
    service: AdvancedSearchService = Depends(get_advanced_search_service)
):
    """
    Perform advanced search with comprehensive filtering and sorting.
    
    Выполнить продвинутый поиск с комплексной фильтрацией и сортировкой.
    
    Features:
    - Multiple search types: vector, sql, fuzzy, hybrid
    - Advanced filtering by categories, units, dates, SKU patterns
    - Multi-field sorting with custom directions
    - Cursor-based pagination
    - Text highlighting and search suggestions
    - Real-time analytics tracking
    
    Args:
        query: Advanced search query with all options
        
    Returns:
        Comprehensive search response with metadata
        
    Raises:
        HTTPException: If search fails or validation errors occur
    """
    try:
        logger.info(f"Advanced search request: {query.query}, type: {query.search_type}")
        
        result = await service.advanced_search(query)
        
        logger.info(
            f"Advanced search completed: {len(result.results)} results, "
            f"{result.search_time_ms:.2f}ms"
        )
        
        return result
        
    except ValidationError as e:
        logger.warning(f"Validation error in advanced search: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {e.message}")
    except DatabaseError as e:
        logger.error(f"Database error in advanced search: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error in advanced search: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/suggestions", response_model=List[SearchSuggestion])
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Search query for suggestions"),
    limit: int = Query(8, ge=1, le=20, description="Maximum number of suggestions"),
    service: AdvancedSearchService = Depends(get_advanced_search_service)
):
    """
    Get search suggestions for autocomplete.
    
    Получить предложения для автодополнения поиска.
    
    Features:
    - Popular queries that start with input
    - Material names containing the query
    - Categories matching the query
    - Cached suggestions for performance
    
    Args:
        q: Search query
        limit: Maximum number of suggestions
        
    Returns:
        List of search suggestions with scores
    """
    try:
        logger.debug(f"Getting suggestions for query: '{q}'")
        
        suggestions = await service._generate_suggestions(q)
        
        # Limit results
        limited_suggestions = suggestions[:limit]
        
        logger.debug(f"Generated {len(limited_suggestions)} suggestions")
        
        return limited_suggestions
        
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get("/popular-queries", response_model=List[PopularQuery])
async def get_popular_queries(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of popular queries"),
    service: AdvancedSearchService = Depends(get_advanced_search_service)
):
    """
    Get popular search queries statistics.
    
    Получить статистику популярных поисковых запросов.
    
    Returns:
        List of popular queries with statistics
    """
    try:
        logger.debug(f"Getting {limit} popular queries")
        
        popular_queries = await service._get_popular_queries(limit)
        
        logger.debug(f"Retrieved {len(popular_queries)} popular queries")
        
        return popular_queries
        
    except Exception as e:
        logger.error(f"Failed to get popular queries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get popular queries: {str(e)}")


@router.get("/analytics")
async def get_search_analytics(
    start_date: Optional[datetime] = Query(
        None, 
        description="Start date for analytics (default: 7 days ago)"
    ),
    end_date: Optional[datetime] = Query(
        None, 
        description="End date for analytics (default: now)"
    ),
    service: AdvancedSearchService = Depends(get_advanced_search_service)
):
    """
    Get search analytics for a date range.
    
    Получить аналитику поиска за период.
    
    Features:
    - Total searches and average metrics
    - Search types distribution
    - Daily statistics breakdown
    - Popular queries analysis
    
    Args:
        start_date: Start date for analytics
        end_date: End date for analytics
        
    Returns:
        Comprehensive analytics data
    """
    try:
        logger.info(f"Getting search analytics: {start_date} to {end_date}")
        
        analytics = await service.get_search_analytics(start_date, end_date)
        
        logger.info(f"Analytics retrieved: {analytics.get('total_searches', 0)} total searches")
        
        return JSONResponse(content=analytics)
        
    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/categories", response_model=List[str])
async def get_available_categories(
    service: AdvancedSearchService = Depends(get_advanced_search_service)
):
    """
    Get all available material categories for filtering.
    
    Получить все доступные категории материалов для фильтрации.
    
    Returns:
        List of unique categories
    """
    try:
        logger.debug("Getting available categories")
        
        # Get all materials to extract categories
        materials = await service.materials_repo.get_all_materials(limit=1000)
        
        # Extract unique categories
        categories = list(set(material.use_category for material in materials if material.use_category))
        categories.sort()
        
        logger.debug(f"Found {len(categories)} unique categories")
        
        return categories
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/units", response_model=List[str])
async def get_available_units(
    service: AdvancedSearchService = Depends(get_advanced_search_service)
):
    """
    Get all available measurement units for filtering.
    
    Получить все доступные единицы измерения для фильтрации.
    
    Returns:
        List of unique units
    """
    try:
        logger.debug("Getting available units")
        
        # Get all materials to extract units
        materials = await service.materials_repo.get_all_materials(limit=1000)
        
        # Extract unique units
        units = list(set(material.unit for material in materials if material.unit))
        units.sort()
        
        logger.debug(f"Found {len(units)} unique units")
        
        return units
        
    except Exception as e:
        logger.error(f"Failed to get units: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get units: {str(e)}")


@router.post("/fuzzy", response_model=List[Material])
async def fuzzy_search(
    q: str = Query(..., min_length=1, description="Search query"),
    threshold: float = Query(0.8, ge=0.0, le=1.0, description="Similarity threshold"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results"),
    service: AdvancedSearchService = Depends(get_advanced_search_service)
):
    """
    Perform fuzzy search with configurable similarity threshold.
    
    Выполнить нечеткий поиск с настраиваемым порогом схожести.
    
    Features:
    - Levenshtein distance calculation
    - Multi-field similarity scoring
    - Configurable similarity threshold
    - Field-weighted scoring
    
    Args:
        q: Search query
        threshold: Minimum similarity threshold (0.0-1.0)
        limit: Maximum number of results
        
    Returns:
        List of materials matching fuzzy criteria
    """
    try:
        logger.info(f"Fuzzy search: '{q}', threshold: {threshold}")
        
        # Create advanced search query for fuzzy search
        from core.schemas.materials import PaginationOptions
        
        advanced_query = AdvancedSearchQuery(
            query=q,
            search_type="fuzzy",
            fuzzy_threshold=threshold,
            pagination=PaginationOptions(page=1, page_size=limit)
        )
        
        result = await service.advanced_search(advanced_query)
        
        # Extract just the materials
        materials = [search_result.material for search_result in result.results]
        
        logger.info(f"Fuzzy search found {len(materials)} results")
        
        return materials
        
    except Exception as e:
        logger.error(f"Fuzzy search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Fuzzy search failed: {str(e)}")


@router.get("/health")
async def search_health_check(
    service: AdvancedSearchService = Depends(get_advanced_search_service)
):
    """
    Health check for search service and dependencies.
    
    Проверка состояния поискового сервиса и зависимостей.
    
    Returns:
        Health status of search components
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check Redis connection
        try:
            await service.redis_db.ping()
            health_status["components"]["redis"] = "healthy"
        except Exception as e:
            health_status["components"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check materials repository
        try:
            # Try to get a small number of materials
            materials = await service.materials_repo.get_all_materials(limit=1)
            health_status["components"]["materials_repo"] = "healthy"
        except Exception as e:
            health_status["components"]["materials_repo"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check search functionality
        try:
            # Perform a simple test search
            test_query = AdvancedSearchQuery(
                query="test",
                search_type="hybrid",
                pagination={"page": 1, "page_size": 1}
            )
            await service.advanced_search(test_query)
            health_status["components"]["search_service"] = "healthy"
        except Exception as e:
            health_status["components"]["search_service"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        ) 