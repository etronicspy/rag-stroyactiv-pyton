#!/usr/bin/env python3

"""
Тестирование присвоения SKU материалам
"""

import asyncio
import time
from typing import List
from services.sku_search_service import SKUSearchService

async def test_sku_assignment():
    """Тестирование присвоения SKU различным материалам"""
    
    print("🔍 ТЕСТИРОВАНИЕ ПРИСВОЕНИЯ SKU МАТЕРИАЛАМ")
    print("=" * 60)
    
    # Инициализация сервиса
    sku_service = SKUSearchService()
    
    # Тестовые материалы для поиска SKU
    test_materials = [
        {
            "name": "Цемент М500 быстротвердеющий",
            "unit": "кг", 
            "color": None,
            "expected": "Должен найти цемент"
        },
        {
            "name": "Арматура стальная диаметр 14мм",
            "unit": "м",
            "color": None,
            "expected": "Должен найти арматуру"
        },
        {
            "name": "Кирпич облицовочный красный одинарный",
            "unit": "шт",
            "color": "красный",
            "expected": "Должен найти красный кирпич"
        },
        {
            "name": "Блок газобетонный 600x300x200",
            "unit": "шт",
            "color": None,
            "expected": "Должен найти газобетон"
        },
        {
            "name": "Плитка керамическая для пола",
            "unit": "м²",
            "color": None,
            "expected": "Должен найти керамическую плитку"
        },
        {
            "name": "Краска акриловая белая матовая",
            "unit": "л",
            "color": "белая",
            "expected": "Должен найти белую краску"
        },
        {
            "name": "Доска сосна обрезная 50x150",
            "unit": "м",
            "color": None,
            "expected": "Должен найти доску"
        },
        {
            "name": "Щебень гранитный фракция 5-10мм",
            "unit": "т",
            "color": None,
            "expected": "Должен найти щебень"
        },
        {
            "name": "Материал неизвестный экзотический",
            "unit": "шт",
            "color": None,
            "expected": "Не должен найти SKU"
        }
    ]
    
    print(f"🧪 Тестируем {len(test_materials)} материалов")
    print()
    
    successful_matches = 0
    total_tests = len(test_materials)
    
    for i, material in enumerate(test_materials, 1):
        print(f"🔍 ТЕСТ {i}/{total_tests}: {material['name']}")
        print(f"   📝 Единица: {material['unit']}")
        print(f"   🎨 Цвет: {material['color'] or 'не указан'}")
        print(f"   💭 Ожидание: {material['expected']}")
        
        start_time = time.time()
        
        try:
            # Выполнить поиск SKU
            search_response = await sku_service.find_sku_by_material_data(
                material_name=material["name"],
                unit=material["unit"],
                normalized_color=material["color"],
                similarity_threshold=0.35,  # Используем порог из системы
                max_candidates=10
            )
            
            processing_time = time.time() - start_time
            
            print(f"   ⏱️  Время поиска: {processing_time:.3f} сек")
            print(f"   📊 Кандидатов найдено: {search_response.candidates_evaluated}")
            print(f"   ✅ Подходящих: {search_response.matching_candidates}")
            
            if search_response.search_successful and search_response.found_sku:
                print(f"   🎯 Найден SKU: {search_response.found_sku}")
                
                if search_response.best_match:
                    best = search_response.best_match
                    print(f"   📋 Лучшее совпадение:")
                    print(f"      - Название: {best.name}")
                    print(f"      - SKU: {best.sku}")
                    print(f"      - Единица: {best.unit}")
                    print(f"      - Similarity: {best.similarity_score:.3f}")
                    print(f"      - Unit match: {best.unit_match}")
                    print(f"      - Color match: {best.color_match}")
                    print(f"      - Overall match: {best.overall_match}")
                
                successful_matches += 1
                print(f"   ✅ РЕЗУЛЬТАТ: SKU НАЙДЕН")
            else:
                print(f"   ❌ РЕЗУЛЬТАТ: SKU НЕ НАЙДЕН")
                if search_response.error_message:
                    print(f"   ⚠️  Ошибка: {search_response.error_message}")
            
            # Показать топ-3 кандидатов для анализа
            if search_response.all_candidates:
                print(f"   📈 Топ-3 кандидата:")
                for j, candidate in enumerate(search_response.all_candidates[:3], 1):
                    print(f"      {j}. {candidate.name} (SKU: {candidate.sku})")
                    print(f"         Similarity: {candidate.similarity_score:.3f}, Unit: {candidate.unit_match}, Overall: {candidate.overall_match}")
        
        except Exception as e:
            print(f"   ❌ ОШИБКА: {str(e)}")
        
        print()
    
    # Итоговая статистика
    success_rate = (successful_matches / total_tests) * 100
    
    print("📊 ИТОГОВАЯ СТАТИСТИКА ПРИСВОЕНИЯ SKU")
    print("=" * 60)
    print(f"✅ Успешных присвоений: {successful_matches}/{total_tests}")
    print(f"📈 Процент успеха: {success_rate:.1f}%")
    print(f"❌ Неуспешных: {total_tests - successful_matches}")
    
    if success_rate >= 70:
        print("🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Система работает корректно")
    elif success_rate >= 50:
        print("✅ ХОРОШИЙ РЕЗУЛЬТАТ! Система в целом работает")
    else:
        print("⚠️  ТРЕБУЕТ ДОРАБОТКИ! Низкий процент успеха")

