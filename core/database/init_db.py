"""Database initialization module.

Модуль для автоматической инициализации БД с поддержкой миграций и seed данных.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import subprocess
import sys
import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from alembic import command
from alembic.config import Config

from core.config import settings
from core.database.adapters.postgresql_adapter import PostgreSQLDatabase
from core.database.seed_data import seed_database


logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Database initializer for migrations and seeding.
    
    Класс для инициализации БД с автоматическим запуском миграций и seed данных.
    """
    
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """Initialize database initializer.
        
        Args:
            db_config: Database configuration (if None, will use settings)
        """
        self.db_config = db_config or settings.get_relational_db_config()
        self.db_adapter = None
    
    async def connect_database(self) -> None:
        """Connect to database.
        
        Устанавливает соединение с БД.
        """
        try:
            self.db_adapter = PostgreSQLDatabase(self.db_config)
            logger.info("Database connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def run_migrations(self) -> None:
        """Run Alembic migrations.
        
        Запускает миграции Alembic для создания схемы БД.
        """
        try:
            # Get project root directory
            project_root = Path(__file__).parent.parent.parent
            alembic_cfg_path = project_root / "alembic.ini"
            
            if not alembic_cfg_path.exists():
                raise FileNotFoundError(f"Alembic config not found at {alembic_cfg_path}")
            
            # Configure Alembic
            alembic_cfg = Config(str(alembic_cfg_path))
            
            # Set database URL in Alembic config
            connection_string = self.db_config.get("connection_string")
            if connection_string:
                alembic_cfg.set_main_option("sqlalchemy.url", connection_string)
            
            logger.info("Running database migrations...")
            
            # Run migrations to latest
            command.upgrade(alembic_cfg, "head")
            
            logger.info("Database migrations completed successfully")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def seed_reference_data(self) -> Dict[str, int]:
        """Seed reference data.
        
        Инициализирует справочные данные в БД.
        
        Returns:
            Dictionary with counts of seeded records
        """
        if not self.db_adapter:
            raise RuntimeError("Database adapter not initialized")
        
        try:
            logger.info("Seeding reference data...")
            
            async with self.db_adapter.get_session() as session:
                seed_results = await seed_database(session)
                logger.info(f"Reference data seeded: {seed_results}")
                return seed_results
                
        except Exception as e:
            logger.error(f"Failed to seed reference data: {e}")
            raise
    
    async def verify_database_health(self) -> Dict[str, Any]:
        """Verify database health after initialization.
        
        Проверяет состояние БД после инициализации.
        
        Returns:
            Health check results
        """
        if not self.db_adapter:
            raise RuntimeError("Database adapter not initialized")
        
        try:
            health_result = await self.db_adapter.health_check()
            logger.info("Database health check passed")
            return health_result
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            raise
    
    async def initialize_database(
        self, 
        run_migrations: bool = True,
        seed_data: bool = True,
        verify_health: bool = True
    ) -> Dict[str, Any]:
        """Initialize database with migrations and seed data.
        
        Полная инициализация БД с миграциями и seed данными.
        
        Args:
            run_migrations: Whether to run migrations
            seed_data: Whether to seed reference data
            verify_health: Whether to verify database health
            
        Returns:
            Initialization results
        """
        results = {
            "migrations": {"status": "skipped"},
            "seeding": {"status": "skipped"},
            "health_check": {"status": "skipped"},
            "success": False
        }
        
        try:
            logger.info("Starting database initialization...")
            
            # Connect to database
            await self.connect_database()
            
            # Run migrations
            if run_migrations:
                try:
                    self.run_migrations()
                    results["migrations"] = {"status": "success"}
                except Exception as e:
                    results["migrations"] = {"status": "failed", "error": str(e)}
                    logger.warning(f"Migration failed but continuing: {e}")
            
            # Seed reference data
            if seed_data:
                try:
                    seed_results = await self.seed_reference_data()
                    results["seeding"] = {"status": "success", "data": seed_results}
                except Exception as e:
                    results["seeding"] = {"status": "failed", "error": str(e)}
                    logger.warning(f"Seeding failed but continuing: {e}")
            
            # Verify health
            if verify_health:
                try:
                    health_results = await self.verify_database_health()
                    results["health_check"] = {"status": "success", "data": health_results}
                except Exception as e:
                    results["health_check"] = {"status": "failed", "error": str(e)}
                    logger.warning(f"Health check failed but continuing: {e}")
            
            results["success"] = True
            logger.info("Database initialization completed successfully")
            
            return results
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            results["error"] = str(e)
            raise
        
        finally:
            # Clean up database connection
            if self.db_adapter:
                try:
                    await self.db_adapter.close()
                except Exception as e:
                    logger.warning(f"Failed to close database connection: {e}")
    
    async def reset_database(self) -> None:
        """Reset database (drop and recreate all tables).
        
        ⚠️ ОПАСНО: Удаляет все данные в БД!
        """
        if not self.db_adapter:
            await self.connect_database()
        
        logger.warning("⚠️ RESETTING DATABASE - ALL DATA WILL BE LOST!")
        
        try:
            # Drop all tables
            await self.db_adapter.drop_tables()
            logger.info("All tables dropped")
            
            # Run migrations to recreate structure
            self.run_migrations()
            logger.info("Database structure recreated")
            
            # Seed reference data
            await self.seed_reference_data()
            logger.info("Reference data seeded")
            
            logger.info("Database reset completed")
            
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            raise


async def initialize_database_on_startup(
    run_migrations: bool = True,
    seed_data: bool = True,
    verify_health: bool = True
) -> Dict[str, Any]:
    """Initialize database on application startup.
    
    Функция для инициализации БД при запуске приложения.
    
    Args:
        run_migrations: Whether to run migrations
        seed_data: Whether to seed reference data  
        verify_health: Whether to verify database health
        
    Returns:
        Initialization results
    """
    initializer = DatabaseInitializer()
    return await initializer.initialize_database(
        run_migrations=run_migrations,
        seed_data=seed_data,
        verify_health=verify_health
    )


def cli_init_database():
    """CLI command to initialize database.
    
    Консольная команда для инициализации БД.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize database")
    parser.add_argument("--no-migrations", action="store_true", help="Skip migrations")
    parser.add_argument("--no-seed", action="store_true", help="Skip seeding")
    parser.add_argument("--no-health-check", action="store_true", help="Skip health check")
    parser.add_argument("--reset", action="store_true", help="Reset database (DANGEROUS!)")
    
    args = parser.parse_args()
    
    async def run_init():
        initializer = DatabaseInitializer()
        
        if args.reset:
            confirm = input("⚠️ This will DELETE ALL DATA. Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                await initializer.reset_database()
            else:
                print("Reset cancelled")
                return
        else:
            results = await initializer.initialize_database(
                run_migrations=not args.no_migrations,
                seed_data=not args.no_seed,
                verify_health=not args.no_health_check
            )
            print("Initialization results:", results)
    
    try:
        asyncio.run(run_init())
        print("✅ Database initialization completed")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_init_database() 