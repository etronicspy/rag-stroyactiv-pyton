"""Database abstractions and interfaces for multi-database support.

Абстракции и интерфейсы для поддержки мульти-БД архитектуры.
"""

from .interfaces import IVectorDatabase, IRelationalDatabase, ICacheDatabase
from .exceptions import DatabaseError, ConnectionError, QueryError, ConfigurationError
from .factories import DatabaseFactory, AIClientFactory, get_vector_database, get_ai_client

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