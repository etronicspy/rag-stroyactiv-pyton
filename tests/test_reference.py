import pytest

def test_create_category(client):
    """Test category creation"""
    response = client.post(
        "/api/v1/reference/categories/",
        json={"name": "Цемент", "description": "Строительные цементы"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Цемент"
    assert data["description"] == "Строительные цементы"

def test_get_categories(client):
    """Test getting all categories"""
    # Create test category first
    client.post(
        "/api/v1/reference/categories/",
        json={"name": "Песок", "description": "Строительный песок"}
    )
    
    response = client.get("/api/v1/reference/categories/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(cat["name"] == "Песок" for cat in data)

def test_create_unit(client):
    """Test unit creation"""
    response = client.post(
        "/api/v1/reference/units/",
        json={"name": "кг", "description": "Килограмм"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "кг"
    assert data["description"] == "Килограмм"

def test_get_units(client):
    """Test getting all units"""
    # Create test unit first
    client.post(
        "/api/v1/reference/units/",
        json={"name": "м³", "description": "Кубический метр"}
    )
    
    response = client.get("/api/v1/reference/units/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(unit["name"] == "м³" for unit in data)

def test_delete_category(client):
    """Test category deletion"""
    # Create category first
    client.post(
        "/api/v1/reference/categories/",
        json={"name": "TestCategory", "description": "For deletion"}
    )
    
    response = client.delete("/api/v1/reference/categories/TestCategory")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_delete_unit(client):
    """Test unit deletion"""
    # Create unit first
    client.post(
        "/api/v1/reference/units/",
        json={"name": "TestUnit", "description": "For deletion"}
    )
    
    response = client.delete("/api/v1/reference/units/TestUnit")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True 