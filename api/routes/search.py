from fastapi import APIRouter
from core.schemas.materials import MaterialSearchQuery, MaterialResponse
from services.materials import MaterialsService
from typing import List

router = APIRouter()
materials_service = MaterialsService()

@router.post("/search", response_model=List[MaterialResponse])
async def search_materials(query: MaterialSearchQuery):
    return await materials_service.search_materials(
        query=query.query,
        limit=query.limit
    ) 