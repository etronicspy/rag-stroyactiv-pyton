"""Dependency injection module for FastAPI.

Модуль для внедрения зависимостей в FastAPI с поддержкой @lru_cache.
"""

from .database import (
    get_vector_db_dependency, 
    get_ai_client_dependency, 
    get_relational_db_dependency,
    get_cache_db_dependency,
    clear_dependency_cache
)

__all__ = [
    "get_vector_db_dependency",
    "get_ai_client_dependency",
    "get_relational_db_dependency", 
    "get_cache_db_dependency",
    "clear_dependency_cache"
] 