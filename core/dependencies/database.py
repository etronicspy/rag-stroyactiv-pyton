"""Database dependency injection functions for FastAPI.

Функции внедрения зависимостей БД для FastAPI с кешированием.
"""

from functools import lru_cache
from typing import Any

from core.database.interfaces import IVectorDatabase
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


def clear_dependency_cache() -> None:
    """Clear all dependency caches.
    
    Полезно для тестирования или при изменении конфигурации.
    """
    get_vector_db_dependency.cache_clear()
    get_ai_client_dependency.cache_clear()
    
    # Also clear factory caches
    DatabaseFactory.clear_cache()
    AIClientFactory.clear_cache() 