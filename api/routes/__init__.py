"""
Инициализация и экспорт всех роутеров API.
"""

from api.routes.materials import router as materials_router
from api.routes.prices import router as prices_router
from api.routes.reference import router as reference_router
from api.routes.tunnel import router as tunnel_router
from api.routes import health_unified, search_unified, enhanced_processing

__all__ = [
    "materials_router",
    "prices_router",
    "reference_router",
    "tunnel_router",
    "health_unified",
    "search_unified",
    "enhanced_processing",
]