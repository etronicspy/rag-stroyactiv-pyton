#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный модуль для парсинга наименований товаров с извлечением метрических единиц
и пересчетом цены за единицу измерения.

Содержит 13 однозначных паттернов с расширенным покрытием:
1. direct_volume - явно указанный объем (м³, л)  
2. direct_area - явно указанная площадь (м²)
3. direct_weight - явно указанный вес (кг, т, г, мл→л)
4. direct_volume_ml - миллилитры → литры
5. roll_length - рулоны с указанием длины  
6. sheet_area_dimensions - тонкие листы (≤50мм) → площадь
7. volume_dimensions - объемные материалы (>50мм) → объем
8. area_dimensions - двумерные размеры → площадь
9. brackets_dimensions - размеры в скобках
10. spaced_dimensions - размеры с пробелами
11. dimensions_without_unit - размеры без указания единиц измерения
12. brick_dimensions - специальный паттерн для кирпичей
13. gas_concrete_dimensions - специальный паттерн для газобетона
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ParsedProduct:
    """Структура для распарсенного товара"""
    original_name: str
    original_price: float
    original_unit: str
    metric_unit: Optional[str] = None
    quantity: Optional[float] = None
    price_per_unit: Optional[float] = None
    price_coefficient: Optional[float] = None
    parsing_method: Optional[str] = None
    confidence: float = 0.0
    needs_ai_verification: bool = False


