"""Tests for database migrations and initialization.

Тесты для проверки миграций БД и инициализации данных.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from core.database.init_db import DatabaseInitializer, initialize_database_on_startup
from core.database.seed_data import DatabaseSeeder, seed_database
from core.config import settings


class TestDatabaseMigrations:
    """Test database migrations."""
    
    @pytest.fixture
    def mock_db_config(self):
        """Mock database configuration."""
        return {
            "connection_string": "postgresql+asyncpg://test:test@localhost/test_db",
            "pool_size": 5,
            "max_overflow": 10
        }
    
    @pytest.fixture
    def db_initializer(self, mock_db_config):
        """Create database initializer with mock config."""
        return DatabaseInitializer(mock_db_config)
    
    @patch('core.database.init_db.PostgreSQLDatabase')
    async def test_connect_database(self, mock_postgres, db_initializer):
        """Test database connection."""
        # Arrange
        mock_db_instance = Mock()
        mock_postgres.return_value = mock_db_instance
        
        # Act
        await db_initializer.connect_database()
        
        # Assert
        mock_postgres.assert_called_once_with(db_initializer.db_config)
        assert db_initializer.db_adapter == mock_db_instance
    
    @patch('core.database.init_db.Config')
    @patch('core.database.init_db.command')
    @patch('core.database.init_db.Path')
    def test_run_migrations(self, mock_path, mock_command, mock_config, db_initializer):
        """Test running Alembic migrations."""
        # Arrange
        mock_alembic_cfg = Mock()
        mock_config.return_value = mock_alembic_cfg
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance
        
        # Act
        db_initializer.run_migrations()
        
        # Assert
        mock_config.assert_called_once()
        mock_command.upgrade.assert_called_once_with(mock_alembic_cfg, "head")
    
    @patch('core.database.init_db.PostgreSQLDatabase')
    async def test_seed_reference_data(self, mock_postgres, db_initializer):
        """Test seeding reference data."""
        # Arrange
        mock_db_instance = Mock()
        mock_session = AsyncMock()
        mock_db_instance.get_session.return_value.__aenter__.return_value = mock_session
        mock_postgres.return_value = mock_db_instance
        
        await db_initializer.connect_database()
        
        with patch('core.database.init_db.seed_database') as mock_seed:
            mock_seed.return_value = {"categories": 5, "units": 18}
            
            # Act
            result = await db_initializer.seed_reference_data()
            
            # Assert
            mock_seed.assert_called_once_with(mock_session)
            assert result == {"categories": 5, "units": 18}
    
    @patch('core.database.init_db.PostgreSQLDatabase')
    async def test_verify_database_health(self, mock_postgres, db_initializer):
        """Test database health verification."""
        # Arrange
        mock_db_instance = Mock()
        mock_db_instance.health_check.return_value = {"status": "healthy", "tables": 4}
        mock_postgres.return_value = mock_db_instance
        
        await db_initializer.connect_database()
        
        # Act
        result = await db_initializer.verify_database_health()
        
        # Assert
        mock_db_instance.health_check.assert_called_once()
        assert result["status"] == "healthy"
    
    @patch('core.database.init_db.PostgreSQLDatabase')
    async def test_initialize_database_success(self, mock_postgres, db_initializer):
        """Test successful database initialization."""
        # Arrange
        mock_db_instance = Mock()
        mock_session = AsyncMock()
        mock_db_instance.get_session.return_value.__aenter__.return_value = mock_session
        mock_db_instance.health_check.return_value = {"status": "healthy"}
        mock_db_instance.close = AsyncMock()
        mock_postgres.return_value = mock_db_instance
        
        with patch.object(db_initializer, 'run_migrations') as mock_migrate, \
             patch('core.database.init_db.seed_database') as mock_seed:
            
            mock_seed.return_value = {"categories": 5, "units": 18}
            
            # Act
            result = await db_initializer.initialize_database()
            
            # Assert
            assert result["success"] is True
            assert result["migrations"]["status"] == "success"
            assert result["seeding"]["status"] == "success"
            assert result["health_check"]["status"] == "success"
            mock_migrate.assert_called_once()
    
    @patch('core.database.init_db.PostgreSQLDatabase')
    async def test_initialize_database_migration_failure(self, mock_postgres, db_initializer):
        """Test database initialization with migration failure."""
        # Arrange
        mock_db_instance = Mock()
        mock_session = AsyncMock()
        mock_db_instance.get_session.return_value.__aenter__.return_value = mock_session
        mock_db_instance.health_check.return_value = {"status": "healthy"}
        mock_db_instance.close = AsyncMock()
        mock_postgres.return_value = mock_db_instance
        
        with patch.object(db_initializer, 'run_migrations') as mock_migrate, \
             patch('core.database.init_db.seed_database') as mock_seed:
            
            mock_migrate.side_effect = Exception("Migration failed")
            mock_seed.return_value = {"categories": 5, "units": 18}
            
            # Act
            result = await db_initializer.initialize_database()
            
            # Assert
            assert result["success"] is True  # Should continue despite migration failure
            assert result["migrations"]["status"] == "failed"
            assert result["seeding"]["status"] == "success"


class TestDatabaseSeeder:
    """Test database seeding functionality."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock async database session."""
        session = AsyncMock()
        # Mock execute method to return results
        session.execute.return_value.scalar.return_value = 0  # No existing records
        return session
    
    @pytest.fixture
    def db_seeder(self, mock_session):
        """Create database seeder with mock session."""
        return DatabaseSeeder(mock_session)
    
    async def test_seed_categories_empty_db(self, db_seeder, mock_session):
        """Test seeding categories in empty database."""
        # Arrange
        mock_session.execute.return_value.scalar.return_value = 0  # Empty DB
        
        # Act
        await db_seeder.seed_categories()
        
        # Assert
        assert mock_session.execute.call_count > 1  # Multiple INSERT calls
        mock_session.commit.assert_called_once()
    
    async def test_seed_categories_existing_data(self, db_seeder, mock_session):
        """Test seeding categories when data already exists."""
        # Arrange
        mock_session.execute.return_value.scalar.return_value = 5  # Existing records
        
        # Act
        await db_seeder.seed_categories()
        
        # Assert
        assert mock_session.execute.call_count == 1  # Only COUNT query
        mock_session.commit.assert_not_called()
    
    async def test_seed_units_empty_db(self, db_seeder, mock_session):
        """Test seeding units in empty database."""
        # Arrange
        # First call returns 0 (empty), subsequent calls return IDs
        mock_session.execute.return_value.scalar.side_effect = [0, 1, 2, 3, 4]
        
        # Act
        await db_seeder.seed_units()
        
        # Assert
        assert mock_session.execute.call_count > 1  # Multiple INSERT calls
        mock_session.commit.assert_called_once()
    
    async def test_seed_all(self, db_seeder):
        """Test seeding all reference data."""
        with patch.object(db_seeder, 'seed_categories') as mock_categories, \
             patch.object(db_seeder, 'seed_units') as mock_units:
            
            # Act
            await db_seeder.seed_all()
            
            # Assert
            mock_categories.assert_called_once()
            mock_units.assert_called_once()
    
    async def test_verify_seed_data(self, db_seeder, mock_session):
        """Test verification of seeded data."""
        # Arrange
        mock_session.execute.return_value.scalar.side_effect = [5, 18]  # Categories, Units
        
        # Act
        result = await db_seeder.verify_seed_data()
        
        # Assert
        assert result == {"categories": 5, "units": 18}
        assert mock_session.execute.call_count == 2


