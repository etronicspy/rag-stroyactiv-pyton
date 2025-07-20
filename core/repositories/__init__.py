"""Repository abstractions and implementations for multi-database support.

Абстракции и реализации репозиториев для мульти-БД архитектуры.
"""

from .base import BaseRepository
from .cached_materials import CachedMaterialsRepository
from .hybrid_materials import HybridMaterialsRepository
from .interfaces import ICategoriesRepository, IMaterialsRepository, IUnitsRepository
from .redis_materials import RedisMaterialsRepository

__all__ = [
    "IMaterialsRepository",
    "ICategoriesRepository", 
    "IUnitsRepository",
    "BaseRepository",
    "RedisMaterialsRepository",
    "HybridMaterialsRepository",
    "CachedMaterialsRepository"
] 