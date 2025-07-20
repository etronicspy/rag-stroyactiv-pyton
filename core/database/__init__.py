"""Database abstractions and interfaces for multi-database support.

Абстракции и интерфейсы для поддержки мульти-БД архитектуры.
"""

from .exceptions import ConfigurationError, ConnectionError, DatabaseError, QueryError
from .factories import (
    AIClientFactory,
    DatabaseFactory,
    get_ai_client,
    get_vector_database,
)
from .interfaces import ICacheDatabase, IRelationalDatabase, IVectorDatabase

__all__ = [
    "IVectorDatabase",
    "IRelationalDatabase", 
    "ICacheDatabase",
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "ConfigurationError",
    "DatabaseFactory",
    "AIClientFactory",
    "get_vector_database",
    "get_ai_client"
] 