from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field, ConfigDict
from enum import Enum

class DatabaseType(str, Enum):
    """Supported database types"""
    QDRANT_CLOUD = "qdrant_cloud"
    QDRANT_LOCAL = "qdrant_local"
    WEAVIATE = "weaviate"
    PINECONE = "pinecone"

class AIProvider(str, Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"

class DatabaseConfig:
    """Database configuration factory"""
    
    @staticmethod
    def get_qdrant_config(url: str, api_key: str, collection_name: str = "materials", vector_size: int = 1536) -> Dict[str, Any]:
        return {
            "url": url,
            "api_key": api_key,
            "collection_name": collection_name,
            "vector_size": vector_size,
            "distance": "cosine",
            "timeout": 30
        }

class AIConfig:
    """AI provider configuration factory"""
    
    @staticmethod
    def get_openai_config(api_key: str, model: str = "text-embedding-ada-002") -> Dict[str, Any]:
        return {
            "api_key": api_key,
            "model": model,
            "max_retries": 3,
            "timeout": 30
        }
    
    @staticmethod
    def get_azure_openai_config(api_key: str, endpoint: str, model: str) -> Dict[str, Any]:
        return {
            "api_key": api_key,
            "endpoint": endpoint,
            "model": model,
            "api_version": "2023-05-15"
        }
    
    @staticmethod
    def get_huggingface_config(model: str = "sentence-transformers/all-MiniLM-L6-v2") -> Dict[str, Any]:
        return {
            "model": model,
            "device": "cpu"  # или "cuda" для GPU
        }

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "RAG Construction Materials API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    
    # === DATABASE CONFIGURATION ===
    # Vector Database
    DATABASE_TYPE: DatabaseType = Field(default=DatabaseType.QDRANT_CLOUD)
    
    # Qdrant settings
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION_NAME: str = "materials"
    QDRANT_VECTOR_SIZE: int = 1536
    QDRANT_TIMEOUT: int = 30
    
    # Alternative vector databases (для будущего использования)
    WEAVIATE_URL: Optional[str] = None
    WEAVIATE_API_KEY: Optional[str] = None
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    
    # === AI CONFIGURATION ===
    AI_PROVIDER: AIProvider = Field(default=AIProvider.OPENAI)
    
    # OpenAI settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "text-embedding-3-small"  # 1536 dimensions
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_TIMEOUT: int = 30
    
    # Azure OpenAI settings (для будущего использования)
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_MODEL: Optional[str] = None
    
    # HuggingFace settings (для будущего использования)
    HUGGINGFACE_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    HUGGINGFACE_DEVICE: str = "cpu"
    
    # Ollama settings (для будущего использования)  
    OLLAMA_URL: Optional[str] = None
    OLLAMA_MODEL: Optional[str] = None
    
    # === PERFORMANCE SETTINGS ===
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    BATCH_SIZE: int = 100
    MAX_CONCURRENT_UPLOADS: int = 5
    
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env.local"
    )
    
    # === CONFIGURATION FACTORIES ===
    def get_vector_db_config(self) -> Dict[str, Any]:
        """Get current vector database configuration"""
        if self.DATABASE_TYPE == DatabaseType.QDRANT_CLOUD or self.DATABASE_TYPE == DatabaseType.QDRANT_LOCAL:
            return DatabaseConfig.get_qdrant_config(
                url=self.QDRANT_URL,
                api_key=self.QDRANT_API_KEY,
                collection_name=self.QDRANT_COLLECTION_NAME,
                vector_size=self.QDRANT_VECTOR_SIZE
            )
        # Здесь можно добавить другие типы БД
        raise ValueError(f"Unsupported database type: {self.DATABASE_TYPE}")
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get current AI provider configuration"""
        if self.AI_PROVIDER == AIProvider.OPENAI:
            return AIConfig.get_openai_config(
                api_key=self.OPENAI_API_KEY,
                model=self.OPENAI_MODEL
            )
        elif self.AI_PROVIDER == AIProvider.AZURE_OPENAI:
            if not all([self.AZURE_OPENAI_API_KEY, self.AZURE_OPENAI_ENDPOINT, self.AZURE_OPENAI_MODEL]):
                raise ValueError("Azure OpenAI configuration is incomplete")
            return AIConfig.get_azure_openai_config(
                api_key=self.AZURE_OPENAI_API_KEY,
                endpoint=self.AZURE_OPENAI_ENDPOINT,
                model=self.AZURE_OPENAI_MODEL
            )
        elif self.AI_PROVIDER == AIProvider.HUGGINGFACE:
            return AIConfig.get_huggingface_config(model=self.HUGGINGFACE_MODEL)
        
        raise ValueError(f"Unsupported AI provider: {self.AI_PROVIDER}")
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_testing(self) -> bool:
        """Check if running in test environment"""
        return self.ENVIRONMENT.lower() in ["test", "testing"]

# Global settings instance
settings = Settings()

# === CLIENT FACTORIES ===
def get_vector_db_client():
    """Factory function to get vector database client"""
    config = settings.get_vector_db_config()
    
    if settings.DATABASE_TYPE in [DatabaseType.QDRANT_CLOUD, DatabaseType.QDRANT_LOCAL]:
        from qdrant_client import QdrantClient
        return QdrantClient(
            url=config["url"],
            api_key=config["api_key"],
            timeout=config["timeout"]
        )
    
    raise ValueError(f"Unsupported database type: {settings.DATABASE_TYPE}")

def get_ai_client():
    """Factory function to get AI client"""
    config = settings.get_ai_config()
    
    if settings.AI_PROVIDER == AIProvider.OPENAI:
        import openai
        return openai.AsyncOpenAI(
            api_key=config["api_key"],
            max_retries=config["max_retries"],
            timeout=config["timeout"]
        )
    elif settings.AI_PROVIDER == AIProvider.HUGGINGFACE:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(config["model"])
    
    raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}") 