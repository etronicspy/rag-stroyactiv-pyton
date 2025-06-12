from typing import List, Optional
from fastapi import APIRouter, HTTPException
from core.schemas.materials import MaterialCreate, MaterialUpdate, Material, MaterialSearchQuery, MaterialBatchCreate, MaterialBatchResponse, MaterialImportRequest
from services.materials_consolidated import MaterialsService

router = APIRouter()
materials_service = MaterialsService()

@router.post("/", response_model=Material)
async def create_material(material: MaterialCreate):
    """Create a new material"""
    return await materials_service.create_material(material)

@router.get("/{material_id}", response_model=Material)
async def get_material(material_id: str):
    """Get a specific material by ID"""
    material = await materials_service.get_material(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

@router.get("/", response_model=List[Material])
async def get_materials(skip: int = 0, limit: int = 10, category: Optional[str] = None):
    """Get all materials with optional filtering"""
    return await materials_service.get_materials(skip=skip, limit=limit, category=category)

@router.put("/{material_id}", response_model=Material)
async def update_material(material_id: str, material: MaterialUpdate):
    """Update a material"""
    updated = await materials_service.update_material(material_id, material)
    if not updated:
        raise HTTPException(status_code=404, detail="Material not found")
    return updated

@router.delete("/{material_id}")
async def delete_material(material_id: str):
    """Delete a material"""
    success = await materials_service.delete_material(material_id)
    if not success:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"success": success}

@router.post("/batch", response_model=MaterialBatchResponse)
async def create_materials_batch(batch_data: MaterialBatchCreate):
    """Batch create materials"""
    try:
        return await materials_service.create_materials_batch(
            batch_data.materials, 
            batch_data.batch_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch creation failed: {str(e)}")

@router.post("/import", response_model=MaterialBatchResponse)
async def import_materials_from_json(import_data: MaterialImportRequest):
    """Import materials from JSON format (sku + name)"""
    try:
        return await materials_service.import_materials_from_json(
            import_data.materials,
            import_data.default_use_category,
            import_data.default_unit,
            import_data.batch_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.post("/search", response_model=List[Material])
async def search_materials(query: MaterialSearchQuery):
    """Search materials by query"""
    return await materials_service.search_materials(query.query, query.limit) 