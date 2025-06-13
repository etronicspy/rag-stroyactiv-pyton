"""
Fast reference tests with mocks to avoid database connections
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from core.schemas.materials import Category, Unit

# Use fast client with mocks
pytest_plugins = ["tests.conftest_fast"]

def test_create_category_fast(fast_client, sample_category):
    """Test category creation with mocks"""
    
    # Mock the service response
    with patch('api.routes.reference.CategoryService') as mock_service_class:
        mock_service = Mock()
        mock_service.create_category = AsyncMock(return_value=sample_category)
        mock_service_class.return_value = mock_service
        
        response = fast_client.post(
            "/api/v1/reference/categories/",
            json={"name": "Цемент", "description": "Строительные цементы"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Тестовая категория"  # From sample_category
        assert data["description"] == "Описание"

def test_get_categories_fast(fast_client, sample_category):
    """Test getting all categories with mocks"""
    
    with patch('api.routes.reference.CategoryService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_categories = AsyncMock(return_value=[sample_category])
        mock_service_class.return_value = mock_service
        
        response = fast_client.get("/api/v1/reference/categories/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Тестовая категория"

def test_create_unit_fast(fast_client, sample_unit):
    """Test unit creation with mocks"""
    
    with patch('api.routes.reference.UnitService') as mock_service_class:
        mock_service = Mock()
        mock_service.create_unit = AsyncMock(return_value=sample_unit)
        mock_service_class.return_value = mock_service
        
        response = fast_client.post(
            "/api/v1/reference/units/",
            json={"name": "кг", "description": "Килограмм"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "кг"
        assert data["description"] == "Килограмм"

def test_get_units_fast(fast_client, sample_unit):
    """Test getting all units with mocks"""
    
    with patch('api.routes.reference.UnitService') as mock_service_class:
        mock_service = Mock()
        mock_service.get_units = AsyncMock(return_value=[sample_unit])
        mock_service_class.return_value = mock_service
        
        response = fast_client.get("/api/v1/reference/units/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "кг"

def test_delete_category_fast(fast_client):
    """Test category deletion with mocks"""
    
    with patch('api.routes.reference.CategoryService') as mock_service_class:
        mock_service = Mock()
        mock_service.delete_category = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        response = fast_client.delete("/api/v1/reference/categories/TestCategory")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

def test_delete_unit_fast(fast_client):
    """Test unit deletion with mocks"""
    
    with patch('api.routes.reference.UnitService') as mock_service_class:
        mock_service = Mock()
        mock_service.delete_unit = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        response = fast_client.delete("/api/v1/reference/units/TestUnit")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

# Test service functionality directly
def test_category_service_implementation():
    """Test CategoryService implementation directly"""
    from services.materials import CategoryService
    
    # Initialize service
    service = CategoryService()
    
    # Test categories dictionary exists
    assert hasattr(service, 'categories')
    assert isinstance(service.categories, dict)

def test_unit_service_implementation():
    """Test UnitService implementation directly"""
    from services.materials import UnitService
    
    # Initialize service
    service = UnitService()
    
    # Test units dictionary exists
    assert hasattr(service, 'units')
    assert isinstance(service.units, dict) 