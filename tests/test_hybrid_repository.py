"""Tests for Hybrid Materials Repository.

Тесты для гибридного репозитория материалов, использующего векторную и реляционную БД.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from core.repositories.hybrid_materials import HybridMaterialsRepository
from core.database.interfaces import IVectorDatabase, IRelationalDatabase
from core.database.exceptions import DatabaseError, QueryError
from core.schemas.materials import Material, MaterialCreate, MaterialUpdate


class TestHybridMaterialsRepository:
    """Test Hybrid Materials Repository."""
    
    @pytest.fixture
    def mock_vector_db(self):
        """Mock vector database."""
        mock_db = AsyncMock(spec=IVectorDatabase)
        return mock_db
    
    @pytest.fixture
    def mock_relational_db(self):
        """Mock relational database."""
        mock_db = AsyncMock(spec=IRelationalDatabase)
        return mock_db
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client."""
        mock_client = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def hybrid_repo(self, mock_vector_db, mock_relational_db, mock_ai_client):
        """Hybrid repository instance for testing."""
        with patch.object(HybridMaterialsRepository, 'get_embedding', new_callable=AsyncMock) as mock_embedding:
            mock_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
            repo = HybridMaterialsRepository(
                vector_db=mock_vector_db,
                relational_db=mock_relational_db,
                ai_client=mock_ai_client
            )
            return repo
    
    @pytest.fixture
    def sample_material_create(self):
        """Sample MaterialCreate for testing."""
        return MaterialCreate(
            name="Test Material",
            use_category="Test Category",
            unit="kg",
            sku="TEST001",
            description="Test description"
        )
    
    @pytest.fixture
    def sample_material_data(self):
        """Sample material data dictionary."""
        return {
            "id": "test-id",
            "name": "Test Material",
            "use_category": "Test Category",
            "unit": "kg",
            "sku": "TEST001",
            "description": "Test description",
            "embedding": [0.1, 0.2, 0.3],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "vector_score": 0.85,
            "search_type": "vector"
        }
    
    def test_init(self, mock_vector_db, mock_relational_db, mock_ai_client):
        """Test repository initialization."""
        repo = HybridMaterialsRepository(
            vector_db=mock_vector_db,
            relational_db=mock_relational_db,
            ai_client=mock_ai_client
        )
        
        assert repo.vector_db == mock_vector_db
        assert repo.relational_db == mock_relational_db
        assert repo.ai_client == mock_ai_client
        assert repo.collection_name == "materials"
    
    @pytest.mark.asyncio
    async def test_create_material_success(self, hybrid_repo, mock_vector_db, mock_relational_db, sample_material_create):
        """Test successful material creation in both databases."""
        # Mock successful operations
        mock_vector_db.upsert.return_value = None
        mock_relational_db.create_material.return_value = {"id": "test-id"}
        
        with patch('uuid.uuid4', return_value=MagicMock(hex="test-id")):
            result = await hybrid_repo.create_material(sample_material_create)
        
        assert isinstance(result, Material)
        assert result.name == sample_material_create.name
        assert result.use_category == sample_material_create.use_category
        
        # Verify both databases were called
        mock_vector_db.upsert.assert_called_once()
        mock_relational_db.create_material.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_material_vector_db_failure(self, hybrid_repo, mock_vector_db, mock_relational_db, sample_material_create):
        """Test material creation with vector database failure."""
        # Mock vector DB failure
        mock_vector_db.upsert.side_effect = DatabaseError("Vector DB failed")
        mock_relational_db.create_material.return_value = {"id": "test-id"}
        
        with pytest.raises(DatabaseError) as exc_info:
            await hybrid_repo.create_material(sample_material_create)
        
        assert "Failed to create material" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_materials_hybrid_success(self, hybrid_repo, mock_vector_db, mock_relational_db, sample_material_data):
        """Test successful hybrid search."""
        query = "test material"
        
        # Mock vector search results
        vector_result = MagicMock()
        vector_result.id = "test-id-1"
        vector_result.score = 0.85
        vector_result.payload = {
            "name": "Vector Material",
            "use_category": "Vector Category",
            "unit": "kg",
            "sku": "VEC001",
            "description": "Vector description",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        vector_result.vector = [0.1, 0.2, 0.3]
        
        # Mock SQL search results
        sql_result = {
            "id": "test-id-2",
            "name": "SQL Material",
            "use_category": "SQL Category",
            "unit": "kg",
            "sku": "SQL001",
            "description": "SQL description",
            "embedding": [0.4, 0.5, 0.6],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "similarity_score": 0.75
        }
        
        # Setup mocks
        mock_vector_db.search.return_value = [vector_result]
        mock_relational_db.search_materials_hybrid.return_value = [sql_result]
        
        results = await hybrid_repo.search_materials_hybrid(query, limit=10)
        
        assert len(results) == 2  # One from each source
        assert results[0]["search_type"] == "vector"  # Higher score should be first
        assert results[1]["search_type"] == "sql"
        
        # Verify both searches were called
        mock_vector_db.search.assert_called_once()
        mock_relational_db.search_materials_hybrid.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_materials_hybrid_vector_failure(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test hybrid search with vector database failure."""
        query = "test material"
        
        # Mock vector DB failure and SQL success
        mock_vector_db.search.side_effect = DatabaseError("Vector search failed")
        mock_relational_db.search_materials_hybrid.return_value = [
            {
                "id": "test-id",
                "name": "SQL Material",
                "similarity_score": 0.75,
                "search_type": "sql"
            }
        ]
        
        results = await hybrid_repo.search_materials_hybrid(query, limit=10)
        
        assert len(results) == 1
        assert results[0]["search_type"] == "sql"
    
    @pytest.mark.asyncio
    async def test_search_materials_fallback_strategy(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test fallback strategy: vector → SQL if 0 results."""
        query = "test material"
        
        # Mock vector search returning empty results
        mock_vector_db.search.return_value = []
        
        # Mock SQL search returning results
        sql_result = {
            "id": "test-id",
            "name": "SQL Material",
            "use_category": "SQL Category",
            "unit": "kg",
            "sku": "SQL001",
            "description": "SQL description",
            "embedding": [0.4, 0.5, 0.6],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "similarity_score": 0.75
        }
        mock_relational_db.search_materials_hybrid.return_value = [sql_result]
        
        results = await hybrid_repo.search_materials(query, limit=10)
        
        assert len(results) == 1
        assert isinstance(results[0], Material)
        assert results[0].name == "SQL Material"
        
        # Verify fallback was triggered
        mock_vector_db.search.assert_called_once()
        mock_relational_db.search_materials_hybrid.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_materials_vector_success_no_fallback(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test that SQL fallback is not triggered when vector search succeeds."""
        query = "test material"
        
        # Mock vector search returning results
        vector_result = MagicMock()
        vector_result.id = "test-id"
        vector_result.score = 0.85
        vector_result.payload = {
            "name": "Vector Material",
            "use_category": "Vector Category",
            "unit": "kg",
            "sku": "VEC001",
            "description": "Vector description",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        vector_result.vector = [0.1, 0.2, 0.3]
        
        mock_vector_db.search.return_value = [vector_result]
        
        results = await hybrid_repo.search_materials(query, limit=10)
        
        assert len(results) == 1
        assert isinstance(results[0], Material)
        assert results[0].name == "Vector Material"
        
        # Verify SQL search was not called
        mock_vector_db.search.assert_called_once()
        mock_relational_db.search_materials_hybrid.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_material_by_id_success(self, hybrid_repo, mock_relational_db):
        """Test successful material retrieval by ID."""
        material_id = "test-id"
        
        # Mock SQL query result
        mock_relational_db.execute_query.return_value = [
            {
                "id": material_id,
                "name": "Test Material",
                "use_category": "Test Category",
                "unit": "kg",
                "sku": "TEST001",
                "description": "Test description",
                "embedding": [0.1, 0.2, 0.3],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        result = await hybrid_repo.get_material_by_id(material_id)
        
        assert isinstance(result, Material)
        assert result.id == material_id
        assert result.name == "Test Material"
        
        mock_relational_db.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_material_by_id_not_found(self, hybrid_repo, mock_relational_db):
        """Test material retrieval when material not found."""
        material_id = "nonexistent-id"
        
        # Mock empty query result
        mock_relational_db.execute_query.return_value = []
        
        result = await hybrid_repo.get_material_by_id(material_id)
        
        assert result is None
        mock_relational_db.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_materials_success(self, hybrid_repo, mock_relational_db):
        """Test successful materials retrieval with pagination."""
        # Mock relational DB response
        mock_relational_db.get_materials.return_value = [
            {
                "id": "test-id-1",
                "name": "Material 1",
                "use_category": "Category 1",
                "unit": "kg",
                "sku": "MAT001",
                "description": "Description 1",
                "embedding": [0.1, 0.2, 0.3],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": "test-id-2",
                "name": "Material 2",
                "use_category": "Category 2",
                "unit": "m",
                "sku": "MAT002",
                "description": "Description 2",
                "embedding": [0.4, 0.5, 0.6],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        results = await hybrid_repo.get_materials(skip=0, limit=10, category="Category")
        
        assert len(results) == 2
        assert all(isinstance(material, Material) for material in results)
        assert results[0].name == "Material 1"
        assert results[1].name == "Material 2"
        
        mock_relational_db.get_materials.assert_called_once_with(0, 10, "Category")
    
    @pytest.mark.asyncio
    async def test_update_material_success(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test successful material update in both databases."""
        material_id = "test-id"
        
        # Mock current material
        current_material_data = {
            "id": material_id,
            "name": "Old Material",
            "use_category": "Old Category",
            "unit": "kg",
            "sku": "OLD001",
            "description": "Old description",
            "embedding": [0.1, 0.2, 0.3],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Mock updated material
        updated_material_data = {
            "id": material_id,
            "name": "Updated Material",
            "use_category": "Updated Category",
            "unit": "kg",
            "sku": "UPD001",
            "description": "Updated description",
            "embedding": [0.4, 0.5, 0.6],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Setup mocks
        mock_relational_db.execute_query.side_effect = [
            [current_material_data],  # First call for get_material_by_id
            [updated_material_data]   # Second call for get_material_by_id after update
        ]
        mock_vector_db.get_by_id.return_value = [MagicMock(payload=current_material_data, vector=[0.1, 0.2, 0.3])]
        mock_vector_db.upsert.return_value = None
        mock_relational_db.execute_command.return_value = 1
        
        material_update = MaterialUpdate(name="Updated Material", use_category="Updated Category")
        
        result = await hybrid_repo.update_material(material_id, material_update)
        
        assert isinstance(result, Material)
        assert result.name == "Updated Material"
        
        # Verify both databases were updated
        mock_vector_db.upsert.assert_called_once()
        mock_relational_db.execute_command.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_material_not_found(self, hybrid_repo, mock_relational_db):
        """Test material update when material not found."""
        material_id = "nonexistent-id"
        
        # Mock empty query result
        mock_relational_db.execute_query.return_value = []
        
        material_update = MaterialUpdate(name="Updated Material")
        result = await hybrid_repo.update_material(material_id, material_update)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_material_success(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test successful material deletion from both databases."""
        material_id = "test-id"
        
        # Mock material exists
        mock_relational_db.execute_query.return_value = [
            {
                "id": material_id,
                "name": "Test Material",
                "use_category": "Test Category",
                "unit": "kg",
                "sku": "TEST001",
                "description": "Test description",
                "embedding": [0.1, 0.2, 0.3],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Mock successful deletions
        mock_vector_db.delete.return_value = None
        mock_relational_db.execute_command.return_value = 1
        
        result = await hybrid_repo.delete_material(material_id)
        
        assert result is True
        
        # Verify both databases were called
        mock_vector_db.delete.assert_called_once_with(
            collection_name="materials",
            point_ids=[material_id]
        )
        mock_relational_db.execute_command.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_material_not_found(self, hybrid_repo, mock_relational_db):
        """Test material deletion when material not found."""
        material_id = "nonexistent-id"
        
        # Mock empty query result
        mock_relational_db.execute_query.return_value = []
        
        result = await hybrid_repo.delete_material(material_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_both_healthy(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test health check when both databases are healthy."""
        # Mock healthy responses
        mock_vector_db.health_check.return_value = {"status": "healthy", "database_type": "Qdrant"}
        mock_relational_db.health_check.return_value = {"status": "healthy", "database_type": "PostgreSQL"}
        
        health = await hybrid_repo.health_check()
        
        assert health["status"] == "healthy"
        assert health["repository_type"] == "hybrid"
        assert health["vector_database"]["status"] == "healthy"
        assert health["relational_database"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_vector_unhealthy(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test health check when vector database is unhealthy."""
        # Mock unhealthy vector DB
        mock_vector_db.health_check.side_effect = Exception("Vector DB down")
        mock_relational_db.health_check.return_value = {"status": "healthy", "database_type": "PostgreSQL"}
        
        health = await hybrid_repo.health_check()
        
        assert health["status"] == "degraded"
        assert health["repository_type"] == "hybrid"
        assert health["vector_database"]["status"] == "unhealthy"
        assert health["relational_database"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_both_unhealthy(self, hybrid_repo, mock_vector_db, mock_relational_db):
        """Test health check when both databases are unhealthy."""
        # Mock unhealthy responses
        mock_vector_db.health_check.side_effect = Exception("Vector DB down")
        mock_relational_db.health_check.side_effect = Exception("SQL DB down")
        
        health = await hybrid_repo.health_check()
        
        assert health["status"] == "degraded"
        assert health["repository_type"] == "hybrid"
        assert health["vector_database"]["status"] == "unhealthy"
        assert health["relational_database"]["status"] == "unhealthy"
    
    def test_combine_search_results(self, hybrid_repo):
        """Test combining search results from vector and SQL sources."""
        vector_results = [
            {"id": "1", "vector_score": 0.9, "name": "Vector Result 1"},
            {"id": "2", "vector_score": 0.7, "name": "Vector Result 2"}
        ]
        
        sql_results = [
            {"id": "3", "similarity_score": 0.8, "name": "SQL Result 1"},
            {"id": "4", "similarity_score": 0.6, "name": "SQL Result 2"}
        ]
        
        combined = hybrid_repo._combine_search_results(
            vector_results, sql_results, vector_weight=0.7, sql_weight=0.3
        )
        
        # Should be sorted by combined score (descending)
        assert len(combined) == 4
        assert combined[0]["id"] == "1"  # 0.9 * 0.7 = 0.63
        assert combined[1]["id"] == "3"  # 0.8 * 0.3 = 0.24
        assert combined[2]["id"] == "2"  # 0.7 * 0.7 = 0.49
        assert combined[3]["id"] == "4"  # 0.6 * 0.3 = 0.18
    
    def test_deduplicate_results(self, hybrid_repo):
        """Test deduplication of search results."""
        results = [
            {"id": "1", "combined_score": 0.9, "name": "Result 1 (high score)"},
            {"id": "2", "combined_score": 0.8, "name": "Result 2"},
            {"id": "1", "combined_score": 0.7, "name": "Result 1 (low score)"},  # Duplicate
            {"id": "3", "combined_score": 0.6, "name": "Result 3"}
        ]
        
        deduplicated = hybrid_repo._deduplicate_results(results)
        
        # Should keep only unique IDs, preserving order (highest score first)
        assert len(deduplicated) == 3
        assert deduplicated[0]["id"] == "1"
        assert deduplicated[0]["name"] == "Result 1 (high score)"  # Higher score kept
        assert deduplicated[1]["id"] == "2"
        assert deduplicated[2]["id"] == "3"
    
    def test_dict_to_material(self, hybrid_repo):
        """Test conversion from dictionary to Material object."""
        data = {
            "id": "test-id",
            "name": "Test Material",
            "use_category": "Test Category",
            "unit": "kg",
            "sku": "TEST001",
            "description": "Test description",
            "embedding": [0.1, 0.2, 0.3],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        material = hybrid_repo._dict_to_material(data)
        
        assert isinstance(material, Material)
        assert material.id == data["id"]
        assert material.name == data["name"]
        assert material.use_category == data["use_category"]
        assert material.unit == data["unit"]
        assert material.sku == data["sku"]
        assert material.description == data["description"]
        assert material.embedding == data["embedding"]
        assert material.created_at == data["created_at"]
        assert material.updated_at == data["updated_at"]
    
    def test_prepare_text_for_embedding(self, hybrid_repo, sample_material_create):
        """Test text preparation for embedding generation."""
        text = hybrid_repo._prepare_text_for_embedding(sample_material_create)
        
        expected = f"{sample_material_create.name} {sample_material_create.use_category} {sample_material_create.sku} {sample_material_create.description}"
        assert text == expected 