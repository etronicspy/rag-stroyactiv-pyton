from typing import List
from fastapi import APIRouter
from core.schemas.materials import Category, Unit
from services.materials import CategoryService, UnitService

router = APIRouter()

@router.post("/categories/", response_model=Category)
async def create_category(category: Category):
    """Create a new category"""
    return await CategoryService.create_category(category.name, category.description)

@router.get("/categories/", response_model=List[Category])
async def get_categories():
    """Get all categories"""
    return await CategoryService.get_categories()

@router.delete("/categories/{name}")
async def delete_category(name: str):
    """Delete a category"""
    success = await CategoryService.delete_category(name)
    return {"success": success}

@router.post("/units/", response_model=Unit)
async def create_unit(unit: Unit):
    """Create a new unit"""
    return await UnitService.create_unit(unit.name, unit.description)

@router.get("/units/", response_model=List[Unit])
async def get_units():
    """Get all units"""
    return await UnitService.get_units()

@router.delete("/units/{name}")
async def delete_unit(name: str):
    """Delete a unit"""
    success = await UnitService.delete_unit(name)
    return {"success": success} 