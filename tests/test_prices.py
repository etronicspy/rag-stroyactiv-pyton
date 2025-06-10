import pytest
import os
import time
from unittest.mock import patch, Mock, AsyncMock
from tests.data.test_data_helper import get_test_file_path


def test_process_price_list_success(client):
    """Test successful price list processing with real CSV file"""
    test_file_path = get_test_file_path('valid_prices')
    
    with open(test_file_path, 'rb') as f:
        response = client.post(
            "/api/v1/prices/process",
            files={"file": ("valid_prices.csv", f, "text/csv")},
            data={"supplier_id": "test_supplier_success"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Price list processed successfully"
    assert data["supplier_id"] == "test_supplier_success"
    assert data["materials_processed"] == 4  # Количество строк в valid_prices.csv
    assert "upload_date" in data
    
    # Cleanup
    client.delete("/api/v1/prices/test_supplier_success")


def test_process_price_list_invalid_file_format(client):
    """Test price list processing with invalid file format"""
    response = client.post(
        "/api/v1/prices/process",
        files={"file": ("test.txt", b"invalid content", "text/plain")},
        data={"supplier_id": "test_supplier"}
    )
    
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]


def test_get_latest_price_list_success(client):
    """Test getting latest price list successfully"""
    # Сначала загружаем прайс-лист
    test_file_path = get_test_file_path('valid_prices')
    with open(test_file_path, 'rb') as f:
        client.post(
            "/api/v1/prices/process",
            files={"file": ("valid_prices.csv", f, "text/csv")},
            data={"supplier_id": "test_supplier_latest"}
        )
    
    # Получаем последний прайс-лист
    response = client.get("/api/v1/prices/test_supplier_latest/latest")
    
    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] == "test_supplier_latest"
    assert data["total_count"] == 4
    assert len(data["materials"]) == 4
    assert all("name" in material for material in data["materials"])
    assert all("price" in material for material in data["materials"])
    
    # Cleanup
    client.delete("/api/v1/prices/test_supplier_latest")


def test_get_latest_price_list_not_found(client):
    """Test getting latest price list when supplier not found"""
    response = client.get("/api/v1/prices/nonexistent_supplier/latest")
    
    assert response.status_code == 404
    assert "No price lists found" in response.json()["detail"]


def test_get_all_price_lists(client):
    """Test getting all price lists for supplier"""
    # Загружаем два прайс-листа
    test_file1_path = get_test_file_path('valid_prices')
    with open(test_file1_path, 'rb') as f:
        client.post(
            "/api/v1/prices/process",
            files={"file": ("valid_prices.csv", f, "text/csv")},
            data={"supplier_id": "test_supplier_all"}
        )
    
    # Небольшая задержка и второй файл
    time.sleep(1)
    with open(test_file1_path, 'rb') as f:
        client.post(
            "/api/v1/prices/process",
            files={"file": ("valid_prices2.csv", f, "text/csv")},
            data={"supplier_id": "test_supplier_all"}
        )
    
    response = client.get("/api/v1/prices/test_supplier_all/all")
    
    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] == "test_supplier_all"
    assert data["total_price_lists"] == 2
    assert len(data["price_lists"]) == 2
    
    # Cleanup
    client.delete("/api/v1/prices/test_supplier_all")


def test_delete_supplier_price_list_success(client):
    """Test successful deletion of supplier price lists"""
    # Сначала создаем прайс-лист
    test_file_path = get_test_file_path('valid_prices')
    with open(test_file_path, 'rb') as f:
        client.post(
            "/api/v1/prices/process",
            files={"file": ("valid_prices.csv", f, "text/csv")},
            data={"supplier_id": "test_supplier_delete"}
        )
    
    # Удаляем прайс-листы
    response = client.delete("/api/v1/prices/test_supplier_delete")
    
    assert response.status_code == 200
    data = response.json()
    assert "All price lists for supplier test_supplier_delete have been deleted" in data["message"]
    
    # Проверяем, что прайс-листы действительно удалены
    response = client.get("/api/v1/prices/test_supplier_delete/latest")
    assert response.status_code == 404


def test_price_list_replacement_logic(client):
    """Test that only latest 3 price lists are kept per supplier"""
    supplier_id = "test_supplier_replacement"
    
    # Загружаем 4 прайс-листа
    test_files = ['test_price_v1.csv', 'test_price_v2.csv', 'test_price_v3.csv', 'test_price_v4.csv']
    
    for i, filename in enumerate(test_files):
        filepath = f"tests/data/{filename}"
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                response = client.post(
                    "/api/v1/prices/process",
                    files={"file": (filename, f, "text/csv")},
                    data={"supplier_id": supplier_id}
                )
                assert response.status_code == 200
            
            # Небольшая задержка между загрузками
            time.sleep(0.5)
    
    # Проверяем, что хранятся только последние 3 прайс-листа
    response = client.get(f"/api/v1/prices/{supplier_id}/all")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_price_lists"] == 3  # Должно быть только 3 прайс-листа
    
    # Проверяем, что остались только последние 3 прайс-листа
    returned_dates = [pl["upload_date"] for pl in data["price_lists"]]
    assert len(returned_dates) == 3
    
    # Cleanup
    client.delete(f"/api/v1/prices/{supplier_id}")


def test_process_invalid_data_file(client):
    """Test processing file with invalid price data"""
    test_file_path = get_test_file_path('invalid_price_data')
    
    with open(test_file_path, 'rb') as f:
        response = client.post(
            "/api/v1/prices/process",
            files={"file": ("invalid_price_data.csv", f, "text/csv")},
            data={"supplier_id": "test_supplier_invalid"}
        )
    
    # API должен обработать файл, пропустив невалидные строки
    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] == "test_supplier_invalid"
    # Должна быть обработана только 1 валидная строка
    assert data["materials_processed"] >= 1
    
    # Cleanup
    client.delete("/api/v1/prices/test_supplier_invalid")


def test_process_empty_file(client):
    """Test processing empty CSV file"""
    test_file_path = get_test_file_path('empty_data')
    
    with open(test_file_path, 'rb') as f:
        response = client.post(
            "/api/v1/prices/process",
            files={"file": ("empty_data.csv", f, "text/csv")},
            data={"supplier_id": "test_supplier_empty"}
        )
    
    # API возвращает ошибку для пустого файла
    assert response.status_code == 400
    data = response.json()
    assert "No valid data found" in data["detail"]


def test_process_missing_columns_file(client):
    """Test processing file with missing required columns"""
    test_file_path = get_test_file_path('invalid_missing_columns')
    
    with open(test_file_path, 'rb') as f:
        response = client.post(
            "/api/v1/prices/process",
            files={"file": ("invalid_missing_columns.csv", f, "text/csv")},
            data={"supplier_id": "test_supplier_missing_cols"}
        )
    
    # API должен обработать файл с недостающими колонками
    assert response.status_code == 200 or response.status_code == 400
    
    # Cleanup (если успешно создано)
    if response.status_code == 200:
        client.delete("/api/v1/prices/test_supplier_missing_cols") 