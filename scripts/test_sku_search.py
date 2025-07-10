#!/usr/bin/env python3

"""
Тестирование системы двухэтапного поиска SKU
ЭТАП 6: Двухэтапный поиск SKU в справочнике материалов
"""

import asyncio
import time
import logging
from services.sku_search_service import get_sku_search_service
from services.combined_embedding_service import get_combined_embedding_service

# Настройка детального логирования для отладки
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

async def test_sku_search():
    """Тестирование поиска SKU в справочнике материалов"""
    
    print("🚀 Тестирование системы двухэтапного поиска SKU...")
    
    # Получить сервисы
    sku_service = get_sku_search_service()
    embedding_service = get_combined_embedding_service()
    
    # Тест подключения
    print("\n1. Тестирование подключений...")
    connection_ok = await sku_service.test_connection()
    
    if not connection_ok:
        print("❌ Подключения не работают!")
        return
    print("✅ Все подключения работают корректно")
    
    # Тестовые сценарии поиска SKU
    print("\n2. Тестирование поиска SKU...")
    print("=" * 80)
    
    # Оставляем только один тест для детальной отладки
    test_cases = [
        {
            "name": "Цемент портландский белый",
            "unit": "кг", 
            "color": "белый",
            "expected_sku_pattern": "CEM"
        }
    ]
    
    total_tests = len(test_cases)
    successful_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        material_name = test_case["name"]
        normalized_unit = test_case["unit"]
        normalized_color = test_case["color"]
        expected_pattern = test_case["expected_sku_pattern"]
        
        print(f"\n📋 Тест {i}/{total_tests}: {material_name}")
        print(f"   Единица: {normalized_unit}")
        print(f"   Цвет: {normalized_color if normalized_color else 'любой'}")
        print(f"   Ожидаемый SKU паттерн: {expected_pattern}")
        
        start_time = time.time()
        
        # Выполнить поиск SKU
        try:
            result = await sku_service.find_sku_by_material_data(
                material_name=material_name,
                normalized_unit=normalized_unit,
                normalized_color=normalized_color
            )
            
            processing_time = time.time() - start_time
            
            # Анализ результата
            if result.found_sku:
                if expected_pattern and result.found_sku.startswith(expected_pattern):
                    print(f"   ✅ SKU найден: {result.found_sku}")
                    successful_tests += 1
                else:
                    print(f"   ⚠️ SKU найден, но не соответствует паттерну: {result.found_sku} (ожидался {expected_pattern})")
            else:
                if expected_pattern is None:
                    print(f"   ✅ SKU не найден")
                    successful_tests += 1  
                else:
                    print(f"   ❌ SKU не найден")
            
            print(f"   🔍 Кандидатов оценено: {result.candidates_evaluated}")
            print(f"   ⏱️ Время: {processing_time:.3f}s")
            
            # Показать детали лучшего кандидата
            if result.best_match:
                print(f"   🏆 Лучший кандидат:")
                print(f"      - SKU: {result.best_match.sku}")
                print(f"      - Название: {result.best_match.material_name}")
                print(f"      - Единица: {result.best_match.normalized_unit}")
                print(f"      - Цвет: {result.best_match.normalized_color}")
                print(f"      - Сходство: {result.best_match.similarity_score:.4f}")
                print(f"      - Unit match: {result.best_match.unit_match}")
                print(f"      - Color match: {result.best_match.color_match}")
                print(f"      - Overall match: {result.best_match.overall_match}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"   ❌ Ошибка: {e}")
            print(f"   ⏱️ Время: {processing_time:.3f}s")
    
    print("\n" + "=" * 80)
    print(f"📊 Результаты тестирования:")
    print(f"   🔢 Всего тестов: {total_tests}")
    print(f"   ✅ Успешных: {successful_tests}")
    print(f"   ❌ Неудачных: {total_tests - successful_tests}")
    print(f"   📈 Процент успеха: {(successful_tests/total_tests)*100:.1f}%")
    
    # Тест производительности
    print("\n3. Тест производительности...")
    performance_tests = ["Цемент"]
    
    for material_name in performance_tests:
        start_time = time.time()
        try:
            result = await sku_service.find_sku_by_material_data(
                material_name=material_name,
                normalized_unit="кг",
                normalized_color=None
            )
            processing_time = time.time() - start_time
            print(f"   ⏱️ {material_name}: {processing_time:.3f}s")
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"   ❌ {material_name}: {processing_time:.3f}s (ошибка: {e})")
    
    # Статистика сервиса
    print("\n4. Статистика сервиса...")
    cache_stats = sku_service.embedding_service.get_cache_statistics()
    print(f"   📋 Размер кеша: {cache_stats.get('cache_size', 0)}")
    
    vector_db_health = await sku_service.vector_db.health_check()
    print(f"   🔌 Vector DB доступна: {vector_db_health.get('status') == 'healthy'}")
    
    config = sku_service.config
    print(f"   ⚙️ Конфигурация:")
    print(f"      - Порог схожести: {config.similarity_threshold}")
    print(f"      - Макс. кандидатов: {config.max_candidates}")
    print(f"      - Коллекция: {config.reference_collection}")
    
    print("🎯 Тестирование двухэтапного поиска SKU завершено!")

if __name__ == "__main__":
    asyncio.run(test_sku_search()) 