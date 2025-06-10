from typing import List
from fastapi import APIRouter
from core.schemas.materials import Category, Unit
from services.materials import CategoryService, UnitService

router = APIRouter()

@router.post("/categories/", response_model=Category)
async def create_category(category: Category):
    """Create a new category"""
    service = CategoryService()
    return await service.create_category(category.name, category.description)

@router.get("/categories/", response_model=List[Category])
async def get_categories():
    """Get all categories"""
    service = CategoryService()
    return await service.get_categories()

@router.delete("/categories/{name}")
async def delete_category(name: str):
    """Delete a category"""
    service = CategoryService()
    success = await service.delete_category(name)
    return {"success": success}

@router.post("/units/", response_model=Unit)
async def create_unit(unit: Unit):
    """Create a new unit"""
    service = UnitService()
    return await service.create_unit(unit.name, unit.description)

@router.get("/units/", response_model=List[Unit])
async def get_units():
    """Get all units"""
    service = UnitService()
    return await service.get_units()

@router.delete("/units/{name}")
async def delete_unit(name: str):
    """Delete a unit"""
    service = UnitService()
    success = await service.delete_unit(name)
    return {"success": success} 