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

@router.get("/search", response_model=List[Material], responses=ERROR_RESPONSES, summary="🔎 Material Search – Семантический поиск материалов", response_description="Список материалов, удовлетворяющих поисковому запросу")
async def search_materials(
    q: str = Query(..., description="Search query string", alias="q"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results to return"),
):
    """Search construction materials by text query using semantic vector search.

    Делает семантический (vector) поиск материалов по текстовому запросу.
    Использует :class:`services.materials.MaterialsService` с векторной БД (Qdrant/Weaviate/Pinecone)
    для получения наиболее релевантных результатов.

    Args:
        q (str): User search query.
        limit (int): Upper bound for the amount of materials returned (1-100).

    Returns:
        List[Material]: Sorted list of materials matching the query ordered by similarity score.

    Raises:
        HTTPException: 500 if underlying service raises an exception.

    Example:
        ```shell
        curl -X GET "https://api.example.com/api/v1/search?q=цемент+М500&limit=20"
        ```

        Example response (HTTP 200):
        ```json
        [
          {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Портландцемент М500 Д0",
            "use_category": "Цемент",
            "unit": "мешок",
            "sku": "CEM500-001",
            "description": "Высокопрочный цемент для конструкционного бетона",
            "embedding": null,
            "created_at": "2025-06-16T16:46:29.421964Z",
            "updated_at": "2025-06-16T16:46:29.421964Z"
          },
          {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "Портландцемент М400",
            "use_category": "Цемент",
            "unit": "мешок",
            "sku": "CEM400-007",
            "description": "Цемент общего назначения",
            "embedding": null,
            "created_at": "2025-06-16T16:46:29.421964Z",
            "updated_at": "2025-06-16T16:46:29.421964Z"
          }
        ]
        ```

    Response Codes:
        200: Successful search.
        400: Validation error (e.g., empty query, invalid limit).
        500: Internal server error / search backend failure.
    """
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