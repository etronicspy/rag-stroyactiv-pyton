"""
Direct service tests to check if our implementations work
"""
import pytest
import asyncio

@pytest.mark.asyncio
async def test_category_service_direct():
    """Test CategoryService directly without API"""
    from services.materials import CategoryService
    
    # Create service
    service = CategoryService()
    
    # Test create category
    category = await service.create_category("Тест", "Тестовая категория")
    assert category.name == "Тест"
    assert category.description == "Тестовая категория"
    
    # Test get categories
    categories = await service.get_categories()
    assert len(categories) == 1
    assert categories[0].name == "Тест"
    
    # Test delete category
    result = await service.delete_category("Тест")
    assert result is True
    
    # Check empty after delete
    categories = await service.get_categories()
    assert len(categories) == 0

@pytest.mark.asyncio
async def test_unit_service_direct():
    """Test UnitService directly without API"""
    from services.materials import UnitService
    
    # Create service
    service = UnitService()
    
    # Test create unit
    unit = await service.create_unit("кг", "Килограмм")
    assert unit.name == "кг"
    assert unit.description == "Килограмм"
    
    # Test get units
    units = await service.get_units()
    assert len(units) == 1
    assert units[0].name == "кг"
    
    # Test delete unit
    result = await service.delete_unit("кг")
    assert result is True
    
    # Check empty after delete
    units = await service.get_units()
    assert len(units) == 0

def test_service_initialization():
    """Test that services can be initialized"""
    from services.materials import CategoryService, UnitService
    
    # Create services
    cat_service = CategoryService()
    unit_service = UnitService()
    
    # Check they have the correct attributes
    assert hasattr(cat_service, 'categories')
    assert hasattr(unit_service, 'units')
    assert isinstance(cat_service.categories, dict)
    assert isinstance(unit_service.units, dict)

def test_sync_version():
    """Test sync version of service creation"""
    from services.materials import CategoryService, UnitService
    from core.schemas.materials import Category, Unit
    
    # Create services
    cat_service = CategoryService()
    unit_service = UnitService()
    
    # Create objects directly (sync)
    category = Category(name="Тест", description="Описание")
    unit = Unit(name="кг", description="Килограмм")
    
    # Store in service storage
    cat_service.categories["Тест"] = category
    unit_service.units["кг"] = unit
    
    # Check they were stored
    assert "Тест" in cat_service.categories
    assert "кг" in unit_service.units
    
    assert cat_service.categories["Тест"].name == "Тест"
    assert unit_service.units["кг"].name == "кг" 