class RegexParser:
    """Улучшенный парсер для извлечения метрических единиц из наименований товаров
    
    Использует 13 однозначных паттернов с расширенным покрытием и строгими границами.
    Каждый паттерн дает только один тип единицы измерения.
    """
    
    def __init__(self):
        # Строгие паттерны для извлечения размеров и единиц
        # Каждый паттерн дает только ОДНУ единицу измерения для однозначности
        self.PATTERNS = [
            # 1. Объем (м³, куб.м) - только кубические метры
            (r'\b(\d+[,.]\d+|\d+)\s*(?:м³|м3|куб\.?м|куб\.?\s*м)\b', 'direct_volume'),
            
            # 2. Объем в литрах - только литры  
            (r'\b(\d+[,.]\d+|\d+)\s*(?:литр[а-я]*|л)\b', 'direct_volume_liters'),
            
            # 3. Площадь (м², кв.м) - только квадратные метры
            (r'\b(\d+[,.]\d+|\d+)\s*(?:м²|м2|кв\.?м|кв\.?\s*м)\b', 'direct_area'),
            
            # 4. Вес в кг - только килограммы  
            (r'\b(\d+[,.]\d+|\d+)\s*кг\b', 'direct_weight_kg'),
            
            # 5. Вес в тоннах - конвертируется в кг
            (r'\b(\d+[,.]\d+|\d+)\s*(?:т|тонн[а-я]*)\b', 'direct_weight_tons'),
            
            # 6. Вес в граммах - конвертируется в кг
            (r'\b(\d+[,.]\d+|\d+)\s*(?:грамм[а-я]*|гр|г)\b', 'direct_weight_grams'),
            
            # 7. Миллилитры - конвертируются в литры
            (r'\b(\d+[,.]\d+|\d+)\s*(?:мл|миллилитр[а-я]*)\b', 'direct_volume_ml'),
            
            # 8. Рулоны с длиной
            (r'\b(\d+[,.]\d+|\d+)\s*м\s+в\s+рулоне\b', 'roll_length'),
            
            # 9. Тонкие листы (толщина ≤ 50мм) → площадь (ОДНОЗНАЧНО!)
            (r'\b(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)([1-4]?\d[,.]\d*|[1-4]?\d)\s*мм\b', 'sheet_area_dimensions'),
            
            # 10. Объемные материалы (толщина > 50мм) → объем  
            (r'\b(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)((?:5[1-9]|[6-9]\d|\d{3,})[,.]\d*|(?:5[1-9]|[6-9]\d|\d{3,}))\s*мм\b', 'volume_dimensions'),
            
            # 11. Объемные материалы в метрах → объем
            (r'\b(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)\s*м\b', 'volume_dimensions_m'),
            
            # 12. Двумерные размеры → площадь
            (r'\b(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)\s*(?:мм|м)\b', 'area_dimensions'),
            
            # 13. Размеры в скобках - ПОМЕЧАЕМ КАК НЕОДНОЗНАЧНЫЕ!
            (r'\((\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)\s*(?:мм|м)?\)', 'ambiguous_dimensions'),
            
            # 14. Специальный паттерн для кирпича - ПОМЕЧАЕМ КАК НЕОДНОЗНАЧНЫЕ!
            (r'\bкирпич\b.*?(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)', 'brick_dimensions'),
            
            # 15. Специальный паттерн для газобетона - ПОМЕЧАЕМ КАК НЕОДНОЗНАЧНЫЕ!
            (r'\bгазобетон\b.*?(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)', 'gas_concrete_dimensions'),
            
            # 16. Размеры без указания единиц измерения - ПОМЕЧАЕМ КАК НЕОДНОЗНАЧНЫЕ!
            (r'\b(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)(?:\s*[х×x]\s*)(\d+[,.]\d*|\d+)\b(?!\s*(?:мм|м|см))', 'dimensions_without_unit'),
            
            # 17. Рубероид и другие рулонные материалы
            (r'\bрубероид\b.*?(\d+)(?:\s*[х×x]\s*)(\d+)', 'roofing_material'),
        ]
    
    def parse_product(self, name: str, price: float, unit: str) -> ParsedProduct:
        """Парсит товар и извлекает метрические единицы"""
        
        result = ParsedProduct(
            original_name=name,
            original_price=price,
            original_unit=unit
        )
        
        # Попробуем извлечь метрические единицы из названия
        metric_data = self._extract_metric_from_name(name)
        if metric_data:
            result.metric_unit = metric_data['unit']
            result.quantity = metric_data['quantity']
            result.price_per_unit = price / metric_data['quantity'] if metric_data['quantity'] > 0 else price
            result.price_coefficient = metric_data['quantity']
            result.parsing_method = metric_data['method']
            result.confidence = metric_data['confidence']
            result.needs_ai_verification = metric_data.get('needs_ai_verification', False)
            return result
        
        # Не удалось извлечь - оставляем в исходном виде
        result.parsing_method = 'no_parsing'
        result.confidence = 0.0
        return result
    
    def _extract_metric_from_name(self, name: str) -> Optional[Dict]:
        """Извлекает метрические единицы из названия товара"""
        
        for pattern, method in self.PATTERNS:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                try:
                    return self._process_match(match, method, name)
                except (ValueError, ZeroDivisionError):
                    continue  # Переходим к следующему паттерну при ошибке
        
        return None
    
    def _process_match(self, match, method: str, name: str) -> Optional[Dict]:
        """Обрабатывает найденное совпадение в зависимости от метода"""
        
        if method == 'direct_volume':
            # Объем в м³
            quantity = float(match.group(1).replace(',', '.'))
            return {'unit': 'м3', 'quantity': quantity, 'method': method, 'confidence': 0.9}
        
        elif method == 'direct_volume_liters':
            # Объем в литрах
            quantity = float(match.group(1).replace(',', '.'))
            return {'unit': 'л', 'quantity': quantity, 'method': method, 'confidence': 0.9}
        
        elif method == 'direct_area':
            # Площадь в м²
            quantity = float(match.group(1).replace(',', '.'))
            return {'unit': 'м2', 'quantity': quantity, 'method': method, 'confidence': 0.9}
        
        elif method == 'direct_weight_kg':
            # Вес в кг
            quantity = float(match.group(1).replace(',', '.'))
            return {'unit': 'кг', 'quantity': quantity, 'method': method, 'confidence': 0.9}
        
        elif method == 'direct_weight_tons':
            # Вес в тоннах → конвертируем в кг
            quantity = float(match.group(1).replace(',', '.')) * 1000
            return {'unit': 'кг', 'quantity': quantity, 'method': method, 'confidence': 0.9}
        
        elif method == 'direct_weight_grams':
            # Вес в граммах → конвертируем в кг
            quantity = float(match.group(1).replace(',', '.')) / 1000
            return {'unit': 'кг', 'quantity': quantity, 'method': method, 'confidence': 0.9}
        
        elif method == 'direct_volume_ml':
            # Миллилитры → конвертируем в литры
            quantity = float(match.group(1).replace(',', '.')) / 1000
            return {'unit': 'л', 'quantity': quantity, 'method': method, 'confidence': 0.9}
        
        elif method == 'roll_length':
            # Рулоны - возвращаем длину в метрах
            quantity = float(match.group(1).replace(',', '.'))
            return {'unit': 'м', 'quantity': quantity, 'method': method, 'confidence': 0.9}
        
        elif method == 'sheet_area_dimensions':
            # Тонкие листы → площадь (ВСЕГДА м²)
            length = float(match.group(1).replace(',', '.')) / 1000  # мм → м
            width = float(match.group(2).replace(',', '.')) / 1000   # мм → м
            area = length * width
            return {'unit': 'м2', 'quantity': round(area, 6), 'method': method, 'confidence': 0.9}
        
        elif method in ['volume_dimensions', 'volume_dimensions_m']:
            # Объемные материалы → объем (ВСЕГДА м³)
            length = float(match.group(1).replace(',', '.'))
            width = float(match.group(2).replace(',', '.'))
            height = float(match.group(3).replace(',', '.'))
            
            # Конвертация в метры если нужно
            if method == 'volume_dimensions':  # в мм
                length_m = length / 1000
                width_m = width / 1000
                height_m = height / 1000
            else:  # в м
                length_m = length
                width_m = width
                height_m = height
            
            volume = length_m * width_m * height_m
            return {'unit': 'м3', 'quantity': round(volume, 6), 'method': method, 'confidence': 0.9}
        
        elif method == 'area_dimensions':
            # Двумерные размеры → площадь
            length = float(match.group(1).replace(',', '.'))
            width = float(match.group(2).replace(',', '.'))
            
            # Определяем единицы по контексту
            if 'мм' in match.group(0):
                area = (length / 1000) * (width / 1000)  # мм → м
            else:
                area = length * width  # уже в м
            
            return {'unit': 'м2', 'quantity': round(area, 6), 'method': method, 'confidence': 0.9}
        
        elif method == 'roofing_material':
            # Рубероид и другие рулонные материалы
            length = float(match.group(1).replace(',', '.'))
            width = float(match.group(2).replace(',', '.'))
            
            # Обычно рубероид в метрах, площадь = длина * ширина
            area = length * width
            return {'unit': 'м2', 'quantity': round(area, 6), 'method': method, 'confidence': 0.8}
        
        elif method in ['ambiguous_dimensions', 'brick_dimensions', 'gas_concrete_dimensions', 'dimensions_without_unit']:
            # Неоднозначные размеры - нужна проверка AI!
            length = float(match.group(1).replace(',', '.'))
            width = float(match.group(2).replace(',', '.'))
            height = float(match.group(3).replace(',', '.'))
            
            # Предполагаем миллиметры, но с низкой уверенностью
            if method == 'brick_dimensions' and 'кирпич' in name.lower():
                # Для кирпича обычно используется штука как единица измерения
                # Но размерность неоднозначна (мм или см)
                return {
                    'unit': 'шт', 
                    'quantity': 1.0, 
                    'method': method, 
                    'confidence': 0.5,
                    'needs_ai_verification': True
                }
            
            elif method == 'gas_concrete_dimensions' and 'газобетон' in name.lower():
                # Для газобетона обычно используется штука или м³
                # Но размерность неоднозначна (мм или см)
                return {
                    'unit': 'шт', 
                    'quantity': 1.0, 
                    'method': method, 
                    'confidence': 0.5,
                    'needs_ai_verification': True
                }
            
            # Для других неоднозначных случаев - пометить для проверки AI
            return {
                'unit': 'шт',  # Временно используем штуки
                'quantity': 1.0,
                'method': method,
                'confidence': 0.3,  # Низкая уверенность
                'needs_ai_verification': True
            }
        
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
            'original_price': parsed_product.original_price,
            'original_unit': parsed_product.original_unit,
            'metric_unit': parsed_product.metric_unit,
            'quantity': parsed_product.quantity,
            'price_per_unit': parsed_product.price_per_unit,
            'price_coefficient': parsed_product.price_coefficient,
            'parsing_method': parsed_product.parsing_method,
            'confidence': parsed_product.confidence,
            'needs_ai_verification': parsed_product.needs_ai_verification
        }


 