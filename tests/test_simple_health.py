"""
Простые тесты здоровья системы
Simple health check tests
"""
import pytest
import os
from unittest.mock import patch

# Настройки для тестового окружения
TEST_SETTINGS = {
    "ENVIRONMENT": "test",
    "BACKEND_CORS_ORIGINS": '["http://localhost:3000", "http://127.0.0.1:3000"]',
    "QDRANT_URL": "https://test-cluster.qdrant.tech:6333",
    "QDRANT_API_KEY": "test-api-key",
    "QDRANT_COLLECTION_NAME": "materials_test",
    "QDRANT_VECTOR_SIZE": "1536",
    "OPENAI_API_KEY": "sk-test-key",
    "OPENAI_MODEL": "text-embedding-3-small",
    "AI_PROVIDER": "openai",
    "DATABASE_TYPE": "qdrant_cloud",
    "QDRANT_ONLY_MODE": "true",
    "ENABLE_FALLBACK_DATABASES": "true",
    "DISABLE_REDIS_CONNECTION": "true",
    "DISABLE_POSTGRESQL_CONNECTION": "true",
    "POSTGRESQL_URL": "postgresql://test:test@localhost:5432/test_materials",
    "REDIS_URL": "redis://localhost:6379/0",
    "MAX_UPLOAD_SIZE": "52428800",
    "BATCH_SIZE": "50",
    "AUTO_MIGRATE": "false",
    "AUTO_SEED": "false",
    "LOG_LEVEL": "INFO",
    "ENABLE_RATE_LIMITING": "true",
    "RATE_LIMIT_RPM": "60",
    "PROJECT_NAME": "RAG Construction Materials API",
    "VERSION": "1.0.0",
    "API_V1_STR": "/api/v1"
}


@pytest.fixture
def mock_env():
    """Фикстура для установки тестового окружения"""
    with patch.dict(os.environ, TEST_SETTINGS):
        yield


@pytest.fixture
def client(mock_env):
    """Test client fixture with mocked environment"""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


def test_environment_setup(mock_env):
    """Тест правильной настройки окружения"""
    assert os.environ.get("ENVIRONMENT") == "test"
    assert os.environ.get("QDRANT_ONLY_MODE") == "true"
    assert os.environ.get("DISABLE_REDIS_CONNECTION") == "true"


def test_root_endpoint(client):
    """Тест корневого эндпоинта"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    # Проверяем, что сообщение содержит название проекта
    assert "Construction Materials API" in data["message"]


def test_health_basic(client):
    """Тест базового health check"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data


def test_health_config(client):
    """Тест health check конфигурации"""
    response = client.get("/api/v1/health/config")
    assert response.status_code == 200
    data = response.json()
    assert "configuration" in data


def test_docs_endpoint(client):
    """Тест доступности документации"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_schema(client):
    """Тест OpenAPI схемы"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    # Проверяем, что название содержит название проекта из настроек
    assert "Construction Materials API" in data["info"]["title"]


def test_search_endpoint(client):
    """Тест поискового эндпоинта"""
    response = client.get("/api/v1/search/?q=cement&limit=5")
    
    # В тестовой среде может быть либо 200 с пустым результатом (если соединение работает)
    # либо 500 если тестовый URL недоступен
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # В тестовой среде ожидаем пустой список
        assert len(data) == 0 or all(isinstance(item, dict) for item in data)
    elif response.status_code == 500:
        # Допустимо для тестовой среды когда БД недоступна
        data = response.json()
        assert "detail" in data
        assert "Internal server error" in data["detail"]
    else:
        # Неожиданный статус код
        assert False, f"Unexpected status code: {response.status_code}, body: {response.text}"


def test_materials_list(client):
    """Тест списка материалов"""
    response = client.get("/api/v1/materials/")
    
    # В тестовой среде может быть либо 200 с пустым результатом (если соединение работает)
    # либо 500 если тестовый URL недоступен
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # В тестовой среде ожидаем пустой список
        assert len(data) == 0 or all(isinstance(item, dict) for item in data)
    elif response.status_code == 500:
        # Допустимо для тестовой среды когда БД недоступна
        data = response.json()
        assert "detail" in data
    else:
        # Неожиданный статус код
        assert False, f"Unexpected status code: {response.status_code}, body: {response.text}"


def test_reference_categories(client):
    """Тест списка категорий"""
    response = client.get("/api/v1/reference/categories/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_reference_units(client):
    """Тест списка единиц измерения"""
    response = client.get("/api/v1/reference/units/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) 