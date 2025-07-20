"""
SKU Search Service for RAG Construction Materials API

Двухэтапный поиск SKU в справочнике материалов:
1. ЭТАП 1: Векторный поиск по комбинированному embedding
2. ЭТАП 2: Точная фильтрация по normalized_unit (строго) и normalized_color (гибко для None)

Согласно диаграмме интеграции ЭТАП 6.
"""

import hashlib
import logging
import time
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from core.config.base import Settings
from core.database.interfaces import IVectorDatabase
from core.schemas.pipeline_models import (
    SKUSearchCandidate,
    SKUSearchConfig,
    SKUSearchResponse,
)
from services.combined_embedding_service import get_combined_embedding_service

logger = logging.getLogger(__name__)


class SKUSearchService:
    """
    Двухэтапный поиск SKU в справочнике материалов
    
    ЛОГИКА ПОИСКА:
    1. ЭТАП 1: Векторный поиск похожих материалов по similarity_threshold
    2. ЭТАП 2: Фильтрация кандидатов:
       - normalized_unit: СТРОГОЕ совпадение 
       - normalized_color: ГИБКАЯ логика (None принимает любой цвет)
    3. РЕЗУЛЬТАТ: SKU первого подходящего материала по векторному рейтингу
    """
    
    def __init__(
        self, 
        vector_db: Optional[IVectorDatabase] = None,
        config: Optional[SKUSearchConfig] = None
    ):
        """
        Initialize SKU Search Service
        
        Args:
            vector_db: Vector database instance for material search
            config: Service configuration
        """
        self.settings = Settings()
        self.config = config or SKUSearchConfig()
        self.logger = logger
        
        # Initialize vector database
        if vector_db is None:
            try:
                # Lazy import to avoid circular imports
                from core.database.factories import DatabaseFactory
                self.vector_db = DatabaseFactory.create_vector_database()
                self.logger.info("✅ Vector database initialized for SKU search")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize vector database: {e}")
                self.vector_db = None
        else:
            self.vector_db = vector_db
        
        # Get combined embedding service
        self.embedding_service = get_combined_embedding_service()
        
        # In-memory cache for search results
        self.search_cache: Dict[str, Tuple[SKUSearchResponse, datetime]] = {}
        
        self.logger.info("SKU Search Service initialized")
    
    async def find_sku_by_material_data(
        self,
        material_name: str,
        unit: str,
        normalized_color: Optional[str] = None,  # Kept for compatibility but ignored
        material_embedding: Optional[List[float]] = None,
        similarity_threshold: Optional[float] = None,
        max_candidates: Optional[int] = None
    ) -> SKUSearchResponse:
        """
        Main method: Find SKU using two-phase search (now via centralized fallback manager)
        """
        from core.database.factories import (
            AllDatabasesUnavailableError,
            get_fallback_manager,
        )
        start_time = time.time()
        threshold = similarity_threshold or self.config.similarity_threshold
        max_cands = max_candidates or self.config.max_candidates
        self.logger.info(f"🔍 Starting SKU search for: {material_name} [{unit}]")
        # Check cache first
        if self.config.cache_enabled:
            cache_key = self._generate_cache_key(material_name, unit, None, threshold)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.debug(f"📋 Cache hit for SKU search: {material_name}")
                return cached_result
        fallback_manager = get_fallback_manager()
        try:
            response = await fallback_manager.find_sku_by_material_data(
                material_name=material_name,
                unit=unit,
                normalized_color=normalized_color,
                material_embedding=material_embedding,
                similarity_threshold=threshold,
                max_candidates=max_cands
            )
            # Cache result
            if self.config.cache_enabled:
                self._cache_result(cache_key, response)
            return response
        except AllDatabasesUnavailableError as e:
            self.logger.error(f"All databases unavailable for SKU search: {e.errors}")
            raise
    
    async def find_sku_by_combined_embedding(
        self,
        material_embedding: List[float],
        normalized_unit: str,
        normalized_color: Optional[str]
    ) -> SKUSearchResponse:
        """
        Find SKU using combined embedding search with fallback manager.
        
        Args:
            material_embedding: Material embedding vector
            normalized_unit: Normalized unit of measurement
            normalized_color: Normalized color (optional)
            
        Returns:
            SKU search response with best match
        """
        start_time = time.time()
        
        try:
            self.logger.debug(f"Searching SKU with combined embedding for unit: {normalized_unit}, color: {normalized_color}")
            
            # Search similar materials using fallback manager
            from core.database.factories import (
                AllDatabasesUnavailableError,
                get_fallback_manager,
            )
            
            fallback_manager = get_fallback_manager()
            search_results = await fallback_manager.search(
                collection_name=self.config.reference_collection,
                query_vector=material_embedding,
                limit=self.config.max_candidates
            )
            
            if not search_results:
                self.logger.debug("No candidates found in vector search")
                return SKUSearchResponse(
                    found_sku=None,
                    search_successful=True,
                    candidates_evaluated=0,
                    matching_candidates=0,
                    search_method="combined_embedding_search",
                    processing_time=time.time() - start_time
                )
            
            # Convert search results to candidates
            candidates = []
            for result in search_results:
                try:
                    candidate = self._convert_vector_result_to_candidate(result)
                    if candidate:
                        candidates.append(candidate)
                except Exception as e:
                    self.logger.warning(f"Failed to convert search result to candidate: {e}")
                    continue
            
            self.logger.debug(f"Found {len(candidates)} candidates from vector search")
            
            # Filter candidates by unit and color
            matching_candidates = []
            for candidate in candidates:
                # Strict unit matching
                unit_match = self._check_unit_match(candidate.unit, normalized_unit)
                
                # Flexible color matching (None color accepts any color)
                color_match = True  # Since we don't have color field in current DB structure
                if normalized_color:
                    # In future, implement color matching logic here
                    color_match = True
                
                # Overall match requires unit match and color compatibility
                overall_match = unit_match and color_match
                
                if overall_match:
                    matching_candidates.append(candidate)
                    self.logger.debug(f"✅ Matching candidate: {candidate.name} (SKU: {candidate.sku})")
                else:
                    self.logger.debug(f"❌ Non-matching candidate: {candidate.name} (unit: {candidate.unit} vs {normalized_unit})")
            
            # Return best match (highest similarity score)
            if matching_candidates:
                # Sort by similarity score (highest first)
                matching_candidates.sort(key=lambda x: x.similarity_score, reverse=True)
                best_match = matching_candidates[0]
                
                self.logger.info(f"✅ Found SKU: {best_match.sku} for material with similarity: {best_match.similarity_score}")
                
                return SKUSearchResponse(
                    found_sku=best_match.sku,
                    search_successful=True,
                    candidates_evaluated=len(candidates),
                    matching_candidates=len(matching_candidates),
                    best_match=best_match,
                    search_method="combined_embedding_search",
                    processing_time=time.time() - start_time,
                    all_candidates=candidates
                )
            else:
                self.logger.warning("No matching candidates found after filtering")
                return SKUSearchResponse(
                    found_sku=None,
                    search_successful=True,
                    candidates_evaluated=len(candidates),
                    matching_candidates=0,
                    search_method="combined_embedding_search",
                    processing_time=time.time() - start_time,
                    all_candidates=candidates
                )
                
        except AllDatabasesUnavailableError as e:
            self.logger.error(f"All databases unavailable for SKU search: {e}")
            return SKUSearchResponse(
                found_sku=None,
                search_successful=False,
                candidates_evaluated=0,
                matching_candidates=0,
                search_method="combined_embedding_search",
                processing_time=time.time() - start_time,
                error_message=f"All databases unavailable: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"Error in combined embedding SKU search: {e}")
            return SKUSearchResponse(
                found_sku=None,
                search_successful=False,
                candidates_evaluated=0,
                matching_candidates=0,
                search_method="combined_embedding_search",
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _phase1_vector_search(
        self, 
        query_embedding: List[float], 
        similarity_threshold: float,
        max_candidates: int
    ) -> List[SKUSearchCandidate]:
        """Phase 1: Vector search for similar materials using fallback manager"""
        try:
            # Perform vector search using fallback manager
            from core.database.factories import (
                AllDatabasesUnavailableError,
                get_fallback_manager,
            )
            
            fallback_manager = get_fallback_manager()
            search_results = await fallback_manager.search(
                collection_name=self.config.reference_collection,
                query_vector=query_embedding,
                limit=max_candidates * 2,  # Get more results for threshold filtering
                filter_conditions=None
            )
            
            # Filter by similarity threshold and convert to candidates
            candidates = []
            for result in search_results:
                # Filter by similarity threshold
                if result["score"] >= similarity_threshold:
                    payload = result.get("payload", {})
                    
                    # Используем реальную структуру данных из Qdrant
                    unit = payload.get("unit", "")
                    color = payload.get("normalized_color") or payload.get("color")  # Может не быть
                    
                    candidate = SKUSearchCandidate(
                        material_id=result["id"],
                        sku=payload.get("sku", ""),
                        name=payload.get("name", ""),  # Исправлено: 'name' вместо 'material_name'
                        unit=unit,  # Исправлено: 'unit' вместо 'normalized_unit'
                        description=payload.get("description", ""),  # Добавлено: новое поле
                        similarity_score=result["score"],
                        unit_match=False,  # Will be evaluated in Phase 2
                        color_match=False,  # Will be evaluated in Phase 2  
                        overall_match=False  # Will be evaluated in Phase 2
                    )
                    candidates.append(candidate)
            
            # Sort by similarity score (highest first) and limit
            candidates.sort(key=lambda x: x.similarity_score, reverse=True)
            candidates = candidates[:max_candidates]
            
            logger.debug(f"Phase 1: Found {len(candidates)} candidates with similarity >= {similarity_threshold}")
            return candidates
            
        except AllDatabasesUnavailableError as e:
            logger.error(f"All databases unavailable for Phase 1 vector search: {e}")
            return []
        except Exception as e:
            logger.error(f"Phase 1 vector search failed: {e}")
            return []
    
    def _phase2_attribute_filtering(
        self,
        candidates: List[SKUSearchCandidate],
        unit: str,
        normalized_color: Optional[str]
    ) -> List[SKUSearchCandidate]:
        """
        ЭТАП 2: Фильтрация кандидатов по атрибутам (адаптировано под реальную БД)
        
        ЛОГИКА ФИЛЬТРАЦИИ:
        1. unit: СТРОГОЕ совпадение с полем 'unit' из БД (шт == шт, шт != кг)
        2. color: ОТКЛЮЧЕНА (поле 'normalized_color' отсутствует в БД)
        
        Args:
            candidates: Кандидаты из векторного поиска
            unit: Требуемая единица измерения (поле 'unit' из БД)
            normalized_color: Игнорируется (совместимость)
            
        Returns:
            Отфильтрованные кандидаты
        """
        matching_candidates = []
        
        for candidate in candidates:
            # 1. Проверка единицы измерения (СТРОГАЯ) - используем поле 'unit' из БД
            unit_match = self._check_unit_match(candidate.unit, unit)
            
            # 2. Цветовая фильтрация отключена (поле отсутствует в БД)
            color_match = True  # Always pass since no color field in DB
            
            # 3. Общий результат (только по единице)
            overall_match = unit_match
            
            # Обновляем кандидата с результатами проверки
            candidate.unit_match = unit_match
            candidate.color_match = color_match  
            candidate.overall_match = overall_match
            
            # Добавляем только подходящих кандидатов
            if overall_match:
                matching_candidates.append(candidate)
            
            logger.debug(
                f"🔍 Candidate {candidate.name}: "
                f"unit={unit_match} ({candidate.unit} vs {unit}), "
                f"overall={overall_match}"
            )
        
        return matching_candidates
    
    def _check_unit_match(self, candidate_unit: str, required_unit: str) -> bool:
        """
        Проверка совпадения единиц измерения с нормализацией
        
        Args:
            candidate_unit: Единица кандидата
            required_unit: Требуемая единица
            
        Returns:
            True если единицы совпадают (с учетом нормализации)
        """
        if not candidate_unit or not required_unit:
            return False
        
        # Нормализуем обе единицы для сравнения
        normalized_candidate = self._normalize_unit_for_comparison(candidate_unit)
        normalized_required = self._normalize_unit_for_comparison(required_unit)
        
        # Строгое сравнение нормализованных единиц
        match = normalized_candidate == normalized_required
        
        logger.debug(f"Unit comparison: '{candidate_unit}' ({normalized_candidate}) vs '{required_unit}' ({normalized_required}) = {match}")
        
        return match
    
    def _normalize_unit_for_comparison(self, unit: str) -> str:
        """
        Нормализация единицы измерения для сравнения
        
        Args:
            unit: Исходная единица
            
        Returns:
            Нормализованная единица
        """
        if not unit:
            return ""
        
        unit_clean = unit.lower().strip()
        
        # Словарь нормализации единиц
        unit_mappings = {
            # Вес
            "кг": "кг",
            "килограмм": "кг", 
            "килограммы": "кг",
            "килограммов": "кг",
            "kg": "кг",
            "кило": "кг",
            
            # Объем  
            "м³": "м³",
            "куб": "м³",
            "кубометр": "м³",
            "кубометры": "м³", 
            "кубометров": "м³",
            "м3": "м³",
            "куб.м": "м³",
            "кубический метр": "м³",
            
            # Площадь
            "м²": "м²",
            "кв.м": "м²",
            "м2": "м²",
            "квадратный метр": "м²",
            "квадратные метры": "м²",
            "квадратных метров": "м²",
            
            # Штуки
            "шт": "шт",
            "штука": "шт",
            "штуки": "шт",
            "штук": "шт",
            "pcs": "шт",
            "pc": "шт",
            
            # Метры
            "м": "м",
            "метр": "м",
            "метры": "м",
            "метров": "м",
            "meter": "м",
            
            # Литры
            "л": "л",
            "литр": "л",
            "литры": "л",
            "литров": "л",
            "liter": "л",
            "l": "л"
        }
        
        return unit_mappings.get(unit_clean, unit_clean)
    
    def _check_color_compatibility(
        self, 
        candidate_color: Optional[str], 
        required_color: Optional[str]
    ) -> bool:
        """
        Проверка совместимости цветов (ГИБКАЯ ЛОГИКА)
        
        КРИТИЧЕСКАЯ ЛОГИКА:
        - Если required_color is None/null -> принимает ЛЮБОЙ цвет (return True)
        - Если required_color указан -> требует ТОЧНОГО совпадения
        
        Args:
            candidate_color: Цвет кандидата
            required_color: Требуемый цвет
            
        Returns:
            True если цвета совместимы
        """
        if required_color is None or required_color == "null":
            # None принимает любой цвет кандидата
            return True
        
        if candidate_color is None:
            # Требуется конкретный цвет, но у кандидата его нет
            return False
        
        # Строгое сравнение цветов
        return candidate_color.lower().strip() == required_color.lower().strip()
    
    def _select_best_match(self, candidates: List[SKUSearchCandidate]) -> Optional[SKUSearchCandidate]:
        """
        Выбор лучшего кандидата по векторному рейтингу
        
        Args:
            candidates: Список отфильтрованных кандидатов
            
        Returns:
            Лучший кандидат или None
        """
        if not candidates:
            return None
        
        # Сортируем по similarity_score (убывание) и выбираем первого
        best_candidate = max(candidates, key=lambda c: c.similarity_score)
        
        # Дополнительная проверка на наличие SKU
        if not best_candidate.sku:
            self.logger.warning(f"Best candidate has no SKU: {best_candidate.name}")  # Исправлено: 'name' вместо 'material_name'
            # Попробуем найти кандидата с SKU
            candidates_with_sku = [c for c in candidates if c.sku]
            if candidates_with_sku:
                best_candidate = max(candidates_with_sku, key=lambda c: c.similarity_score)
            else:
                return None
        
        return best_candidate
    
    def _convert_search_result_to_candidate(self, search_result: Dict[str, Any]) -> Optional[SKUSearchCandidate]:
        """
        Конвертация результата векторного поиска в кандидата (адаптировано под реальную БД)
        
        Args:
            search_result: Результат из Qdrant
            
        Returns:
            SKUSearchCandidate или None при ошибке
        """
        try:
            payload = search_result.get("payload", {})
            
            # Отладочный вывод
            self.logger.debug(f"Converting search result: {search_result}")
            self.logger.debug(f"Payload keys: {list(payload.keys())}")
            self.logger.debug(f"Name: {payload.get('name')}, Unit: {payload.get('unit')}")
            
            return SKUSearchCandidate(
                material_id=str(search_result.get("id")),
                sku=payload.get("sku"),
                name=payload.get("name", "UNKNOWN"),  # Fallback to avoid empty string
                unit=payload.get("unit", "UNKNOWN"),  # Fallback to avoid empty string
                description=payload.get("description", ""),  # Using 'description' field from DB
                similarity_score=float(search_result.get("score", 0.0)),
                unit_match=False,  # Будет заполнено в фильтрации
                color_match=False,  # Будет заполнено в фильтрации  
                overall_match=False  # Будет заполнено в фильтрации
            )
            
        except Exception as e:
            self.logger.error(f"Failed to convert search result: {e}")
            self.logger.error(f"Search result data: {search_result}")
            return None
    
    def _convert_vector_result_to_candidate(self, result: Dict[str, Any]) -> Optional[SKUSearchCandidate]:
        """
        Convert vector database result to SKU search candidate.
        
        Args:
            result: Vector database search result
            
        Returns:
            SKU search candidate or None if conversion fails
        """
        try:
            payload = result.get("payload", {})
            
            return SKUSearchCandidate(
                material_id=str(result.get("id", "")),
                sku=payload.get("sku"),
                name=payload.get("name", ""),
                unit=payload.get("unit", ""),
                description=payload.get("description"),
                similarity_score=result.get("score", 0.0),
                unit_match=True,  # Will be checked later
                color_match=True,  # Will be checked later
                overall_match=True  # Will be checked later
            )
        except Exception as e:
            self.logger.error(f"Failed to convert vector result to candidate: {e}")
            return None
    
    def _generate_cache_key(
        self,
        material_name: str,
        normalized_unit: str,
        normalized_color: Optional[str],
        similarity_threshold: float
    ) -> str:
        """Generate cache key for search request"""
        cache_data = f"{material_name}_{normalized_unit}_{normalized_color or 'none'}_{similarity_threshold}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[SKUSearchResponse]:
        """Get cached search result if not expired"""
        if cache_key not in self.search_cache:
            return None
        
        result, cached_at = self.search_cache[cache_key]
        if datetime.utcnow() - cached_at > timedelta(seconds=self.config.cache_ttl):
            del self.search_cache[cache_key]
            return None
        
        return result
    
    def _cache_result(self, cache_key: str, response: SKUSearchResponse) -> None:
        """Cache search result"""
        # Simple cache size management
        if len(self.search_cache) > 1000:  # Max 1000 cached results
            # Remove oldest 20%
            sorted_cache = sorted(
                self.search_cache.items(),
                key=lambda x: x[1][1]  # Sort by timestamp
            )
            for key, _ in sorted_cache[:200]:
                del self.search_cache[key]
        
        self.search_cache[cache_key] = (response, datetime.utcnow())
    
    def _create_error_response(self, error_message: str, start_time: float) -> SKUSearchResponse:
        """Create error response"""
        return SKUSearchResponse(
            found_sku=None,
            search_successful=False,
            candidates_evaluated=0,
            matching_candidates=0,
            best_match=None,
            search_method="error",
            processing_time=time.time() - start_time,
            error_message=error_message
        )
    
    async def test_connection(self) -> bool:
        """Test vector database and embedding service connection using fallback manager
        
        Returns:
            True if both connections work
        """
        try:
            # Test vector database connection using fallback manager
            from core.database.factories import (
                AllDatabasesUnavailableError,
                get_fallback_manager,
            )
            
            fallback_manager = get_fallback_manager()
            health_status = await fallback_manager.health_check()
            vector_db_ok = health_status.get("status") == "healthy"
            
            # Test embedding service connection  
            embedding_ok = await self.embedding_service.test_connection()
            
            if vector_db_ok and embedding_ok:
                logger.info("✅ All connections working properly")
                return True
            else:
                logger.error(f"❌ Connection test failed - Vector DB: {vector_db_ok}, Embeddings: {embedding_ok}")
                return False
                
        except AllDatabasesUnavailableError as e:
            logger.error(f"All databases unavailable for connection test: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "cache_size": len(self.search_cache),
            "config": self.config.model_dump(),
            "vector_db_available": self.vector_db is not None
        }


# Singleton pattern for service
_sku_search_service_instance: Optional[SKUSearchService] = None


@lru_cache(maxsize=1)
def get_sku_search_service() -> SKUSearchService:
    """
    Get or create SKU Search Service singleton
    
    Returns:
        SKUSearchService instance
    """
    global _sku_search_service_instance
    
    if _sku_search_service_instance is None:
        _sku_search_service_instance = SKUSearchService()
        logger.info("✅ SKU Search Service singleton created")
    
    return _sku_search_service_instance 