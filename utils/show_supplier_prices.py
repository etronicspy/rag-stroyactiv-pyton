#!/usr/bin/env python3
"""
Утилита для просмотра структуры содержимого прайсов поставщика
"""

import requests
import json
import sys
import os
from typing import Dict, List, Any
from collections import Counter

# Добавляем корневую папку проекта в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def format_price(price: float, currency: str = "RUB") -> str:
    """Форматировать цену для отображения"""
    if price is None:
        return "N/A"
    currency_symbol = {"RUB": "₽", "USD": "$", "EUR": "€"}.get(currency, currency)
    return f"{price:.2f} {currency_symbol}"

def truncate_text(text: str, max_length: int = 30) -> str:
    """Обрезать текст с многоточием"""
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length-3] + "..."

def show_supplier_prices(supplier_id: str, api_url: str = "http://localhost:8000"):
    """Показать структуру прайсов поставщика"""
    
    print("=" * 80)
    print(f"📋 СТРУКТУРА ПРАЙСОВ ПОСТАВЩИКА: {supplier_id}")
    print("=" * 80)
    
    try:
        # Получаем все прайс-листы поставщика
        response = requests.get(f"{api_url}/api/v1/prices/{supplier_id}/all")
        
        if response.status_code == 404:
            print(f"❌ Поставщик '{supplier_id}' не найден или у него нет прайс-листов")
            return
        elif response.status_code != 200:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return
            
        data = response.json()
        
        if data["total_price_lists"] == 0:
            print(f"📭 У поставщика '{supplier_id}' нет загруженных прайс-листов")
            return
        
        print(f"📊 Всего прайс-листов: {data['total_price_lists']}")
        print()
        
        # Анализ по каждому прайс-листу
        for i, price_list in enumerate(data["price_lists"], 1):
            print(f"📋 Прайс-лист #{i}")
            print(f"   📅 Дата загрузки: {price_list['upload_date']}")
            print(f"   📦 Количество материалов: {price_list['materials_count']}")
            
            materials = price_list["materials"]
            if not materials:
                print("   📭 Нет материалов")
                continue
            
            # Анализ структуры данных
            analyze_materials_structure(materials)
            
            # Показать примеры материалов
            print(f"\n   📦 ПРИМЕРЫ МАТЕРИАЛОВ (показано до 5):")
            show_materials_sample(materials[:5])
            
            print("-" * 60)
        
        # Общая статистика по всем прайс-листам
        all_materials = []
        for price_list in data["price_lists"]:
            all_materials.extend(price_list["materials"])
        
        if all_materials:
            print(f"\n📊 ОБЩАЯ СТАТИСТИКА (всего материалов: {len(all_materials)}):")
            show_overall_statistics(all_materials)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения с API: {e}")
        print("Убедитесь, что сервер запущен на http://localhost:8000")
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

def analyze_materials_structure(materials: List[Dict[str, Any]]):
    """Анализ структуры данных материалов"""
    
    if not materials:
        return
    
    # Определяем формат прайс-листа
    sample_material = materials[0]
    
    # Новый расширенный формат
    if any(key in sample_material for key in ["sku", "unit_price", "calc_unit", "pricelistid"]):
        print("   🆕 Формат: Расширенный (новый)")
        analyze_extended_format(materials)
    else:
        print("   📝 Формат: Базовый (legacy)")
        analyze_legacy_format(materials)

def analyze_extended_format(materials: List[Dict[str, Any]]):
    """Анализ расширенного формата материалов"""
    
    # Собираем статистику по полям
    field_stats = {}
    price_types = ["unit_price", "unit_calc_price", "buy_price", "sale_price"]
    
    for material in materials:
        for field in material.keys():
            if field not in field_stats:
                field_stats[field] = {"total": 0, "filled": 0}
            field_stats[field]["total"] += 1
            if material[field] is not None and material[field] != "":
                field_stats[field]["filled"] += 1
    
    print("   📊 Заполненность полей:")
    key_fields = ["name", "sku", "use_category", "calc_unit"] + price_types
    for field in key_fields:
        if field in field_stats:
            filled = field_stats[field]["filled"]
            total = field_stats[field]["total"]
            percentage = (filled / total * 100) if total > 0 else 0
            print(f"      • {field}: {filled}/{total} ({percentage:.1f}%)")
    
    # Анализ цен
    print("   💰 Типы цен:")
    for price_type in price_types:
        prices = [m.get(price_type) for m in materials if m.get(price_type) is not None]
        if prices:
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            currency = materials[0].get(f"{price_type}_currency", "RUB")
            print(f"      • {price_type}: {len(prices)} материалов, ср. {format_price(avg_price, currency)}, мин-макс: {format_price(min_price, currency)}-{format_price(max_price, currency)}")