async def test_specific_sku_search():
    """Детальный тест конкретного поиска SKU"""
    
    print("\n🔬 ДЕТАЛЬНЫЙ АНАЛИЗ ПОИСКА SKU")
    print("=" * 60)
    
    sku_service = SKUSearchService()
    
    # Тест с очень похожим материалом
    material_name = "Цемент портландцемент М500"
    unit = "кг"
    similarity_threshold = 0.35
    max_candidates = 20
    
    print("🔍 Тестовый запрос:")
    print(f"   Материал: {material_name}")
    print(f"   Единица: {unit}")
    print(f"   Порог: {similarity_threshold}")
    print()
    
    start_time = time.time()
    response = await sku_service.find_sku_by_material_data(
        material_name=material_name,
        unit=unit,
        normalized_color=None,
        similarity_threshold=similarity_threshold,
        max_candidates=max_candidates
    )
    processing_time = time.time() - start_time
    
    print(f"⏱️  Время обработки: {processing_time:.3f} сек")
    print(f"🔍 Метод поиска: {response.search_method}")
    print(f"📊 Кандидатов оценено: {response.candidates_evaluated}")
    print(f"✅ Подходящих кандидатов: {response.matching_candidates}")
    print()
    
    if response.found_sku:
        print(f"🎯 НАЙДЕН SKU: {response.found_sku}")
        print()
        
        if response.best_match:
            best = response.best_match
            print("🏆 ЛУЧШЕЕ СОВПАДЕНИЕ:")
            print(f"   📋 Название: {best.name}")
            print(f"   🏷️  SKU: {best.sku}")
            print(f"   📏 Единица: {best.unit}")
            print(f"   📊 Vector similarity: {best.similarity_score:.4f}")
            print(f"   ✅ Unit exact match: {best.unit_match}")
            print(f"   🎨 Color match: {best.color_match}")
            print(f"   🎯 Overall match: {best.overall_match}")
            print()
    
    # Показать все кандидаты для анализа
    if response.all_candidates:
        print("📋 ВСЕ КАНДИДАТЫ (топ-10):")
        for i, candidate in enumerate(response.all_candidates[:10], 1):
            match_icon = "✅" if candidate.overall_match else "❌"
            unit_icon = "📏✅" if candidate.unit_match else "📏❌"
            
            print(f"   {i:2d}. {match_icon} {candidate.name}")
            print(f"       SKU: {candidate.sku}, Sim: {candidate.similarity_score:.3f}, {unit_icon}")

if __name__ == "__main__":
    asyncio.run(test_sku_assignment())
    asyncio.run(test_specific_sku_search()) 