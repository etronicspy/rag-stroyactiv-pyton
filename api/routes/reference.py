from typing import List
from fastapi import APIRouter, Depends
from core.schemas.materials import Category, Unit
from services.materials import CategoryService, UnitService
from core.database.interfaces import IVectorDatabase
from core.dependencies.database import get_vector_db_dependency

router = APIRouter()

def get_category_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency)
) -> CategoryService:
    """Get CategoryService with dependency injection."""
    return CategoryService(vector_db=vector_db)

def get_unit_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency)
) -> UnitService:
    """Get UnitService with dependency injection."""
    return UnitService(vector_db=vector_db)

@router.post("/categories/", response_model=Category)
async def create_category(
    category: Category,
    service: CategoryService = Depends(get_category_service)
):
    """
    Create a new material category.
    
    Parameters:
    - category: Category data (name, description)
    - Returns: Created category with timestamps
    """
    return await service.create_category(category.name, category.description)

@router.get("/categories/", response_model=List[Category])
async def get_categories(
    service: CategoryService = Depends(get_category_service)
):
    """
    Get all material categories.
    
    Parameters:
    - Returns: List of all available categories
    """
    return await service.get_categories()

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service)
):
    """
    Delete a material category by ID.
    
    Parameters:
    - category_id: Category ID to delete
    - Returns: Success status
    """
    success = await service.delete_category(category_id)
    return {"success": success}

@router.delete("/categories/by-name/{name}")
async def delete_category_by_name(
    name: str,
    service: CategoryService = Depends(get_category_service)
):
    """
    Delete a material category by name (legacy API).
    
    Parameters:
    - name: Category name to delete
    - Returns: Success status
    """
    success = await service.delete_category_by_name(name)
    return {"success": success}

@router.post("/units/", response_model=Unit)
async def create_unit(
    unit: Unit,
    service: UnitService = Depends(get_unit_service)
):
    """
    Create a new measurement unit.
    
    Parameters:
    - unit: Unit data (name, description)
    - Returns: Created unit with timestamps
    """
    return await service.create_unit(unit.name, unit.description)

@router.get("/units/", response_model=List[Unit])
async def get_units(
    service: UnitService = Depends(get_unit_service)
):
    """
    Get all measurement units.
    
    Parameters:
    - Returns: List of all available measurement units
    """
    return await service.get_units()

@router.delete("/units/{unit_id}")
async def delete_unit(
    unit_id: str,
    service: UnitService = Depends(get_unit_service)
):
    """
    Delete a measurement unit by ID.
    
    Parameters:
    - unit_id: Unit ID to delete
    - Returns: Success status
    """
    success = await service.delete_unit(unit_id)
    return {"success": success}

@router.delete("/units/by-name/{name}")
async def delete_unit_by_name(
    name: str,
    service: UnitService = Depends(get_unit_service)
):
    """
    Delete a measurement unit by name (legacy API).
    
    Parameters:
    - name: Unit name to delete
    - Returns: Success status
    """
    success = await service.delete_unit_by_name(name)
    return {"success": success} 