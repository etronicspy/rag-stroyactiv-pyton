#!/usr/bin/env python3

"""
Проверка коллекции materials в Qdrant для отладки поиска SKU
"""

import asyncio
from core.database.adapters.qdrant_adapter import QdrantVectorDatabase
from core.config.base import Settings

async def check_qdrant_collection():
    """Проверка коллекции materials в Qdrant"""
    
    print("🔍 Проверка коллекции materials в Qdrant...")
    
    # Создать клиент Qdrant напрямую
    settings = Settings()
    qdrant_config = settings.get_vector_db_config()
    vector_db = QdrantVectorDatabase(qdrant_config)
    
    # Проверить health
    health = await vector_db.health_check()
    print(f"🏥 Health check: {health}")
    
    collection_name = "materials"
    
    # Проверить существование коллекции
    exists = await vector_db.collection_exists(collection_name)
    print(f"📋 Коллекция '{collection_name}' существует: {exists}")
    
    if not exists:
        print("❌ Коллекция materials не существует!")
        print("💡 Нужно создать коллекцию и загрузить справочные данные")
        return
    
    # Получить все записи из коллекции
    print(f"\n📊 Получение всех записей из коллекции '{collection_name}'...")
    all_records = await vector_db.scroll_all(collection_name, with_payload=True, with_vectors=False)
    
    print(f"📝 Найдено записей: {len(all_records)}")
    
    if len(all_records) == 0:
        print("❌ Коллекция пуста!")
        return
    
    # Показать примеры записей
    print("\n🔍 Примеры записей:")
    available_fields = set()
    
    for i, record in enumerate(all_records[:5]):  # Показать первые 5
        payload = record.get("payload", {})
        available_fields.update(payload.keys())
        
        print(f"  {i+1}. ID: {record['id']}")
        print(f"     SKU: {payload.get('sku', 'N/A')}")
        print(f"     Название: {payload.get('name', 'N/A')}")
        print(f"     Единица: {payload.get('unit', 'N/A')}")
        print(f"     Описание: {payload.get('description', 'N/A')}")
        print(f"     Normalized Unit: {payload.get('normalized_unit', 'НЕТ ПОЛЯ')}")
        print(f"     Normalized Color: {payload.get('normalized_color', 'НЕТ ПОЛЯ')}")
        print(f"     Все поля: {list(payload.keys())}")
        print()
    
    print(f"📋 Все доступные поля в коллекции: {sorted(available_fields)}")
    
    # Группировка по SKU паттернам
    print("📈 Статистика по типам материалов:")
    sku_patterns = {}
    none_sku_count = 0
    
    for record in all_records:
        payload = record.get("payload", {})
        sku = payload.get("sku")
        
        if sku is None or sku == "UNKNOWN":
            none_sku_count += 1
        elif isinstance(sku, str) and sku.startswith("CEM"):
            sku_patterns["Цемент (CEM)"] = sku_patterns.get("Цемент (CEM)", 0) + 1
        elif isinstance(sku, str) and sku.startswith("BRK"):
            sku_patterns["Кирпич (BRK)"] = sku_patterns.get("Кирпич (BRK)", 0) + 1
        elif isinstance(sku, str) and sku.startswith("SND"):
            sku_patterns["Песок (SND)"] = sku_patterns.get("Песок (SND)", 0) + 1
        elif isinstance(sku, str) and sku.startswith("ARM"):
            sku_patterns["Арматура (ARM)"] = sku_patterns.get("Арматура (ARM)", 0) + 1
        elif isinstance(sku, str) and sku.startswith("BLK"):
            sku_patterns["Блоки (BLK)"] = sku_patterns.get("Блоки (BLK)", 0) + 1
        elif isinstance(sku, str) and sku.startswith("GRV"):
            sku_patterns["Гравий/Щебень (GRV)"] = sku_patterns.get("Гравий/Щебень (GRV)", 0) + 1
        elif isinstance(sku, str) and sku.startswith("MTL"):
            sku_patterns["Металл (MTL)"] = sku_patterns.get("Металл (MTL)", 0) + 1
        else:
            sku_patterns["Другие"] = sku_patterns.get("Другие", 0) + 1
    
    if none_sku_count > 0:
        print(f"  ❌ None/UNKNOWN SKU: {none_sku_count} записей")
    
    for pattern, count in sku_patterns.items():
        print(f"  - {pattern}: {count} записей")
    
    # Тест поиска конкретного материала
    print("\n🎯 Тест векторного поиска...")
    test_embedding = [0.1] * 1536  # Фиктивный вектор для теста
    search_results = await vector_db.search(
        collection_name=collection_name,
        query_vector=test_embedding,
        limit=5
    )
    
    print(f"🔍 Результаты тестового поиска: {len(search_results)} записей")
    for i, result in enumerate(search_results[:3]):
        payload = result.get("payload", {})
        print(f"  {i+1}. Score: {result.get('score', 0):.4f}, SKU: {payload.get('sku', 'N/A')}, Name: {payload.get('name', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(check_qdrant_collection()) 