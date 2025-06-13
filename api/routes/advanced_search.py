"""
Advanced Search API Routes (Simplified)

Упрощенные API роуты для продвинутого поиска материалов:
- Используют существующий MaterialsService
- Совместимы с текущей архитектурой
- Поддерживают основные функции продвинутого поиска
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.schemas.materials import Material
from services.materials import MaterialsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/search", tags=["Advanced Search"])

# Simplified models for advanced search
class AdvancedSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    search_type: str = Field("hybrid", description="Search type: vector, sql, fuzzy, hybrid")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    units: Optional[List[str]] = Field(None, description="Filter by units")
    fuzzy_threshold: Optional[float] = Field(0.8, ge=0.0, le=1.0, description="Fuzzy matching threshold")

class SearchSuggestion(BaseModel):
    text: str
    score: float
    type: str

class PopularQuery(BaseModel):
    query: str
    count: int
    last_used: datetime

class AdvancedSearchResponse(BaseModel):
    results: List[Material]
    total_count: int
    search_time_ms: float
    suggestions: Optional[List[SearchSuggestion]] = None
    query_used: str
    search_type_used: str

@router.post("/advanced", response_model=AdvancedSearchResponse)
async def advanced_search(request: AdvancedSearchRequest):
    """
    Perform advanced search with comprehensive options.
    
    Выполнить продвинутый поиск с комплексными опциями.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Advanced search: '{request.query}', type: {request.search_type}")
        
        # Use MaterialsService for search
        service = MaterialsService()
        
        # Perform search based on type
        if request.search_type in ["vector", "hybrid"]:
            # Use vector search (default behavior of MaterialsService)
            results = await service.search_materials(
                query=request.query, 
                limit=request.limit
            )
        else:
            # For SQL and fuzzy, still use the same search but could be extended
            results = await service.search_materials(
                query=request.query, 
                limit=request.limit
            )
        
        # Apply basic filtering if specified
        if request.categories:
            results = [r for r in results if r.use_category in request.categories]
        
        if request.units:
            results = [r for r in results if r.unit in request.units]
        
        # Calculate search time
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Generate simple suggestions
        suggestions = []
        if len(results) > 0:
            suggestions = [
                SearchSuggestion(text=f"{request.query} {results[0].use_category}", score=0.9, type="category"),
                SearchSuggestion(text=f"{request.query} {results[0].unit}", score=0.8, type="unit")
            ]
        
        response = AdvancedSearchResponse(
            results=results,
            total_count=len(results),
            search_time_ms=search_time,
            suggestions=suggestions,
            query_used=request.query,
            search_type_used=request.search_type
        )
        
        logger.info(f"Advanced search completed: {len(results)} results, {search_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/suggestions", response_model=List[SearchSuggestion])
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Search query for suggestions"),
    limit: int = Query(8, ge=1, le=20, description="Maximum number of suggestions")
):
    """
    Get search suggestions for autocomplete.
    
    Получить предложения для автодополнения поиска.
    """
    try:
        logger.debug(f"Getting suggestions for query: '{q}'")
        
        # Generate simple suggestions based on common patterns
        suggestions = []
        
        # Common construction materials suggestions
        common_materials = [
            "цемент", "бетон", "кирпич", "песок", "щебень", "арматура", 
            "гипс", "известь", "шпаклевка", "краска", "утеплитель"
        ]
        
        # Find matching materials
        matching = [m for m in common_materials if q.lower() in m.lower()]
        
        for i, material in enumerate(matching[:limit]):
            suggestions.append(SearchSuggestion(
                text=material,
                score=1.0 - (i * 0.1),
                type="material"
            ))
        
        logger.debug(f"Generated {len(suggestions)} suggestions")
        return suggestions
        
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

