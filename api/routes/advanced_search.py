"""
Advanced Search API Routes (Simplified)

Упрощенные API роуты для продвинутого поиска материалов:
- Используют существующий MaterialsService
- Совместимы с текущей архитектурой
- Поддерживают основные функции продвинутого поиска
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from fastapi import APIRouter, HTTPException, Query
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
    
    Parameters:
    - request: Advanced search parameters (query, search_type, limit, categories, units)  
    - Returns: Search results with analytics (timing, suggestions, total count)
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
    
    Parameters:
    - q: Search query for suggestions (minimum 1 character)
    - limit: Maximum number of suggestions (default: 8, max: 20)
    - Returns: List of search suggestions with scores and types
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

@router.get("/categories", response_model=List[str])
async def get_available_categories():
    """
    Get available material categories.
    
    Parameters:
    - Returns: List of all available material categories
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
    
    Parameters:
    - Returns: List of all available measurement units
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