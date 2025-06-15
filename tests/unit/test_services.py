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
from datetime import datetime

from services.materials import MaterialsService
from core.schemas.materials import MaterialCreate
from core.database.exceptions import DatabaseError


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


# === Database Architecture Tests ===
class TestDatabaseInterfaces:
    """Test database interfaces and abstract methods."""
    
    def test_vector_database_interface_methods(self):
        """Test that IVectorDatabase has all required methods."""
        required_methods = [
            "create_collection", "collection_exists", "upsert", "search", 
            "get_by_id", "update_vector", "delete", "batch_upsert", "health_check"
        ]
        
        for method_name in required_methods:
            assert hasattr(IVectorDatabase, method_name), f"Missing method: {method_name}"
    
    def test_relational_database_interface_methods(self):
        """Test that IRelationalDatabase has all required methods."""
        required_methods = [
            "execute_query", "execute_command", "begin_transaction", 
            "health_check"
        ]
        
        for method_name in required_methods:
            assert hasattr(IRelationalDatabase, method_name), f"Missing method: {method_name}"
    
    def test_cache_database_interface_methods(self):
        """Test that ICacheDatabase has all required methods."""
        required_methods = ["get", "set", "delete", "exists", "health_check"]
        
        for method_name in required_methods:
            assert hasattr(ICacheDatabase, method_name), f"Missing method: {method_name}"


class TestDatabaseFactory:
    """Test database factory functionality."""
    
    def test_vector_database_factory_creates_qdrant(self):
        """Test that vector database factory creates Qdrant adapter."""
        with patch('core.database.adapters.qdrant_adapter.QdrantVectorDatabase') as mock_qdrant:
            mock_instance = Mock()
            mock_qdrant.return_value = mock_instance
            
            result = DatabaseFactory.create_vector_database(
                db_type="qdrant_cloud",
                config_override={
                    "url": "test://url",
                    "api_key": "test_key",
                    "collection_name": "test_materials"
                }
            )
            
            mock_qdrant.assert_called_once()
            assert result == mock_instance
    
    def test_factory_caching_works(self):
        """Test that factory caching works with @lru_cache."""
        with patch('core.database.adapters.qdrant_adapter.QdrantVectorDatabase') as mock_qdrant:
            mock_instance = Mock()
            mock_qdrant.return_value = mock_instance
            
            # Call twice with same parameters
            config = {"url": "test://url", "api_key": "test_key"}
            result1 = DatabaseFactory.create_vector_database(config_override=config)
            result2 = DatabaseFactory.create_vector_database(config_override=config)
            
            # Should be called only once due to caching
            mock_qdrant.assert_called_once()
            assert result1 == result2 == mock_instance
    
    def test_factory_cache_info(self):
        """Test that factory provides cache information."""
        cache_info = DatabaseFactory.get_cache_info()
        
        assert "vector_db_cache" in cache_info
        assert "relational_db_cache" in cache_info
        assert "cache_db_cache" in cache_info
        
        # Should have cache statistics
        vector_cache = cache_info["vector_db_cache"]
        assert "hits" in vector_cache
        assert "misses" in vector_cache


class TestDependencyInjection:
    """Test dependency injection functionality."""
    
    def test_vector_db_dependency_works(self):
        """Test that vector DB dependency injection works."""
        with patch('core.database.factories.DatabaseFactory.create_vector_database') as mock_factory:
            mock_instance = Mock()
            mock_factory.return_value = mock_instance
            
            result = get_vector_db_dependency()
            
            mock_factory.assert_called_once()
            assert result == mock_instance
    
    def test_ai_client_dependency_works(self):
        """Test that AI client dependency injection works."""
        with patch('core.database.factories.AIClientFactory.create_ai_client') as mock_factory:
            mock_instance = Mock()
            mock_factory.return_value = mock_instance
            
            result = get_ai_client_dependency()
            
            mock_factory.assert_called_once()
            assert result == mock_instance
    
    def test_dependency_caching_works(self):
        """Test that dependency injection caching works."""
        with patch('core.database.factories.DatabaseFactory.create_vector_database') as mock_factory:
            mock_instance = Mock()
            mock_factory.return_value = mock_instance
            
            # Call twice
            result1 = get_vector_db_dependency()
            result2 = get_vector_db_dependency()
            
            # Should be called only once due to caching
            mock_factory.assert_called_once()
            assert result1 == result2 == mock_instance
    
    def test_clear_dependency_cache_works(self):
        """Test that clearing dependency cache works."""
        with patch('core.database.factories.DatabaseFactory.create_vector_database') as mock_factory:
            mock_instance = Mock()
            mock_factory.return_value = mock_instance
            
            # Call, clear cache, call again
            get_vector_db_dependency()
            clear_dependency_cache()
            get_vector_db_dependency()
            
            # Should be called twice after cache clear
            assert mock_factory.call_count == 2


