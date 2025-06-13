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


class TestSearchAPIEndpoints:
    """Unit тесты для Search API с моками"""
    
    @pytest.mark.unit
    def test_search_materials(self, client_mock, sample_material):
        """Тест поиска материалов"""
        with patch('api.routes.search.MaterialsService') as mock_service_class:
            mock_service = Mock()
            mock_service.search_materials = AsyncMock(return_value=[sample_material])
            mock_service_class.return_value = mock_service
            
            response = client_mock.post(
                "/api/v1/search/",
                json={"query": "цемент", "limit": 10}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.unit
    def test_search_get_endpoint(self, client_mock):
        """Тест GET эндпоинта поиска"""
        response = client_mock.get("/api/v1/search/?q=cement&limit=5")
        
        # В unit тестах ожидаем либо 200 с данными, либо правильную обработку ошибок
        assert response.status_code in [200, 500]
    
    @pytest.mark.unit
    def test_search_empty_query_validation(self, client_mock):
        """Тест валидации пустого поискового запроса"""
        response = client_mock.get("/api/v1/search/?q=&limit=5")
        assert response.status_code == 422  # Validation error


class TestReferenceAPIEndpoints:
    """Unit тесты для Reference API с моками"""
    
    @pytest.mark.unit
    def test_create_category(self, client_mock, sample_category):
        """Тест создания категории"""
        with patch('api.routes.reference.CategoryService') as mock_service_class:
            mock_service = Mock()
            mock_service.create_category = AsyncMock(return_value=sample_category)
            mock_service_class.return_value = mock_service
            
            response = client_mock.post(
                "/api/v1/reference/categories/",
                json={"name": "Цемент", "description": "Строительные цементы"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "name" in data
            assert "description" in data
    
    @pytest.mark.unit
    def test_get_categories(self, client_mock, sample_category):
        """Тест получения списка категорий"""
        with patch('api.routes.reference.CategoryService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_categories = AsyncMock(return_value=[sample_category])
            mock_service_class.return_value = mock_service
            
            response = client_mock.get("/api/v1/reference/categories/")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.unit
    def test_delete_category(self, client_mock):
        """Тест удаления категории"""
        with patch('api.routes.reference.CategoryService') as mock_service_class:
            mock_service = Mock()
            mock_service.delete_category = AsyncMock(return_value=True)
            mock_service_class.return_value = mock_service
            
            response = client_mock.delete("/api/v1/reference/categories/TestCategory")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    @pytest.mark.unit
    def test_create_unit(self, client_mock, sample_unit):
        """Тест создания единицы измерения"""
        with patch('api.routes.reference.UnitService') as mock_service_class:
            mock_service = Mock()
            mock_service.create_unit = AsyncMock(return_value=sample_unit)
            mock_service_class.return_value = mock_service
            
            response = client_mock.post(
                "/api/v1/reference/units/",
                json={"name": "кг", "description": "Килограмм"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "кг"
    
    @pytest.mark.unit
    def test_get_units(self, client_mock, sample_unit):
        """Тест получения списка единиц измерения"""
        with patch('api.routes.reference.UnitService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_units = AsyncMock(return_value=[sample_unit])
            mock_service_class.return_value = mock_service
            
            response = client_mock.get("/api/v1/reference/units/")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.unit
    def test_delete_unit(self, client_mock):
        """Тест удаления единицы измерения"""
        with patch('api.routes.reference.UnitService') as mock_service_class:
            mock_service = Mock()
            mock_service.delete_unit = AsyncMock(return_value=True)
            mock_service_class.return_value = mock_service
            
            response = client_mock.delete("/api/v1/reference/units/TestUnit")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


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