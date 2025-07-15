"""Database dependency injection functions for FastAPI.

Функции внедрения зависимостей БД для FastAPI с кешированием.
"""

from functools import lru_cache
from typing import Any, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker

from core.database.interfaces import IVectorDatabase, IRelationalDatabase, ICacheDatabase
from core.repositories.interfaces import IMaterialsRepository
from core.repositories.hybrid_materials import HybridMaterialsRepository

# Глобальный кеш для engine чтобы избежать повторного создания
_db_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


@lru_cache(maxsize=1)
def get_vector_db_dependency() -> IVectorDatabase:
    """Dependency injection function for vector database.
    
    Используется как dependency в FastAPI роутах:
    
    @app.get("/endpoint")
    async def endpoint(vector_db: IVectorDatabase = Depends(get_vector_db_dependency)):
        ...
    
    Returns:
        Vector database client instance
    """
    from core.database.factories import DatabaseFactory
    return DatabaseFactory.create_vector_database()


@lru_cache(maxsize=1)
def get_ai_client_dependency() -> Any:
    """Dependency injection function for AI client.
    
    Используется как dependency в FastAPI роутах:
    
    @app.get("/endpoint")
    async def endpoint(ai_client = Depends(get_ai_client_dependency)):
        ...
    
    Returns:
        AI client instance
    """
    from core.database.factories import AIClientFactory
    return AIClientFactory.create_ai_client()


@lru_cache(maxsize=1)
def get_relational_db_dependency() -> IRelationalDatabase:
    """Dependency injection function for relational database.
    
    Используется как dependency в FastAPI роутах:
    
    @app.get("/endpoint")
    async def endpoint(rel_db: IRelationalDatabase = Depends(get_relational_db_dependency)):
        ...
    
    Returns:
        Relational database client instance
    """
    from core.database.factories import DatabaseFactory
    return DatabaseFactory.create_relational_database()


@lru_cache(maxsize=1)
def get_cache_db_dependency() -> ICacheDatabase:
    """Dependency injection function for cache database.
    
    Используется как dependency в FastAPI роутах:
    
    @app.get("/endpoint")
    async def endpoint(cache_db: ICacheDatabase = Depends(get_cache_db_dependency)):
        ...
    
    Returns:
        Cache database client instance
    """
    from core.database.factories import DatabaseFactory
    return DatabaseFactory.create_cache_database()


@lru_cache(maxsize=1)
def get_materials_repository() -> IMaterialsRepository:
    """Dependency injection function for materials repository.
    
    Используется как dependency в FastAPI роутах:
    
    @app.get("/endpoint")
    async def endpoint(repository: IMaterialsRepository = Depends(get_materials_repository)):
        ...
    
    Returns:
        Materials repository instance
    """
    vector_db = get_vector_db_dependency()
    relational_db = get_relational_db_dependency()
    return HybridMaterialsRepository(vector_db=vector_db, relational_db=relational_db)


@asynccontextmanager
async def get_db_session():
    """Get PostgreSQL database session as async context manager.
    
    Используется для получения SQLAlchemy AsyncSession:
    
    async with get_db_session() as session:
        repository = ProcessingRepository(session)
        ...
    
    Yields:
        AsyncSession: SQLAlchemy async session
        
    Raises:
        ConnectionError: If session creation fails
    """
    global _db_engine, _session_factory
    
    # Инициализируем engine и session_factory только один раз
    if _db_engine is None or _session_factory is None:
        from core.config.base import get_settings
        from sqlalchemy.ext.asyncio import create_async_engine
        
        settings = get_settings()
        
        # Создаем engine с кешированием
        _db_engine = create_async_engine(
            settings.POSTGRESQL_URL,
            echo=False,
            pool_size=5,
            max_overflow=10
        )
        
        _session_factory = async_sessionmaker(
            _db_engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False
        )
    
    # Создаем и возвращаем сессию
    async with _session_factory() as session:
        yield session


def clear_dependency_cache() -> None:
    """Clear all dependency caches.
    
    Полезно для тестирования или при изменении конфигурации.
    """
    get_vector_db_dependency.cache_clear()
    get_ai_client_dependency.cache_clear()
    get_relational_db_dependency.cache_clear()
    get_cache_db_dependency.cache_clear()
    get_materials_repository.cache_clear()
    
    # Also clear factory caches
    from core.database.factories import DatabaseFactory, AIClientFactory
    DatabaseFactory.clear_cache()
    AIClientFactory.clear_cache() 