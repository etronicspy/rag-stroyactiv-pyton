import pytest
import os
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch
from typing import Dict, Any
import logging

# Настраиваем логирование для тестов
logging.basicConfig(level=logging.INFO)

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

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Устанавливаем переменные окружения для тестов"""
    # Патчим переменные окружения
    original_env = {}
    for key, value in TEST_SETTINGS.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Восстанавливаем оригинальные значения
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value

@pytest.fixture
def client():
    """Test client fixture with proper environment"""
    with patch.dict(os.environ, TEST_SETTINGS):
        from main import app
        return TestClient(app)

@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing"""
    from unittest.mock import MagicMock
    
    client = MagicMock()
    client.get_collections.return_value = MagicMock(collections=[])
    client.create_collection.return_value = True
    client.delete_collection.return_value = True
    client.search.return_value = []
    client.upsert.return_value = True
    
    return client

@pytest.fixture
def sample_material_data():
    """Sample material data for testing"""
    return {
        "name": "Test Cement",
        "use_category": "Building Materials",
        "unit": "kg",
        "price": 45.50,
        "description": "Test cement for unit testing",
        "sku": "TEST_001"
    }

@pytest.fixture
def sample_price_data():
    """Sample price data for testing"""
    return [
        {
            "name": "Cement Portland Test",
            "use_category": "Building Materials",
            "unit": "kg", 
            "price": 45.50,
            "description": "High quality cement for testing"
        },
        {
            "name": "Sand Construction Test",
            "use_category": "Building Materials",
            "unit": "m3",
            "price": 1200.00,
            "description": "Washed construction sand for testing"
        }
    ]

@pytest.fixture
def test_supplier_id():
    """Generate unique test supplier ID"""
    import time
    return f"TEST_{int(time.time())}"

# Дополнительные фикстуры для мокирования сервисов
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    from unittest.mock import AsyncMock, MagicMock
    
    client = AsyncMock()
    client.embeddings = AsyncMock()
    client.embeddings.create = AsyncMock()
    client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536)]
    )
    
    return client

@pytest.fixture
def mock_database_services():
    """Mock all database services"""
    from unittest.mock import MagicMock
    
    return {
        "vector_db": MagicMock(),
        "postgresql": MagicMock(),
        "redis": MagicMock()
    } 