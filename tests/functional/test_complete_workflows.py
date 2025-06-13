# === Price Lists Functional Tests ===
class TestPriceListWorkflows:
    """Functional tests for price list processing workflows."""
    
    @pytest.fixture
    def setup_references(self, client):
        """Create necessary reference data for price list tests."""
        # Create categories
        client.post("/api/v1/reference/categories/", json={"name": "Цемент", "description": "Цементы"})
        client.post("/api/v1/reference/categories/", json={"name": "Песок", "description": "Песок и щебень"})
        
        # Create units
        client.post("/api/v1/reference/units/", json={"name": "кг", "description": "Килограмм"})
        client.post("/api/v1/reference/units/", json={"name": "м³", "description": "Кубический метр"})
    
    def test_complete_price_list_workflow(self, client, setup_references):
        """Test complete price list processing workflow."""
        import io
        import time
        
        # Create test CSV content
        csv_content = """name,price,unit,description,category
Портландцемент М500,150.00,кг,Высококачественный цемент,Цемент
Песок речной,800.00,м³,Чистый речной песок,Песок
Цемент белый,200.00,кг,Белый цемент для декоративных работ,Цемент
Щебень гранитный,1200.00,м³,Щебень фракции 5-20мм,Песок"""
        
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        supplier_id = "test_supplier_workflow"
        
        # Step 1: Process price list
        response = client.post(
            "/api/v1/prices/process",
            files={
                "file": ("valid_prices.csv", csv_file, "text/csv"),
                "supplier_id": (None, supplier_id)
            }
        )
        
        assert response.status_code == 200
        process_data = response.json()
        assert process_data["message"] == "Price list processed successfully"
        assert process_data["supplier_id"] == supplier_id
        assert process_data["materials_processed"] == 4
        assert "upload_date" in process_data
        
        # Step 2: Get latest price list
        response = client.get(f"/api/v1/prices/{supplier_id}/latest")
        assert response.status_code == 200
        
        latest_data = response.json()
        assert latest_data["supplier_id"] == supplier_id
        assert latest_data["total_count"] == 4
        assert len(latest_data["materials"]) == 4
        
        # Verify materials content
        material_names = [m["name"] for m in latest_data["materials"]]
        assert "Портландцемент М500" in material_names
        assert "Песок речной" in material_names
        assert "Цемент белый" in material_names
        assert "Щебень гранитный" in material_names
        
        # Step 3: Upload second price list (version 2)
        time.sleep(1)  # Ensure different timestamp
        
        csv_content_v2 = """name,price,unit,description,category
Портландцемент М500,155.00,кг,Высококачественный цемент обновленная цена,Цемент
Песок речной,820.00,м³,Чистый речной песок обновленная цена,Песок
Бетон М300,3500.00,м³,Готовый бетон марки М300,Цемент"""
        
        csv_file_v2 = io.BytesIO(csv_content_v2.encode('utf-8'))
        
        response = client.post(
            "/api/v1/prices/process",
            files={
                "file": ("prices_v2.csv", csv_file_v2, "text/csv"),
                "supplier_id": (None, supplier_id)
            }
        )
        
        assert response.status_code == 200
        process_data_v2 = response.json()
        assert process_data_v2["materials_processed"] == 3
        
        # Step 4: Get all price lists for supplier
        response = client.get(f"/api/v1/prices/{supplier_id}/all")
        assert response.status_code == 200
        
        all_data = response.json()
        assert all_data["supplier_id"] == supplier_id
        assert all_data["total_price_lists"] == 2
        assert len(all_data["price_lists"]) == 2
        
        # Verify order (latest first)
        price_lists = all_data["price_lists"]
        assert price_lists[0]["materials_count"] == 3  # Latest (v2)
        assert price_lists[1]["materials_count"] == 4  # Original
        
        # Step 5: Verify latest is now v2
        response = client.get(f"/api/v1/prices/{supplier_id}/latest")
        assert response.status_code == 200
        
        latest_v2_data = response.json()
        assert latest_v2_data["total_count"] == 3
        
        # Find updated material
        updated_cement = next(
            (m for m in latest_v2_data["materials"] if m["name"] == "Портландцемент М500"),
            None
        )
        assert updated_cement is not None
        assert updated_cement["price"] == 155.00  # Updated price
        
        # Step 6: Delete all price lists
        response = client.delete(f"/api/v1/prices/{supplier_id}")
        assert response.status_code == 200
        
        delete_data = response.json()
        assert f"All price lists for supplier {supplier_id} have been deleted" in delete_data["message"]
        
        # Step 7: Verify deletion
        response = client.get(f"/api/v1/prices/{supplier_id}/latest")
        assert response.status_code == 404
        assert "No price lists found" in response.json()["detail"]
    
    def test_price_list_validation_workflow(self, client, setup_references):
        """Test price list validation and error handling."""
        import io
        
        supplier_id = "test_supplier_validation"
        
        # Test 1: Invalid file format
        text_content = "This is not a CSV file"
        text_file = io.BytesIO(text_content.encode('utf-8'))
        
        response = client.post(
            "/api/v1/prices/process",
            files={
                "file": ("invalid.txt", text_file, "text/plain"),
                "supplier_id": (None, supplier_id)
            }
        )
        
        assert response.status_code == 400
        assert "Invalid file format" in response.json()["detail"]
        
        # Test 2: Missing required columns
        invalid_csv = """name,description
Material 1,Description 1
Material 2,Description 2"""
        
        invalid_file = io.BytesIO(invalid_csv.encode('utf-8'))
        
        response = client.post(
            "/api/v1/prices/process",
            files={
                "file": ("invalid_columns.csv", invalid_file, "text/csv"),
                "supplier_id": (None, supplier_id)
            }
        )
        
        assert response.status_code == 400
        assert "Missing required columns" in response.json()["detail"]
        
        # Test 3: Invalid price data
        invalid_price_csv = """name,price,unit,description,category
Material 1,invalid_price,кг,Description 1,Цемент
Material 2,200.00,кг,Description 2,Цемент"""
        
        invalid_price_file = io.BytesIO(invalid_price_csv.encode('utf-8'))
        
        response = client.post(
            "/api/v1/prices/process",
            files={
                "file": ("invalid_prices.csv", invalid_price_file, "text/csv"),
                "supplier_id": (None, supplier_id)
            }
        )
        
        # Should process valid rows and skip invalid ones
        assert response.status_code == 200
        data = response.json()
        assert data["materials_processed"] == 1  # Only valid row processed
        
        # Cleanup
        client.delete(f"/api/v1/prices/{supplier_id}")
    
    def test_price_list_retention_policy(self, client, setup_references):
        """Test price list retention policy (max 3 versions)."""
        import io
        import time
        
        supplier_id = "test_supplier_retention"
        
        # Upload 4 price lists
        for i in range(4):
            csv_content = f"""name,price,unit,description,category
Material Version {i + 1},{100 + i * 10}.00,кг,Description {i + 1},Цемент"""
            
            csv_file = io.BytesIO(csv_content.encode('utf-8'))
            
            response = client.post(
                "/api/v1/prices/process",
                files={
                    "file": (f"prices_v{i+1}.csv", csv_file, "text/csv"),
                    "supplier_id": (None, supplier_id)
                }
            )
            
            assert response.status_code == 200
            time.sleep(0.1)  # Small delay to ensure different timestamps
        
        # Check that only 3 price lists are retained
        response = client.get(f"/api/v1/prices/{supplier_id}/all")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_price_lists"] == 3  # Should keep only last 3
        
        # Verify that the oldest (version 1) was deleted
        latest_response = client.get(f"/api/v1/prices/{supplier_id}/latest")
        latest_material = latest_response.json()["materials"][0]
        assert "Version 4" in latest_material["name"]  # Latest should be version 4
        
        # Cleanup
        client.delete(f"/api/v1/prices/{supplier_id}")
    
    def test_empty_file_handling(self, client, setup_references):
        """Test handling of empty CSV file."""
        import io
        
        supplier_id = "test_supplier_empty"
        
        # Test empty file
        empty_csv = ""
        empty_file = io.BytesIO(empty_csv.encode('utf-8'))
        
        response = client.post(
            "/api/v1/prices/process",
            files={
                "file": ("empty.csv", empty_file, "text/csv"),
                "supplier_id": (None, supplier_id)
            }
        )
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
        
        # Test file with only headers
        headers_only_csv = "name,price,unit,description,category"
        headers_file = io.BytesIO(headers_only_csv.encode('utf-8'))
        
        response = client.post(
            "/api/v1/prices/process",
            files={
                "file": ("headers_only.csv", headers_file, "text/csv"),
                "supplier_id": (None, supplier_id)
            }
        )
        
        assert response.status_code == 400
        assert "no data" in response.json()["detail"].lower() 