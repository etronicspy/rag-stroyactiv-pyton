#!/usr/bin/env python3

"""
Перегенерация эмбеддингов для всех справочных материалов
"""

import asyncio
import time

from core.database.factories import AllDatabasesUnavailableError, get_fallback_manager
from core.schemas.pipeline_models import CombinedEmbeddingRequest
from services.combined_embedding_service import CombinedEmbeddingService


async def regenerate_all_embeddings():
    """Перегенерировать эмбеддинги для всех материалов в справочнике"""
    
    print("🔄 ПЕРЕГЕНЕРАЦИЯ ЭМБЕДДИНГОВ СПРАВОЧНЫХ МАТЕРИАЛОВ")
    print("=" * 60)
    
    try:
        # Инициализация сервисов
        fallback_manager = get_fallback_manager()
        embedding_service = CombinedEmbeddingService()
        
        # Получить все материалы из коллекции
        print("📊 Получение всех материалов из коллекции 'materials'...")
        all_records = await fallback_manager.scroll_all("materials", with_payload=True, with_vectors=False)
        
        if not all_records:
            print("❌ Материалы не найдены")
            return
        
        print(f"📋 Найдено материалов: {len(all_records)}")
        print()
        
        # Статистика
        updated_count = 0
        error_count = 0
        batch_size = 10
        start_time = time.time()
        
        print("🚀 Начинаю перегенерацию эмбеддингов...")
        print(f"📦 Размер батча: {batch_size}")
        print()
        
        # Обработка батчами
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i:i + batch_size]
            batch_start_time = time.time()
            
            print(f"📦 Обработка батча {i//batch_size + 1}/{(len(all_records) + batch_size - 1)//batch_size}")
            print(f"   Материалы: {i+1}-{min(i+batch_size, len(all_records))}")
            
            # Подготовить данные для батча
            batch_materials = []
            batch_ids = []
            
            for record in batch:
                payload = record.get("payload", {})
                record_id = record.get("id")
                
                # Создать объект материала для эмбеддинга
                material = CombinedEmbeddingRequest(
                    material_name=payload.get("name", ""),
                    normalized_unit=payload.get("unit", ""),
                    normalized_color=None  # В нашей БД нет цветов
                )
                
                batch_materials.append(material)
                batch_ids.append(record_id)
            
            try:
                # Генерация эмбеддингов для батча
                print(f"   🧠 Генерация эмбеддингов для {len(batch_materials)} материалов...")
                batch_response = await embedding_service.generate_batch_embeddings(batch_materials)
                
                if len(batch_response.results) != len(batch_materials):
                    print(f"   ⚠️  Предупреждение: получено {len(batch_response.results)} результатов для {len(batch_materials)} материалов")
                
                # Обновить векторы в Qdrant
                print("   💾 Обновление векторов в Qdrant...")
                print(f"   📈 Успешно: {batch_response.successful_count}, ошибок: {batch_response.failed_count}")
                
                for j, (material, result, record_id) in enumerate(zip(batch_materials, batch_response.results, batch_ids)):
                    try:
                        # Получить оригинальные данные для сохранения
                        original_payload = batch[j].get("payload", {})
                        
                        # Проверить успешность генерации эмбеддинга
                        if not result.success or not result.material_embedding:
                            print(f"     ⚠️  Пропускаем материал {material.material_name}: эмбеддинг не сгенерирован")
                            error_count += 1
                            continue
                        
                        # Обновить вектор для материала
                        await fallback_manager.upsert(
                            collection_name="materials",
                            vectors=[{
                                "id": record_id,
                                "vector": result.material_embedding,
                                "payload": {
                                    "name": original_payload.get("name", ""),
                                    "sku": original_payload.get("sku", ""),
                                    "unit": original_payload.get("unit", ""),
                                    "description": original_payload.get("description", ""),
                                    "use_category": original_payload.get("use_category", ""),
                                    "created_at": original_payload.get("created_at", ""),
                                    "updated_at": original_payload.get("updated_at", "")
                                }
                            }]
                        )
                        
                        updated_count += 1
                        
                        if (j + 1) % 5 == 0:
                            print(f"     ✅ Обновлено {j + 1}/{len(batch_materials)} в текущем батче")
                        
                    except Exception as e:
                        print(f"     ❌ Ошибка обновления материала {material.material_name}: {e}")
                        error_count += 1
                
                batch_time = time.time() - batch_start_time
                print(f"   ⏱️  Батч обработан за {batch_time:.2f} сек")
                print()
                
            except Exception as e:
                print(f"   ❌ Ошибка обработки батча: {e}")
                error_count += len(batch_materials)
                continue
        
        # Финальная статистика
        total_time = time.time() - start_time
        
        print("🎉 ПЕРЕГЕНЕРАЦИЯ ЭМБЕДДИНГОВ ЗАВЕРШЕНА!")
        print("=" * 60)
        print("📊 СТАТИСТИКА:")
        print(f"   ✅ Успешно обновлено: {updated_count} материалов")
        print(f"   ❌ Ошибок: {error_count}")
        print(f"   📋 Всего обработано: {len(all_records)} материалов")
        print(f"   ⏱️  Общее время: {total_time:.2f} сек")
        print(f"   ⚡ Скорость: {len(all_records)/total_time:.2f} материалов/сек")
        print()
        
        if updated_count > 0:
            print("🔍 ТЕСТИРОВАНИЕ ОБНОВЛЕННЫХ ЭМБЕДДИНГОВ:")
            await test_updated_embeddings(fallback_manager, embedding_service)
        
    except AllDatabasesUnavailableError as e:
        print(f"❌ Все базы данных недоступны: {e}")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

async def test_updated_embeddings(fallback_manager, embedding_service):
    """Тестирование обновленных эмбеддингов"""
    
    try:
        # Тестовый поиск
        test_queries = [
            "цемент портландский",
            "арматура 12мм",
            "блок газобетонный",
            "краска белая"
        ]
        
        print("🔍 Тестовые запросы:")
        
        for query in test_queries:
            print(f"\n   🔎 Запрос: '{query}'")
            
            # Генерация эмбеддинга для запроса
            query_result = await embedding_service.generate_material_embedding(
                material_name=query,
                normalized_unit="шт",
                normalized_color=None
            )
            
            query_embedding = query_result.material_embedding
            
            # Поиск похожих материалов
            results = await fallback_manager.search(
                collection_name="materials",
                query_vector=query_embedding,
                limit=3
            )
            
            if results:
                print(f"   📋 Найдено {len(results)} похожих материалов:")
                for i, result in enumerate(results[:3], 1):
                    payload = result.get("payload", {})
                    score = result.get("score", 0)
                    print(f"     {i}. {payload.get('name', 'N/A')} (similarity: {score:.3f})")
            else:
                print("   ❌ Похожие материалы не найдены")
        
        print("\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    asyncio.run(regenerate_all_embeddings()) 