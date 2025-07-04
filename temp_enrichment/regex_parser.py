#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для парсинга наименований товаров с извлечением метрических единиц
и пересчетом цены за единицу измерения.

Содержит 5 строгих паттернов:
1. direct_volume - явно указанный объем (м³, л)
2. direct_area - явно указанная площадь (м²)
3. direct_weight - явно указанный вес (кг, т)
4. area_from_dimensions - размеры С единицами измерения (мм, м)
5. volume_from_dimensions - размеры С единицами измерения (мм, м)
"""

import re
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass


@dataclass
class ParsedProduct:
    """Структура для распарсенного товара"""
    original_name: str
    clean_name: str
    original_price: float
    original_unit: str
    metric_unit: Optional[str] = None
    quantity: Optional[float] = None
    price_per_unit: Optional[float] = None
    price_coefficient: Optional[float] = None
    parsing_method: Optional[str] = None
    confidence: float = 0.0


class RegexParser:
    """Парсер для извлечения метрических единиц из наименований товаров
    
    Использует только 5 строгих паттернов без предположений:
    1. direct_volume - явно указанный объем (м³, л)
    2. direct_area - явно указанная площадь (м²)
    3. direct_weight - явно указанный вес (кг, т)
    4. area_from_dimensions - размеры С единицами измерения (мм, м)
    5. volume_from_dimensions - размеры С единицами измерения (мм, м)
    """
    
    def __init__(self):
        # Метрические единицы и их коэффициенты
        self.METRIC_UNITS = {
            'м': 1, 'м2': 1, 'м3': 1, 'кг': 1, 'т': 1000, 'л': 1,
            'метр': 1, 'метра': 1, 'метров': 1,
            'кв.м': 1, 'кв м': 1, 'м²': 1, 'м³': 1,
            'куб.м': 1, 'куб м': 1, 'куб.': 1,
            'литр': 1, 'литра': 1, 'литров': 1,
            'грамм': 0.001, 'грамма': 0.001, 'граммов': 0.001, 'гр': 0.001, 'г': 0.001
        }
        
        # Строгие паттерны для извлечения размеров и единиц
        self.PATTERNS = [
            # 1. Объем (м³, куб.м, литры) - с поддержкой запятой как десятичного разделителя
            (r'(\d+[,.]\d+|\d+)\s*(м³|м3|куб\.?м|куб\.?\s*м|литр[а-я]*|л)\b', 'direct_volume'),
            
            # 2. Площадь (м², кв.м) - с поддержкой запятой
            (r'(\d+[,.]\d+|\d+)\s*(м²|м2|кв\.?м|кв\.?\s*м)\b', 'direct_area'),
            
            # 3. Вес (кг, т, г) - с поддержкой запятой
            (r'(\d+[,.]\d+|\d+)\s*(кг|т|тонн[а-я]*|грамм[а-я]*|гр|г)\b', 'direct_weight'),
            
            # 4. Размеры 2D с единицами (ДxШ в мм или м) - для расчета площади
            (r'(\d+[,.]\d*|\d+)(?:х|x|×)(\d+[,.]\d*|\d+)\s*(мм|м)\b', 'area_from_dimensions'),
            
            # 5. Размеры 3D с единицами (ДxШxВ в мм или м) - для расчета объема
            (r'(\d+[,.]\d*|\d+)(?:х|x|×)(\d+[,.]\d*|\d+)(?:х|x|×)(\d+[,.]\d*|\d+)\s*(мм|м)\b', 'volume_from_dimensions'),
        ]
    
    def parse_product(self, name: str, price: float, unit: str) -> ParsedProduct:
        """Парсит товар и извлекает метрические единицы"""
        
        result = ParsedProduct(
            original_name=name,
            clean_name=name,
            original_price=price,
            original_unit=unit
        )
        
        # Попробуем извлечь метрические единицы прямо из названия
        metric_data = self._extract_metric_from_name(name)
        if metric_data:
            result.metric_unit = metric_data['unit']
            result.quantity = metric_data['quantity']
            result.price_per_unit = price / metric_data['quantity'] if metric_data['quantity'] > 0 else price
            result.price_coefficient = metric_data['quantity']
            result.parsing_method = metric_data['method']
            result.confidence = 0.9
            return result
        
        # Не удалось извлечь - возвращаем как есть
        result.parsing_method = 'no_parsing'
        result.confidence = 0.0
        return result
    
    def _extract_metric_from_name(self, name: str) -> Optional[Dict]:
        """Извлекает метрические единицы прямо из названия"""
        
        for pattern, method in self.PATTERNS:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                if method in ['direct_volume', 'direct_area', 'direct_weight']:
                    # Для прямых единиц (объем, площадь, вес)
                    quantity_str = match.group(1)
                    unit_str = match.group(2).lower()
                    
                    # Обрабатываем запятую как десятичный разделитель
                    quantity_str = quantity_str.replace(',', '.')
                    quantity = float(quantity_str)
                    
                    # Нормализуем единицу
                    normalized_unit = self._normalize_unit(unit_str, method)
                    if normalized_unit:
                        return {
                            'unit': normalized_unit,
                            'quantity': quantity,
                            'method': method
                        }
                
                elif method == 'area_from_dimensions':
                    # Для площади из размеров (ДxШ)
                    length_str = match.group(1).replace(',', '.')
                    width_str = match.group(2).replace(',', '.')
                    unit_str = match.group(3).lower()
                    
                    length = float(length_str)
                    width = float(width_str)
                    
                    # Конвертируем мм в м если нужно
                    if unit_str == 'мм':
                        length /= 1000
                        width /= 1000
                    
                    area = length * width
                    return {
                        'unit': 'м2',
                        'quantity': round(area, 6),
                        'method': method
                    }
                
                elif method == 'volume_from_dimensions':
                    # Три размера. Если третье значение (толщина) <= 50 мм – это листовой материал → площадь
                    length_str = match.group(1).replace(',', '.')
                    width_str = match.group(2).replace(',', '.')
                    height_str = match.group(3).replace(',', '.')
                    unit_str = match.group(4).lower()
                    
                    # Конвертация единиц
                    if unit_str == 'мм':
                        length /= 1000
                        width /= 1000
                        height_mm = float(height_str)
                        thickness_m = height_mm / 1000
                    else:
                        height_mm = float(height_str) * 1000  # в м указаны, для проверки толщины
                        thickness_m = float(height_str)

                    # Если толщина <= 0.05 м (50 мм) → считаем площадью
                    if thickness_m <= 0.05:
                        area = length * width
                        return {
                            'unit': 'м2',
                            'quantity': round(area, 6),
                            'method': 'area_from_dimensions'
                        }

                    # Иначе считаем объём
                    if unit_str == 'мм':
                        height = height_mm / 1000
                    else:
                        height = thickness_m
                    volume = length * width * height
                    return {
                        'unit': 'м3',
                        'quantity': round(volume, 6),
                        'method': method
                    }
        
        return None
    
    def _normalize_unit(self, unit_str: str, method: str) -> Optional[str]:
        """Нормализует единицу измерения"""
        
        if method == 'direct_volume':
            if unit_str in ['м³', 'м3', 'куб.м', 'куб м', 'куб.']:
                return 'м3'
            elif unit_str in ['литр', 'литра', 'литров', 'л']:
                return 'л'
        
        elif method == 'direct_area':
            if unit_str in ['м²', 'м2', 'кв.м', 'кв м']:
                return 'м2'
        
        elif method == 'direct_weight':
            if unit_str in ['кг']:
                return 'кг'
            elif unit_str in ['т', 'тонн', 'тонна', 'тонны']:
                return 'т'
            elif unit_str in ['грамм', 'грамма', 'граммов', 'гр', 'г']:
                return 'кг'  # Конвертируем в кг
        
        return None
    
    def parse_price_list(self, products: List[Dict]) -> List[ParsedProduct]:
        """Парсит список товаров"""
        
        results = []
        for product in products:
            name = product.get('name', '')
            price = float(product.get('price', 0))
            unit = product.get('unit', 'шт')
            
            parsed = self.parse_product(name, price, unit)
            results.append(parsed)
        
        return results
    
    def to_dict(self, parsed_product: ParsedProduct) -> Dict:
        """Конвертирует ParsedProduct в словарь"""
        
        return {
            'original_name': parsed_product.original_name,
            'clean_name': parsed_product.clean_name,
            'original_price': parsed_product.original_price,
            'original_unit': parsed_product.original_unit,
            'metric_unit': parsed_product.metric_unit,
            'quantity': parsed_product.quantity,
            'price_per_unit': parsed_product.price_per_unit,
            'price_coefficient': parsed_product.price_coefficient,
            'parsing_method': parsed_product.parsing_method,
            'confidence': parsed_product.confidence
        }


def main():
    """Тестовая функция"""
    import json
    
    # Загрузить тестовые данные
    with open('price_sample.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    # Создать парсер
    parser = RegexParser()
    
    # Парсить товары
    results = []
    success_count = 0
    
    for product in products:
        parsed = parser.parse_product(product['name'], product['price'], product['unit'])
        result_dict = parser.to_dict(parsed)
        results.append(result_dict)
        
        if parsed.parsing_method != 'no_parsing':
            success_count += 1
            print(f"✅ {parsed.original_name} → {parsed.quantity} {parsed.metric_unit}, "
                  f"{parsed.price_per_unit:.2f} руб/{parsed.metric_unit}")
        else:
            print(f"❌ {parsed.original_name}")
    
    # Вывести статистику
    total = len(products)
    success_rate = success_count / total * 100
    
    print(f"\n📊 СТАТИСТИКА:")
    print(f"Всего товаров: {total}")
    print(f"Успешно обработано: {success_count} ({success_rate:.1f}%)")
    print(f"Не обработано: {total - success_count} ({100 - success_rate:.1f}%)")
    
    # Сохранить результаты
    with open('regex_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Результаты сохранены в: regex_results.json")


if __name__ == "__main__":
    main() 