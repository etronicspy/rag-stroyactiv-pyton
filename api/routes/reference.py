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

@router.delete("/categories/{name}")
async def delete_category(
    name: str,
    service: CategoryService = Depends(get_category_service)
):
    """
    Delete a material category.
    
    Parameters:
    - name: Category name to delete
    - Returns: Success status
    """
    success = await service.delete_category(name)
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

@router.delete("/units/{name}")
async def delete_unit(
    name: str,
    service: UnitService = Depends(get_unit_service)
):
    """
    Delete a measurement unit.
    
    Parameters:
    - name: Unit name to delete
    - Returns: Success status
    """
    success = await service.delete_unit(name)
    return {"success": success} 