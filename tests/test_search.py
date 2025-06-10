import pytest
from unittest.mock import patch, Mock, AsyncMock


@pytest.fixture
def mock_materials_service():
    """Mock MaterialsService for testing"""
    service = Mock()
    service.search_materials = AsyncMock()
    return service


def test_search_materials_success(client, mock_materials_service):
    """Test successful materials search"""
    mock_materials_service.search_materials.return_value = [
        {
            "id": "1",
            "name": "Портландцемент М500",
            "category": "Цемент", 
            "unit": "кг",
            "description": "Высококачественный цемент",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        },
        {
            "id": "2", 
            "name": "Цемент белый",
            "category": "Цемент",
            "unit": "кг", 
            "description": "Белый цемент для декоративных работ",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
    ]
    
    with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
        response = client.get("/api/v1/search/?q=цемент&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "Портландцемент М500"
    assert data[1]["name"] == "Цемент белый"
    mock_materials_service.search_materials.assert_called_once_with(query="цемент", limit=10)


def test_search_materials_empty_result(client, mock_materials_service):
    """Test materials search with empty result"""
    mock_materials_service.search_materials.return_value = []
    
    with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
        response = client.get("/api/v1/search/?q=несуществующий материал")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0
    mock_materials_service.search_materials.assert_called_once_with(query="несуществующий материал", limit=10)


def test_search_materials_custom_limit(client, mock_materials_service):
    """Test materials search with custom limit"""
    mock_materials_service.search_materials.return_value = [
        {
            "id": "1",
            "name": "Песок речной",
            "category": "Песок",
            "unit": "м³",
            "description": "Чистый речной песок",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
    ]
    
    with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
        response = client.get("/api/v1/search/?q=песок&limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Песок речной"
    mock_materials_service.search_materials.assert_called_once_with(query="песок", limit=5)


def test_search_materials_missing_query(client):
    """Test materials search without query parameter"""
    response = client.get("/api/v1/search/")
    assert response.status_code == 422  # Validation error


def test_search_materials_empty_query(client, mock_materials_service):
    """Test materials search with empty query"""
    mock_materials_service.search_materials.return_value = []
    
    with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
        response = client.get("/api/v1/search/?q=")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0
    mock_materials_service.search_materials.assert_called_once_with(query="", limit=10)


def test_search_materials_service_error(client, mock_materials_service):
    """Test materials search when service raises exception"""
    mock_materials_service.search_materials.side_effect = Exception("Database connection error")
    
    with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
        response = client.get("/api/v1/search/?q=цемент")
    
    # The endpoint doesn't handle exceptions, so it should return 500
    assert response.status_code == 500


def test_search_materials_large_limit(client, mock_materials_service):
    """Test materials search with large limit value"""
    mock_materials_service.search_materials.return_value = []
    
    with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
        response = client.get("/api/v1/search/?q=материал&limit=1000")
    
    assert response.status_code == 200
    mock_materials_service.search_materials.assert_called_once_with(query="материал", limit=1000)


def test_search_materials_zero_limit(client, mock_materials_service):
    """Test materials search with zero limit"""
    mock_materials_service.search_materials.return_value = []
    
    with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
        response = client.get("/api/v1/search/?q=материал&limit=0")
    
    assert response.status_code == 200
    mock_materials_service.search_materials.assert_called_once_with(query="материал", limit=0)


def test_search_materials_negative_limit(client, mock_materials_service):
    """Test materials search with negative limit"""
    mock_materials_service.search_materials.return_value = []
    
    with patch('api.routes.search.MaterialsService', return_value=mock_materials_service):
        response = client.get("/api/v1/search/?q=материал&limit=-5")
    
    assert response.status_code == 200
    mock_materials_service.search_materials.assert_called_once_with(query="материал", limit=-5) 