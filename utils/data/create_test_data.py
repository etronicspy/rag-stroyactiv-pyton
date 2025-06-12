#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для массового создания тестовых данных через API
"""
import requests
import json
from typing import List, Dict

BASE_URL = "http://localhost:8000/api/v1"

def create_categories() -> List[str]:
    """Создаем категории"""
    categories = [
        {"name": "Цемент", "description": "Вяжущие материалы на основе цемента"},
        {"name": "Бетон", "description": "Готовые бетонные смеси"},
        {"name": "Кирпич", "description": "Кирпичные изделия"},
        {"name": "Металл", "description": "Металлические конструкции и арматура"},
        {"name": "Песок", "description": "Песчаные материалы"},
        {"name": "Щебень", "description": "Щебеночные материалы"},
        {"name": "Изоляция", "description": "Изоляционные материалы"},
    ]
    
    created_categories = []
    print("🏗️ Создание категорий...")
    
    for category in categories:
        try:
            response = requests.post(f"{BASE_URL}/reference/categories/", json=category)
            if response.status_code == 200:
                created_categories.append(category["name"])
                print(f"✅ Категория '{category['name']}' создана")
            else:
                print(f"⚠️ Ошибка создания категории '{category['name']}': {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    return created_categories

def create_units() -> List[str]:
    """Создаем единицы измерения"""
    units = [
        {"name": "кг", "description": "Килограмм"},
        {"name": "т", "description": "Тонна"},
        {"name": "м³", "description": "Кубический метр"},
        {"name": "м²", "description": "Квадратный метр"},
        {"name": "м", "description": "Метр"},
        {"name": "шт", "description": "Штука"},
        {"name": "упак", "description": "Упаковка"},
        {"name": "л", "description": "Литр"},
    ]
    
    created_units = []
    print("\n📏 Создание единиц измерения...")
    
    for unit in units:
        try:
            response = requests.post(f"{BASE_URL}/reference/units/", json=unit)
            if response.status_code == 200:
                created_units.append(unit["name"])
                print(f"✅ Единица '{unit['name']}' создана")
            else:
                print(f"⚠️ Ошибка создания единицы '{unit['name']}': {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    return created_units

def create_materials(categories: List[str], units: List[str]) -> List[Dict]:
    """Создаем 10 материалов"""
    materials = [
        {"name": "Портландцемент М400", "category": "Цемент", "unit": "кг", 
         "description": "Высокопрочный портландцемент марки М400 для строительных работ"},
        {"name": "Бетон М300 В22.5", "category": "Бетон", "unit": "м³", 
         "description": "Товарный бетон марки М300 класса В22.5 для фундаментов"},
        {"name": "Кирпич керамический полнотелый", "category": "Кирпич", "unit": "шт", 
         "description": "Красный керамический кирпич полнотелый М150"},
        {"name": "Арматура А500С d12", "category": "Металл", "unit": "м", 
         "description": "Стальная арматура периодического профиля диаметром 12мм"},
        {"name": "Песок речной крупный", "category": "Песок", "unit": "т", 
         "description": "Речной песок крупной фракции для бетонных работ"},
        {"name": "Щебень гранитный 5-20", "category": "Щебень", "unit": "т", 
         "description": "Гранитный щебень фракции 5-20мм для бетона"},
        {"name": "Цемент белый М500", "category": "Цемент", "unit": "кг", 
         "description": "Белый портландцемент М500 для декоративных работ"},
        {"name": "Пенополистирол 100мм", "category": "Изоляция", "unit": "м²", 
         "description": "Пенополистирольные плиты толщиной 100мм для утепления"},
        {"name": "Бетон самоуплотняющийся", "category": "Бетон", "unit": "м³", 
         "description": "Высокотекучий самоуплотняющийся бетон для сложных конструкций"},
        {"name": "Цементно-песчаная смесь", "category": "Цемент", "unit": "кг", 
         "description": "Готовая сухая цементно-песчаная смесь для штукатурных работ"},
    ]
    
    created_materials = []
    print("\n🧱 Создание материалов...")
    
    for i, material in enumerate(materials, 1):
        try:
            response = requests.post(f"{BASE_URL}/materials/", json=material)
            if response.status_code == 200:
                result = response.json()
                created_materials.append(result)
                print(f"✅ {i}. Материал '{material['name']}' создан (ID: {result.get('id', 'N/A')})")
            else:
                print(f"⚠️ Ошибка создания материала '{material['name']}': {response.status_code}")
                print(f"   Ответ: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    return created_materials

def test_search():
    """Тестируем поиск созданных материалов"""
    print("\n🔍 Тестирование поиска...")
    
    search_queries = ["цемент", "бетон", "кирпич", "арматура"]
    
    for query in search_queries:
        try:
            response = requests.get(f"{BASE_URL}/search/?q={query}&limit=3")
            if response.status_code == 200:
                results = response.json()
                print(f"🔍 Поиск '{query}': найдено {len(results)} результатов")
                for result in results[:2]:  # Показываем первые 2
                    print(f"   - {result.get('name', 'N/A')}")
            else:
                print(f"⚠️ Ошибка поиска '{query}': {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")

def main():
    """Основная функция"""
    print("🚀 МАССОВОЕ СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ")
    print("=" * 50)
    
    # Проверяем доступность API
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code != 200:
            print("❌ API недоступен. Убедитесь, что сервер запущен на localhost:8000")
            return
        print("✅ API доступен")
    except Exception as e:
        print(f"❌ Не удается подключиться к API: {e}")
        return
    
    # Создаем данные
    categories = create_categories()
    units = create_units()
    materials = create_materials(categories, units)
    
    # Тестируем поиск
    test_search()
    
    print("\n" + "=" * 50)
    print("✅ СОЗДАНИЕ ДАННЫХ ЗАВЕРШЕНО")
    print(f"📊 Создано: {len(categories)} категорий, {len(units)} единиц, {len(materials)} материалов")
    print("\n🌐 Доступно по адресам:")
    print("   - Материалы: http://localhost:8000/api/v1/materials/")
    print("   - Категории: http://localhost:8000/api/v1/reference/categories/")
    print("   - Единицы: http://localhost:8000/api/v1/reference/units/")
    print("   - Поиск: http://localhost:8000/api/v1/search/?q=цемент")

if __name__ == "__main__":
    main() 