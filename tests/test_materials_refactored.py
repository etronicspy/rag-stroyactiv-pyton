"""Tests for refactored MaterialsService using new multi-database architecture.

Тесты для рефакторенного MaterialsService с новой мульти-БД архитектурой.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.schemas.materials import MaterialCreate, MaterialUpdate, MaterialImportItem
from core.database.exceptions import DatabaseError, ConnectionError
from services.materials_new import MaterialsService


class TestMaterialsServiceRefactored:
    """Test refactored MaterialsService with dependency injection."""
    
    @pytest.fixture
    def mock_vector_db(self):
        """Mock vector database client."""
        mock_db = Mock()
        mock_db.collection_exists = AsyncMock(return_value=True)
        mock_db.create_collection = AsyncMock()
        mock_db.upsert = AsyncMock()
        mock_db.get_by_id = AsyncMock()
        mock_db.search = AsyncMock()
        mock_db.delete = AsyncMock()
        mock_db.batch_upsert = AsyncMock()
        mock_db.health_check = AsyncMock(return_value={
            "status": "healthy",
            "database_type": "Qdrant",
            "timestamp": datetime.utcnow().isoformat()
        })
        return mock_db
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client for embeddings."""
        mock_client = Mock()
        return mock_client
    
    @pytest.fixture
    def materials_service(self, mock_vector_db, mock_ai_client):
        """Create MaterialsService with mocked dependencies."""
        service = MaterialsService(vector_db=mock_vector_db, ai_client=mock_ai_client)
        return service
    
    @pytest.fixture
    def sample_material_create(self):
        """Sample MaterialCreate object."""
        return MaterialCreate(
            name="Тестовый цемент",
            use_category="Цемент",
            unit="кг",
            sku="CEM001",
            description="Портландцемент М400"
        )
    
    async def test_service_initialization(self, materials_service):
        """Test service initialization with dependency injection."""
        assert materials_service.collection_name == "materials"
        assert materials_service.vector_db is not None
        assert materials_service.ai_client is not None
    
    async def test_ensure_collection_exists_creates_collection(self, materials_service, mock_vector_db):
        """Test collection creation when it doesn't exist."""
        mock_vector_db.collection_exists.return_value = False
        
        await materials_service._ensure_collection_exists()
        
        mock_vector_db.collection_exists.assert_called_once_with("materials")
        mock_vector_db.create_collection.assert_called_once_with(
            collection_name="materials",
            vector_size=1536,
            distance_metric="cosine"
        )
    
    async def test_ensure_collection_exists_skips_if_exists(self, materials_service, mock_vector_db):
        """Test collection creation is skipped when collection exists."""
        mock_vector_db.collection_exists.return_value = True
        
        await materials_service._ensure_collection_exists()
        
        mock_vector_db.collection_exists.assert_called_once_with("materials")
        mock_vector_db.create_collection.assert_not_called()
    
    @patch('services.materials_new.MaterialsService.get_embedding')
    async def test_create_material_success(self, mock_get_embedding, materials_service, 
                                         mock_vector_db, sample_material_create):
        """Test successful material creation."""
        # Mock embedding generation
        mock_embedding = [0.1] * 1536
        mock_get_embedding.return_value = mock_embedding
        
        # Call create_material
        result = await materials_service.create_material(sample_material_create)
        
        # Verify embedding was generated
        mock_get_embedding.assert_called_once()
        
        # Verify vector database upsert was called
        mock_vector_db.upsert.assert_called_once()
        call_args = mock_vector_db.upsert.call_args[1]
        assert call_args["collection_name"] == "materials"
        assert len(call_args["vectors"]) == 1
        
        vector_data = call_args["vectors"][0]
        assert vector_data["vector"] == mock_embedding
        assert vector_data["payload"]["name"] == sample_material_create.name
        assert vector_data["payload"]["use_category"] == sample_material_create.use_category
        
        # Verify returned material
        assert result.name == sample_material_create.name
        assert result.use_category == sample_material_create.use_category
        assert result.id is not None
        assert result.embedding == mock_embedding[:10]  # Truncated
    
    @patch('services.materials_new.MaterialsService.get_embedding')
    async def test_create_material_database_error(self, mock_get_embedding, materials_service, 
                                                 mock_vector_db, sample_material_create):
        """Test material creation with database error."""
        mock_get_embedding.return_value = [0.1] * 1536
        mock_vector_db.upsert.side_effect = Exception("Database connection failed")
        
        with pytest.raises(DatabaseError) as exc_info:
            await materials_service.create_material(sample_material_create)
        
        assert "Failed to create material" in str(exc_info.value)
    
    async def test_get_material_success(self, materials_service, mock_vector_db):
        """Test successful material retrieval."""
        # Mock vector database response
        mock_result = {
            "id": "test-id",
            "vector": [0.1] * 10,
            "payload": {
                "name": "Тестовый материал",
                "use_category": "Тест",
                "unit": "шт",
                "sku": "TEST001",
                "description": "Тестовое описание",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        }
        mock_vector_db.get_by_id.return_value = mock_result
        
        result = await materials_service.get_material("test-id")
        
        mock_vector_db.get_by_id.assert_called_once_with(
            collection_name="materials",
            vector_id="test-id"
        )
        
        assert result is not None
        assert result.id == "test-id"
        assert result.name == "Тестовый материал"
        assert result.use_category == "Тест"
    
    async def test_get_material_not_found(self, materials_service, mock_vector_db):
        """Test material retrieval when material doesn't exist."""
        mock_vector_db.get_by_id.return_value = None
        
        result = await materials_service.get_material("nonexistent-id")
        
        assert result is None
    
    @patch('services.materials_new.MaterialsService.get_embedding')
    async def test_search_materials_vector_success(self, mock_get_embedding, materials_service, mock_vector_db):
        """Test successful vector search."""
        # Mock embedding and search results
        mock_get_embedding.return_value = [0.1] * 1536
        mock_search_results = [
            {
                "id": "result-1",
                "vector": [0.1] * 10,
                "payload": {
                    "name": "Цемент М400",
                    "use_category": "Цемент",
                    "unit": "кг",
                    "sku": "CEM400",
                    "description": "Портландцемент",
                    "created_at": "2024-01-01T12:00:00",
                    "updated_at": "2024-01-01T12:00:00"
                }
            }
        ]
        mock_vector_db.search.return_value = mock_search_results
        
        results = await materials_service.search_materials("цемент", limit=10)
        
        # Verify embedding generation and search
        mock_get_embedding.assert_called_once_with("цемент")
        mock_vector_db.search.assert_called_once_with(
            collection_name="materials",
            query_vector=[0.1] * 1536,
            limit=10,
            filter_conditions=None
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0].name == "Цемент М400"
        assert results[0].use_category == "Цемент"
    
    @patch('services.materials_new.MaterialsService.get_embedding')
    async def test_search_materials_no_results_fallback(self, mock_get_embedding, materials_service, mock_vector_db):
        """Test search fallback when vector search returns no results."""
        mock_get_embedding.return_value = [0.1] * 1536
        mock_vector_db.search.return_value = []  # No vector results
        
        results = await materials_service.search_materials("nonexistent", limit=10)
        
        # Should return empty list (fallback not yet implemented)
        assert len(results) == 0
    
    async def test_delete_material_success(self, materials_service, mock_vector_db):
        """Test successful material deletion."""
        result = await materials_service.delete_material("test-id")
        
        mock_vector_db.delete.assert_called_once_with(
            collection_name="materials",
            vector_id="test-id"
        )
        assert result is True
    
    async def test_delete_material_database_error(self, materials_service, mock_vector_db):
        """Test material deletion with database error."""
        mock_vector_db.delete.side_effect = Exception("Delete failed")
        
        with pytest.raises(DatabaseError) as exc_info:
            await materials_service.delete_material("test-id")
        
        assert "Failed to delete material" in str(exc_info.value)
    
    @patch('services.materials_new.MaterialsService.get_embedding')
    async def test_create_materials_batch_success(self, mock_get_embedding, materials_service, mock_vector_db):
        """Test successful batch material creation."""
        # Mock embedding generation
        mock_get_embedding.return_value = [0.1] * 1536
        
        # Create test materials
        materials = [
            MaterialCreate(name="Материал 1", use_category="Тест", unit="шт"),
            MaterialCreate(name="Материал 2", use_category="Тест", unit="шт")
        ]
        
        result = await materials_service.create_materials_batch(materials, batch_size=2)
        
        # Verify batch upsert was called
        mock_vector_db.batch_upsert.assert_called_once()
        
        # Verify result
        assert result.success is True
        assert result.total_processed == 2
        assert result.successful_creates == 2
        assert result.failed_creates == 0
        assert len(result.created_materials) == 2
    
    async def test_import_materials_from_json(self, materials_service):
        """Test material import from JSON format."""
        import_items = [
            MaterialImportItem(name="Цемент М400", sku="CEM400"),
            MaterialImportItem(name="Кирпич красный", sku="BRICK001")
        ]
        
        # Mock the batch creation method
        with patch.object(materials_service, 'create_materials_batch') as mock_batch:
            mock_batch.return_value = Mock(
                success=True,
                total_processed=2,
                successful_creates=2,
                failed_creates=0
            )
            
            result = await materials_service.import_materials_from_json(
                import_items,
                default_category="Стройматериалы",
                default_unit="шт"
            )
            
            # Verify batch creation was called
            mock_batch.assert_called_once()
            call_args = mock_batch.call_args[0][0]  # First argument (materials list)
            
            # Verify category and unit inference
            assert len(call_args) == 2
            assert call_args[0].name == "Цемент М400"
            assert call_args[0].use_category == "Цемент"  # Inferred from name
            assert call_args[0].unit == "кг"  # Inferred from name
            
            assert call_args[1].name == "Кирпич красный"
            assert call_args[1].use_category == "Кирпич"  # Inferred from name
            assert call_args[1].unit == "шт"  # Inferred from name
    
    def test_category_inference(self, materials_service):
        """Test category inference from material names."""
        category_map = materials_service._get_category_mapping()
        
        # Test successful inference
        assert materials_service._infer_category("Цемент М400", category_map) == "Цемент"
        assert materials_service._infer_category("Кирпич красный", category_map) == "Кирпич"
        assert materials_service._infer_category("Доска обрезная", category_map) == "Пиломатериалы"
        
        # Test no match
        assert materials_service._infer_category("Неизвестный материал", category_map) is None
    
    def test_unit_inference(self, materials_service):
        """Test unit inference from material names."""
        unit_map = materials_service._get_unit_mapping()
        
        # Test successful inference
        assert materials_service._infer_unit("Цемент М400", unit_map) == "кг"
        assert materials_service._infer_unit("Песок речной", unit_map) == "м³"
        assert materials_service._infer_unit("Кирпич красный", unit_map) == "шт"
        
        # Test no match
        assert materials_service._infer_unit("Неизвестный материал", unit_map) is None
    
    def test_prepare_text_for_embedding(self, materials_service, sample_material_create):
        """Test text preparation for embedding generation."""
        text = materials_service._prepare_text_for_embedding(sample_material_create)
        
        expected = "Тестовый цемент Цемент CEM001 Портландцемент М400"
        assert text == expected
    
    def test_convert_vector_result_to_material(self, materials_service):
        """Test conversion of vector database result to Material object."""
        vector_result = {
            "id": "test-id",
            "vector": [0.1] * 1536,
            "payload": {
                "name": "Тестовый материал",
                "use_category": "Тест",
                "unit": "шт",
                "sku": "TEST001",
                "description": "Описание",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        }
        
        material = materials_service._convert_vector_result_to_material(vector_result)
        
        assert material is not None
        assert material.id == "test-id"
        assert material.name == "Тестовый материал"
        assert material.use_category == "Тест"
        assert material.unit == "шт"
        assert material.sku == "TEST001"
        assert material.description == "Описание"
        assert len(material.embedding) == 10  # Truncated
    
    def test_parse_timestamp(self, materials_service):
        """Test timestamp parsing."""
        # Valid timestamp
        valid_timestamp = "2024-01-01T12:00:00"
        parsed = materials_service._parse_timestamp(valid_timestamp)
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 1
        
        # Invalid timestamp - should return current time
        invalid_timestamp = "invalid-date"
        parsed = materials_service._parse_timestamp(invalid_timestamp)
        assert isinstance(parsed, datetime)
        
        # None timestamp - should return current time
        parsed = materials_service._parse_timestamp(None)
        assert isinstance(parsed, datetime)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 