"""Repository abstractions and implementations for multi-database support.

Абстракции и реализации репозиториев для мульти-БД архитектуры.
"""

from .interfaces import IMaterialsRepository, ICategoriesRepository, IUnitsRepository
from .base import BaseRepository
from .redis_materials import RedisMaterialsRepository
from .hybrid_materials import HybridMaterialsRepository
from .cached_materials import CachedMaterialsRepository

__all__ = [
    "IMaterialsRepository",
    "ICategoriesRepository", 
    "IUnitsRepository",
    "BaseRepository",
    "RedisMaterialsRepository",
    "HybridMaterialsRepository",
    "CachedMaterialsRepository"
] 