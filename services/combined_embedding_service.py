"""
Combined Embedding Service for RAG Construction Materials API

Генерирует комбинированные embeddings для материалов из комбинации:
name + normalized_unit + normalized_color

Согласно диаграмме интеграции ЭТАП 5.
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from functools import lru_cache

import openai
from openai import AsyncOpenAI

from core.config.base import Settings
from core.schemas.pipeline_models import (
    CombinedEmbeddingRequest,
    CombinedEmbeddingResult,
    BatchEmbeddingRequest,
    BatchEmbeddingResponse,
    EmbeddingCacheEntry,
    CombinedEmbeddingConfig
)


logger = logging.getLogger(__name__)


class CombinedEmbeddingService:
    """
    Service for generating combined material embeddings.
    
    Creates material_embedding from: name + normalized_unit + normalized_color
    Used for vector search in materials reference database.
    """
    
    def __init__(self, config: Optional[CombinedEmbeddingConfig] = None):
        """Initialize Combined Embedding Service"""
        self.config = config or CombinedEmbeddingConfig()
        self.ai_settings = Settings()
        self._client: Optional[AsyncOpenAI] = None
        
        # In-memory cache for embeddings
        self.embedding_cache: Dict[str, EmbeddingCacheEntry] = {}
        
        logger.info("✅ Combined Embedding Service initialized successfully")

    @property
    def client(self) -> AsyncOpenAI:
        """Get or create OpenAI async client"""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.ai_settings.OPENAI_API_KEY,
                timeout=self.ai_settings.OPENAI_TIMEOUT,
                max_retries=self.ai_settings.OPENAI_MAX_RETRIES
            )
        return self._client

    def _generate_material_key(self, name: str, normalized_unit: str, normalized_color: Optional[str]) -> str:
        """Generate unique cache key for material"""
        # Normalize the combination for consistent caching
        color_part = normalized_color or "NO_COLOR"
        material_text = f"{name.strip()} | {normalized_unit.strip()} | {color_part}"
        
        # Create hash for cache key
        return hashlib.md5(material_text.encode('utf-8')).hexdigest()

    def _combine_material_text(self, name: str, normalized_unit: str, normalized_color: Optional[str]) -> str:
        """
        Combine material components into text for embedding generation.
        
        Formats according to diagram: name + normalized_unit + normalized_color
        """
        # Handle None/null color case
        color_part = normalized_color if normalized_color else "без_цвета"
        
        # Generate combined text based on configuration
        if "{name}" in self.config.text_format:
            material_text = self.config.text_format.format(
                name=name,
                normalized_unit=normalized_unit,
                normalized_color=normalized_color or "без_цвета"
            )
        else:
            # Fallback format
            material_text = f"{name} {normalized_unit} {normalized_color or 'без_цвета'}"
        
        logger.debug(f"Combined material text: '{material_text}'")
        return material_text

    def _get_cached_embedding(self, cache_key: str) -> Optional[List[float]]:
        """Get embedding from cache if available and not expired"""
        if not self.config.cache_enabled:
            return None
        
        if cache_key not in self.embedding_cache:
            return None
        
        cache_entry = self.embedding_cache[cache_key]
        
        # Check expiration (convert seconds to timedelta)
        if cache_entry.created_at + timedelta(seconds=self.config.cache_ttl_seconds) < datetime.utcnow():
            del self.embedding_cache[cache_key]
            return None
        
        # Update access statistics
        cache_entry.access_count += 1
        cache_entry.last_accessed = datetime.utcnow()
        
        return cache_entry.embedding
    
    def _cache_embedding(self, cache_key: str, embedding: List[float]) -> None:
        """Cache embedding with LRU eviction"""
        if not self.config.cache_enabled:
            return
        
        # LRU eviction if cache is full
        if len(self.embedding_cache) >= self.config.max_cache_size:
            # Remove oldest entries (by created_at)
            oldest_keys = sorted(
                self.embedding_cache.keys(),
                key=lambda k: self.embedding_cache[k].created_at
            )[:self.config.max_cache_size // 4]  # Remove 25%
            
            for old_key in oldest_keys:
                del self.embedding_cache[old_key]
        
        # Cache new embedding
        cache_entry = EmbeddingCacheEntry(
            embedding=embedding,
            created_at=datetime.utcnow(),
            access_count=1,
            last_accessed=datetime.utcnow()
        )
        self.embedding_cache[cache_key] = cache_entry
        
        logger.debug(f"Cached embedding for {cache_key}, cache size: {len(self.embedding_cache)}")
    
    def _clear_cache_entry(self, cache_key: str) -> None:
        """Remove specific cache entry"""
        if cache_key in self.embedding_cache:
            del self.embedding_cache[cache_key]

    async def generate_material_embedding(
        self, 
        material_name: str, 
        normalized_unit: str, 
        normalized_color: Optional[str] = None
    ) -> CombinedEmbeddingResult:
        """
        Generate combined material embedding from name + unit + color.
        
        Args:
            material_name: Name of the material
            normalized_unit: Normalized unit of measurement  
            normalized_color: Normalized color (None for colorless materials)
            
        Returns:
            CombinedEmbeddingResult with embedding and metadata
        """
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_material_key(material_name, normalized_unit, normalized_color)
            
            # Check cache first
            cached_embedding = self._get_cached_embedding(cache_key)
            if cached_embedding is not None:
                processing_time = time.time() - start_time
                material_text = self._combine_material_text(material_name, normalized_unit, normalized_color)
                
                logger.info(f"✅ Cache hit for material embedding: {material_name}")
                return CombinedEmbeddingResult(
                    material_embedding=cached_embedding,
                    embedding_text=material_text,
                    processing_time=processing_time,
                    success=True
                )
            
            # Generate combined text
            material_text = self._combine_material_text(material_name, normalized_unit, normalized_color)
            
            # Generate embedding via OpenAI
            logger.debug(f"🧠 Generating embedding for: '{material_text}'")
            
            response = await self.client.embeddings.create(
                model=self.config.embedding_model,
                input=material_text,
                encoding_format="float"
            )
            
            if not response.data:
                raise ValueError("No embedding data received from OpenAI")
            
            embedding = response.data[0].embedding
            
            # Validate embedding dimensions
            if len(embedding) != 1536:
                logger.warning(f"Unexpected embedding dimensions: {len(embedding)}, expected 1536")
            
            # Cache the embedding
            self._cache_embedding(cache_key, embedding)
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Generated material embedding: {material_name} ({len(embedding)}dim, {processing_time:.3f}s)")
            
            return CombinedEmbeddingResult(
                material_embedding=embedding,
                embedding_text=material_text,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            material_text = self._combine_material_text(material_name, normalized_unit, normalized_color)
            
            logger.error(f"❌ Failed to generate embedding for {material_name}: {str(e)}")
            
            return CombinedEmbeddingResult(
                material_embedding=[],
                embedding_text=material_text,
                processing_time=processing_time,
                success=False
            )

    async def generate_batch_embeddings(
        self, 
        materials: List[CombinedEmbeddingRequest],
        batch_size: Optional[int] = None
    ) -> BatchEmbeddingResponse:
        """
        Generate embeddings for multiple materials in parallel.
        
        Args:
            materials: List of material requests
            batch_size: Number of materials to process in parallel
            
        Returns:
            BatchEmbeddingResponse with all results and statistics
        """
        start_time = time.time()
        actual_batch_size = batch_size or self.config.batch_size
        
        logger.info(f"🔄 Starting batch embedding generation for {len(materials)} materials (batch_size={actual_batch_size})")
        
        results: List[CombinedEmbeddingResult] = []
        
        # Process materials in batches to avoid overwhelming the API
        for i in range(0, len(materials), actual_batch_size):
            batch = materials[i:i + actual_batch_size]
            
            # Create tasks for parallel processing
            tasks = [
                self.generate_material_embedding(
                    material.material_name,
                    material.normalized_unit,
                    material.normalized_color
                )
                for material in batch
            ]
            
            # Execute batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Exception in batch processing for {batch[j].material_name}: {str(result)}")
                    # Create failed result
                    material_text = self._combine_material_text(
                        batch[j].material_name,
                        batch[j].normalized_unit,
                        batch[j].normalized_color
                    )
                    failed_result = CombinedEmbeddingResult(
                        material_embedding=[],
                        embedding_text=material_text,
                        processing_time=0.0,
                        success=False
                    )
                    results.append(failed_result)
                else:
                    results.append(result)
            
            logger.debug(f"Completed batch {i//actual_batch_size + 1}/{(len(materials)-1)//actual_batch_size + 1}")
        
        # Calculate statistics
        total_processing_time = time.time() - start_time
        successful_count = sum(1 for r in results if r.success)
        failed_count = len(results) - successful_count
        average_time = total_processing_time / len(results) if results else 0.0
        
        logger.info(f"✅ Batch embedding completed: {successful_count}/{len(materials)} successful in {total_processing_time:.3f}s")
        
        return BatchEmbeddingResponse(
            results=results,
            total_processed=len(materials),
            successful_count=successful_count,
            failed_count=failed_count,
            total_processing_time=total_processing_time,
            average_time_per_item=average_time
        )

    def get_cache_statistics(self) -> Dict[str, any]:
        """Get cache statistics for monitoring"""
        if not self.config.cache_enabled:
            return {"caching": "disabled"}
        
        return {
            "cache_enabled": True,
            "cache_size": len(self.embedding_cache),
            "max_cache_size": self.config.max_cache_size,
            "cache_ttl_seconds": self.config.cache_ttl_seconds,
            "total_access_count": sum(entry.access_count for entry in self.embedding_cache.values())
        }

    async def clear_cache(self) -> None:
        """Clear all cached embeddings"""
        self.embedding_cache.clear()
        logger.info("🧹 Embedding cache cleared")

    async def test_connection(self) -> bool:
        """Test OpenAI connection with a simple embedding request"""
        try:
            test_result = await self.generate_material_embedding(
                material_name="Тестовый материал",
                normalized_unit="шт",
                normalized_color=None
            )
            
            if test_result.success and len(test_result.material_embedding) == 1536:
                logger.info("✅ OpenAI connection test successful")
                return True
            else:
                logger.error("❌ OpenAI connection test failed: invalid response")
                return False
                
        except Exception as e:
            logger.error(f"❌ OpenAI connection test failed: {str(e)}")
            return False


# Singleton instance
@lru_cache(maxsize=1)
def get_combined_embedding_service() -> CombinedEmbeddingService:
    """Get singleton instance of CombinedEmbeddingService"""
    return CombinedEmbeddingService() 