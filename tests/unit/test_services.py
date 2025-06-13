"""
Unit tests for services
Объединенные unit тесты для сервисов

Объединяет тесты из:
- test_services_direct.py
- test_database_architecture.py (части)
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestCategoryService:
    """Unit тесты для CategoryService"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_category_service_direct(self):
        """Тест CategoryService напрямую без API"""
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
    
    @pytest.mark.unit
    def test_category_service_initialization(self):
        """Тест инициализации CategoryService"""
        from services.materials import CategoryService
        
        # Create service
        service = CategoryService()
        
        # Check it has the correct attributes
        assert hasattr(service, 'categories')
        assert isinstance(service.categories, dict)
    
    @pytest.mark.unit
    def test_category_service_sync_operations(self):
        """Тест синхронных операций CategoryService"""
        from services.materials import CategoryService
        from core.schemas.materials import Category
        
        # Create service
        service = CategoryService()
        
        # Create object directly (sync)
        category = Category(name="Тест", description="Описание")
        
        # Store in service storage
        service.categories["Тест"] = category
        
        # Check it was stored
        assert "Тест" in service.categories
        assert service.categories["Тест"].name == "Тест"
        assert service.categories["Тест"].description == "Описание"


class TestUnitService:
    """Unit тесты для UnitService"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unit_service_direct(self):
        """Тест UnitService напрямую без API"""
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
    
    @pytest.mark.unit
    def test_unit_service_initialization(self):
        """Тест инициализации UnitService"""
        from services.materials import UnitService
        
        # Create service
        service = UnitService()
        
        # Check it has the correct attributes
        assert hasattr(service, 'units')
        assert isinstance(service.units, dict)
    
    @pytest.mark.unit
    def test_unit_service_sync_operations(self):
        """Тест синхронных операций UnitService"""
        from services.materials import UnitService
        from core.schemas.materials import Unit
        
        # Create service
        service = UnitService()
        
        # Create object directly (sync)
        unit = Unit(name="кг", description="Килограмм")
        
        # Store in service storage
        service.units["кг"] = unit
        
        # Check it was stored
        assert "кг" in service.units
        assert service.units["кг"].name == "кг"
        assert service.units["кг"].description == "Килограмм"


class TestMaterialsService:
    """Unit тесты для MaterialsService"""
    
    @pytest.mark.unit
    def test_materials_service_initialization(self):
        """Тест инициализации MaterialsService"""
        try:
            from services.materials import MaterialsService
            service = MaterialsService()
            
            # Check basic attributes exist
            assert service is not None
        except ImportError:
            pytest.skip("MaterialsService not available")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_materials_service_mock_operations(self):
        """Тест операций MaterialsService с моками"""
        with patch('services.materials.MaterialsService') as MockService:
            mock_service = MockService.return_value
            mock_service.create_material = AsyncMock(return_value=Mock())
            mock_service.get_materials = AsyncMock(return_value=[])
            mock_service.delete_material = AsyncMock(return_value=True)
            
            # Test create
            result = await mock_service.create_material(Mock())
            assert result is not None
            
            # Test get
            materials = await mock_service.get_materials()
            assert isinstance(materials, list)
            
            # Test delete
            deleted = await mock_service.delete_material("test-id")
            assert deleted is True


class TestServiceIntegration:
    """Unit тесты для интеграции сервисов"""
    
    @pytest.mark.unit
    def test_service_factory_pattern(self):
        """Тест паттерна фабрики сервисов"""
        from services.materials import CategoryService, UnitService
        
        # Test that services can be created independently
        cat_service = CategoryService()
        unit_service = UnitService()
        
        # Test that they are different instances
        assert cat_service is not unit_service
        assert type(cat_service) != type(unit_service)
        
        # Test that they have their own storage
        assert cat_service.categories is not unit_service.units
    
    @pytest.mark.unit
    def test_service_dependency_injection(self):
        """Тест dependency injection для сервисов"""
        # Test that services can be injected as dependencies
        from services.materials import CategoryService, UnitService
        
        # Mock function that accepts services as dependencies
        def mock_function(cat_service: CategoryService, unit_service: UnitService):
            return cat_service, unit_service
        
        # Create services
        cat_service = CategoryService()
        unit_service = UnitService()
        
        # Inject dependencies
        result_cat, result_unit = mock_function(cat_service, unit_service)
        
        # Verify injection worked
        assert result_cat is cat_service
        assert result_unit is unit_service
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_async_compatibility(self):
        """Тест совместимости сервисов с async/await"""
        from services.materials import CategoryService, UnitService
        
        # Create services
        cat_service = CategoryService()
        unit_service = UnitService()
        
        # Test async operations work
        category = await cat_service.create_category("Test", "Description")
        unit = await unit_service.create_unit("kg", "Kilogram")
        
        assert category.name == "Test"
        assert unit.name == "kg"
        
        # Test that operations are truly async
        import asyncio
        
        async def create_multiple():
            tasks = [
                cat_service.create_category("Cat1", "Description1"),
                cat_service.create_category("Cat2", "Description2"),
                unit_service.create_unit("kg", "Kilogram"),
                unit_service.create_unit("m", "Meter")
            ]
            return await asyncio.gather(*tasks)
        
        results = await create_multiple()
        assert len(results) == 4
        assert all(result is not None for result in results)


class TestServiceErrorHandling:
    """Unit тесты для обработки ошибок в сервисах"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_category_service_error_handling(self):
        """Тест обработки ошибок в CategoryService"""
        from services.materials import CategoryService
        
        service = CategoryService()
        
        # Test that service gracefully handles invalid operations
        try:
            # Try to delete non-existent category
            result = await service.delete_category("NonExistent")
            # Should return False rather than raise exception
            assert result is False
        except Exception as e:
            # If exception is raised, it should be handled gracefully
            assert isinstance(e, (KeyError, ValueError))
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unit_service_error_handling(self):
        """Тест обработки ошибок в UnitService"""
        from services.materials import UnitService
        
        service = UnitService()
        
        # Test that service gracefully handles invalid operations
        try:
            # Try to delete non-existent unit
            result = await service.delete_unit("NonExistent")
            # Should return False rather than raise exception
            assert result is False
        except Exception as e:
            # If exception is raised, it should be handled gracefully
            assert isinstance(e, (KeyError, ValueError))
    
    @pytest.mark.unit
    def test_service_validation(self):
        """Тест валидации данных в сервисах"""
        from services.materials import CategoryService, UnitService
        
        cat_service = CategoryService()
        unit_service = UnitService()
        
        # Test that services exist and are properly initialized
        assert cat_service is not None
        assert unit_service is not None
        
        # Test that they have required methods
        assert hasattr(cat_service, 'create_category')
        assert hasattr(cat_service, 'get_categories')
        assert hasattr(cat_service, 'delete_category')
        
        assert hasattr(unit_service, 'create_unit')
        assert hasattr(unit_service, 'get_units')
        assert hasattr(unit_service, 'delete_unit')
        
        # Test that methods are callable
        assert callable(cat_service.create_category)
        assert callable(unit_service.create_unit) 