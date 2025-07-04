#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой пример использования гибридного парсера цен строительных материалов
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from regex_parser import RegexParser
from ai_fallback import AIFallbackParser, HybridParser

# Загружаем переменные окружения из .env.local в корне проекта, если он существует
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / '.env.local', override=False)

# Создаем парсеры
regex_parser = RegexParser()

# Пример данных
products = [
    {"name": "Цемент 50кг", "price": 300.0, "unit": "меш"},
    {"name": "OSB-3 2500x1250x12 мм", "price": 919.0, "unit": "шт"},
    {"name": "Кирпич полнотелый М-150 (250x120x65)", "price": 13.0, "unit": "шт"},
]

# 1. Только Regex парсер
print("\n1. ТОЛЬКО REGEX ПАРСЕР")
print("-" * 50)
for product in products:
    result = regex_parser.parse_product(product["name"], product["price"], product["unit"])
    print(f"📦 {product['name']}")
    if result.parsing_method != 'no_parsing':
        print(f"  ✅ {result.quantity} {result.metric_unit}, {result.price_per_unit:.2f} руб/{result.metric_unit}")
    else:
        print(f"  ❌ Не удалось обработать regex парсером")
    print()

# 2. Гибридный парсер (если доступен API ключ)
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print("\n2. ГИБРИДНЫЙ ПАРСЕР")
    print("-" * 50)
    
    ai_parser = AIFallbackParser(api_key=api_key)
    hybrid_parser = HybridParser(regex_parser, ai_parser)
    
    results = hybrid_parser.parse_batch(products)
    
    for i, (product, result) in enumerate(zip(products, results)):
        print(f"📦 {product['name']}")
        if result['parsing_method'] != 'no_parsing':
            print(f"  ✅ {result['quantity']} {result['metric_unit']}, {result['price_per_unit']:.2f} руб/{result['metric_unit']}")
            print(f"  📊 Метод: {result['parsing_method']}")
        else:
            print(f"  ❌ Не удалось обработать")
        print()
    
    # Статистика
    stats = hybrid_parser.get_stats()
    print("\n📊 СТАТИСТИКА:")
    print(f"Всего товаров: {stats['total_products']}")
    print(f"Regex успешно: {stats['regex_success']} ({stats['regex_success_rate']:.1f}%)")
    print(f"AI fallback: {stats['ai_fallback']} ({stats['ai_fallback_rate']:.1f}%)")
    print(f"Не обработано: {stats['total_failed']} ({100 - stats['total_success_rate']:.1f}%)")
else:
    print("\n⚠️ Гибридный парсер недоступен: нет OPENAI_API_KEY")
    print("   Для тестирования установите переменную окружения OPENAI_API_KEY") 