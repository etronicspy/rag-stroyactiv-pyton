"""
Unit tests for API endpoints with mocks
Объединенные unit тесты для всех API эндпоинтов с использованием моков

Объединяет тесты из:
- test_health.py
- test_simple_health.py  
- test_basic_functionality.py
- test_materials_fast.py
- test_reference_fast.py
"""
import pytest
import os
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from core.schemas.materials import Material, MaterialCreate, MaterialBatchResponse
from core.schemas.materials import Category, Unit


# === Root API Tests ===
class TestRootAPI:
    """Test root API endpoint."""
    
    def test_root_endpoint(self, client_mock):
        """Test root endpoint."""
        response = client_mock.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs_url" in data
        assert data["message"] == "Welcome to Construction Materials API"
        assert data["docs_url"] == "/docs"


class TestHealthEndpoints:
    """Комплексные тесты health check эндпоинтов"""
    
    @pytest.mark.unit
    def test_basic_health_check(self, client_mock):
        """Тест базового health check"""
        response = client_mock.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "environment" in data
    
    @pytest.mark.unit
    def test_health_config_check(self, client_mock):
        """Тест health check конфигурации"""
        response = client_mock.get("/api/v1/health/config")
        assert response.status_code == 200
        data = response.json()
        assert "configuration" in data
        
        configuration = data["configuration"]
        # Проверяем наличие AI сервиса
        ai_service_exists = any(key in configuration for key in ["openai", "huggingface", "ai_provider"])
        assert ai_service_exists, f"AI service not found in configuration: {list(configuration.keys())}"
        
        # Проверяем наличие БД сервиса
        db_service_exists = any(key in configuration for key in ["database_type", "qdrant", "vector_db"])
        assert db_service_exists, f"DB service not found in configuration: {list(configuration.keys())}"
    
    @pytest.mark.unit
    def test_detailed_health_check(self, client_mock):
        """Тест детального health check"""
        response = client_mock.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        # Проверяем что детальный health check возвращает структурированные данные
        assert "overall_status" in data or "status" in data or "databases" in data


class TestBasicAPIEndpoints:
    """Тесты базовых API эндпоинтов"""
    
    @pytest.mark.unit
    def test_root_endpoint(self, client_mock):
        """Тест корневого эндпоинта"""
        response = client_mock.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Test API" in data["message"] or "Construction Materials API" in data["message"]
    
    @pytest.mark.unit
    def test_docs_endpoint(self, client_mock):
        """Тест доступности Swagger документации"""
        response = client_mock.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.unit
    def test_openapi_schema(self, client_mock):
        """Тест доступности OpenAPI схемы"""
        response = client_mock.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "Test API" in data["info"]["title"] or "Construction Materials API" in data["info"]["title"]


