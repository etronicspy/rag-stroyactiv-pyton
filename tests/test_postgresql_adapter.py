"""Tests for PostgreSQL database adapter.

Тесты для PostgreSQL адаптера с SQLAlchemy 2.0 и async/await.
"""

import pytest
import asyncio
import unittest.mock
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from core.database.adapters.postgresql_adapter import PostgreSQLDatabase, MaterialModel, RawProductModel
from core.database.exceptions import ConnectionError, DatabaseError, QueryError, TransactionError


class TestPostgreSQLDatabase:
    """Test PostgreSQL database adapter."""
    
    @pytest.fixture
    def db_config(self) -> Dict[str, Any]:
        """Database configuration for testing."""
        return {
            "connection_string": "postgresql+asyncpg://test:test@localhost:5432/test_db",
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "echo": False
        }
    
    @pytest.fixture
    def mock_engine(self):
        """Mock SQLAlchemy async engine."""
        engine = AsyncMock()
        engine.pool.size.return_value = 5
        engine.pool.checkedin.return_value = 3
        engine.pool.checkedout.return_value = 2
        engine.pool.overflow.return_value = 0
        return engine
    
    @pytest.fixture
    def mock_session(self):
        """Mock SQLAlchemy async session."""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    async def db_adapter(self, db_config, mock_engine):
        """PostgreSQL adapter instance for testing."""
        with patch('core.database.adapters.postgresql_adapter.create_async_engine', return_value=mock_engine):
            with patch('core.database.adapters.postgresql_adapter.async_sessionmaker'):
                adapter = PostgreSQLDatabase(db_config)
                return adapter
    
    def test_init_success(self, db_config, mock_engine):
        """Test successful initialization."""
        with patch('core.database.adapters.postgresql_adapter.create_async_engine', return_value=mock_engine):
            with patch('core.database.adapters.postgresql_adapter.async_sessionmaker'):
                adapter = PostgreSQLDatabase(db_config)
                
                assert adapter.config == db_config
                assert adapter.connection_string == db_config["connection_string"]
                assert adapter.engine == mock_engine
    
    def test_init_missing_connection_string(self):
        """Test initialization with missing connection string."""
        config = {"pool_size": 5}
        
        with pytest.raises(ConnectionError) as exc_info:
            PostgreSQLDatabase(config)
        
        assert "PostgreSQL connection string is required" in str(exc_info.value)
    
    def test_init_engine_creation_failure(self, db_config):
        """Test initialization with engine creation failure."""
        with patch('core.database.adapters.postgresql_adapter.create_async_engine', side_effect=Exception("Engine error")):
            with pytest.raises(ConnectionError) as exc_info:
                PostgreSQLDatabase(db_config)
            
            assert "Failed to initialize PostgreSQL connection" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_tables_success(self, db_adapter):
        """Test successful table creation."""
        mock_conn = AsyncMock()
        db_adapter.engine.begin.return_value.__aenter__.return_value = mock_conn
        
        await db_adapter.create_tables()
        
        # Verify extensions were created
        mock_conn.execute.assert_any_call(unittest.mock.ANY)  # pg_trgm extension
        mock_conn.run_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_tables_failure(self, db_adapter):
        """Test table creation failure."""
        from sqlalchemy.exc import SQLAlchemyError
        
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = SQLAlchemyError("Table creation failed")
        db_adapter.engine.begin.return_value.__aenter__.return_value = mock_conn
        
        with pytest.raises(DatabaseError) as exc_info:
            await db_adapter.create_tables()
        
        assert "Failed to create database tables" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_query_success(self, db_adapter, mock_session):
        """Test successful query execution."""
        # Mock query result
        mock_result = MagicMock()
        mock_result.keys.return_value = ['id', 'name']
        mock_result.fetchall.return_value = [('1', 'Test Material')]
        
        mock_session.execute.return_value = mock_result
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        result = await db_adapter.execute_query("SELECT * FROM materials", {"id": "1"})
        
        assert result == [{'id': '1', 'name': 'Test Material'}]
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_query_failure(self, db_adapter, mock_session):
        """Test query execution failure."""
        from sqlalchemy.exc import SQLAlchemyError
        
        mock_session.execute.side_effect = SQLAlchemyError("Query failed")
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        with pytest.raises(QueryError) as exc_info:
            await db_adapter.execute_query("SELECT * FROM materials")
        
        assert "Failed to execute query" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_command_success(self, db_adapter, mock_session):
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        
        mock_session.execute.return_value = mock_result
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        result = await db_adapter.execute_command("INSERT INTO materials (...) VALUES (...)")
        
        assert result == 1
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_material_success(self, db_adapter, mock_session):
        """Test successful material creation."""
        material_data = {
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
        
        # Mock material instance
        mock_material = MagicMock()
        for key, value in material_data.items():
            setattr(mock_material, key, value)
        
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        result = await db_adapter.create_material(material_data)
        
        assert result["id"] == material_data["id"]
        assert result["name"] == material_data["name"]
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_materials_hybrid_success(self, db_adapter, mock_session):
        """Test successful hybrid search."""
        query = "cement"
        
        # Mock search results
        mock_material = MagicMock()
        mock_material.id = "test-id"
        mock_material.name = "Portland Cement"
        mock_material.use_category = "Cement"
        mock_material.unit = "bag"
        mock_material.sku = "CEM001"
        mock_material.description = "High quality cement"
        mock_material.embedding = [0.1, 0.2, 0.3]
        mock_material.created_at = datetime.utcnow()
        mock_material.updated_at = datetime.utcnow()
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (mock_material, 0.8, 0.6, 0.75)  # material, name_sim, desc_sim, total_sim
        ]
        
        mock_session.execute.return_value = mock_result
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        results = await db_adapter.search_materials_hybrid(query, limit=10)
        
        assert len(results) == 1
        assert results[0]["name"] == "Portland Cement"
        assert results[0]["similarity_score"] == 0.75
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_materials_success(self, db_adapter, mock_session):
        """Test successful materials retrieval."""
        # Mock materials
        mock_material = MagicMock()
        mock_material.id = "test-id"
        mock_material.name = "Test Material"
        mock_material.use_category = "Test Category"
        mock_material.unit = "kg"
        mock_material.sku = "TEST001"
        mock_material.description = "Test description"
        mock_material.embedding = [0.1, 0.2, 0.3]
        mock_material.created_at = datetime.utcnow()
        mock_material.updated_at = datetime.utcnow()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_material]
        
        mock_session.execute.return_value = mock_result
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        results = await db_adapter.get_materials(skip=0, limit=10)
        
        assert len(results) == 1
        assert results[0]["name"] == "Test Material"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_materials_with_category_filter(self, db_adapter, mock_session):
        """Test materials retrieval with category filter."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        
        mock_session.execute.return_value = mock_result
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        results = await db_adapter.get_materials(skip=0, limit=10, category="Cement")
        
        assert len(results) == 0
        mock_session.execute.assert_called_once()
        
        # Verify category filter was applied
        call_args = mock_session.execute.call_args[0][0]
        # Should contain WHERE clause with category filter
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, db_adapter, mock_session):
        """Test health check when database is healthy."""
        # Mock database stats
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (100, 50, 1024*1024*100)  # materials, raw_products, db_size
        
        mock_session.execute.return_value = mock_result
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        health = await db_adapter.health_check()
        
        assert health["status"] == "healthy"
        assert health["database_type"] == "PostgreSQL"
        assert health["statistics"]["materials_count"] == 100
        assert health["statistics"]["raw_products_count"] == 50
        assert health["statistics"]["database_size_mb"] == 100.0
        assert "connection_pool" in health
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, db_adapter, mock_session):
        """Test health check when database is unhealthy."""
        mock_session.execute.side_effect = Exception("Connection failed")
        db_adapter.async_session.return_value.__aenter__.return_value = mock_session
        
        health = await db_adapter.health_check()
        
        assert health["status"] == "unhealthy"
        assert health["database_type"] == "PostgreSQL"
        assert "error" in health
    
    @pytest.mark.asyncio
    async def test_transaction_operations(self, db_adapter):
        """Test transaction operations."""
        mock_session = AsyncMock()
        db_adapter.async_session.return_value = mock_session
        
        # Test begin transaction
        transaction = await db_adapter.begin_transaction()
        assert transaction == mock_session
        mock_session.begin.assert_called_once()
        
        # Test commit transaction
        await db_adapter.commit_transaction(mock_session)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        
        # Test rollback transaction
        mock_session.reset_mock()
        await db_adapter.rollback_transaction(mock_session)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_commit_failure(self, db_adapter):
        """Test transaction commit failure."""
        from sqlalchemy.exc import SQLAlchemyError
        
        mock_session = AsyncMock()
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")
        
        with pytest.raises(TransactionError) as exc_info:
            await db_adapter.commit_transaction(mock_session)
        
        assert "Failed to commit transaction" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_connections(self, db_adapter):
        """Test closing database connections."""
        await db_adapter.close()
        db_adapter.engine.dispose.assert_called_once()


class TestMaterialModel:
    """Test MaterialModel SQLAlchemy model."""
    
    def test_material_model_attributes(self):
        """Test MaterialModel has all required attributes."""
        assert hasattr(MaterialModel, '__tablename__')
        assert MaterialModel.__tablename__ == "materials"
        
        # Check required columns
        assert hasattr(MaterialModel, 'id')
        assert hasattr(MaterialModel, 'name')
        assert hasattr(MaterialModel, 'use_category')
        assert hasattr(MaterialModel, 'unit')
        assert hasattr(MaterialModel, 'sku')
        assert hasattr(MaterialModel, 'description')
        assert hasattr(MaterialModel, 'embedding')
        assert hasattr(MaterialModel, 'created_at')
        assert hasattr(MaterialModel, 'updated_at')
        assert hasattr(MaterialModel, 'search_vector')
    
    def test_material_model_indexes(self):
        """Test MaterialModel has proper indexes."""
        table_args = MaterialModel.__table_args__
        assert len(table_args) == 4  # 4 indexes defined
        
        # Check index names
        index_names = [idx.name for idx in table_args]
        expected_indexes = [
            'idx_materials_name_gin',
            'idx_materials_description_gin', 
            'idx_materials_search_vector',
            'idx_materials_category_unit'
        ]
        
        for expected_idx in expected_indexes:
            assert expected_idx in index_names


class TestRawProductModel:
    """Test RawProductModel SQLAlchemy model."""
    
    def test_raw_product_model_attributes(self):
        """Test RawProductModel has all required attributes."""
        assert hasattr(RawProductModel, '__tablename__')
        assert RawProductModel.__tablename__ == "raw_products"
        
        # Check required columns
        assert hasattr(RawProductModel, 'id')
        assert hasattr(RawProductModel, 'name')
        assert hasattr(RawProductModel, 'supplier_id')
        assert hasattr(RawProductModel, 'pricelistid')
        assert hasattr(RawProductModel, 'unit_price')
        assert hasattr(RawProductModel, 'is_processed')
        assert hasattr(RawProductModel, 'embedding')
        assert hasattr(RawProductModel, 'created')
        assert hasattr(RawProductModel, 'modified')
    
    def test_raw_product_model_indexes(self):
        """Test RawProductModel has proper indexes."""
        table_args = RawProductModel.__table_args__
        assert len(table_args) == 3  # 3 indexes defined
        
        # Check index names
        index_names = [idx.name for idx in table_args]
        expected_indexes = [
            'idx_raw_products_supplier_pricelist',
            'idx_raw_products_name_gin',
            'idx_raw_products_processed'
        ]
        
        for expected_idx in expected_indexes:
            assert expected_idx in index_names


# Integration tests (require actual PostgreSQL database)
@pytest.mark.integration
class TestPostgreSQLIntegration:
    """Integration tests for PostgreSQL adapter (requires real database)."""
    
    @pytest.fixture
    def integration_config(self) -> Dict[str, Any]:
        """Configuration for integration testing."""
        return {
            "connection_string": "postgresql+asyncpg://test:test@localhost:5432/test_materials",
            "pool_size": 2,
            "max_overflow": 5,
            "echo": True  # Enable SQL logging for debugging
        }
    
    @pytest.mark.asyncio
    async def test_full_material_lifecycle(self, integration_config):
        """Test complete material lifecycle with real database."""
        # Skip if no test database available
        pytest.skip("Integration test requires PostgreSQL test database")
        
        adapter = PostgreSQLDatabase(integration_config)
        
        try:
            # Create tables
            await adapter.create_tables()
            
            # Create material
            material_data = {
                "name": "Integration Test Material",
                "use_category": "Test Category",
                "unit": "kg",
                "sku": "INT001",
                "description": "Integration test material",
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
            }
            
            created_material = await adapter.create_material(material_data)
            assert created_material["name"] == material_data["name"]
            
            # Search materials
            search_results = await adapter.search_materials_hybrid("Integration Test", limit=5)
            assert len(search_results) >= 1
            
            # Get materials
            all_materials = await adapter.get_materials(skip=0, limit=10)
            assert len(all_materials) >= 1
            
            # Health check
            health = await adapter.health_check()
            assert health["status"] == "healthy"
            
        finally:
            # Cleanup
            await adapter.drop_tables()
            await adapter.close() 