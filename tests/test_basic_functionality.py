"""
Базовые тесты функциональности API
Basic functionality tests for the API
"""
import pytest
import os
from unittest.mock import patch
from tests.conftest_test import TEST_SETTINGS


class TestBasicAPI:
    """Тесты базовой функциональности API"""
    
    def test_root_endpoint(self, client):
        """Тест корневого эндпоинта"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "RAG Construction Materials API" in data["message"]
    
    def test_health_basic(self, client):
        """Тест базового health check"""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "environment" in data
    
    def test_health_config(self, client):
        """Тест конфигурационного health check"""
        response = client.get("/api/v1/health/config")
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
    
    def test_docs_endpoint(self, client):
        """Тест доступности Swagger документации"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_schema(self, client):
        """Тест доступности OpenAPI схемы"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "RAG Construction Materials API"


class TestMaterialsAPI:
    """Тесты API материалов"""
    
    def test_materials_list_empty(self, client):
        """Тест получения пустого списка материалов"""
        response = client.get("/api/v1/materials/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_endpoint(self, client):
        """Тест поискового эндпоинта"""
        # Тест простого поиска
        response = client.get("/api/v1/search/?q=cement&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_empty_query(self, client):
        """Тест поиска с пустым запросом"""
        response = client.get("/api/v1/search/?q=&limit=5")
        assert response.status_code == 422  # Validation error for empty query


class TestReferenceAPI:
    """Тесты справочных данных"""
    
    def test_categories_list(self, client):
        """Тест получения списка категорий"""
        response = client.get("/api/v1/reference/categories/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_units_list(self, client):
        """Тест получения списка единиц измерения"""
        response = client.get("/api/v1/reference/units/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestEnvironmentConfiguration:
    """Тесты конфигурации окружения"""
    
    def test_environment_variables(self):
        """Тест правильной настройки переменных окружения"""
        # Проверяем, что тестовые переменные установлены
        assert os.environ.get("ENVIRONMENT") == "test"
        assert os.environ.get("QDRANT_ONLY_MODE") == "true"
        assert os.environ.get("DISABLE_REDIS_CONNECTION") == "true"
        assert os.environ.get("DISABLE_POSTGRESQL_CONNECTION") == "true"
    
    def test_cors_configuration(self):
        """Тест конфигурации CORS"""
        cors_origins = os.environ.get("BACKEND_CORS_ORIGINS")
        assert cors_origins is not None
        # Проверяем, что это валидный JSON
        import json
        try:
            origins = json.loads(cors_origins)
            assert isinstance(origins, list)
        except json.JSONDecodeError:
            pytest.fail("BACKEND_CORS_ORIGINS is not valid JSON")


@pytest.mark.asyncio
class TestAsyncFunctionality:
    """Тесты асинхронной функциональности"""
    
    async def test_async_health_check(self, client):
        """Тест асинхронного health check"""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data or "status" in data 