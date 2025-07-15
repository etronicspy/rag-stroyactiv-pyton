"""
Application constants and default values.

This module centralizes all magic numbers and default values 
to improve code maintainability and consistency.
"""

from enum import IntEnum

class VectorSize(IntEnum):
    """Standard vector dimensions for different embedding models."""
    OPENAI_SMALL = 1536       # text-embedding-3-small
    OPENAI_LARGE = 3072       # text-embedding-3-large  
    OPENAI_ADA_002 = 1536     # text-embedding-ada-002 (legacy)
    HUGGINGFACE_MINI = 384    # sentence-transformers/all-MiniLM-L6-v2
    HUGGINGFACE_BASE = 768    # sentence-transformers/all-mpnet-base-v2

class DefaultTimeouts(IntEnum):
    """Default timeout values in seconds."""
    DATABASE = 30
    AI_CLIENT = 30
    SSH_TUNNEL = 30
    REDIS = 30
    HTTP_REQUEST = 30
    CONNECTION_POOL = 30

class DefaultPorts(IntEnum):
    """Default network ports."""
    POSTGRESQL = 5432
    REDIS = 6379
    SSH_TUNNEL_LOCAL = 5435
    QDRANT_LOCAL = 6333

class FileSizeLimits(IntEnum):
    """File size limits in bytes."""
    MAX_UPLOAD_MB = 50
    MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024  # 50MB
    MAX_CONFIG_FILE_MB = 100
    MAX_CONFIG_FILE_BYTES = MAX_CONFIG_FILE_MB * 1024 * 1024  # 100MB

class DatabaseNames:
    """Standard database and collection names."""
    POSTGRESQL_DB = "stbr_rag1"
    QDRANT_COLLECTION = "materials"
    WEAVIATE_CLASS = "Materials"
    PINECONE_INDEX = "materials"
    REDIS_KEY_PREFIX = "rag_materials:"

class ModelNames:
    """Default model names for AI providers."""
    OPENAI_EMBEDDING = "text-embedding-3-small"
    OPENAI_EMBEDDING_LEGACY = "text-embedding-ada-002"
    AZURE_API_VERSION = "2023-05-15"
    HUGGINGFACE_DEFAULT = "sentence-transformers/all-MiniLM-L6-v2"

class ConnectionPools:
    """Connection pool configuration defaults."""
    POSTGRESQL_POOL_SIZE = 10
    POSTGRESQL_MAX_OVERFLOW = 20
    REDIS_MAX_CONNECTIONS = 10
    BATCH_SIZE = 100
    MAX_CONCURRENT_UPLOADS = 5

class RateLimits:
    """Rate limiting defaults."""
    REQUESTS_PER_MINUTE = 60
    REQUESTS_PER_HOUR = 1000
    BURST_LIMIT = 10

class CacheSettings:
    """Cache configuration defaults."""
    REDIS_DEFAULT_TTL = 3600  # 1 hour in seconds
    HEALTH_CHECK_INTERVAL = 30  # seconds
    HEARTBEAT_INTERVAL = 60     # seconds

class SSHDefaults:
    """SSH tunnel default configuration."""
    REMOTE_HOST = "31.130.148.200"
    REMOTE_USER = "root"
    KEY_PATH = "~/.ssh/postgres_key"
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 5
    KEEP_ALIVE = 60


class DefaultBatchSizes(IntEnum):
    """Default batch sizes for various operations."""
    PARSER_BATCH = 10
    EMBEDDING_BATCH = 100
    DATABASE_BATCH = 500
    PROCESSING_BATCH = 50


class DefaultRetries(IntEnum):
    """Default retry attempt counts."""
    API_REQUESTS = 3
    DATABASE_OPERATIONS = 5
    NETWORK_REQUESTS = 3
    PARSER_OPERATIONS = 3


class DefaultConfidenceThresholds:
    """Default confidence thresholds for AI operations."""
    PARSER_CONFIDENCE = 0.85
    EMBEDDING_SIMILARITY = 0.7
    CLASSIFICATION_CONFIDENCE = 0.8
    VALIDATION_CONFIDENCE = 0.9


class ParserDefaults:
    """Default values specific to parser operations."""
    OPENAI_MODEL = "gpt-4o-mini"
    EMBEDDING_MODEL = "text-embedding-3-small"
    TEMPERATURE = 0.1
    MAX_TOKENS = 1000
    BATCH_SIZE = 10
    TIMEOUT = 30
    RETRY_ATTEMPTS = 3
    CONFIDENCE_THRESHOLD = 0.85
    CACHE_TTL = 3600  # 1 hour 


class ParserConstants:
    """Constants for parser configuration and defaults (legacy compatibility)."""
    OPENAI_MODEL = "gpt-4o-mini"
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536
    CONFIDENCE_THRESHOLD = 0.85
    BATCH_SIZE = 10
    TIMEOUT = 30
    RETRY_ATTEMPTS = 3
    CACHE_TTL = 3600 