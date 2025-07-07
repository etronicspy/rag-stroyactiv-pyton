"""
Configuration settings for AI-Only Material Parser

This module contains all configuration parameters for the AI-based material parsing system.
Uses environment variables for sensitive data like API keys.
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path


def load_env_from_project_root():
    """Load environment variables from project root .env.local file"""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env.local"
    
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not load .env.local: {e}")


@dataclass
class ParserConfig:
    """Configuration class for AI Material Parser"""
    
    # OpenAI API Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4o-mini"  # Cost-effective model for parsing
    openai_temperature: float = 0.1  # Low temperature for consistent results
    openai_max_tokens: int = 200  # Limited tokens for structured output
    openai_timeout: int = 30  # Timeout in seconds
    
    # Embeddings Configuration
    embeddings_model: str = "text-embedding-3-small"  # Cost-effective embeddings model
    embeddings_enabled: bool = True  # Enable/disable embeddings generation
    embeddings_dimensions: int = 1536  # Dimensions for embeddings (default for text-embedding-3-small)
    
    # Parser Behavior Settings
    confidence_threshold: float = 0.8  # Minimum confidence for results
    enable_validation: bool = True  # Validate parsed results
    enable_caching: bool = True  # Cache AI responses
    max_retries: int = 3  # Max retry attempts for API calls
    
    # Units Configuration
    default_unit: str = "шт"  # Default unit when parsing fails
    supported_metric_units: List[str] = None  # Will be set from units_config
    
    # Logging Configuration
    enable_debug_logging: bool = False
    log_ai_requests: bool = True
    log_level: str = "INFO"
    
    # Price Calculation Settings
    default_price_coefficient: float = 1.0
    min_price_coefficient: float = 0.001  # Minimum allowed coefficient
    max_price_coefficient: float = 10000.0  # Maximum allowed coefficient
    
    # Integration Settings
    integration_mode: bool = False  # Set to True when integrated with main project
    use_main_project_config: bool = False  # Use main project's OpenAI config
    
    def __post_init__(self):
        """Post-initialization validation"""
        # Load environment variables from project root .env.local file
        load_env_from_project_root()
        
        # Reload OpenAI API key after loading .env.local
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        if self.supported_metric_units is None:
            self.supported_metric_units = ["кг", "м3", "м2", "м", "л", "шт"]
        
        # Validate OpenAI API key (only if not testing mode)
        if (not self.openai_api_key and 
            not self.use_main_project_config and 
            os.getenv("PARSER_TESTING_MODE") != "true"):
            import warnings
            warnings.warn(
                "OpenAI API key not found. Parser will work in testing mode. "
                "Set OPENAI_API_KEY environment variable for full functionality."
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "openai_model": self.openai_model,
            "openai_temperature": self.openai_temperature,
            "openai_max_tokens": self.openai_max_tokens,
            "openai_timeout": self.openai_timeout,
            "confidence_threshold": self.confidence_threshold,
            "enable_validation": self.enable_validation,
            "enable_caching": self.enable_caching,
            "max_retries": self.max_retries,
            "default_unit": self.default_unit,
            "supported_metric_units": self.supported_metric_units,
            "enable_debug_logging": self.enable_debug_logging,
            "log_ai_requests": self.log_ai_requests,
            "log_level": self.log_level,
            "default_price_coefficient": self.default_price_coefficient,
            "min_price_coefficient": self.min_price_coefficient,
            "max_price_coefficient": self.max_price_coefficient,
            "integration_mode": self.integration_mode,
            "use_main_project_config": self.use_main_project_config
        }


# Default configuration instance
DEFAULT_CONFIG = ParserConfig()

# Environment-specific configurations
DEVELOPMENT_CONFIG = ParserConfig(
    enable_debug_logging=True,
    log_ai_requests=True,
    enable_caching=True,
    max_retries=2
)

PRODUCTION_CONFIG = ParserConfig(
    enable_debug_logging=False,
    log_ai_requests=False,
    enable_caching=True,
    max_retries=3,
    openai_timeout=60
)

# Integration configuration for main project
INTEGRATION_CONFIG = ParserConfig(
    integration_mode=True,
    use_main_project_config=True,
    enable_debug_logging=False,
    log_ai_requests=True,
    enable_caching=True
)


def get_config(env: str = "default") -> ParserConfig:
    """Get configuration based on environment"""
    configs = {
        "default": DEFAULT_CONFIG,
        "development": DEVELOPMENT_CONFIG,
        "production": PRODUCTION_CONFIG,
        "integration": INTEGRATION_CONFIG
    }
    
    return configs.get(env, DEFAULT_CONFIG)


def validate_config(config: ParserConfig) -> bool:
    """Validate configuration settings"""
    try:
        # Check required fields
        if not config.openai_model:
            raise ValueError("OpenAI model is required")
        
        # Check numeric ranges
        if not (0.0 <= config.openai_temperature <= 2.0):
            raise ValueError("OpenAI temperature must be between 0.0 and 2.0")
        
        if not (0.0 <= config.confidence_threshold <= 1.0):
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        
        if config.openai_max_tokens <= 0:
            raise ValueError("OpenAI max tokens must be positive")
        
        if config.openai_timeout <= 0:
            raise ValueError("OpenAI timeout must be positive")
        
        # Check price coefficient ranges
        if config.min_price_coefficient >= config.max_price_coefficient:
            raise ValueError("Min price coefficient must be less than max")
        
        return True
    
    except Exception as e:
        print(f"Configuration validation error: {e}")
        return False 