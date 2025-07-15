"""
Parser Configuration Module

This module provides comprehensive configuration management for parser operations,
including AI model settings, performance tuning, validation rules, and debugging options.
"""

from typing import Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

from core.config.constants import (
    DefaultTimeouts,
    DefaultRetries,
    DefaultBatchSizes,
    DefaultConfidenceThresholds
)

print("DEBUG: core/config/parsers.py loaded")


class ParserConstants:
    """Constants specific to parser operations."""
    
    # AI Model defaults
    DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
    DEFAULT_EMBEDDING_DIMENSIONS = 1536
    
    # Parsing defaults
    DEFAULT_BATCH_SIZE = 10
    MAX_BATCH_SIZE = 50
    MIN_BATCH_SIZE = 1
    
    # Confidence thresholds
    DEFAULT_CONFIDENCE_THRESHOLD = 0.85
    MIN_CONFIDENCE_THRESHOLD = 0.1
    MAX_CONFIDENCE_THRESHOLD = 1.0
    
    # Timeout settings
    DEFAULT_PARSER_TIMEOUT = 30
    DEFAULT_AI_REQUEST_TIMEOUT = 45
    DEFAULT_BATCH_TIMEOUT = 300
    
    # Retry settings
    DEFAULT_RETRY_ATTEMPTS = 3
    MAX_RETRY_ATTEMPTS = 10
    
    # Cache settings
    DEFAULT_CACHE_TTL = 3600  # 1 hour
    DEFAULT_EMBEDDING_CACHE_TTL = 86400  # 24 hours


class ParserModelConfig(BaseModel):
    """Configuration for AI models used in parsing."""
    
    openai_model: str = Field(
        default=ParserConstants.DEFAULT_OPENAI_MODEL,
        description="OpenAI model for parsing operations"
    )
    
    embedding_model: str = Field(
        default=ParserConstants.DEFAULT_EMBEDDING_MODEL,
        description="Model for generating embeddings"
    )
    
    embedding_dimensions: int = Field(
        default=ParserConstants.DEFAULT_EMBEDDING_DIMENSIONS,
        description="Dimensions for embedding vectors"
    )
    
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for AI model responses"
    )
    
    max_tokens: Optional[int] = Field(
        default=1000,
        ge=1,
        le=8000,
        description="Maximum tokens for AI responses"
    )
    
    @field_validator('embedding_dimensions')
    @classmethod
    def validate_embedding_dimensions(cls, v):
        """Validate embedding dimensions."""
        valid_dimensions = [1536, 3072]
        if v not in valid_dimensions:
            raise ValueError(f"Embedding dimensions must be one of {valid_dimensions}")
        return v


class ParserPerformanceConfig(BaseModel):
    """Configuration for parser performance settings."""
    
    batch_size: int = Field(
        default=ParserConstants.DEFAULT_BATCH_SIZE,
        description="Default batch size for processing"
    )
    
    max_batch_size: int = Field(
        default=ParserConstants.MAX_BATCH_SIZE,
        description="Maximum allowed batch size"
    )
    
    timeout: int = Field(
        default=ParserConstants.DEFAULT_PARSER_TIMEOUT,
        description="Default timeout for parsing operations"
    )
    
    ai_request_timeout: int = Field(
        default=ParserConstants.DEFAULT_AI_REQUEST_TIMEOUT,
        description="Timeout for AI API requests"
    )
    
    batch_timeout: int = Field(
        default=ParserConstants.DEFAULT_BATCH_TIMEOUT,
        description="Timeout for batch processing"
    )
    
    retry_attempts: int = Field(
        default=ParserConstants.DEFAULT_RETRY_ATTEMPTS,
        description="Number of retry attempts for failed requests"
    )
    
    max_concurrent_requests: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent AI requests"
    )
    
    @field_validator('batch_size', 'max_batch_size')
    @classmethod
    def validate_batch_size(cls, v):
        """Validate batch size settings."""
        if v < ParserConstants.MIN_BATCH_SIZE:
            raise ValueError(f"Batch size must be at least {ParserConstants.MIN_BATCH_SIZE}")
        if v > ParserConstants.MAX_BATCH_SIZE:
            raise ValueError(f"Batch size cannot exceed {ParserConstants.MAX_BATCH_SIZE}")
        return v


class ParserValidationConfig(BaseModel):
    """Configuration for parser validation settings."""
    
    confidence_threshold: float = Field(
        default=ParserConstants.DEFAULT_CONFIDENCE_THRESHOLD,
        description="Minimum confidence threshold for accepting parse results"
    )
    
    enable_validation: bool = Field(
        default=True,
        description="Enable validation of parse results"
    )
    
    enable_strict_validation: bool = Field(
        default=False,
        description="Enable strict validation mode"
    )
    
    require_units: bool = Field(
        default=True,
        description="Require unit extraction for material parsing"
    )
    
    require_coefficients: bool = Field(
        default=False,
        description="Require coefficient extraction"
    )
    
    validate_colors: bool = Field(
        default=True,
        description="Enable color validation"
    )
    
    @field_validator('confidence_threshold')
    @classmethod
    def validate_confidence_threshold(cls, v):
        """Validate confidence threshold."""
        if v < ParserConstants.MIN_CONFIDENCE_THRESHOLD:
            raise ValueError(f"Confidence threshold must be at least {ParserConstants.MIN_CONFIDENCE_THRESHOLD}")
        if v > ParserConstants.MAX_CONFIDENCE_THRESHOLD:
            raise ValueError(f"Confidence threshold cannot exceed {ParserConstants.MAX_CONFIDENCE_THRESHOLD}")
        return v


