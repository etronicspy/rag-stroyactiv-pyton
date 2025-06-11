"""
Общие утилиты для оптимизации работы с векторной базой данных и AI
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from datetime import datetime
from functools import lru_cache
import hashlib

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from core.config import settings, get_vector_db_client, get_ai_client

logger = logging.getLogger(__name__)

class VectorCache:
    """Кэш для векторов с TTL"""
    
    def __init__(self, max_size: int = 1000):
        self._cache = {}
        self._timestamps = {}
        self.max_size = max_size
        self.ttl = 3600  # 1 час
    
    def _is_expired(self, key: str) -> bool:
        """Проверить, истёк ли срок кэша"""
        if key not in self._timestamps:
            return True
        return (datetime.now().timestamp() - self._timestamps[key]) > self.ttl
    
    def get(self, key: str) -> Optional[List[float]]:
        """Получить вектор из кэша"""
        if key in self._cache and not self._is_expired(key):
            return self._cache[key]
        return None
    
    def set(self, key: str, vector: List[float]) -> None:
        """Сохранить вектор в кэш"""
        if len(self._cache) >= self.max_size:
            # Удаляем старейшие записи
            oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
        
        self._cache[key] = vector
        self._timestamps[key] = datetime.now().timestamp()
    
    def clear(self) -> None:
        """Очистить кэш"""
        self._cache.clear()
        self._timestamps.clear()

# Глобальный экземпляр кэша векторов
vector_cache = VectorCache()

class OptimizedEmbeddingService:
    """Оптимизированный сервис для работы с эмбеддингами"""
    
    def __init__(self):
        self.ai_client = get_ai_client()
        self._batch_size = 50  # Размер батча для массовой обработки
    
    @lru_cache(maxsize=128)
    def _get_cache_key(self, text: str) -> str:
        """Генерировать ключ для кэша"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    async def get_embedding(self, text: str) -> List[float]:
        """Получить эмбеддинг с кэшированием"""
        cache_key = self._get_cache_key(text)
        
        # Проверяем кэш
        cached_vector = vector_cache.get(cache_key)
        if cached_vector is not None:
            return cached_vector
        
        # Генерируем новый эмбеддинг
        try:
            if settings.AI_PROVIDER.value == "openai":
                ai_config = settings.get_ai_config()
                if "text-embedding-3" in ai_config["model"]:
                    response = await self.ai_client.embeddings.create(
                        input=text,
                        model=ai_config["model"],
                        dimensions=1536
                    )
                else:
                    response = await self.ai_client.embeddings.create(
                        input=text,
                        model=ai_config["model"]
                    )
                embedding = response.data[0].embedding
            elif settings.AI_PROVIDER.value == "huggingface":
                embedding = self.ai_client.encode([text])[0].tolist()
            else:
                raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")
            
            # Сохраняем в кэш
            vector_cache.set(cache_key, embedding)
            return embedding
            
        except Exception as e:
            logger.error(f"Error getting embedding for text: {text[:50]}... Error: {e}")
            raise
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Получить эмбеддинги для списка текстов с батчевой обработкой"""
        embeddings = []
        
        # Обрабатываем по батчам
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i:i + self._batch_size]
            
            # Проверяем кэш для каждого текста в батче
            batch_embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            for j, text in enumerate(batch):
                cache_key = self._get_cache_key(text)
                cached_vector = vector_cache.get(cache_key)
                
                if cached_vector is not None:
                    batch_embeddings.append(cached_vector)
                else:
                    batch_embeddings.append(None)  # Заглушка
                    uncached_texts.append(text)
                    uncached_indices.append(j)
            
            # Генерируем эмбеддинги для некэшированных текстов
            if uncached_texts:
                try:
                    if settings.AI_PROVIDER.value == "openai":
                        ai_config = settings.get_ai_config()
                        if "text-embedding-3" in ai_config["model"]:
                            response = await self.ai_client.embeddings.create(
                                input=uncached_texts,
                                model=ai_config["model"],
                                dimensions=1536
                            )
                        else:
                            response = await self.ai_client.embeddings.create(
                                input=uncached_texts,
                                model=ai_config["model"]
                            )
                        
                        new_embeddings = [data.embedding for data in response.data]
                    elif settings.AI_PROVIDER.value == "huggingface":
                        new_embeddings = self.ai_client.encode(uncached_texts).tolist()
                    else:
                        raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")
                    
                    # Сохраняем в кэш и подставляем в результат
                    for idx, text, embedding in zip(uncached_indices, uncached_texts, new_embeddings):
                        cache_key = self._get_cache_key(text)
                        vector_cache.set(cache_key, embedding)
                        batch_embeddings[idx] = embedding
                        
                except Exception as e:
                    logger.error(f"Error getting batch embeddings: {e}")
                    raise
            
            embeddings.extend(batch_embeddings)
        
        return embeddings

class OptimizedQdrantService:
    """Оптимизированный сервис для работы с Qdrant"""
    
    def __init__(self):
        self.client = get_vector_db_client()
    
    @lru_cache(maxsize=16)
    def collection_exists(self, collection_name: str) -> bool:
        """Проверить существование коллекции с кэшированием"""
        try:
            collections = self.client.get_collections()
            return any(c.name == collection_name for c in collections.collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def ensure_collection_exists(self, collection_name: str, vector_size: int = 1536) -> bool:
        """Создать коллекцию если не существует"""
        if not self.collection_exists(collection_name):
            try:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Created collection: {collection_name}")
                # Обновляем кэш
                self.collection_exists.cache_clear()
                return True
            except Exception as e:
                logger.error(f"Error creating collection {collection_name}: {e}")
                return False
        return True
    
    def upsert_points_batch(self, collection_name: str, points: List[PointStruct], 
                           batch_size: int = 100) -> bool:
        """Загрузить точки батчами для оптимизации"""
        try:
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                logger.debug(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
            return True
        except Exception as e:
            logger.error(f"Error upserting points batch: {e}")
            return False
    
    def get_points_with_payload(self, collection_name: str, 
                               limit: int = 1000, 
                               offset: Optional[str] = None) -> List[Any]:
        """Получить точки с payload, поддерживающий пагинацию"""
        try:
            if offset:
                results = self.client.scroll(
                    collection_name=collection_name,
                    limit=limit,
                    with_payload=True,
                    with_vectors=True,
                    offset=offset
                )
            else:
                results = self.client.scroll(
                    collection_name=collection_name,
                    limit=limit,
                    with_payload=True,
                    with_vectors=True
                )
            
            if isinstance(results, tuple):
                return results[0]
            return results
            
        except Exception as e:
            logger.error(f"Error getting points: {e}")
            return []

def calculate_cosine_similarity_batch(vectors1: List[List[float]], 
                                    vectors2: List[List[float]]) -> List[List[float]]:
    """Эффективное вычисление косинусного сходства для батчей векторов"""
    try:
        v1_array = np.array(vectors1)
        v2_array = np.array(vectors2)
        
        # Нормализация векторов
        v1_norm = v1_array / np.linalg.norm(v1_array, axis=1, keepdims=True)
        v2_norm = v2_array / np.linalg.norm(v2_array, axis=1, keepdims=True)
        
        # Вычисление косинусного сходства
        similarities = np.dot(v1_norm, v2_norm.T)
        
        return similarities.tolist()
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity batch: {e}")
        return [[0.0] * len(vectors2) for _ in vectors1]

def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Вычислить косинусное сходство между двумя векторами"""
    try:
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0

