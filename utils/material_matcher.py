import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
from dataclasses import dataclass, asdict
import json

from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from core.config import settings
from services.materials_consolidated import MaterialsService  
from services.price_processor import PriceProcessor
from .common import (
    embedding_service, 
    qdrant_service, 
    parallel_processing
)
from .common_utils import (
    calculate_cosine_similarity,
    calculate_cosine_similarity_batch,
    format_confidence,
    generate_unique_id
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MaterialMatch:
    """Класс для хранения результата сопоставления материалов"""
    reference_id: str
    reference_name: str
    reference_use_category: str
    reference_unit: str
    price_item_name: str
    price_item_use_category: str  
    price_item_unit: str
    price_item_price: float
    price_item_supplier: str
    name_similarity: float
    unit_similarity: float
    combined_score: float
    match_confidence: str  # "high", "medium", "low"
    created_at: datetime

class MaterialMatcher:
    """Оптимизированный класс для семантического сопоставления материалов"""
    
    def __init__(self):
        self.materials_service = MaterialsService()
        self.price_processor = PriceProcessor()
        
        # Пороги для определения качества совпадения
        self.HIGH_CONFIDENCE_THRESHOLD = 0.85
        self.MEDIUM_CONFIDENCE_THRESHOLD = 0.70
        self.UNIT_MATCH_WEIGHT = 0.3
        self.NAME_MATCH_WEIGHT = 0.7
        
        # Коллекция для хранения результатов сопоставления
        self.matches_collection = "material_matches"
        
    async def _get_embedding(self, text: str) -> List[float]:
        """Получить эмбеддинг для текста (оптимизированная версия)"""
        return await embedding_service.get_embedding(text)

    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Вычислить косинусное сходство между двумя векторами (оптимизированная версия)"""
        return calculate_cosine_similarity(vec1, vec2)

    def _determine_confidence(self, score: float) -> str:
        """Определить уровень уверенности в совпадении (оптимизированная версия)"""
        return format_confidence(score, self.HIGH_CONFIDENCE_THRESHOLD, self.MEDIUM_CONFIDENCE_THRESHOLD)

    async def _get_unit_embedding_cached(self, unit: str) -> List[float]:
        """Получить эмбеддинг единицы измерения с кэшированием (оптимизированная версия)"""
        return await embedding_service.get_embedding(unit)

    async def _ensure_matches_collection_exists(self):
        """Создать коллекцию для сопоставлений если не существует (оптимизировано)"""
        qdrant_service.ensure_collection_exists(self.matches_collection)

    async def get_reference_materials(self) -> List[Dict[str, Any]]:
        """Получить все эталонные материалы"""
        try:
            materials = await self.materials_service.get_materials(limit=1000)
            return [
                {
                    "id": material.id,
                    "name": material.name,
                    "use_category": material.use_category,
                    "unit": material.unit,
                    "description": material.description or "",
                    "embedding": material.embedding
                }
                for material in materials
            ]
        except Exception as e:
            logger.error(f"Error getting reference materials: {e}")
            return []

    def get_price_list_materials_with_embeddings(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Получить материалы из последнего прайс-листа поставщика с эмбеддингами (оптимизировано)"""
        try:
            collection_name = f"supplier_{supplier_id}_prices"
            
            # Проверить существование коллекции
            if not qdrant_service.collection_exists(collection_name):
                logger.warning(f"Collection {collection_name} not found")
                return []
            
            # Получить все точки с векторами и payload
            points = qdrant_service.get_points_with_payload(collection_name, limit=1000)
            
            materials = []
            for point in points:
                materials.append({
                    "id": str(point.id),
                    "name": point.payload.get("name"),
                    "use_category": point.payload.get("use_category", ""), 
                    "unit": point.payload.get("unit"),
                    "price": point.payload.get("price"),
                    "description": point.payload.get("description", ""),
                    "supplier": supplier_id,
                    "embedding": point.vector,  # Используем существующий эмбеддинг
                    "upload_date": point.payload.get("upload_date")
                })
            
            # Сортировать по дате загрузки (новые первыми)
            materials.sort(key=lambda x: x.get("upload_date", ""), reverse=True)
            
            logger.info(f"Retrieved {len(materials)} materials with embeddings from {collection_name}")
            return materials
            
        except Exception as e:
            logger.error(f"Error getting price list materials with embeddings: {e}")
            return []

    async def match_materials(self, supplier_id: str) -> List[MaterialMatch]:
        """Сопоставить материалы из прайс-листа с эталонными материалами используя существующие эмбеддинги"""
        logger.info(f"Starting material matching for supplier: {supplier_id}")
        
        # Получить эталонные материалы и материалы из прайс-листа с эмбеддингами
        reference_materials = await self.get_reference_materials()
        price_materials = self.get_price_list_materials_with_embeddings(supplier_id)
        
        if not reference_materials:
            logger.warning("No reference materials found")
            return []
        
        if not price_materials:
            logger.warning(f"No price materials found for supplier {supplier_id}")
            return []
        
        logger.info(f"Found {len(reference_materials)} reference materials and {len(price_materials)} price materials")
        
        # Предварительно кэшировать все уникальные единицы измерения
        unique_units = set()
        for ref_mat in reference_materials:
            unique_units.add(ref_mat['unit'])
        for price_mat in price_materials:
            unique_units.add(price_mat['unit'])
        
        logger.info(f"Pre-caching embeddings for {len(unique_units)} unique units")
        for unit in unique_units:
            await self._get_unit_embedding_cached(unit)
        
        matches = []
        
        # Для каждого материала из прайс-листа найти лучшее совпадение с эталоном
        for i, price_item in enumerate(price_materials):
            logger.info(f"Processing price item {i+1}/{len(price_materials)}: {price_item['name']}")
            best_match = None
            best_score = 0.0
            
            # Использовать существующий эмбеддинг для материала из прайса
            price_name_embedding = price_item.get('embedding')
            if not price_name_embedding:
                logger.warning(f"No embedding found for price item: {price_item['name']}")
                continue
                
            # Получить кэшированный эмбеддинг единицы измерения
            price_unit_embedding = await self._get_unit_embedding_cached(price_item['unit'])
            
            # Сравнить с каждым эталонным материалом
            for ref_material in reference_materials:
                try:
                    # Использовать существующий эмбеддинг для эталонного материала
                    ref_name_embedding = ref_material.get('embedding')
                    if not ref_name_embedding:
                        logger.warning(f"No embedding found for reference material: {ref_material['name']}")
                        continue
                    
                    # Получить кэшированный эмбеддинг единицы измерения
                    ref_unit_embedding = await self._get_unit_embedding_cached(ref_material['unit'])
                    
                    # Вычислить сходство по названию и единице измерения
                    name_similarity = self._calculate_cosine_similarity(price_name_embedding, ref_name_embedding)
                    unit_similarity = self._calculate_cosine_similarity(price_unit_embedding, ref_unit_embedding)
                    
                    # Комбинированный счет с весами
                    combined_score = (
                        name_similarity * self.NAME_MATCH_WEIGHT + 
                        unit_similarity * self.UNIT_MATCH_WEIGHT
                    )
                    
                    logger.debug(f"  vs reference {ref_material['name']}: name={name_similarity:.3f}, unit={unit_similarity:.3f}, combined={combined_score:.3f}")
                    
                    # Сохранить лучшее совпадение
                    if combined_score > best_score:
                        best_score = combined_score
                        best_match = MaterialMatch(
                            reference_id=ref_material.get('id', ''),
                            reference_name=ref_material['name'],
                            reference_use_category=ref_material['use_category'],
                            reference_unit=ref_material['unit'],
                            price_item_name=price_item['name'],
                            price_item_use_category=price_item['use_category'],
                            price_item_unit=price_item['unit'],
                            price_item_price=price_item['price'],
                            price_item_supplier=supplier_id,
                            name_similarity=name_similarity,
                            unit_similarity=unit_similarity,
                            combined_score=combined_score,
                            match_confidence=self._determine_confidence(combined_score),
                            created_at=datetime.utcnow()
                        )
                
                except Exception as e:
                    logger.error(f"Error processing reference material {ref_material.get('name', 'unknown')}: {e}")
                    continue
            
            if best_match:
                matches.append(best_match)
                logger.info(f"Best match for '{price_item['name']}': '{best_match.reference_name}' (score: {best_match.combined_score:.3f}, confidence: {best_match.match_confidence})")
        
        logger.info(f"Found {len(matches)} matches using existing embeddings")
        return matches

    async def match_materials_with_vector_search(self, supplier_id: str, top_k: int = 5) -> List[MaterialMatch]:
        """Сопоставить материалы используя векторный поиск с параллельной обработкой (максимально оптимизировано)"""
        logger.info(f"Starting highly optimized material matching for supplier: {supplier_id}")
        
        # Получить материалы из прайс-листа с эмбеддингами
        price_materials = self.get_price_list_materials_with_embeddings(supplier_id)
        
        if not price_materials:
            logger.warning(f"No price materials found for supplier {supplier_id}")
            return []
        
        logger.info(f"Found {len(price_materials)} price materials")
        
        # Предварительно получить все уникальные единицы измерения для кэширования
        unique_units = set()
        for item in price_materials:
            unique_units.add(item['unit'])
        
        # Параллельно получить эмбеддинги для всех единиц измерения
        unit_embeddings_tasks = [self._get_unit_embedding_cached(unit) for unit in unique_units]
        await parallel_processing(unit_embeddings_tasks, max_concurrent=5)
        
        # Функция для обработки одного материала
        async def process_material(price_item):
            try:
                price_name_embedding = price_item.get('embedding')
                if not price_name_embedding:
                    logger.warning(f"No embedding found for price item: {price_item['name']}")
                    return None
                
                # Поиск похожих материалов в коллекции эталонных материалов
                search_results = qdrant_service.client.search(
                    collection_name="materials",
                    query_vector=price_name_embedding,
                    limit=top_k,
                    with_payload=True,
                    score_threshold=0.5  # Минимальный порог сходства
                )
                
                if not search_results:
                    return None
                
                # Получить эмбеддинг единицы измерения для прайс-материала
                price_unit_embedding = await self._get_unit_embedding_cached(price_item['unit'])
                
                best_match = None
                best_score = 0.0
                
                for result in search_results:
                    try:
                        ref_material = result.payload
                        
                        # Получить эмбеддинг единицы измерения для эталонного материала
                        ref_unit_embedding = await self._get_unit_embedding_cached(ref_material['unit'])
                        
                        # Использовать скор из векторного поиска как name_similarity
                        name_similarity = result.score
                        
                        # Вычислить сходство единиц измерения
                        unit_similarity = self._calculate_cosine_similarity(price_unit_embedding, ref_unit_embedding)
                        
                        # Комбинированный счет с весами
                        combined_score = (
                            name_similarity * self.NAME_MATCH_WEIGHT + 
                            unit_similarity * self.UNIT_MATCH_WEIGHT
                        )
                        
                        if combined_score > best_score:
                            best_score = combined_score
                            best_match = MaterialMatch(
                                reference_id=str(result.id),
                                reference_name=ref_material['name'],
                                reference_use_category=ref_material.get('use_category', ''),
                                reference_unit=ref_material['unit'],
                                price_item_name=price_item['name'],
                                price_item_use_category=price_item['use_category'],
                                price_item_unit=price_item['unit'],
                                price_item_price=price_item['price'],
                                price_item_supplier=supplier_id,
                                name_similarity=name_similarity,
                                unit_similarity=unit_similarity,
                                combined_score=combined_score,
                                match_confidence=self._determine_confidence(combined_score),
                                created_at=datetime.utcnow()
                            )
                    
                    except Exception as e:
                        logger.error(f"Error processing search result: {e}")
                        continue
                
                return best_match
                    
            except Exception as e:
                logger.error(f"Error in vector search for '{price_item['name']}': {e}")
                return None
        
        # Параллельная обработка всех материалов
        logger.info("Starting parallel processing of materials...")
        processing_tasks = [process_material(item) for item in price_materials]
        match_results = await parallel_processing(processing_tasks, max_concurrent=8)
        
        # Фильтруем None результаты
        matches = [match for match in match_results if match is not None]
        
        logger.info(f"Found {len(matches)} matches using highly optimized vector search")
        return matches

    async def save_matches_to_collection(self, matches: List[MaterialMatch]) -> bool:
        """Сохранить результаты сопоставления в коллекцию Qdrant (оптимизировано)"""
        try:
            await self._ensure_matches_collection_exists()
            
            # Подготовить тексты для батчевого получения эмбеддингов
            match_texts = []
            for match in matches:
                match_text = f"{match.reference_name} {match.price_item_name} {match.reference_use_category} {match.price_item_use_category}"
                match_texts.append(match_text)
            
            # Получить все эмбеддинги за один раз
            match_embeddings = await embedding_service.get_embeddings_batch(match_texts)
            
            # Создать точки
            points = []
            for i, (match, embedding) in enumerate(zip(matches, match_embeddings)):
                point_id = generate_unique_id(match_texts[i], "MATCH_")
                
                # Подготовить payload с сериализуемыми данными
                payload = asdict(match)
                payload['created_at'] = match.created_at.isoformat()
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Сохранить в батчах
            success = qdrant_service.upsert_points_batch(self.matches_collection, points)
            
            if success:
                logger.info(f"Saved {len(matches)} matches to collection {self.matches_collection}")
            return success
            
        except Exception as e:
            logger.error(f"Error saving matches to collection: {e}")
            return False

    def get_matches_by_supplier(self, supplier_id: str, confidence_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить сопоставления для конкретного поставщика (оптимизировано)"""
        try:
            filter_conditions = [
                FieldCondition(key="price_item_supplier", match=MatchValue(value=supplier_id))
            ]
            
            if confidence_filter:
                filter_conditions.append(
                    FieldCondition(key="match_confidence", match=MatchValue(value=confidence_filter))
                )
            
            search_filter = Filter(must=filter_conditions)
            
            results = qdrant_service.client.scroll(
                collection_name=self.matches_collection,
                scroll_filter=search_filter,
                limit=1000
            )
            
            matches = [point.payload for point in results[0]]
            return matches
            
        except Exception as e:
            logger.error(f"Error getting matches for supplier {supplier_id}: {e}")
            return []

    async def generate_matches_report(self, supplier_id: str) -> Dict[str, Any]:
        """Сгенерировать отчет по сопоставлению материалов"""
        matches = self.get_matches_by_supplier(supplier_id)
        
        if not matches:
            return {
                "supplier_id": supplier_id,
                "total_matches": 0,
                "matches": [],
                "statistics": {
                    "high_confidence": 0,
                    "medium_confidence": 0,  
                    "low_confidence": 0,
                    "average_score": 0.0
                }
            }
        
        # Статистика
        high_conf = len([m for m in matches if m["match_confidence"] == "high"])
        medium_conf = len([m for m in matches if m["match_confidence"] == "medium"])
        low_conf = len([m for m in matches if m["match_confidence"] == "low"])
        avg_score = sum(m["combined_score"] for m in matches) / len(matches)
        
        return {
            "supplier_id": supplier_id,
            "total_matches": len(matches),
            "matches": matches,
            "statistics": {
                "high_confidence": high_conf,
                "medium_confidence": medium_conf,
                "low_confidence": low_conf,
                "average_score": round(avg_score, 3)
            }
        }

async def main():
    """Главная функция для демонстрации работы"""
    matcher = MaterialMatcher()
    
    # Пример использования - сопоставить материалы для поставщика
    supplier_id = "Поставщик_Строй_Материалы"
    
    print(f"🔍 Начинаю сопоставление материалов для поставщика: {supplier_id}")
    print("\n🚀 Метод 1: Оптимизированное сопоставление с векторным поиском")
    
    # Выполнить быстрое сопоставление с векторным поиском
    matches_fast = await matcher.match_materials_with_vector_search(supplier_id, top_k=3)
    
    if matches_fast:
        print(f"✅ Найдено {len(matches_fast)} быстрых сопоставлений")
        
        # Сохранить в коллекцию
        if await matcher.save_matches_to_collection(matches_fast):
            print("💾 Результаты сохранены в коллекцию")
        
        # Сгенерировать отчет
        report = await matcher.generate_matches_report(supplier_id)
        
        print("\n📊 СТАТИСТИКА БЫСТРОГО СОПОСТАВЛЕНИЯ:")
        print(f"   Всего совпадений: {report['total_matches']}")
        print(f"   Высокая уверенность: {report['statistics']['high_confidence']}")
        print(f"   Средняя уверенность: {report['statistics']['medium_confidence']}")
        print(f"   Низкая уверенность: {report['statistics']['low_confidence']}")
        print(f"   Средний скор: {report['statistics']['average_score']}")
        
        print("\n🎯 ЛУЧШИЕ СОВПАДЕНИЯ (ВЕКТОРНЫЙ ПОИСК):")
        high_confidence_matches = [m for m in matches_fast if m.match_confidence == "high"]
        for match in high_confidence_matches[:5]:  # Показать топ-5
            print(f"   • {match.price_item_name} → {match.reference_name}")
            print(f"     Категории: {match.price_item_use_category} → {match.reference_use_category}")
            print(f"     Единицы: {match.price_item_unit} → {match.reference_unit}")
            print(f"     Скор: {match.combined_score:.3f}, Цена: {match.price_item_price}₽")
            print()
        
        # Сохранить детальный отчет в JSON
        with open(f"matches_report_fast_{supplier_id}.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        print(f"📄 Детальный отчет сохранен в matches_report_fast_{supplier_id}.json")
        
        print("\n" + "="*60)
        print("⚡ ОПТИМИЗАЦИЯ С ЭМБЕДДИНГАМИ ЗАВЕРШЕНА")
        print("="*60)
        print(f"✅ Использованы существующие эмбеддинги из таблиц")
        print(f"🚀 Векторный поиск Qdrant для ускорения")  
        print(f"🧠 Кэширование эмбеддингов единиц измерения")
        print(f"📈 Семантическое сопоставление по названиям и единицам")
        
    else:
        print("❌ Сопоставления не найдены")

if __name__ == "__main__":
    asyncio.run(main()) 