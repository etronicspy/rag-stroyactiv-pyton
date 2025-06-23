"""Alembic environment configuration for async PostgreSQL migrations.

Конфигурация Alembic для асинхронных миграций PostgreSQL.
"""

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import models for autogenerate
from core.database.adapters.postgresql_adapter import Base
from core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """Get database URL from settings or environment."""
    # Try to get from settings first
    try:
        db_config = settings.get_relational_db_config()
        return db_config.get("connection_string")
    except:
        # Fallback to environment variable
        return os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Use synchronous approach to avoid asyncio issues during startup
    from sqlalchemy import create_engine
    
    try:
        # Get database URL
        url = get_database_url()
        
        # Convert async URL to sync URL for migrations
        if url and "asyncpg" in url:
            url = url.replace("postgresql+asyncpg://", "postgresql://")
        
        # Create synchronous engine for migrations
        connectable = create_engine(url, poolclass=pool.NullPool)
        
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
            )

            with context.begin_transaction():
                context.run_migrations()
                
    except Exception as e:
        # Log error but don't crash startup
        print(f"Migration error (non-critical): {e}")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 