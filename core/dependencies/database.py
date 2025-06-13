"""Database dependency injection functions for FastAPI.

Функции внедрения зависимостей БД для FastAPI с кешированием.
"""

from functools import lru_cache
from typing import Any

from core.database.interfaces import IVectorDatabase, IRelationalDatabase, ICacheDatabase
from core.database.factories import DatabaseFactory, AIClientFactory


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
    return AIClientFactory.create_ai_client()


@lru_cache(maxsize=1)
def get_relational_db_dependency() -> IRelationalDatabase:
    """Dependency injection function for relational database.
    
    Используется как dependency в FastAPI роутах:
    
    @app.get("/endpoint")
    async def endpoint(rel_db: IRelationalDatabase = Depends(get_relational_db_dependency)):
        ...
    
    Returns:
        Relational database client instance (real or mock)
    """
    return DatabaseFactory.create_relational_database()


@lru_cache(maxsize=1)
def get_cache_db_dependency() -> ICacheDatabase:
    """Dependency injection function for cache database.
    
    Используется как dependency в FastAPI роутах:
    
    @app.get("/endpoint")
    async def endpoint(cache_db: ICacheDatabase = Depends(get_cache_db_dependency)):
        ...
    
    Returns:
        Cache database client instance (real or mock)
    """
    return DatabaseFactory.create_cache_database()


def clear_dependency_cache() -> None:
    """Clear all dependency caches.
    
    Полезно для тестирования или при изменении конфигурации.
    """
    get_vector_db_dependency.cache_clear()
    get_ai_client_dependency.cache_clear()
    get_relational_db_dependency.cache_clear()
    get_cache_db_dependency.cache_clear()
    
    # Also clear factory caches
    DatabaseFactory.clear_cache()
    AIClientFactory.clear_cache() 