class TestMaterialsAPIEndpoints:
    """Unit тесты для Materials API с моками"""
    
    @pytest.mark.unit
    def test_create_material(self, client_mock, sample_material):
        """Тест создания материала с моком"""
        with patch('api.routes.materials.get_materials_service') as mock_service_dep:
            mock_service = Mock()
            mock_service.create_material = AsyncMock(return_value=sample_material)
            mock_service_dep.return_value = mock_service
            
            response = client_mock.post(
                "/api/v1/materials/",
                json={
                    "name": "Портландцемент М500",
                    "use_category": "Цемент",
                    "unit": "кг",
                    "description": "Высококачественный цемент"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "name" in data
    
    @pytest.mark.unit
    def test_get_material(self, client_mock, sample_material):
        """Тест получения конкретного материала"""
        with patch('api.routes.materials.get_materials_service') as mock_service_dep:
            mock_service = Mock()
            mock_service.get_material = AsyncMock(return_value=sample_material)
            mock_service_dep.return_value = mock_service
            
            response = client_mock.get("/api/v1/materials/test-id")
            
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "name" in data
    
    @pytest.mark.unit
    def test_get_materials_list(self, client_mock, sample_material):
        """Тест получения списка материалов"""
        with patch('api.routes.materials.get_materials_service') as mock_service_dep:
            mock_service = Mock()
            mock_service.get_materials = AsyncMock(return_value=[sample_material])
            mock_service_dep.return_value = mock_service
            
            response = client_mock.get("/api/v1/materials/")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.unit
    def test_update_material(self, client_mock, sample_material):
        """Тест обновления материала"""
        # Для этого теста просто проверим что обновление проходит без ошибок
        response = client_mock.put(
            "/api/v1/materials/test-id",
            json={
                "name": "Обновленный материал",
                "description": "Обновленное описание"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # В unit тестах достаточно проверить что запрос выполнился
        assert "name" in data
        assert "id" in data
    
    @pytest.mark.unit
    def test_delete_material(self, client_mock):
        """Тест удаления материала"""
        with patch('api.routes.materials.get_materials_service') as mock_service_dep:
            mock_service = Mock()
            mock_service.delete_material = AsyncMock(return_value=True)
            mock_service_dep.return_value = mock_service
            
            response = client_mock.delete("/api/v1/materials/test-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    @pytest.mark.unit
    def test_batch_create_materials(self, client_mock):
        """Тест batch создания материалов"""
        mock_batch_response = MaterialBatchResponse(
            success=True,
            total_processed=2,
            successful_creates=2,
            failed_creates=0,
            created_materials=[],
            errors=[]
        )
        
        with patch('api.routes.materials.get_materials_service') as mock_service_dep:
            mock_service = Mock()
            mock_service.create_materials_batch = AsyncMock(return_value=mock_batch_response)
            mock_service_dep.return_value = mock_service
            
            materials_data = [
                {
                    "name": "Цемент М500 batch 1",
                    "use_category": "Цемент",
                    "unit": "кг",
                    "sku": "BTH0001",
                    "description": "Тест батч 1"
                },
                {
                    "name": "Цемент М400 batch 2",
                    "use_category": "Цемент",
                    "unit": "кг",
                    "sku": "BTH0002",
                    "description": "Тест батч 2"
                }
            ]
            
            response = client_mock.post(
                "/api/v1/materials/batch",
                json={
                    "materials": materials_data,
                    "batch_size": 2
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["total_processed"] == 2
    
    @pytest.mark.unit
    def test_materials_validation_error(self, client_mock):
        """Тест валидационной ошибки при создании материала"""
        response = client_mock.post(
            "/api/v1/materials/",
            json={
                "name": "",  # Invalid: empty name
                "use_category": "Цемент",
                "unit": "кг"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestSearchAPI:
    """Test search API endpoints."""
    
    @pytest.fixture
    def mock_materials_service(self):
        """Mock MaterialsService for testing."""
        service = Mock()
        service.search_materials = AsyncMock()
        return service
    
    def test_search_materials_success(self, client_mock, mock_materials_service):
        """Test successful materials search."""
        mock_materials_service.search_materials.return_value = [
            {
                "id": "1",
                "name": "Портландцемент М500",
                "use_category": "Цемент", 
                "unit": "кг",
                "description": "Высококачественный цемент",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            },
            {
                "id": "2", 
                "name": "Цемент белый",
                "use_category": "Цемент",
                "unit": "кг", 
                "description": "Белый цемент для декоративных работ",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        ]
        
        with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
            response = client_mock.get("/api/v1/search/?q=цемент&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "Портландцемент М500"
        assert data[1]["name"] == "Цемент белый"
        mock_materials_service.search_materials.assert_called_once_with(query="цемент", limit=10)
    
    def test_search_materials_empty_result(self, client_mock, mock_materials_service):
        """Test materials search with empty result."""
        mock_materials_service.search_materials.return_value = []
        
        with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
            response = client_mock.get("/api/v1/search/?q=несуществующий материал")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
        mock_materials_service.search_materials.assert_called_once_with(query="несуществующий материал", limit=10)
    
    def test_search_materials_custom_limit(self, client_mock, mock_materials_service):
        """Test materials search with custom limit."""
        mock_materials_service.search_materials.return_value = [
            {
                "id": "1",
                "name": "Песок речной",
                "use_category": "Песок",
                "unit": "м³",
                "description": "Чистый речной песок",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        ]
        
        with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
            response = client_mock.get("/api/v1/search/?q=песок&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Песок речной"
        mock_materials_service.search_materials.assert_called_once_with(query="песок", limit=5)
    
    def test_search_materials_missing_query(self, client_mock):
        """Test materials search without query parameter."""
        response = client_mock.get("/api/v1/search/")
        assert response.status_code == 422  # Validation error
    
    def test_search_materials_empty_query(self, client_mock, mock_materials_service):
        """Test materials search with empty query."""
        mock_materials_service.search_materials.return_value = []
        
        with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
            response = client_mock.get("/api/v1/search/?q=")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
        mock_materials_service.search_materials.assert_called_once_with(query="", limit=10)
    
    def test_search_materials_service_error(self, client_mock, mock_materials_service):
        """Test materials search when service raises exception."""
        mock_materials_service.search_materials.side_effect = Exception("Database connection error")
        
        with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
            response = client_mock.get("/api/v1/search/?q=цемент")
        
        # The endpoint should handle exceptions gracefully
        assert response.status_code == 500
    
    def test_search_materials_large_limit(self, client_mock, mock_materials_service):
        """Test materials search with large limit value."""
        mock_materials_service.search_materials.return_value = []
        
        with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
            response = client_mock.get("/api/v1/search/?q=материал&limit=1000")
        
        assert response.status_code == 200
        mock_materials_service.search_materials.assert_called_once_with(query="материал", limit=1000)
    
    def test_search_materials_zero_limit(self, client_mock, mock_materials_service):
        """Test materials search with zero limit."""
        mock_materials_service.search_materials.return_value = []
        
        with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
            response = client_mock.get("/api/v1/search/?q=материал&limit=0")
        
        assert response.status_code == 200
        mock_materials_service.search_materials.assert_called_once_with(query="материал", limit=0)


class TestReferenceAPI:
    """Test reference API endpoints for categories and units."""
    
    def test_create_category_success(self, client_mock):
        """Test successful category creation."""
        category_data = {
            "name": "Тестовая категория",
            "description": "Описание тестовой категории"
        }
        
        response = client_mock.post("/api/v1/reference/categories/", json=category_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == category_data["name"]
        assert data["description"] == category_data["description"]
        assert "id" in data
    
    def test_create_category_validation_error(self, client_mock):
        """Test category creation with validation error."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "description": "Описание"
        }
        
        response = client_mock.post("/api/v1/reference/categories/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_categories_success(self, client_mock):
        """Test getting all categories."""
        # First create some categories
        categories = [
            {"name": "Категория 1", "description": "Описание 1"},
            {"name": "Категория 2", "description": "Описание 2"}
        ]
        
        for category in categories:
            client_mock.post("/api/v1/reference/categories/", json=category)
        
        response = client_mock.get("/api/v1/reference/categories/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_create_unit_success(self, client_mock):
        """Test successful unit creation."""
        unit_data = {
            "name": "тест_единица",
            "description": "Тестовая единица измерения"
        }
        
        response = client_mock.post("/api/v1/reference/units/", json=unit_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == unit_data["name"]
        assert data["description"] == unit_data["description"]
        assert "id" in data
    
    def test_create_unit_validation_error(self, client_mock):
        """Test unit creation with validation error."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "description": "Описание"
        }
        
        response = client_mock.post("/api/v1/reference/units/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_units_success(self, client_mock):
        """Test getting all units."""
        # First create some units
        units = [
            {"name": "кг_тест", "description": "Килограмм тестовый"},
            {"name": "м_тест", "description": "Метр тестовый"}
        ]
        
        for unit in units:
            client_mock.post("/api/v1/reference/units/", json=unit)
        
        response = client_mock.get("/api/v1/reference/units/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_create_duplicate_category(self, client_mock):
        """Test creating duplicate category."""
        category_data = {
            "name": "Уникальная категория",
            "description": "Описание"
        }
        
        # Create first category
        response1 = client_mock.post("/api/v1/reference/categories/", json=category_data)
        assert response1.status_code == 200
        
        # Try to create duplicate
        response2 = client_mock.post("/api/v1/reference/categories/", json=category_data)
        # Should handle duplicate gracefully (depending on implementation)
        assert response2.status_code in [200, 409]  # Either success or conflict
    
    def test_create_duplicate_unit(self, client_mock):
        """Test creating duplicate unit."""
        unit_data = {
            "name": "уникальная_единица",
            "description": "Описание"
        }
        
        # Create first unit
        response1 = client_mock.post("/api/v1/reference/units/", json=unit_data)
        assert response1.status_code == 200
        
        # Try to create duplicate
        response2 = client_mock.post("/api/v1/reference/units/", json=unit_data)
        # Should handle duplicate gracefully (depending on implementation)
        assert response2.status_code in [200, 409]  # Either success or conflict


class TestEnvironmentConfiguration:
    """Тесты конфигурации окружения"""
    
    @pytest.mark.unit
    def test_environment_variables(self):
        """Тест правильной настройки переменных окружения"""
        # Проверяем базовые переменные
        assert os.environ.get("ENVIRONMENT") is not None
        assert os.environ.get("API_V1_STR") is not None
    
    @pytest.mark.unit
    def test_cors_configuration(self):
        """Тест конфигурации CORS"""
        cors_origins = os.environ.get("BACKEND_CORS_ORIGINS")
        if cors_origins:
            import json
            try:
                origins = json.loads(cors_origins)
                assert isinstance(origins, list)
            except json.JSONDecodeError:
                pytest.fail("BACKEND_CORS_ORIGINS is not valid JSON")


# === API Validation Tests ===
class TestAPIValidation:
    """API validation and edge case tests."""
    
    def test_create_material_missing_fields(self, client_mock):
        """Test material creation with missing required fields."""
        response = client_mock.post(
            "/api/v1/materials/",
            json={
                "name": "Неполный материал"
                # missing category, unit, description
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_category_missing_name(self, client_mock):
        """Test category creation with missing name."""
        response = client_mock.post(
            "/api/v1/reference/categories/",
            json={
                "description": "Категория без имени"
                # missing name
            }
        )
        assert response.status_code == 422
    
    def test_create_unit_missing_name(self, client_mock):
        """Test unit creation with missing name."""
        response = client_mock.post(
            "/api/v1/reference/units/",
            json={
                "description": "Единица без имени"
                # missing name
            }
        )
        assert response.status_code == 422
    
    def test_create_material_empty_strings(self, client_mock):
        """Test material creation with empty strings."""
        response = client_mock.post(
            "/api/v1/materials/",
            json={
                "name": "",
                "use_category": "",
                "unit": "",
                "description": ""
            }
        )
        assert response.status_code == 422
    
    def test_invalid_json_format(self, client_mock):
        """Test API with invalid JSON."""
        response = client_mock.post(
            "/api/v1/materials/",
            content="invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422


# === API Limits and Pagination Tests ===
class TestAPILimitsAndPagination:
    """API limits and pagination tests."""
    
    def test_get_materials_with_limit(self, client_mock):
        """Test materials API with limit parameter."""
        response = client_mock.get("/api/v1/materials/?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_get_materials_with_zero_limit(self, client_mock):
        """Test materials API with zero limit."""
        response = client_mock.get("/api/v1/materials/?limit=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_materials_with_large_limit(self, client_mock):
        """Test materials API with large limit."""
        response = client_mock.get("/api/v1/materials/?limit=1000")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_materials_with_negative_limit(self, client_mock):
        """Test materials API with negative limit."""
        response = client_mock.get("/api/v1/materials/?limit=-1")
        # API doesn't validate negative limits, returns all results
        assert response.status_code == 200


# === API Response Structure Tests ===
class TestAPIResponseStructure:
    """Test API response structure consistency."""
    
    def test_material_response_structure(self, client_mock):
        """Test material response has required fields."""
        response = client_mock.post(
            "/api/v1/materials/",
            json={
                "name": "Тест материал",
                "use_category": "Тест",
                "unit": "кг",
                "description": "Тестовое описание"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "name", "use_category", "unit", "description", "created_at", "updated_at"]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"
    
    def test_category_response_structure(self, client_mock):
        """Test category response has required fields."""
        response = client_mock.post(
            "/api/v1/reference/categories/",
            json={
                "name": "Тест категория",
                "description": "Тестовое описание"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "name", "description"]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"
    
    def test_unit_response_structure(self, client_mock):
        """Test unit response has required fields."""
        response = client_mock.post(
            "/api/v1/reference/units/",
            json={
                "name": "тест_единица",
                "description": "Тестовое описание"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "name", "description"]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"


# === API Edge Cases Tests ===
class TestAPIEdgeCases:
    """Test API edge cases and special scenarios."""
    
    def test_very_long_material_name(self, client_mock):
        """Test material creation with very long name."""
        long_name = "Очень длинное название материала " * 20  # ~600 characters
        
        response = client_mock.post(
            "/api/v1/materials/",
            json={
                "name": long_name,
                "use_category": "Тест",
                "unit": "кг",
                "description": "Тестовое описание"
            }
        )
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 422, 413]  # Success, validation error, or payload too large
    
    def test_unicode_material(self, client_mock):
        """Test material creation with Unicode characters."""
        response = client_mock.post(
            "/api/v1/materials/",
            json={
                "name": "Материал с эмодзи 🏗️🔨",
                "use_category": "Тест 🏠",
                "unit": "кг",
                "description": "Описание с символами: αβγδε"
            }
        )
        
        # Should handle Unicode gracefully
        assert response.status_code in [200, 422]
    
    def test_search_with_special_unicode(self, client_mock):
        """Test search with special Unicode characters."""
        response = client_mock.get("/api/v1/search/?q=🏗️ материал αβγ&limit=5")
        
        # Should handle Unicode in search gracefully
        assert response.status_code in [200, 422] 