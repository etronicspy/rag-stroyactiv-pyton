"""Dependency injection module for FastAPI.

Модуль для внедрения зависимостей в FastAPI с поддержкой @lru_cache.
"""

from .database import get_vector_db_dependency, get_ai_client_dependency, clear_dependency_cache

__all__ = [
    "get_vector_db_dependency",
    "get_ai_client_dependency",
    "clear_dependency_cache"
] 