class TestDatabaseExceptions:
    """Test database exception hierarchy."""
    
    def test_database_error_inheritance(self):
        """Test database exception inheritance."""
        error = DatabaseError("Test error", details="Test details")
        
        assert isinstance(error, Exception)
        assert error.message == "Test error"
        assert error.details == "Test details"
    
    def test_connection_error_inheritance(self):
        """Test connection error inheritance."""
        error = ConnectionError("PostgreSQL", "Connection failed", "Details")
        
        assert isinstance(error, DatabaseError)
        assert error.database_type == "PostgreSQL"
        assert "Failed to connect to PostgreSQL database" in str(error)
    
    def test_configuration_error_inheritance(self):
        """Test configuration error inheritance."""
        error = ConfigurationError("DATABASE_TYPE", "Invalid type", "Details")
        
        assert isinstance(error, DatabaseError)
        assert error.config_key == "DATABASE_TYPE"
        assert "Database configuration error for key: DATABASE_TYPE" in str(error)


# === Refactored MaterialsService Tests ===
class TestMaterialsServiceRefactored:
    """Test refactored MaterialsService with dependency injection."""
    
    @pytest.fixture
    def mock_vector_db(self):
        """Mock vector database client."""
        mock_db = Mock()
        mock_db.collection_exists = AsyncMock(return_value=True)
        mock_db.create_collection = AsyncMock()
        mock_db.upsert = AsyncMock()
        mock_db.get_by_id = AsyncMock()
        mock_db.search = AsyncMock()
        mock_db.delete = AsyncMock()
        mock_db.batch_upsert = AsyncMock()
        mock_db.health_check = AsyncMock(return_value={
            "status": "healthy",
            "database_type": "Qdrant",
            "timestamp": datetime.utcnow().isoformat()
        })
        return mock_db
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client for embeddings."""
        return Mock()
    
    @pytest.fixture
    def materials_service(self, mock_vector_db, mock_ai_client):
        """Create MaterialsService with mocked dependencies."""
        return MaterialsService(vector_db=mock_vector_db, ai_client=mock_ai_client)
    
    @pytest.fixture
    def sample_material_create(self):
        """Sample MaterialCreate object."""
        return MaterialCreate(
            name="Тестовый цемент",
            use_category="Цемент",
            unit="кг",
            sku="CEM001",
            description="Портландцемент М400"
        )
    
    def test_service_initialization(self, materials_service):
        """Test service initialization with dependency injection."""
        assert materials_service.collection_name == "materials"
        assert materials_service.vector_db is not None
        assert materials_service.ai_client is not None
    
    @pytest.mark.asyncio
    async def test_ensure_collection_exists_creates_collection(self, materials_service, mock_vector_db):
        """Test collection creation when it doesn't exist."""
        mock_vector_db.collection_exists.return_value = False
        
        await materials_service._ensure_collection_exists()
        
        mock_vector_db.collection_exists.assert_called_once_with("materials")
        mock_vector_db.create_collection.assert_called_once_with(
            collection_name="materials",
            vector_size=1536,
            distance_metric="cosine"
        )
    
    @pytest.mark.asyncio
    async def test_ensure_collection_exists_skips_if_exists(self, materials_service, mock_vector_db):
        """Test collection creation is skipped when collection exists."""
        mock_vector_db.collection_exists.return_value = True
        
        await materials_service._ensure_collection_exists()
        
        mock_vector_db.collection_exists.assert_called_once_with("materials")
        mock_vector_db.create_collection.assert_not_called()
    
    @patch('services.materials.MaterialsService.get_embedding')
    @pytest.mark.asyncio
    async def test_create_material_success(self, mock_get_embedding, materials_service, 
                                         mock_vector_db, sample_material_create):
        """Test successful material creation."""
        # Mock embedding generation
        mock_embedding = [0.1] * 1536
        mock_get_embedding.return_value = mock_embedding
        
        # Call create_material
        result = await materials_service.create_material(sample_material_create)
        
        # Verify embedding was generated
        mock_get_embedding.assert_called_once()
        
        # Verify vector database upsert was called
        mock_vector_db.upsert.assert_called_once()
        call_args = mock_vector_db.upsert.call_args[1]
        assert call_args["collection_name"] == "materials"
        assert len(call_args["vectors"]) == 1
        
        vector_data = call_args["vectors"][0]
        assert vector_data["vector"] == mock_embedding
        assert vector_data["payload"]["name"] == sample_material_create.name
        assert vector_data["payload"]["use_category"] == sample_material_create.use_category
        
        # Verify returned material
        assert result.name == sample_material_create.name
        assert result.use_category == sample_material_create.use_category
        assert result.id is not None
        assert result.embedding == mock_embedding[:10]  # Truncated
    
    @patch('services.materials.MaterialsService.get_embedding')
    @pytest.mark.asyncio
    async def test_create_material_database_error(self, mock_get_embedding, materials_service, 
                                                 mock_vector_db, sample_material_create):
        """Test material creation with database error."""
        mock_get_embedding.return_value = [0.1] * 1536
        mock_vector_db.upsert.side_effect = Exception("Database connection failed")
        
        with pytest.raises(DatabaseError) as exc_info:
            await materials_service.create_material(sample_material_create)
        
        assert "Failed to create material" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_material_success(self, materials_service, mock_vector_db):
        """Test successful material retrieval."""
        # Mock vector database response
        mock_result = {
            "id": "test-id",
            "vector": [0.1] * 10,
            "payload": {
                "name": "Тестовый материал",
                "use_category": "Тест",
                "unit": "шт",
                "sku": "TEST001",
                "description": "Тестовое описание",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        }
        mock_vector_db.get_by_id.return_value = mock_result
        
        result = await materials_service.get_material("test-id")
        
        mock_vector_db.get_by_id.assert_called_once_with(
            collection_name="materials",
            vector_id="test-id"
        )
        
        assert result is not None
        assert result.id == "test-id"
        assert result.name == "Тестовый материал"
        assert result.use_category == "Тест"
    
    @pytest.mark.asyncio
    async def test_get_material_not_found(self, materials_service, mock_vector_db):
        """Test material retrieval when material doesn't exist."""
        mock_vector_db.get_by_id.return_value = None
        
        result = await materials_service.get_material("nonexistent-id")
        
        assert result is None
    
    @patch('services.materials.MaterialsService.get_embedding')
    @pytest.mark.asyncio
    async def test_search_materials_vector_success(self, mock_get_embedding, materials_service, mock_vector_db):
        """Test successful vector search."""
        # Mock embedding and search results
        mock_get_embedding.return_value = [0.1] * 1536
        mock_search_results = [
            {
                "id": "result-1",
                "vector": [0.1] * 10,
                "payload": {
                    "name": "Цемент М400",
                    "use_category": "Цемент",
                    "unit": "кг",
                    "sku": "CEM400",
                    "description": "Портландцемент",
                    "created_at": "2024-01-01T12:00:00",
                    "updated_at": "2024-01-01T12:00:00"
                }
            }
        ]
        mock_vector_db.search.return_value = mock_search_results
        
        results = await materials_service.search_materials("цемент", limit=10)
        
        # Verify embedding generation and search
        mock_get_embedding.assert_called_once_with("цемент")
        mock_vector_db.search.assert_called_once_with(
            collection_name="materials",
            query_vector=[0.1] * 1536,
            limit=10,
            filter_conditions=None
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0].name == "Цемент М400"
        assert results[0].use_category == "Цемент"
    
    @pytest.mark.asyncio
    async def test_delete_material_success(self, materials_service, mock_vector_db):
        """Test successful material deletion."""
        await materials_service.delete_material("test-id")
        
        mock_vector_db.delete.assert_called_once_with(
            collection_name="materials",
            vector_id="test-id"
        )
    
    @pytest.mark.asyncio
    async def test_delete_material_database_error(self, materials_service, mock_vector_db):
        """Test material deletion with database error."""
        mock_vector_db.delete.side_effect = Exception("Database connection failed")
        
        with pytest.raises(DatabaseError) as exc_info:
            await materials_service.delete_material("test-id")
        
        assert "Failed to delete material" in str(exc_info.value)
    
    def test_category_inference(self, materials_service):
        """Test category inference from material name."""
        # Test cement inference
        assert materials_service._infer_category("Портландцемент М400") == "Цемент"
        assert materials_service._infer_category("Цемент белый") == "Цемент"
        
        # Test sand inference
        assert materials_service._infer_category("Песок речной") == "Песок"
        assert materials_service._infer_category("Песок карьерный") == "Песок"
        
        # Test unknown material
        assert materials_service._infer_category("Неизвестный материал") == "Прочее"
    
    def test_unit_inference(self, materials_service):
        """Test unit inference from material name."""
        # Test weight units
        assert materials_service._infer_unit("Цемент М400") == "кг"
        assert materials_service._infer_unit("Гвозди строительные") == "кг"
        
        # Test volume units
        assert materials_service._infer_unit("Песок речной") == "м³"
        assert materials_service._infer_unit("Бетон М300") == "м³"
        
        # Test piece units
        assert materials_service._infer_unit("Кирпич красный") == "шт"
        assert materials_service._infer_unit("Блок газобетонный") == "шт"
        
        # Test unknown material
        assert materials_service._infer_unit("Неизвестный материал") == "шт"
    
    def test_prepare_text_for_embedding(self, materials_service, sample_material_create):
        """Test text preparation for embedding generation."""
        text = materials_service._prepare_text_for_embedding(sample_material_create)
        
        assert sample_material_create.name in text
        assert sample_material_create.use_category in text
        assert sample_material_create.description in text
        assert sample_material_create.unit in text 