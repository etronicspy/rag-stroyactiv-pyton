#!/usr/bin/env python3
"""
Гибридный парсер: объединяет regex и AI парсеры для оптимального результата
"""

from typing import Dict, List, Optional, Any
from ai_parser import AIParser, AIParseResult
from regex_parser import RegexParser


class HybridParser:
    """Гибридный парсер: regex + AI fallback"""
    
    def __init__(self, regex_parser: RegexParser, ai_parser: Optional[AIParser] = None):
        """
        Args:
            regex_parser: Основной regex парсер
            ai_parser: AI парсер для fallback (опциональный)
        """
        self.regex_parser = regex_parser
        self.ai_parser = ai_parser
        self.stats = {
            "regex_success": 0,
            "ai_fallback": 0,
            "total_failed": 0
        }
        
        # Очередь для батчинга
        self.batch_queue = []
        self.batch_size = 5  # Максимальный размер батча
    
    def parse_product(self, name: str, price: float, unit: str) -> Dict:
        """
        Обработка товара через гибридный подход
        
        1. Сначала пытаемся regex парсером
        2. Если не получилось - используем AI fallback
        """
        # Попытка 1: Regex парсер
        result = self.regex_parser.parse_product(name, price, unit)
        
        if result.parsing_method != 'no_parsing':
            self.stats["regex_success"] += 1
            return self._convert_to_dict(result)
        
        # Попытка 2: AI fallback
        if self.ai_parser:
            ai_result = self.ai_parser.parse_product(name, price, unit)
            if ai_result:
                self.stats["ai_fallback"] += 1
                # Конвертировать AI результат в единый формат
                return self._convert_ai_to_dict(ai_result, name, price, unit)
        
        # Не удалось обработать
        self.stats["total_failed"] += 1
        return self._convert_to_dict(result)
    
    def parse_batch(self, products: List[Dict]) -> List[Dict]:
        """
        Обработка батча товаров через гибридный подход
        
        Args:
            products: Список товаров в формате [{"name": str, "price": float, "unit": str}, ...]
            
        Returns:
            Список обработанных товаров
        """
        results = []
        ai_fallback_products = []
        
        # Сначала обрабатываем все товары через regex
        for product in products:
            name = product.get('name', '')
            price = float(product.get('price', 0))
            unit = product.get('unit', 'шт')
            
            result = self.regex_parser.parse_product(name, price, unit)
            
            if result.parsing_method != 'no_parsing':
                self.stats["regex_success"] += 1
                results.append(self._convert_to_dict(result))
            else:
                # Добавляем в список для AI fallback
                ai_fallback_products.append(product)
                # Временно добавляем неудачный результат
                results.append(self._convert_to_dict(result))
        
        # Если есть товары для AI fallback и AI парсер доступен
        if ai_fallback_products and self.ai_parser:
            # Обрабатываем батч через AI
            ai_results = self.ai_parser.parse_batch(ai_fallback_products)
            
            # Обновляем результаты
            for product, ai_result in ai_results:
                name = product.get('name', '')
                price = float(product.get('price', 0))
                unit = product.get('unit', 'шт')
                
                if ai_result:
                    self.stats["ai_fallback"] += 1
                    # Находим соответствующий индекс в результатах
                    for i, result in enumerate(results):
                        if result['original_name'] == name:
                            results[i] = self._convert_ai_to_dict(ai_result, name, price, unit)
                            break
                else:
                    self.stats["total_failed"] += 1
        else:
            # Нет AI парсера - все неудачные товары остаются неудачными
            self.stats["total_failed"] += len(ai_fallback_products)
        
        return results
    
    def _convert_to_dict(self, parsed_product) -> Dict:
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
            'confidence': parsed_product.confidence
        }
    
    def _convert_ai_to_dict(self, ai_result: AIParseResult, name: str, price: float, unit: str) -> Dict:
        """Конвертировать AI результат в единый формат"""
        
        quantity = ai_result.price_coefficient
        price_per_unit = price / quantity if quantity > 0 else price
        
        return {
            'original_name': name,
            'original_price': price,
            'original_unit': unit,
            'metric_unit': ai_result.metric_unit,
            'quantity': quantity,
            'price_per_unit': price_per_unit,
            'price_coefficient': quantity,
            'parsing_method': ai_result.parsing_method,
            'confidence': ai_result.confidence
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику гибридного парсера"""
        total = sum(self.stats.values())
        stats = {
            "total_products": total,
            "regex_success": self.stats["regex_success"],
            "ai_fallback": self.stats["ai_fallback"],
            "total_failed": self.stats["total_failed"],
            "regex_success_rate": self.stats["regex_success"] / max(1, total) * 100,
            "ai_fallback_rate": self.stats["ai_fallback"] / max(1, total) * 100,
            "total_success_rate": (self.stats["regex_success"] + self.stats["ai_fallback"]) / max(1, total) * 100
        }
        
        # Добавить статистику AI, если доступна
        if self.ai_parser:
            stats["ai_stats"] = self.ai_parser.get_stats()
        
        return stats 