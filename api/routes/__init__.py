"""
Инициализация и экспорт всех роутеров API.
"""

from api.routes.health_unified import router as health_router
from api.routes.search_unified import router as search_router
from api.routes.materials import router as materials_router
from api.routes.prices import router as prices_router
from api.routes.reference import router as reference_router
from api.routes.tunnel import router as tunnel_router

__all__ = [
    "health_router",
    "search_router",
    "materials_router",
    "prices_router",
    "reference_router",
    "tunnel_router",
] 