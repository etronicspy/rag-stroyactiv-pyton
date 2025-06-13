"""
Fast materials tests with mocks to avoid database connections
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from core.schemas.materials import Material, MaterialCreate
from datetime import datetime

# Use fast client with mocks
pytest_plugins = ["tests.conftest_fast"]

def test_create_material_fast(fast_client, sample_material):
    """Test material creation with mocks"""
    
    with patch('api.routes.materials.get_materials_service') as mock_service_dep:
        mock_service = Mock()
        mock_service.create_material = AsyncMock(return_value=sample_material)
        mock_service_dep.return_value = mock_service
        
        response = fast_client.post(
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
        assert data["name"] == "Тестовый материал"  # From sample_material
        assert "id" in data

def test_get_material_fast(fast_client, sample_material):
    """Test getting a specific material with mocks"""
    
    with patch('api.routes.materials.get_materials_service') as mock_service_dep:
        mock_service = Mock()
        mock_service.get_material = AsyncMock(return_value=sample_material)
        mock_service_dep.return_value = mock_service
        
        response = fast_client.get("/api/v1/materials/test-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-id"
        assert data["name"] == "Тестовый материал"

def test_get_materials_fast(fast_client, sample_material):
    """Test getting all materials with mocks"""
    
    with patch('api.routes.materials.get_materials_service') as mock_service_dep:
        mock_service = Mock()
        mock_service.get_materials = AsyncMock(return_value=[sample_material])
        mock_service_dep.return_value = mock_service
        
        response = fast_client.get("/api/v1/materials/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Тестовый материал"

def test_update_material_fast(fast_client, sample_material):
    """Test updating a material with mocks"""
    
    # Create updated material
    updated_material = Material(
        id="test-id",
        name="Обновленный материал",
        use_category="Цемент",
        unit="кг",
        sku="TEST001",
        description="Обновленное описание",
        embedding=[0.1, 0.2, 0.3],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    with patch('api.routes.materials.get_materials_service') as mock_service_dep:
        mock_service = Mock()
        mock_service.update_material = AsyncMock(return_value=updated_material)
        mock_service_dep.return_value = mock_service
        
        response = fast_client.put(
            "/api/v1/materials/test-id",
            json={
                "name": "Обновленный материал",
                "description": "Обновленное описание"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Обновленный материал"
        assert data["description"] == "Обновленное описание"

def test_delete_material_fast(fast_client):
    """Test material deletion with mocks"""
    
    with patch('api.routes.materials.get_materials_service') as mock_service_dep:
        mock_service = Mock()
        mock_service.delete_material = AsyncMock(return_value=True)
        mock_service_dep.return_value = mock_service
        
        response = fast_client.delete("/api/v1/materials/test-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

def test_search_materials_fast(fast_client, sample_material):
    """Test materials search with mocks"""
    
    with patch('api.routes.search.MaterialsService') as mock_service_class:
        mock_service = Mock()
        mock_service.search_materials = AsyncMock(return_value=[sample_material])
        mock_service_class.return_value = mock_service
        
        response = fast_client.post(
            "/api/v1/search/",
            json={"query": "цемент", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Тестовый материал"

def test_batch_create_materials_fast(fast_client):
    """Test batch creation of materials with mocks"""
    
    from core.schemas.materials import MaterialBatchResponse
    
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
        
        response = fast_client.post(
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
        assert data["successful_creates"] == 2
        assert data["failed_creates"] == 0

# Test error cases
def test_create_material_validation_error_fast(fast_client):
    """Test material creation with validation error"""
    
    response = fast_client.post(
        "/api/v1/materials/",
        json={
            "name": "",  # Invalid: empty name
            "use_category": "Цемент",
            "unit": "кг"
        }
    )
    
    assert response.status_code == 422  # Validation error

def test_get_nonexistent_material_fast(fast_client):
    """Test getting a non-existent material"""
    
    with patch('api.routes.materials.get_materials_service') as mock_service_dep:
        mock_service = Mock()
        mock_service.get_material = AsyncMock(return_value=None)
        mock_service_dep.return_value = mock_service
        
        response = fast_client.get("/api/v1/materials/nonexistent")
        
        assert response.status_code == 404 