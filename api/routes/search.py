from fastapi import APIRouter, Query, HTTPException
from typing import List
import logging

from core.models.materials import Material
from services.materials import MaterialsService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[Material])
async def search_materials(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of results to return")
) -> List[Material]:
    """
    Search materials using semantic search
    """
    try:
        service = MaterialsService()
        return await service.search_materials(query=q, limit=limit)
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during search") 