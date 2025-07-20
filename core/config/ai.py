"""
AI provider configuration factories and utilities.

This module provides configuration factories for all supported AI providers:
- OpenAI
- Azure OpenAI  
- HuggingFace
- Ollama
"""

import os
from typing import Any, Dict


def get_env_int(key: str, default: int) -> int:
    """Get integer value from environment variable."""
    return int(os.getenv(key, str(default)))


def get_env_str(key: str, default: str) -> str:
    """Get string value from environment variable."""
    return os.getenv(key, default)


class DefaultTimeouts:
    """Default timeout values for various operations."""
    DATABASE = get_env_int("DEFAULT_TIMEOUT_DATABASE", 30)
    AI_CLIENT = get_env_int("DEFAULT_TIMEOUT_AI_CLIENT", 30)
    CONNECTION_POOL = get_env_int("DEFAULT_TIMEOUT_CONNECTION_POOL", 30)
    REDIS = get_env_int("DEFAULT_TIMEOUT_REDIS", 10)
    SSH_TUNNEL = get_env_int("DEFAULT_TIMEOUT_SSH_TUNNEL", 30)


class ModelNames:
    """AI model names for different providers."""
    OPENAI_EMBEDDING = get_env_str("MODEL_NAME_OPENAI_EMBEDDING", "text-embedding-3-small")
    HUGGINGFACE_DEFAULT = get_env_str("MODEL_NAME_HUGGINGFACE_DEFAULT", "sentence-transformers/all-MiniLM-L6-v2")
    AZURE_API_VERSION = get_env_str("MODEL_NAME_AZURE_API_VERSION", "2023-05-15")


class BaseAIConfig:
    """Base configuration class with common AI provider settings."""
    
    @staticmethod
    def _get_base_config(
        timeout: int = None, 
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """Get base configuration common to all AI providers.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            **kwargs: Additional configuration parameters
            
        Returns:
            Base configuration dictionary
        """
        config = {
            "timeout": timeout or DefaultTimeouts.AI_CLIENT,
            "max_retries": max_retries,
        }
        config.update(kwargs)
        return config

class OpenAIConfig(BaseAIConfig):
    """Configuration factory for OpenAI services."""
    
    @staticmethod
    def get_openai_config(
        api_key: str, 
        model: str = None,
        timeout: int = None,
        max_retries: int = None
    ) -> Dict[str, Any]:
        """Get OpenAI configuration.
        
        Args:
            api_key: OpenAI API key
            model: Model name for embeddings
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            
        Returns:
            OpenAI configuration dictionary
        """
        base = OpenAIConfig._get_base_config(
            timeout=timeout,
            max_retries=max_retries
        )
        
        return {
            **base,
            "api_key": api_key,
            "model": model or ModelNames.OPENAI_EMBEDDING,
        }
    
    @staticmethod
    def get_azure_openai_config(
        api_key: str, 
        endpoint: str, 
        model: str,
        api_version: str = None,
        timeout: int = None,
        max_retries: int = None
    ) -> Dict[str, Any]:
        """Get Azure OpenAI configuration.
        
        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL
            model: Deployment model name
            api_version: Azure OpenAI API version
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            
        Returns:
            Azure OpenAI configuration dictionary
        """
        base = OpenAIConfig._get_base_config(
            timeout=timeout,
            max_retries=max_retries
        )
        
        return {
            **base,
            "api_key": api_key,
            "endpoint": endpoint,
            "model": model,
            "api_version": api_version or ModelNames.AZURE_API_VERSION,
        }

class HuggingFaceConfig(BaseAIConfig):
    """Configuration factory for HuggingFace services."""
    
    @staticmethod
    def get_huggingface_config(
        model: str = None, 
        device: str = "cpu",
        **kwargs
    ) -> Dict[str, Any]:
        """Get HuggingFace configuration.
        
        Args:
            model: HuggingFace model name
            device: Device to run on ('cpu' or 'cuda')
            **kwargs: Additional model configuration
            
        Returns:
            HuggingFace configuration dictionary
        """
        base = HuggingFaceConfig._get_base_config(**kwargs)
        
        return {
            **base,
            "model": model or ModelNames.HUGGINGFACE_DEFAULT,
            "device": device,
        }

class OllamaConfig(BaseAIConfig):
    """Configuration factory for Ollama services."""
    
    @staticmethod
    def get_ollama_config(
        url: str = "http://localhost:11434",
        model: str = "llama2",
        timeout: int = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get Ollama configuration.
        
        Args:
            url: Ollama server URL
            model: Ollama model name
            timeout: Request timeout in seconds
            **kwargs: Additional model configuration
            
        Returns:
            Ollama configuration dictionary
        """
        base = OllamaConfig._get_base_config(timeout=timeout, **kwargs)
        
        return {
            **base,
            "url": url,
            "model": model,
        }

class AIConfig:
    """Unified AI provider configuration factory."""
    
    # OpenAI providers
    get_openai_config = OpenAIConfig.get_openai_config
    get_azure_openai_config = OpenAIConfig.get_azure_openai_config
    
    # Other providers
    get_huggingface_config = HuggingFaceConfig.get_huggingface_config
    get_ollama_config = OllamaConfig.get_ollama_config 