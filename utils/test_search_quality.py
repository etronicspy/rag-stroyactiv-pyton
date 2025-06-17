#!/usr/bin/env python3
"""
Тест качества семантического поиска по эмбеддингам
"""

import requests
import json
import time
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

def test_search_quality():
    """Тестирует качество семантического поиска по различным запросам"""
    
    # Тестовые запросы с ожидаемыми категориями результатов
    test_queries = {
        "цемент": ["Цемент", "Бетон"],  # Ожидаем цемент и связанные материалы
        "арматура": ["Арматура", "Металл"],  # Ожидаем арматуру и металлические изделия
        "кирпич": ["Кирпич", "Камень"],  # Ожидаем кирпич и каменные материалы
        "бетон": ["Бетон", "Цемент"],  # Ожидаем бетон и цементные смеси
        "металл": ["Металл", "Арматура"],  # Ожидаем металлические изделия
        "строительные материалы": None,  # Общий запрос - любые категории подходят
        "cement": ["Цемент", "Бетон"],  # Английский запрос
        "стальная арматура": ["Арматура", "Металл"],  # Составной запрос
        "строительная смесь": ["Цемент", "Бетон"],  # Поиск по назначению
        "M400": ["Цемент"],  # Поиск по марке
    }
    
    print("=" * 60)
    print("🔍 АНАЛИЗ КАЧЕСТВА СЕМАНТИЧЕСКОГО ПОИСКА")
    print("=" * 60)
    
    overall_results = {
        "total_queries": len(test_queries),
        "successful_queries": 0,
        "relevant_results": 0,
        "total_results": 0,
        "avg_response_time": 0,
        "embedding_type": "unknown"
    }
    
    response_times = []
    
    for query, expected_categories in test_queries.items():
        print(f"\n📝 Тестирую запрос: '{query}'")
        
        start_time = time.time()
        
        try:
            # Выполняем поисковый запрос
            response = requests.get(
                f"{BASE_URL}/search/",
                params={"q": query, "limit": 5},
                timeout=10
            )
            
            response_time = (time.time() - start_time) * 1000
            response_times.append(response_time)
            
            if response.status_code == 200:
                results = response.json()
                overall_results["successful_queries"] += 1
                overall_results["total_results"] += len(results)
                
                print(f"   ⏱️  Время ответа: {response_time:.0f}ms")
                print(f"   📊 Найдено результатов: {len(results)}")
                
                if results:
                    print("   🎯 Результаты:")
                    relevant_count = 0
                    
                    for i, result in enumerate(results, 1):
                        name = result.get("name", "")
                        category = result.get("use_category", "")
                        description = (result.get("description") or "")[:50]
                        
                        # Проверяем релевантность
                        is_relevant = False
                        if expected_categories is None:  # Общий запрос
                            is_relevant = True
                        elif any(exp_cat.lower() in category.lower() for exp_cat in expected_categories):
                            is_relevant = True
                        elif any(exp_cat.lower() in name.lower() for exp_cat in expected_categories):
                            is_relevant = True
                        
                        if is_relevant:
                            relevant_count += 1
                            print(f"      ✅ {i}. {name} [{category}] - {description}...")
                        else:
                            print(f"      ❌ {i}. {name} [{category}] - {description}...")
                    
                    overall_results["relevant_results"] += relevant_count
                    
                    # Вычисляем точность для этого запроса
                    precision = (relevant_count / len(results)) * 100 if results else 0
                    print(f"   📈 Точность: {precision:.1f}% ({relevant_count}/{len(results)})")
                    
                else:
                    print("   ⚠️  Результатов не найдено")
                    
            else:
                print(f"   ❌ Ошибка запроса: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Ошибка: {e}")
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА КАЧЕСТВА ПОИСКА")
    print("=" * 60)
    
    if response_times:
        overall_results["avg_response_time"] = sum(response_times) / len(response_times)
    
    overall_precision = 0
    if overall_results["total_results"] > 0:
        overall_precision = (overall_results["relevant_results"] / overall_results["total_results"]) * 100
    
    print(f"✅ Успешных запросов: {overall_results['successful_queries']}/{overall_results['total_queries']} "
          f"({(overall_results['successful_queries']/overall_results['total_queries']*100):.1f}%)")
    print(f"🎯 Общая точность: {overall_precision:.1f}% "
          f"({overall_results['relevant_results']}/{overall_results['total_results']})")
    print(f"⏱️  Среднее время ответа: {overall_results['avg_response_time']:.0f}ms")
    
    # Оцениваем качество
    if overall_precision >= 80:
        quality_grade = "Отличное"
        quality_emoji = "🌟"
    elif overall_precision >= 60:
        quality_grade = "Хорошее"
        quality_emoji = "👍"
    elif overall_precision >= 40:
        quality_grade = "Удовлетворительное"
        quality_emoji = "👌"
    else:
        quality_grade = "Требует улучшения"
        quality_emoji = "⚠️"
    
    print(f"{quality_emoji} Качество семантического поиска: {quality_grade}")
    
    # Проверяем тип эмбеддингов
    if overall_results["avg_response_time"] > 1000:  # > 1 секунды
        print("🧠 Вероятно используются реальные эмбеддинги OpenAI (медленнее)")
    else:
        print("🔧 Вероятно используются mock эмбеддинги (быстрее)")
    
    return overall_results

def test_semantic_similarity():
    """Тестирует семантическую схожесть результатов"""
    print("\n" + "=" * 60)
    print("🧠 ТЕСТ СЕМАНТИЧЕСКОЙ СХОЖЕСТИ")
    print("=" * 60)
    
    # Тестируем синонимы и связанные термины
    similarity_tests = [
        ("цемент", "портландцемент"),
        ("арматура", "металлическая арматура"),
        ("бетон", "железобетон"),
        ("кирпич", "строительный кирпич"),
        ("cement", "цемент"),  # Английский-русский
    ]
    
    for term1, term2 in similarity_tests:
        print(f"\n🔗 Сравниваю: '{term1}' vs '{term2}'")
        
        try:
            # Получаем результаты для первого термина
            resp1 = requests.get(f"{BASE_URL}/search/", params={"q": term1, "limit": 3})
            resp2 = requests.get(f"{BASE_URL}/search/", params={"q": term2, "limit": 3})
            
            if resp1.status_code == 200 and resp2.status_code == 200:
                results1 = resp1.json()
                results2 = resp2.json()
                
                # Ищем пересечения в результатах
                names1 = {r.get("name", "") for r in results1}
                names2 = {r.get("name", "") for r in results2}
                
                intersection = names1.intersection(names2)
                union = names1.union(names2)
                
                similarity = len(intersection) / len(union) * 100 if union else 0
                
                print(f"   📊 Схожесть результатов: {similarity:.1f}%")
                if intersection:
                    print(f"   🤝 Общие результаты: {', '.join(list(intersection)[:3])}")
                else:
                    print("   ❌ Общих результатов не найдено")
                
        except Exception as e:
            print(f"   💥 Ошибка: {e}")

if __name__ == "__main__":
    # Проверяем доступность API
    try:
        response = requests.get(f"{BASE_URL}/health/", timeout=5)
        if response.status_code == 200:
            print("✅ API доступен, начинаем тестирование...\n")
            test_search_quality()
            test_semantic_similarity()
        else:
            print(f"❌ API недоступен: {response.status_code}")
    except Exception as e:
        print(f"💥 Не удалось подключиться к API: {e}")
        print("Убедитесь, что сервер запущен на http://localhost:8000") 