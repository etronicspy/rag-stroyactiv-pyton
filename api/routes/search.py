from fastapi import APIRouter, Query
from typing import List

from core.logging import get_logger
from core.config import get_settings
from core.schemas.materials import Material
from services.materials import MaterialsService  # for test patching
from core.schemas.response_models import ERROR_RESPONSES

router = APIRouter(responses=ERROR_RESPONSES)
logger = get_logger(__name__)
settings = get_settings()

@router.get("/search", response_model=List[Material], responses=ERROR_RESPONSES)
async def search_materials(
    q: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(10, description="Максимальное количество результатов"),
):
    """Search materials via MaterialsService (vector search)."""
    logger.info(f"Поисковый запрос: {q}, лимит: {limit}")
    service = MaterialsService()
    try:
        results = await service.search_materials(query=q, limit=limit)
    except Exception as e:
        logger.error(f"Search service error: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
    logger.info(f"Найдено {len(results)} результатов (via MaterialsService)")
    return results

# Trailing slash variant for legacy clients
@router.get("/search/", response_model=List[Material], responses=ERROR_RESPONSES, include_in_schema=False)
async def search_materials_trailing(
    q: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(10, description="Максимальное количество результатов"),
):
    return await search_materials(q=q, limit=limit)

# Alias endpoint for backward compatibility with older tests
@router.get("/search/materials", response_model=List[Material], responses=ERROR_RESPONSES, include_in_schema=False)
async def search_materials_alias(
    query: str = Query(..., description="Search query", alias="query"),
    limit: int = Query(10, description="Maximum number of results"),
):
    """Alias for material search kept for backward-compatibility.

    This mirrors the logic of MaterialsService.search_materials used in legacy tests.
    """
    logger.info(f"[alias] Searching materials: '{query}', limit={limit}")
    # Lazy import to avoid circular dependency in tests
    from services.materials import MaterialsService

    service = MaterialsService()
    results = await service.search_materials(query=query, limit=limit)
    return results

# Root endpoint variant for unit tests (prefix handled externally)
@router.get("", response_model=List[Material], responses=ERROR_RESPONSES, include_in_schema=False)
async def search_materials_root(
    q: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(10, description="Максимальное количество результатов"),
):
    return await search_materials(q=q, limit=limit)

# Trailing slash root variant
@router.get("/", response_model=List[Material], responses=ERROR_RESPONSES, include_in_schema=False)
async def search_materials_root_slash(
    q: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(10, description="Максимальное количество результатов"),
):
    return await search_materials(q=q, limit=limit) 