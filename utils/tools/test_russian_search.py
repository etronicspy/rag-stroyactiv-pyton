#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест поиска на русском языке
"""
import asyncio
import requests
import json
from typing import List, Dict
import sys

def test_search_api(query: str, limit: int = 3) -> None:
    """Тестирует API поиска с русским запросом"""
    url = "http://localhost:8000/api/v1/search/"
    params = {"q": query, "limit": limit}
    
    print(f"\n🔍 Поиск: '{query}'")
    print(f"URL: {url}")
    print(f"Параметры: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
        print(f"Encoding: {response.encoding}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Найдено результатов: {len(data)}")
            
            for i, item in enumerate(data[:3], 1):
                print(f"\n  {i}. {item.get('name', 'Без названия')}")
                print(f"     Категория: {item.get('category', 'Не указана')}")
                print(f"     Единица: {item.get('unit', 'Не указана')}")
                print(f"     Описание: {item.get('description', 'Отсутствует')}")
        else:
            print(f"Ошибка: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        print(f"Ответ сервера: {response.text[:200]}...")

def test_create_material(name: str, category: str, unit: str, description: str) -> None:
    """Создает материал с русскими названиями"""
    url = "http://localhost:8000/api/v1/materials/"
    data = {
        "name": name,
        "category": category,
        "unit": unit,
        "description": description
    }
    
    print(f"\n➕ Создание материала: '{name}'")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Материал создан с ID: {result.get('id')}")
        else:
            print(f"❌ Ошибка создания: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Основная функция тестирования"""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ ПОИСКА НА РУССКОМ ЯЗЫКЕ")
    print("=" * 60)
    
    # Проверяем доступность сервера
    try:
        response = requests.get("http://localhost:8000/api/v1/health/", timeout=5)
        if response.status_code == 200:
            print("✅ Сервер доступен")
        else:
            print(f"⚠️ Сервер отвечает с кодом: {response.status_code}")
    except Exception as e:
        print(f"❌ Сервер недоступен: {e}")
        print("Убедитесь, что сервер запущен: python3 -m uvicorn main:app --port 8000")
        return
    
    # Создаем тестовые материалы с русскими названиями
    test_materials = [
        ("Цемент М400 (белый)", "Цемент", "кг", "Высококачественный белый цемент для декоративных работ"),
        ("Бетон М300", "Бетон", "м³", "Готовый бетон средней прочности для фундаментов"),
        ("Арматура А500С", "Металл", "м", "Стальная арматура для железобетонных конструкций"),
        ("Кирпич керамический красный", "Кирпич", "шт", "Строительный кирпич из глины"),
        ("Песок речной мытый", "Песок", "т", "Очищенный речной песок для строительных работ")
    ]
    
    print("\n📋 Создание тестовых материалов...")
    for name, category, unit, description in test_materials:
        test_create_material(name, category, unit, description)
        
    # Тестируем различные поисковые запросы
    test_queries = [
        "цемент",
        "белый цемент",
        "бетон для фундамента",
        "арматура стальная",
        "кирпич красный",
        "песок речной",
        "материал для строительства",
        "прочный бетон М300",
        "декоративный цемент",
        "железобетон"
    ]
    
    print(f"\n🔍 Тестирование поиска ({len(test_queries)} запросов)...")
    for query in test_queries:
        test_search_api(query)
        
    # Тестируем специальные символы и Unicode
    print(f"\n🌏 Тестирование Unicode и специальных символов...")
    unicode_queries = [
        "цемент М-400 (прочный)",
        "бетон ★ премиум",
        "материал №1",
        "строительные материалы 2024"
    ]
    
    for query in unicode_queries:
        test_search_api(query)
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)

if __name__ == "__main__":
    main() 