def generate_unique_id(text: str, prefix: str = "") -> str:
    """Генерировать уникальный ID из текста"""
    hash_obj = hashlib.md5(text.encode('utf-8'))
    return f"{prefix}{hash_obj.hexdigest()[:8].upper()}"

async def parallel_processing(tasks: List, max_concurrent: int = 10) -> List[Any]:
    """Параллельная обработка задач с ограничением на количество одновременных операций"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(task):
        async with semaphore:
            if asyncio.iscoroutine(task):
                return await task
            elif callable(task):
                return await task() if asyncio.iscoroutinefunction(task) else task()
            else:
                return task
    
    return await asyncio.gather(*[process_with_semaphore(task) for task in tasks])

def format_confidence(score: float, 
                     high_threshold: float = 0.85, 
                     medium_threshold: float = 0.70) -> str:
    """Определить уровень уверенности по скору"""
    if score >= high_threshold:
        return "high"
    elif score >= medium_threshold:
        return "medium"
    else:
        return "low"

def format_price(price: Union[float, str]) -> str:
    """Форматировать цену для отображения"""
    try:
        price_float = float(price)
        return f"{price_float:.2f}₽"
    except (ValueError, TypeError):
        return "N/A"

def truncate_text(text: str, max_length: int = 30) -> str:
    """Обрезать текст с многоточием"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

# Глобальные экземпляры сервисов
embedding_service = OptimizedEmbeddingService()
qdrant_service = OptimizedQdrantService() 