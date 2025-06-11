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

def test_create_materials_batch(client, setup_references):
    """Test batch creation of materials"""
    materials_data = [
        {
            "name": "Цемент М500 batch 1",
            "category": "Цемент",
            "unit": "кг",
            "article": "BTH0001",
            "description": "Тест батч 1"
        },
        {
            "name": "Цемент М400 batch 2",
            "category": "Цемент",
            "unit": "кг",
            "article": "BTH0002",
            "description": "Тест батч 2"
        },
        {
            "name": "Песок речной batch 3",
            "category": "Песок",
            "unit": "м³",
            "article": "BTH0003",
            "description": "Тест батч 3"
        }
    ]
    
    response = client.post(
        "/api/v1/materials/batch",
        json={
            "materials": materials_data,
            "batch_size": 2
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_processed"] == 3
    assert data["successful_creates"] == 3
    assert data["failed_creates"] == 0
    assert "processing_time_seconds" in data
    assert len(data["created_materials"]) == 3
    
    # Verify all materials were created with proper data
    for i, created_material in enumerate(data["created_materials"]):
        assert created_material["name"] == materials_data[i]["name"]
        assert created_material["category"] == materials_data[i]["category"]
        assert "id" in created_material

def test_import_materials_from_json(client, setup_references):
    """Test importing materials from JSON format"""
    import_data = [
        {"article": "CEM0001", "name": "Цемент портландский М400"},
        {"article": "SND0001", "name": "Песок строительный мытый"},
        {"article": "BRK0001", "name": "Кирпич керамический красный"},
        {"article": "ARM0001", "name": "Арматура А500С Ø12мм"},
    ]
    
    response = client.post(
        "/api/v1/materials/import",
        json={
            "materials": import_data,
            "default_category": "Стройматериалы",
            "default_unit": "шт",
            "batch_size": 2
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_processed"] == 4
    assert data["successful_creates"] == 4
    assert data["failed_creates"] == 0
    
    # Verify materials were created with inferred categories
    materials = data["created_materials"]
    assert len(materials) == 4
    
    # Check that smart categorization worked
    cement_material = next(m for m in materials if "цемент" in m["name"].lower())
    assert cement_material["category"] == "Цемент"
    
    sand_material = next(m for m in materials if "песок" in m["name"].lower())
    assert sand_material["category"] == "Песок"
    
    brick_material = next(m for m in materials if "кирпич" in m["name"].lower())
    assert brick_material["category"] == "Кирпич"
    
    rebar_material = next(m for m in materials if "арматура" in m["name"].lower())
    assert rebar_material["category"] == "Арматура"
    
    # Check that articles are stored in separate field
    for i, material in enumerate(materials):
        expected_article = import_data[i]["article"]
        assert material["article"] == expected_article

def test_batch_with_errors(client, setup_references):
    """Test batch creation with some invalid materials"""
    materials_data = [
        {
            "name": "Валидный материал",
            "category": "Цемент",
            "unit": "кг",
            "article": "TST0001",
            "description": "Корректный материал"
        },
        {
            "name": "Валидное имя материала",  # Valid name
            "category": "Цемент",
            "unit": "кг",
            "article": "TST0002",
            "description": "Корректный материал"
        },
        {
            "name": "Еще один валидный материал",
            "category": "Песок",
            "unit": "м³",
            "article": "TST0003",
            "description": "Еще корректный материал"
        }
    ]
    
    response = client.post(
        "/api/v1/materials/batch",
        json={
            "materials": materials_data,
            "batch_size": 10
        }
    )
    
    # Should return 200 with all successful creates now
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 3
    # All materials should be created successfully now
    assert data["successful_creates"] == 3
    assert data["failed_creates"] == 0

def test_empty_batch(client, setup_references):
    """Test batch creation with empty materials list"""
    response = client.post(
        "/api/v1/materials/batch",
        json={
            "materials": [],
            "batch_size": 10
        }
    )
    
    # Should fail validation due to min_items=1
    assert response.status_code == 422

def test_large_batch_size_limit(client, setup_references):
    """Test batch creation with batch size exceeding limits"""
    materials_data = [
        {
            "name": f"Материал {i}",
            "category": "Цемент",
            "unit": "кг",
            "description": f"Описание {i}"
        }
        for i in range(5)
    ]
    
    response = client.post(
        "/api/v1/materials/batch",
        json={
            "materials": materials_data,
            "batch_size": 600  # Exceeds max limit of 500
        }
    )
    
    # Should fail validation
    assert response.status_code == 422 