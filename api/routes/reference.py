from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from core.schemas.materials import (
    MaterialCreate, MaterialUpdate, MaterialResponse,
    CategoryCreate, CategoryInDB, UnitCreate, UnitInDB
)
from services.materials import MaterialsService, CategoryService, UnitService

router = APIRouter()
materials_service = MaterialsService()

# Materials endpoints
@router.post("/materials", response_model=MaterialResponse)
async def create_material(material: MaterialCreate):
    return await materials_service.create_material(material)

@router.get("/materials", response_model=List[MaterialResponse])
async def get_materials(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None
):
    return await materials_service.get_materials(skip, limit, category)

@router.get("/materials/{material_id}", response_model=MaterialResponse)
async def get_material(material_id: str):
    material = await materials_service.get_material(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

@router.put("/materials/{material_id}", response_model=MaterialResponse)
async def update_material(material_id: str, material: MaterialUpdate):
    updated_material = await materials_service.update_material(material_id, material)
    if not updated_material:
        raise HTTPException(status_code=404, detail="Material not found")
    return updated_material

@router.delete("/materials/{material_id}")
async def delete_material(material_id: str):
    deleted = await materials_service.delete_material(material_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"message": "Material deleted successfully"}

# Categories endpoints
@router.get("/categories", response_model=List[CategoryInDB])
async def get_categories():
    return await CategoryService.get_categories()

@router.post("/categories", response_model=CategoryInDB)
async def create_category(category: CategoryCreate):
    return await CategoryService.create_category(**category.model_dump())

@router.delete("/categories/{name}")
async def delete_category(name: str):
    deleted = await CategoryService.delete_category(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

# Units endpoints
@router.get("/units", response_model=List[UnitInDB])
async def get_units():
    return await UnitService.get_units()

@router.post("/units", response_model=UnitInDB)
async def create_unit(unit: UnitCreate):
    return await UnitService.create_unit(**unit.model_dump())

@router.delete("/units/{name}")
async def delete_unit(name: str):
    deleted = await UnitService.delete_unit(name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Unit not found")
    return {"message": "Unit deleted successfully"} 