import pytest
import asyncio
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from core.config import settings
import tempfile
from datetime import datetime
import time
from typing import Dict, List, Any
import logging

# Настраиваем логирование для тестов
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def client():
    """Test client fixture"""
    from main import app
    return TestClient(app)

@pytest.fixture(scope="session")
def qdrant_client():
    """Real Qdrant client for testing"""
    # Добавляем проверку подключения и ретрай логику
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=30  # Увеличиваем таймаут
            )
            # Проверяем подключение
            client.get_collections()
            print(f"✅ Successfully connected to Qdrant at {settings.QDRANT_URL}")
            return client
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed to connect to Qdrant: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise Exception(f"Failed to connect to Qdrant after {max_retries} attempts: {e}")

@pytest.fixture(autouse=True)
def cleanup_test_collections(qdrant_client):
    """Clean up test collections before and after each test"""
    # Cleanup before test
    _cleanup_test_collections(qdrant_client)
    
    yield
    
    # Cleanup after test (опционально для реальной БД)
    # Для реальной БД можно оставить данные для анализа
    if not _is_production_db():
        _cleanup_test_collections(qdrant_client)

def _is_production_db() -> bool:
    """Check if we're using production database"""
    # Можно добавить логику для определения prod окружения
    return "prod" in settings.QDRANT_URL.lower() or "production" in settings.QDRANT_URL.lower()

def _cleanup_test_collections(client: QdrantClient):
    """Helper function to clean up test collections"""
    try:
        collections = client.get_collections()
        test_collections = [
            c.name for c in collections.collections 
            if (c.name.startswith('supplier_TEST') or 
                c.name.startswith('test_') or
                c.name.startswith('supplier_SUP_TEST'))
        ]
        
        for collection_name in test_collections:
            try:
                client.delete_collection(collection_name)
                print(f"🧹 Deleted test collection: {collection_name}")
            except Exception as e:
                print(f"⚠️ Error deleting collection {collection_name}: {e}")
                
    except Exception as e:
        print(f"⚠️ Error getting collections: {e}")

# Additional fixtures for common test data
@pytest.fixture
def sample_price_data():
    """Sample price data for testing with correct column names"""
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
    return f"TEST_{int(time.time())}" 