def analyze_legacy_format(materials: List[Dict[str, Any]]):
    """Анализ базового формата материалов"""
    
    # Категории
    categories = [m.get("use_category") for m in materials if m.get("use_category")]
    category_counts = Counter(categories)
    
    print(f"   🏷️ Категории ({len(category_counts)}):")
    for category, count in category_counts.most_common(5):
        print(f"      • {category}: {count} материалов")
    
    # Единицы измерения
    units = [m.get("unit") for m in materials if m.get("unit")]
    unit_counts = Counter(units)
    
    print(f"   📏 Единицы измерения ({len(unit_counts)}):")
    for unit, count in unit_counts.most_common(5):
        print(f"      • {unit}: {count} материалов")
    
    # Цены
    prices = [m.get("price") for m in materials if m.get("price") is not None]
    if prices:
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        print(f"   💰 Цены: ср. {format_price(avg_price)}, мин-макс: {format_price(min_price)}-{format_price(max_price)}")

def show_materials_sample(materials: List[Dict[str, Any]]):
    """Показать примеры материалов"""
    
    if not materials:
        return
    
    # Определяем формат и показываем соответствующую таблицу
    sample_material = materials[0]
    
    if any(key in sample_material for key in ["sku", "unit_price", "calc_unit"]):
        show_extended_materials_table(materials)
    else:
        show_legacy_materials_table(materials)

def show_extended_materials_table(materials: List[Dict[str, Any]]):
    """Показать таблицу материалов в расширенном формате"""
    
    print(f"      {'№':<2} {'Название':<25} {'SKU':<12} {'Категория':<15} {'Ед.':<8} {'Цена (основная)':<15}")
    print("      " + "-" * 82)
    
    for i, material in enumerate(materials, 1):
        name = truncate_text(material.get("name", ""), 25)
        sku = truncate_text(material.get("sku", ""), 12)
        category = truncate_text(material.get("use_category", ""), 15)
        unit = truncate_text(material.get("calc_unit", ""), 8)
        
        # Приоритет цен: unit_price > sale_price > buy_price > unit_calc_price
        price = None
        currency = "RUB"
        for price_field in ["unit_price", "sale_price", "buy_price", "unit_calc_price"]:
            if material.get(price_field) is not None:
                price = material[price_field]
                currency = material.get(f"{price_field}_currency", "RUB")
                break
        
        price_str = format_price(price, currency) if price is not None else "N/A"
        
        print(f"      {i:<2} {name:<25} {sku:<12} {category:<15} {unit:<8} {price_str:<15}")

def show_legacy_materials_table(materials: List[Dict[str, Any]]):
    """Показать таблицу материалов в базовом формате"""
    
    print(f"      {'№':<2} {'Название':<30} {'Категория':<20} {'Ед.':<8} {'Цена':<12}")
    print("      " + "-" * 75)
    
    for i, material in enumerate(materials, 1):
        name = truncate_text(material.get("name", ""), 30)
        category = truncate_text(material.get("use_category", ""), 20)
        unit = truncate_text(material.get("unit", ""), 8)
        price = material.get("price")
        price_str = format_price(price) if price is not None else "N/A"
        
        print(f"      {i:<2} {name:<30} {category:<20} {unit:<8} {price_str:<12}")

def show_overall_statistics(all_materials: List[Dict[str, Any]]):
    """Показать общую статистику по всем материалам"""
    
    # Уникальные категории
    categories = set(m.get("use_category") for m in all_materials if m.get("use_category"))
    print(f"   🏷️ Уникальных категорий: {len(categories)}")
    
    # Уникальные единицы измерения
    units = set()
    for m in all_materials:
        if m.get("unit"):
            units.add(m.get("unit"))
        if m.get("calc_unit"):
            units.add(m.get("calc_unit"))
    print(f"   📏 Уникальных единиц измерения: {len(units)}")
    
    # Статистика по ценам
    all_prices = []
    for m in all_materials:
        # Собираем все виды цен
        for price_field in ["price", "unit_price", "sale_price", "buy_price", "unit_calc_price"]:
            price = m.get(price_field)
            if price is not None:
                all_prices.append(price)
    
    if all_prices:
        print(f"   💰 Всего цен: {len(all_prices)}")
        print(f"   💰 Диапазон цен: {format_price(min(all_prices))} - {format_price(max(all_prices))}")
        print(f"   💰 Средняя цена: {format_price(sum(all_prices) / len(all_prices))}")

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("Использование: python utils/show_supplier_prices.py <supplier_id>")
        print()
        print("Примеры:")
        print("  python utils/show_supplier_prices.py Поставщик_Строй_Материалы")
        print("  python utils/show_supplier_prices.py supplier_1")
        return
    
    supplier_id = sys.argv[1]
    show_supplier_prices(supplier_id)

if __name__ == "__main__":
    main() 