class ParserCacheConfig(BaseModel):
    """Configuration for parser caching settings."""
    
    enable_caching: bool = Field(
        default=True,
        description="Enable caching for parser operations"
    )
    
    cache_ttl: int = Field(
        default=ParserConstants.DEFAULT_CACHE_TTL,
        description="Cache time-to-live in seconds"
    )
    
    embedding_cache_ttl: int = Field(
        default=ParserConstants.DEFAULT_EMBEDDING_CACHE_TTL,
        description="Embedding cache time-to-live in seconds"
    )
    
    enable_persistent_cache: bool = Field(
        default=False,
        description="Enable persistent cache storage"
    )
    
    cache_size_limit: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Maximum number of cached items"
    )


class ParserDebugConfig(BaseModel):
    """Configuration for parser debugging and logging."""
    
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode for detailed logging"
    )
    
    log_ai_requests: bool = Field(
        default=True,
        description="Log AI API requests and responses"
    )
    
    log_parse_results: bool = Field(
        default=True,
        description="Log parsing results"
    )
    
    save_debug_files: bool = Field(
        default=False,
        description="Save debug files for analysis"
    )
    
    debug_file_path: str = Field(
        default="debug/parser",
        description="Path for debug files"
    )


class ParserConfig(BaseSettings):
    """
    Comprehensive parser configuration with environment variable support.
    
    This configuration integrates with the main project configuration system
    and provides all settings needed for parser operations.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="PARSER_",
        case_sensitive=False,
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # API Keys (from main config)
    openai_api_key: str = Field(
        description="OpenAI API key for AI operations"
    )
    
    # Model configuration
    models: ParserModelConfig = Field(
        default_factory=ParserModelConfig,
        description="AI model configuration"
    )
    
    # Performance configuration
    performance: ParserPerformanceConfig = Field(
        default_factory=ParserPerformanceConfig,
        description="Performance and timeout settings"
    )
    
    # Validation configuration
    validation: ParserValidationConfig = Field(
        default_factory=ParserValidationConfig,
        description="Validation settings"
    )
    
    # Cache configuration
    cache: ParserCacheConfig = Field(
        default_factory=ParserCacheConfig,
        description="Cache configuration"
    )
    
    # Debug configuration
    debug: ParserDebugConfig = Field(
        default_factory=ParserDebugConfig,
        description="Debug and logging configuration"
    )
    
    # Integration settings
    integration_mode: bool = Field(
        default=True,
        description="Enable integration with main project systems"
    )
    
    use_main_project_config: bool = Field(
        default=True,
        description="Use main project configuration for shared settings"
    )
    
    # Environment-specific settings
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Current environment"
    )
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_openai_api_key(cls, v):
        """Validate OpenAI API key."""
        if not v or not v.strip():
            raise ValueError("OpenAI API key is required")
        if not v.startswith('sk-'):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v.strip()
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_environments = ["development", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of {valid_environments}")
        return v
    
    def get_timeout_config(self) -> Dict[str, int]:
        """Get timeout configuration dictionary."""
        return {
            'parser_timeout': self.performance.timeout,
            'ai_request_timeout': self.performance.ai_request_timeout,
            'batch_timeout': self.performance.batch_timeout
        }
    
    def get_retry_config(self) -> Dict[str, int]:
        """Get retry configuration dictionary."""
        return {
            'max_retries': self.performance.retry_attempts,
            'backoff_factor': 2.0,
            'max_backoff': 60.0
        }
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration dictionary."""
        return {
            'confidence_threshold': self.validation.confidence_threshold,
            'enable_validation': self.validation.enable_validation,
            'strict_mode': self.validation.enable_strict_validation,
            'require_units': self.validation.require_units,
            'require_coefficients': self.validation.require_coefficients,
            'validate_colors': self.validation.validate_colors
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug.debug_mode or self.environment == "development"


@lru_cache(maxsize=1)
def get_parser_config() -> ParserConfig:
    """
    Get cached parser configuration instance.
    
    Returns:
        ParserConfig: Cached configuration instance
    """
    return ParserConfig()


def get_parser_settings() -> ParserConfig:
    """
    Get parser settings with proper error handling.
    
    Returns:
        ParserConfig: Parser configuration instance
        
    Raises:
        ValueError: If configuration is invalid
        OSError: If environment files cannot be read
    """
    try:
        return get_parser_config()
    except Exception as e:
        raise ValueError(f"Failed to load parser configuration: {e}")


# Export constants for use in other modules
__all__ = [
    'ParserConstants',
    'ParserModelConfig',
    'ParserPerformanceConfig',
    'ParserValidationConfig',
    'ParserCacheConfig',
    'ParserDebugConfig',
    'ParserConfig',
    'get_parser_config',
    'get_parser_settings'
] 