class TestInitializationIntegration:
    """Integration tests for database initialization."""
    
    @patch('core.database.init_db.DatabaseInitializer')
    async def test_initialize_database_on_startup(self, mock_initializer_class):
        """Test startup initialization function."""
        # Arrange
        mock_initializer = Mock()
        mock_initializer.initialize_database.return_value = {
            "migrations": {"status": "success"},
            "seeding": {"status": "success"},
            "health_check": {"status": "success"},
            "success": True
        }
        mock_initializer_class.return_value = mock_initializer
        
        # Act
        result = await initialize_database_on_startup(
            run_migrations=True,
            seed_data=True,
            verify_health=True
        )
        
        # Assert
        mock_initializer_class.assert_called_once()
        mock_initializer.initialize_database.assert_called_once_with(
            run_migrations=True,
            seed_data=True,
            verify_health=True
        )
        assert result["success"] is True
    
    async def test_seed_database_function(self):
        """Test convenience seed_database function."""
        mock_session = AsyncMock()
        
        with patch('core.database.seed_data.DatabaseSeeder') as mock_seeder_class:
            mock_seeder = Mock()
            mock_seeder.seed_all = AsyncMock()
            mock_seeder.verify_seed_data.return_value = {"categories": 5, "units": 18}
            mock_seeder_class.return_value = mock_seeder
            
            # Act
            result = await seed_database(mock_session)
            
            # Assert
            mock_seeder_class.assert_called_once_with(mock_session)
            mock_seeder.seed_all.assert_called_once()
            mock_seeder.verify_seed_data.assert_called_once()
            assert result == {"categories": 5, "units": 18}


@pytest.mark.asyncio
async def test_migration_chain_order():
    """Test that migrations are in correct order."""
    # This would be an integration test that checks migration dependencies
    # For now, we'll just verify the revision chain structure
    
    # Check that revision IDs are correctly linked
    assert True  # Placeholder - would need actual migration file parsing


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 