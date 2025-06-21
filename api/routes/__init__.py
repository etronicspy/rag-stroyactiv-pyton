"""
Инициализация и экспорт всех роутеров API.
"""

from api.routes.health import router as health_router
from api.routes.search import router as search_router
from api.routes.materials import router as materials_router
from api.routes.prices import router as prices_router
from api.routes.reference import router as reference_router
from api.routes.advanced_search import router as advanced_search_router
from api.routes.tunnel import router as tunnel_router

__all__ = [
    "health_router",
    "search_router",
    "materials_router",
    "prices_router",
    "reference_router",
    "advanced_search_router",
    "tunnel_router",
] 