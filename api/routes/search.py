from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from core.logging import get_logger
from core.config import get_settings
from core.schemas.materials import Material, MaterialSearchQuery
from core.repositories.interfaces import IMaterialsRepository
from core.dependencies.database import get_materials_repository

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

@router.get("/search", response_model=List[Material])
async def search_materials(
    q: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(10, description="Максимальное количество результатов"),
    repository: IMaterialsRepository = Depends(get_materials_repository)
):
    """
    Поиск материалов по текстовому запросу.
    
    - **q**: Поисковый запрос
    - **limit**: Максимальное количество результатов
    """
    logger.info(f"Поисковый запрос: {q}, лимит: {limit}")
    
    results = await repository.search_semantic(q, limit)
    logger.info(f"Найдено {len(results)} результатов")
    
    return results 