#!/usr/bin/env python3
"""
Утилита для сохранения упрощенных результатов сопоставления материалов (оптимизировано)
Сохраняет только имена, единицы измерения и уникальные артикулы
"""

import asyncio
from datetime import datetime

from .material_matcher import MaterialMatcher
from .common import qdrant_service
from .common_utils import generate_unique_id, truncate_text
from qdrant_client.models import PointStruct, Distance, VectorParams

async def save_simple_matches(supplier_id: str):
    """Сохранить упрощенные результаты сопоставления (оптимизированная версия)"""
    
    print("💾 ОПТИМИЗИРОВАННОЕ СОХРАНЕНИЕ УПРОЩЕННЫХ РЕЗУЛЬТАТОВ")
    print("="*60)
    print("📋 Сохраняются только: имена, единицы и артикулы")
    print("="*60)
    
    matcher = MaterialMatcher()
    
    # Получить результаты сопоставления
    print(f"🔍 Выполняю оптимизированное сопоставление для поставщика: {supplier_id}")
    matches = await matcher.match_materials_with_vector_search(supplier_id, top_k=5)
    
    if not matches:
        print("❌ Нет результатов для сохранения")
        return
    
    print(f"✅ Найдено {len(matches)} совпадений")
    
    # Создать упрощенную коллекцию если не существует
    simple_collection_name = "simple_material_matches"
    
    # Создаем коллекцию с минимальным размером вектора (только для индексации)
    qdrant_service.ensure_collection_exists(simple_collection_name, vector_size=1)
    
    # Подготовить упрощенные точки для сохранения
    simple_points = []
    
    for i, match in enumerate(matches):
        # Генерировать уникальный артикул
        article_text = f"{match.price_item_name}_{match.reference_name}_{supplier_id}"
        article_code = generate_unique_id(article_text, "MT")
        
        # Упрощенный payload с только необходимыми полями
        simple_payload = {
            "article_code": article_code,
            "price_material_name": match.price_item_name,
            "price_material_unit": match.price_item_unit,
            "reference_material_name": match.reference_name,
            "reference_material_unit": match.reference_unit,
            "match_score": round(float(match.combined_score), 3),
            "confidence": match.match_confidence,
            "supplier": supplier_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Простой вектор (не используется для поиска, только для соответствия схеме)
        simple_vector = [0.5]
        
        point = PointStruct(
            id=article_code,  # Используем артикул как ID
            vector=simple_vector,
            payload=simple_payload
        )
        simple_points.append(point)
    
    try:
        # Сохранить в упрощенную коллекцию батчевым способом
        success = qdrant_service.upsert_points_batch(simple_collection_name, simple_points)
        
        if success:
            print(f"💾 Успешно сохранено {len(simple_points)} упрощенных записей")
            
            # Показать результаты
            await view_simple_matches()
        else:
            print("❌ Ошибка при сохранении")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

async def view_simple_matches():
    """Просмотреть упрощенные сохраненные совпадения (оптимизированная версия)"""
    
    print(f"\n👀 ПРОСМОТР УПРОЩЕННЫХ СОВПАДЕНИЙ")
    print("="*80)
    
    try:
        # Получить все точки из упрощенной коллекции
        points = qdrant_service.get_points_with_payload("simple_material_matches", limit=100)
        
        if not points:
            print("📭 Коллекция пуста")
            return
        
        print(f"📊 Найдено {len(points)} упрощенных записей:")
        print()
        
        # Заголовок таблицы
        print(f"{'Артикул':<12} {'Материал из прайса':<25} {'Ед.':<5} {'→':<2} {'Эталонный материал':<25} {'Ед.':<5} {'Скор':<6}")
        print("=" * 85)
        
        # Сортировать по скору (по убыванию)
        sorted_points = sorted(points, key=lambda p: p.payload.get('match_score', 0), reverse=True)
        
        for point in sorted_points:
            payload = point.payload
            
            # Обрезать длинные названия
            price_name = truncate_text(payload.get('price_material_name', ''), 25)
            ref_name = truncate_text(payload.get('reference_material_name', ''), 25)
            
            print(f"{payload.get('article_code', ''):<12} "
                  f"{price_name:<25} "
                  f"{payload.get('price_material_unit', ''):<5} "
                  f"→ "
                  f"{ref_name:<25} "
                  f"{payload.get('reference_material_unit', ''):<5} "
                  f"{payload.get('match_score', 0):<6.3f}")
        
        print("=" * 85)
        
        # Краткая статистика
        high_count = len([p for p in points if p.payload.get('confidence') == 'high'])
        medium_count = len([p for p in points if p.payload.get('confidence') == 'medium'])
        low_count = len([p for p in points if p.payload.get('confidence') == 'low'])
        
        print(f"\n📈 КРАТКАЯ СТАТИСТИКА:")
        print(f"   🟢 Высокая точность: {high_count}")
        print(f"   🟡 Средняя точность: {medium_count}")
        print(f"   🔴 Низкая точность: {low_count}")
        print(f"   📦 Всего пар: {len(points)}")
        
        # Показать примеры артикулов
        print(f"\n🏷️ ПРИМЕРЫ АРТИКУЛОВ:")
        for i, point in enumerate(sorted_points[:3], 1):
            payload = point.payload
            print(f"   {i}. {payload.get('article_code')} - "
                  f"{payload.get('price_material_name')} → "
                  f"{payload.get('reference_material_name')}")
        
        # Создать CSV экспорт для удобства
        csv_data = []
        csv_data.append("Артикул,Материал_из_прайса,Единица_прайс,Эталонный_материал,Единица_эталон,Скор,Уверенность")
        
        for point in sorted_points:
            payload = point.payload
            csv_line = (f"{payload.get('article_code', '')},"
                       f"{payload.get('price_material_name', '')},"
                       f"{payload.get('price_material_unit', '')},"
                       f"{payload.get('reference_material_name', '')},"
                       f"{payload.get('reference_material_unit', '')},"
                       f"{payload.get('match_score', 0)},"
                       f"{payload.get('confidence', '')}")
            csv_data.append(csv_line)
        
        # Сохранить CSV файл
        csv_filename = f"simple_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(csv_data))
        
        print(f"\n📄 CSV файл сохранен: {csv_filename}")
        
    except Exception as e:
        print(f"❌ Ошибка просмотра: {e}")

async def main():
    """Главная функция"""
    supplier_id = "Поставщик_Строй_Материалы"
    await save_simple_matches(supplier_id)

if __name__ == "__main__":
    asyncio.run(main()) 