from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from core.logging import get_logger
from core.config.base import settings
from core.schemas.materials import MaterialSearchResponse, MaterialSearchQuery
from core.repositories.interfaces import MaterialsRepositoryInterface
from core.dependencies.database import get_materials_repository

router = APIRouter()
logger = get_logger(__name__)

@router.get("/search", response_model=List[MaterialSearchResponse])
async def search_materials(
    q: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(10, description="Максимальное количество результатов"),
    repository: MaterialsRepositoryInterface = Depends(get_materials_repository)
):
    """
    Поиск материалов по текстовому запросу.
    
    - **q**: Поисковый запрос
    - **limit**: Максимальное количество результатов
    """
    logger.info(f"Поисковый запрос: {q}, лимит: {limit}")
    
    query = MaterialSearchQuery(
        query=q,
        limit=limit
    )
    
    results = await repository.search(query)
    logger.info(f"Найдено {len(results)} результатов")
    
    return results 