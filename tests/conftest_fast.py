"""
Fast test configuration with mocks to avoid database connections
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import asyncio
import logging

# Настраиваем логирование для тестов
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def mock_vector_db():
    """Mock vector database"""
    mock_db = Mock()
    mock_db.upsert = AsyncMock(return_value=True)
    mock_db.search = AsyncMock(return_value=[])
    mock_db.get_by_id = AsyncMock(return_value=None)
    mock_db.delete = AsyncMock(return_value=True)
    mock_db.create_collection = AsyncMock(return_value=True)
    mock_db.collection_exists = AsyncMock(return_value=True)
    return mock_db

@pytest.fixture
def fast_client():
    """Test client with mocked dependencies"""
    
    # Override settings for Qdrant-only mode
    with patch('core.config.get_settings') as mock_settings:
        from core.config import Settings
        settings = Settings(
            PROJECT_NAME="Test API",
            QDRANT_URL="https://test.qdrant.com",
            QDRANT_API_KEY="test-key",
            OPENAI_API_KEY="test-openai-key",
            QDRANT_ONLY_MODE=True,
            ENABLE_FALLBACK_DATABASES=True,
            DISABLE_REDIS_CONNECTION=True,
            DISABLE_POSTGRESQL_CONNECTION=True
        )
        mock_settings.return_value = settings
        
        # Mock vector database client
        with patch('core.config.get_vector_db_client') as mock_vector_client:
            mock_vector_client.return_value = Mock()
            
            # Mock AI client
            with patch('core.config.get_ai_client') as mock_ai:
                mock_ai.return_value = Mock()
                
                # Mock Qdrant client import
                with patch('qdrant_client.QdrantClient') as mock_qdrant:
                    mock_qdrant.return_value.get_collections.return_value = Mock()
                    
                    from main import app
                    return TestClient(app)

@pytest.fixture
def mock_materials_service():
    """Mock MaterialsService"""
    service = Mock()
    service.create_material = AsyncMock()
    service.get_material = AsyncMock()
    service.get_materials = AsyncMock(return_value=[])
    service.update_material = AsyncMock()
    service.delete_material = AsyncMock(return_value=True)
    service.search_materials = AsyncMock(return_value=[])
    service.create_materials_batch = AsyncMock()
    return service

@pytest.fixture
def mock_category_service():
    """Mock CategoryService"""
    service = Mock()
    service.create_category = AsyncMock()
    service.get_categories = AsyncMock(return_value=[])
    service.delete_category = AsyncMock(return_value=True)
    return service

@pytest.fixture
def mock_unit_service():
    """Mock UnitService"""
    service = Mock()
    service.create_unit = AsyncMock()
    service.get_units = AsyncMock(return_value=[])
    service.delete_unit = AsyncMock(return_value=True)
    return service

# Auto-use mocks for all tests in this configuration
@pytest.fixture(autouse=True)
def mock_all_services(mock_materials_service, mock_category_service, mock_unit_service):
    """Auto-mock all services to prevent database connections"""
    with patch('services.materials.MaterialsService', return_value=mock_materials_service), \
         patch('services.materials.CategoryService', return_value=mock_category_service), \
         patch('services.materials.UnitService', return_value=mock_unit_service), \
         patch('api.routes.materials.get_materials_service', return_value=mock_materials_service):
        yield

@pytest.fixture
def sample_category():
    """Sample category for testing"""
    from core.schemas.materials import Category
    return Category(name="Тестовая категория", description="Описание")

@pytest.fixture
def sample_unit():
    """Sample unit for testing"""
    from core.schemas.materials import Unit
    return Unit(name="кг", description="Килограмм")

@pytest.fixture
def sample_material():
    """Sample material for testing"""
    from core.schemas.materials import Material
    from datetime import datetime
    return Material(
        id="test-id",
        name="Тестовый материал",
        use_category="Тестовая категория",
        unit="кг",
        sku="TEST001",
        description="Тестовое описание",
        embedding=[0.1, 0.2, 0.3],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ) 