import pytest
from unittest.mock import patch
import uuid

@pytest.fixture
def setup_references(client):
    """Create necessary reference data"""
    client.post("/api/v1/reference/categories/", json={"name": "Цемент", "description": "Цементы"})
    client.post("/api/v1/reference/units/", json={"name": "кг", "description": "Килограмм"})

def test_create_material(client, setup_references):
    """Test material creation"""
    response = client.post(
        "/api/v1/materials/",
        json={
            "name": "Портландцемент М500",
            "category": "Цемент",
            "unit": "кг",
            "description": "Высококачественный цемент для строительных работ"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Портландцемент М500"
    assert data["category"] == "Цемент"
    assert data["unit"] == "кг"
    assert "id" in data
    assert "embedding" in data

def test_get_material(client, setup_references):
    """Test getting a specific material"""
    # Create material first
    create_response = client.post(
        "/api/v1/materials/",
        json={
            "name": "Портландцемент М400",
            "category": "Цемент",
            "unit": "кг",
            "description": "Стандартный цемент для общих работ"
        }
    )
    material_id = create_response.json()["id"]
    
    # Get the material
    response = client.get(f"/api/v1/materials/{material_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Портландцемент М400"
    assert data["id"] == material_id

def test_get_materials(client, setup_references):
    """Test getting all materials"""
    # Create test materials
    client.post(
        "/api/v1/materials/",
        json={
            "name": "Цемент М500",
            "category": "Цемент",
            "unit": "кг",
            "description": "Описание 1"
        }
    )
    client.post(
        "/api/v1/materials/",
        json={
            "name": "Цемент М400",
            "category": "Цемент",
            "unit": "кг",
            "description": "Описание 2"
        }
    )
    
    response = client.get("/api/v1/materials/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

def test_update_material(client, setup_references):
    """Test updating a material"""
    # Create material first
    create_response = client.post(
        "/api/v1/materials/",
        json={
            "name": "Старое название",
            "category": "Цемент",
            "unit": "кг",
            "description": "Старое описание"
        }
    )
    material_id = create_response.json()["id"]
    
    # Update the material
    response = client.put(
        f"/api/v1/materials/{material_id}",
        json={
            "name": "Новое название",
            "description": "Новое описание"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Новое название"
    assert data["description"] == "Новое описание"
    assert "embedding" in data  # Should have new embedding

def test_delete_material(client, setup_references):
    """Test material deletion"""
    # Create material first
    create_response = client.post(
        "/api/v1/materials/",
        json={
            "name": "Для удаления",
            "category": "Цемент",
            "unit": "кг",
            "description": "Тестовый материал для удаления"
        }
    )
    material_id = create_response.json()["id"]
    
    # Delete the material
    response = client.delete(f"/api/v1/materials/{material_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify it's deleted
    get_response = client.get(f"/api/v1/materials/{material_id}")
    assert get_response.status_code == 404

def test_search_materials(client, setup_references):
    """Test materials search"""
    # Create test materials
    client.post(
        "/api/v1/materials/",
        json={
            "name": "Портландцемент белый",
            "category": "Цемент",
            "unit": "кг",
            "description": "Белый цемент для декоративных работ"
        }
    )
    client.post(
        "/api/v1/materials/",
        json={
            "name": "Портландцемент серый",
            "category": "Цемент",
            "unit": "кг",
            "description": "Серый цемент для общих работ"
        }
    )
    
    # Search for materials
    response = client.post(
        "/api/v1/materials/search",
        json={"query": "белый декоративный цемент", "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # First result should be the white cement
    assert "белый" in data[0]["name"].lower() 