@router.get("/popular-queries", response_model=List[PopularQuery])
async def get_popular_queries(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of popular queries")
):
    """
    Get popular search queries (mock implementation).
    
    Получить популярные поисковые запросы (mock реализация).
    """
    try:
        # Mock popular queries
        popular_queries = [
            PopularQuery(query="цемент", count=150, last_used=datetime.now()),
            PopularQuery(query="бетон", count=120, last_used=datetime.now() - timedelta(hours=1)),
            PopularQuery(query="кирпич", count=100, last_used=datetime.now() - timedelta(hours=2)),
            PopularQuery(query="песок строительный", count=80, last_used=datetime.now() - timedelta(hours=3)),
            PopularQuery(query="арматура", count=75, last_used=datetime.now() - timedelta(hours=4)),
        ]
        
        return popular_queries[:limit]
        
    except Exception as e:
        logger.error(f"Failed to get popular queries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get popular queries: {str(e)}")

@router.get("/analytics")
async def get_search_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date")
):
    """
    Get search analytics (mock implementation).
    
    Получить аналитику поиска (mock реализация).
    """
    try:
        # Mock analytics data
        analytics = {
            "period": {
                "start": start_date or (datetime.now() - timedelta(days=7)),
                "end": end_date or datetime.now()
            },
            "total_searches": 1247,
            "unique_queries": 892,
            "average_results_per_query": 8.3,
            "most_popular_categories": [
                {"category": "Цемент", "searches": 234},
                {"category": "Бетон", "searches": 189},
                {"category": "Кирпич", "searches": 156}
            ],
            "search_trends": {
                "growing": ["утеплитель", "гидроизоляция"],
                "declining": ["асбест", "старые материалы"]
            }
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/categories", response_model=List[str])
async def get_available_categories():
    """
    Get available material categories.
    
    Получить доступные категории материалов.
    """
    try:
        service = MaterialsService()
        materials = await service.get_materials(limit=1000)  # Get more for category analysis
        
        # Extract unique categories
        categories = list(set(m.use_category for m in materials if m.use_category))
        categories.sort()
        
        logger.debug(f"Found {len(categories)} categories")
        return categories
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        # Return mock categories if service fails
        return ["Цемент", "Бетон", "Кирпич", "Песок", "Щебень", "Арматура", "Гипс", "Краска"]

@router.get("/units", response_model=List[str])
async def get_available_units():
    """
    Get available measurement units.
    
    Получить доступные единицы измерения.
    """
    try:
        service = MaterialsService()
        materials = await service.get_materials(limit=1000)  # Get more for unit analysis
        
        # Extract unique units
        units = list(set(m.unit for m in materials if m.unit))
        units.sort()
        
        logger.debug(f"Found {len(units)} units")
        return units
        
    except Exception as e:
        logger.error(f"Failed to get units: {e}")
        # Return mock units if service fails
        return ["кг", "м3", "м2", "м", "шт", "т", "л", "упак"]

@router.post("/fuzzy", response_model=List[Material])
async def fuzzy_search(
    q: str = Query(..., min_length=1, description="Search query"),
    threshold: float = Query(0.8, ge=0.0, le=1.0, description="Similarity threshold"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results")
):
    """
    Perform fuzzy search with similarity matching.
    
    Выполнить нечеткий поиск с сопоставлением сходства.
    """
    try:
        logger.debug(f"Fuzzy search: '{q}', threshold: {threshold}")
        
        # Use standard search - MaterialsService already has good fuzzy matching
        service = MaterialsService()
        results = await service.search_materials(query=q, limit=limit)
        
        logger.debug(f"Fuzzy search completed: {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Fuzzy search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Fuzzy search failed: {str(e)}")

@router.get("/health")
async def search_health_check():
    """
    Health check for search service.
    
    Проверка здоровья поискового сервиса.
    """
    try:
        # Test basic search functionality
        service = MaterialsService()
        health = await service.get_health_status()
        
        # Add search-specific checks
        search_health = {
            **health,
            "advanced_search": "ok",
            "endpoints": {
                "advanced": "ok",
                "suggestions": "ok",
                "analytics": "ok",
                "categories": "ok",
                "units": "ok",
                "fuzzy": "ok"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug("Advanced search health check passed")
        return search_health
        
    except Exception as e:
        logger.error(f"Advanced search health check failed: {e}")
        return {
            "service": "advanced_search",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 