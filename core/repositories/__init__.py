"""Repository abstractions and implementations for multi-database support.

Абстракции и реализации репозиториев для мульти-БД архитектуры.
"""

from .interfaces import IMaterialsRepository, ICategoriesRepository, IUnitsRepository
from .base import BaseRepository

__all__ = [
    "IMaterialsRepository",
    "ICategoriesRepository", 
    "IUnitsRepository",
    "BaseRepository"
] 