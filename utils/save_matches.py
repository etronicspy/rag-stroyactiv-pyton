#!/usr/bin/env python3
"""
Утилита для корректного сохранения результатов сопоставления материалов (оптимизировано)
"""

import asyncio
import json
from datetime import datetime

from .material_matcher import MaterialMatcher
from .common import qdrant_service, embedding_service
from .common_utils import generate_unique_id, format_price, truncate_text
from qdrant_client.models import PointStruct

async def save_and_view_matches(supplier_id: str):
    """Сохранить и показать результаты сопоставления (оптимизированная версия)"""
    
    print("💾 ОПТИМИЗИРОВАННОЕ СОХРАНЕНИЕ РЕЗУЛЬТАТОВ СОПОСТАВЛЕНИЯ")
    print("="*60)
    
    matcher = MaterialMatcher()
    
    # Получить результаты сопоставления
    print(f"🔍 Выполняю оптимизированное сопоставление для поставщика: {supplier_id}")
    matches = await matcher.match_materials_with_vector_search(supplier_id, top_k=5)
    
    if not matches:
        print("❌ Нет результатов для сохранения")
        return
    
    print(f"✅ Найдено {len(matches)} совпадений")
    
    # Подготовить тексты для батчевого получения эмбеддингов
    match_texts = []
    for match in matches:
        match_text = f"{match.reference_name} {match.price_item_name} {match.reference_use_category} {match.price_item_use_category}"
        match_texts.append(match_text)
    
    # Получить все эмбеддинги за один раз
    print("🚀 Получение эмбеддингов батчевым способом...")
    match_embeddings = await embedding_service.get_embeddings_batch(match_texts)
    
    # Подготовить точки для сохранения
    points = []
    for i, (match, embedding) in enumerate(zip(matches, match_embeddings)):
        point_id = generate_unique_id(match_texts[i], f"{supplier_id}_")
        
        # Подготовить payload с сериализуемыми данными
        payload = {
            "reference_id": match.reference_id,
            "reference_name": match.reference_name,
            "reference_category": match.reference_category,
            "reference_unit": match.reference_unit,
            "price_item_name": match.price_item_name,
            "price_item_category": match.price_item_category,
            "price_item_unit": match.price_item_unit,
            "price_item_price": float(match.price_item_price),
            "price_item_supplier": match.price_item_supplier,
            "name_similarity": float(match.name_similarity),
            "unit_similarity": float(match.unit_similarity),
            "combined_score": float(match.combined_score),
            "match_confidence": match.match_confidence,
            "created_at": match.created_at.isoformat(),
            "match_id": f"{supplier_id}_{i+1}"
        }
        
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        )
        points.append(point)
    
    try:
        # Сохранить в коллекцию батчевым способом
        print("💾 Сохранение в векторную базу данных...")
        success = qdrant_service.upsert_points_batch("material_matches", points)
        
        if success:
            print(f"✅ Успешно сохранено {len(points)} совпадений в коллекцию 'material_matches'")
            
            # Показать сохраненные данные
            await view_saved_matches()
            
            # Сохранить также в JSON файл для резервного копирования
            matches_data = []
            for match in matches:
                match_dict = {
                    "reference_name": match.reference_name,
                    "reference_category": match.reference_category,
                    "reference_unit": match.reference_unit,
                    "price_item_name": match.price_item_name,
                    "price_item_category": match.price_item_category,
                    "price_item_unit": match.price_item_unit,
                    "price_item_price": float(match.price_item_price),
                    "price_item_supplier": match.price_item_supplier,
                    "name_similarity": float(match.name_similarity),
                    "unit_similarity": float(match.unit_similarity),
                    "combined_score": float(match.combined_score),
                    "match_confidence": match.match_confidence,
                    "created_at": match.created_at.isoformat()
                }
                matches_data.append(match_dict)
            
            filename = f"saved_matches_{supplier_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(matches_data, f, ensure_ascii=False, indent=2)
            
            print(f"📄 Резервная копия сохранена в файл: {filename}")
        else:
            print("❌ Ошибка при сохранении в векторную базу данных")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

async def view_saved_matches():
    """Просмотреть сохраненные совпадения (оптимизированная версия)"""
    
    print(f"\n👀 ПРОСМОТР СОХРАНЕННЫХ СОВПАДЕНИЙ")
    print("-"*60)
    
    try:
        # Получить все точки из коллекции
        points = qdrant_service.get_points_with_payload("material_matches", limit=100)
        
        if not points:
            print("📭 Коллекция пуста")
            return
        
        print(f"📊 Найдено {len(points)} сохраненных совпадений:")
        print()
        
        # Заголовок таблицы
        print(f"{'ID':>3} {'Материал из прайса':<25} {'→':<2} {'Эталонный материал':<25} {'Скор':>6} {'Ув-ть':>8} {'Цена':>8}")
        print("-" * 85)
        
        # Сортировать по combined_score (по убыванию)
        sorted_points = sorted(points, key=lambda p: p.payload.get('combined_score', 0), reverse=True)
        
        for point in sorted_points:
            payload = point.payload
            
            confidence_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}[payload.get('match_confidence', 'low')]
            
            price_name = truncate_text(payload.get('price_item_name', ''), 25)
            ref_name = truncate_text(payload.get('reference_name', ''), 25)
            price_formatted = format_price(payload.get('price_item_price', 0))
            
            print(f"{point.id:>3} {price_name:<25} → {ref_name:<25} {payload.get('combined_score', 0):>6.3f} {confidence_icon}{payload.get('match_confidence', 'low'):>7} {price_formatted:>8}")
        
        print("-" * 85)
        
        # Статистика
        high_count = len([p for p in points if p.payload.get('match_confidence') == 'high'])
        medium_count = len([p for p in points if p.payload.get('match_confidence') == 'medium'])
        low_count = len([p for p in points if p.payload.get('match_confidence') == 'low'])
        avg_score = sum(p.payload.get('combined_score', 0) for p in points) / len(points)
        
        print(f"\n📈 СТАТИСТИКА:")
        print(f"   🟢 Высокая уверенность: {high_count}")
        print(f"   🟡 Средняя уверенность: {medium_count}")
        print(f"   🔴 Низкая уверенность: {low_count}")
        print(f"   📊 Средний скор: {avg_score:.3f}")
        
        # Показать детали для лучшего совпадения
        if sorted_points:
            best_match = sorted_points[0].payload
            print(f"\n🏆 ЛУЧШЕЕ СОВПАДЕНИЕ:")
            print(f"   Материал из прайса: {best_match.get('price_item_name')}")
            print(f"   Эталонный материал: {best_match.get('reference_name')}")
            print(f"   Категории: {best_match.get('price_item_use_category')} → {best_match.get('reference_use_category')}")
            print(f"   Единицы: {best_match.get('price_item_unit')} → {best_match.get('reference_unit')}")
            print(f"   Сходство названий: {best_match.get('name_similarity', 0):.3f}")
            print(f"   Сходство единиц: {best_match.get('unit_similarity', 0):.3f}")
            print(f"   Общий скор: {best_match.get('combined_score', 0):.3f}")
            print(f"   Цена: {best_match.get('price_item_price', 0):.2f}₽")
        
    except Exception as e:
        print(f"❌ Ошибка просмотра: {e}")

async def main():
    """Главная функция"""
    supplier_id = "Поставщик_Строй_Материалы"
    await save_and_view_matches(supplier_id)

if __name__ == "__main__":
    asyncio.run(main()) 