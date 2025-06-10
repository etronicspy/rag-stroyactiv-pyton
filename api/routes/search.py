from fastapi import APIRouter, Query
from typing import List

from core.models.materials import Material
from services.materials import MaterialsService

router = APIRouter()

@router.get("/", response_model=List[Material])
async def search_materials(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of results to return")
) -> List[Material]:
    """
    Search materials using semantic search
    """
    service = MaterialsService()
    return await service.search_materials(query=q, limit=limit) 