#!/usr/bin/env python3
"""
AI Fallback модуль для обработки сложных товаров, которые не смог обработать regex парсер.
Оптимизирован для минимизации затрат на API запросы.
"""

import json, os, time, hashlib, yaml
from typing import Optional, Dict, Any, List, Tuple
import openai
from dataclasses import dataclass
from packaging import version


@dataclass
class AIParseResult:
    """Результат обработки товара через AI"""
    metric_unit: str
    price_coefficient: float
    parsing_method: str = "ai_fallback"
    confidence: float = 0.85


class AIFallbackParser:
    """AI парсер для сложных товаров с оптимизацией запросов"""
    
    def __init__(self, api_key: Optional[str] = None, cache_file: str = "ai_cache.json"):
        """
        Инициализация AI парсера
        
        Args:
            api_key: OpenAI API ключ (если None, берется из переменной окружения)
            cache_file: Путь к файлу кеша для хранения результатов
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter")
        
        # Определяем, является ли установленная версия openai "legacy" (< 1.0)
        self._use_legacy_client = version.parse(openai.__version__) < version.parse("1.0.0")

        if self._use_legacy_client:
            # Старый (<1.0) клиент
            openai.api_key = self.api_key
            self._client = openai  # type: ignore
        else:
            # Новый (>=1.0) клиент
            try:
                from openai import OpenAI  # type: ignore
            except ImportError as exc:
                raise ImportError("OpenAI >=1.0 detected but 'OpenAI' class not found") from exc

            self._client = OpenAI(api_key=self.api_key)  # pylint: disable=not-callable
        self.cost_per_token = 0.0015 / 1000  # GPT-3.5-turbo стоимость за токен
        self.total_cost = 0.0
        self.total_requests = 0
        self.total_tokens = 0
        
        # Загрузка промптов
        self._prompts = self._load_prompts()
        
        # Кеширование результатов
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
        # Батчинг запросов
        self.batch_size = 5  # Количество товаров в одном запросе
        self.batch_queue = []
    
    def _load_prompts(self, path: str = "prompts.yaml") -> Dict[str, str]:
        """Читает YAML с шаблонами промптов."""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        # fallback: минимальные шаблоны
        return {
            "system": "Ты эксперт по строительным материалам.",
            "single": "ТОВАР: {name}\nЦЕНА: {price} {unit}",
            "batch_intro": "Товары:",
            "batch_item": "{idx}. {name} - {price} {unit}",
        }
    
    def _load_cache(self) -> Dict:
        """Загружает кеш из файла"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache: {str(e)}")
        return {}
    
    def _save_cache(self):
        """Сохраняет кеш в файл"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {str(e)}")
    
    def _get_cache_key(self, name: str, price: float, unit: str) -> str:
        """Генерирует ключ кеша для товара"""
        # Используем хеш для уникальной идентификации товара
        data = f"{name.lower()}|{price}|{unit.lower()}"
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    
    def parse_product(self, name: str, price: float, unit: str) -> Optional[AIParseResult]:
        """
        Обработка товара через AI
        
        Args:
            name: Название товара
            price: Цена
            unit: Единица измерения
            
        Returns:
            AIParseResult если успешно, None если неудачно
        """
        # Проверяем кеш
        cache_key = self._get_cache_key(name, price, unit)
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            return AIParseResult(
                metric_unit=cached_result['metric_unit'],
                price_coefficient=cached_result['price_coefficient'],
                confidence=cached_result.get('confidence', 0.85)
            )
        
        try:
            # Отправить запрос к OpenAI
            prompt = self._create_prompt(name, price, unit)
            
            response = self._chat_completion([
                {"role": "system", "content": self._prompts["system"]},
                {"role": "user", "content": prompt}
            ], 100)
            
            # Обновить статистику
            self._update_stats(response)
            
            # Парсить ответ
            result = self._parse_ai_response(response.choices[0].message.content, name, price, unit)
            
            # Сохраняем в кеш
            if result:
                self.cache[cache_key] = {
                    'metric_unit': result.metric_unit,
                    'price_coefficient': result.price_coefficient,
                    'confidence': result.confidence
                }
                self._save_cache()
            
            return result
            
        except Exception as e:
            print(f"❌ AI parsing error for '{name}': {str(e)}")
            return None
    
    def parse_batch(self, products: List[Dict]) -> List[Tuple[Dict, Optional[AIParseResult]]]:
        """
        Обработка батча товаров через один запрос к AI
        
        Args:
            products: Список товаров в формате [{"name": str, "price": float, "unit": str}, ...]
            
        Returns:
            Список кортежей (товар, результат)
        """
        # Проверяем кеш для всех товаров
        uncached_products = []
        results = []
        
        for product in products:
            name = product.get('name', '')
            price = float(product.get('price', 0))
            unit = product.get('unit', 'шт')
            
            cache_key = self._get_cache_key(name, price, unit)
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                result = AIParseResult(
                    metric_unit=cached_result['metric_unit'],
                    price_coefficient=cached_result['price_coefficient'],
                    confidence=cached_result.get('confidence', 0.85)
                )
                results.append((product, result))
            else:
                uncached_products.append(product)
                results.append((product, None))
        
        # Если есть некешированные товары, отправляем запрос
        if uncached_products:
            try:
                # Создаем один запрос для всех товаров
                batch_prompt = self._create_batch_prompt(uncached_products)
                
                response = self._chat_completion([
                    {"role": "system", "content": self._prompts["system"]},
                    {"role": "user", "content": batch_prompt}
                ], 500)
                
                # Обновить статистику
                self._update_stats(response)
                
                # Парсить ответ для всех товаров
                batch_results = self._parse_batch_response(response.choices[0].message.content, uncached_products)
                
                # Обновляем результаты и кеш
                for i, product in enumerate(uncached_products):
                    if i < len(batch_results) and batch_results[i]:
                        name = product.get('name', '')
                        price = float(product.get('price', 0))
                        unit = product.get('unit', 'шт')
                        
                        cache_key = self._get_cache_key(name, price, unit)
                        self.cache[cache_key] = {
                            'metric_unit': batch_results[i].metric_unit,
                            'price_coefficient': batch_results[i].price_coefficient,
                            'confidence': batch_results[i].confidence
                        }
                        
                        # Обновляем результат в общем списке
                        for j, (orig_product, _) in enumerate(results):
                            if orig_product.get('name') == name:
                                results[j] = (orig_product, batch_results[i])
                                break
                
                # Сохраняем кеш
                self._save_cache()
                
            except Exception as e:
                print(f"❌ AI batch parsing error: {str(e)}")
        
        return results
    
    def _create_prompt(self, name: str, price: float, unit: str) -> str:
        """Создать оптимизированный промпт для AI"""
        return self._prompts["single"].format(name=name, price=price, unit=unit)
    
    def _create_batch_prompt(self, products: List[Dict]) -> str:
        """Создать оптимизированный промпт для батча товаров"""
        intro = self._prompts["batch_intro"].strip() + "\n"
        products_text = intro
        for i, product in enumerate(products):
            name = product.get('name', '')
            price = float(product.get('price', 0))
            unit = product.get('unit', 'шт')
            item_fmt = self._prompts["batch_item"].format(idx=i+1, name=name, price=price, unit=unit)
            products_text += item_fmt + "\n"
        return products_text
    
    def _parse_ai_response(self, response: str, name: str, price: float, unit: str) -> Optional[AIParseResult]:
        """Парсить ответ AI"""
        try:
            # Извлечь JSON из ответа
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return None
                
            json_str = json_match.group()
            data = json.loads(json_str)
            
            # Валидировать данные
            metric_unit = data.get('metric_unit', '').strip()
            price_coefficient = float(data.get('price_coefficient', 0))
            
            if not metric_unit or price_coefficient <= 0:
                return None
            
            return AIParseResult(
                metric_unit=metric_unit,
                price_coefficient=price_coefficient,
                confidence=0.85
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"❌ AI response parsing error: {str(e)}")
            return None
    
    def _parse_batch_response(self, response: str, products: List[Dict]) -> List[Optional[AIParseResult]]:
        """Парсить ответ AI для батча товаров"""
        try:
            # Извлечь JSON-массив из ответа
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if not json_match:
                return [None] * len(products)
                
            json_str = json_match.group()
            data_list = json.loads(json_str)
            
            results = []
            allowed_units = {"м3", "м2", "кг", "л", "м"}
            for i, data in enumerate(data_list):
                if i >= len(products):
                    break

                # Если элемент None или не словарь — считаем неудачным
                if not isinstance(data, dict):
                    results.append(None)
                    continue

                metric_unit_raw = data.get("metric_unit")
                price_coef_raw = data.get("price_coefficient")

                try:
                    metric_unit = str(metric_unit_raw).strip() if metric_unit_raw is not None else ""
                except Exception:
                    metric_unit = ""

                try:
                    price_coefficient = float(price_coef_raw)
                except Exception:
                    price_coefficient = 0.0

                valid = metric_unit in allowed_units and price_coefficient > 0

                if not valid:
                    results.append(None)
                else:
                    results.append(
                        AIParseResult(
                            metric_unit=metric_unit,
                            price_coefficient=price_coefficient,
                            confidence=0.85,
                        )
                    )
            
            # Добавляем None для оставшихся товаров, если ответ неполный
            while len(results) < len(products):
                results.append(None)
                
            return results
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"❌ AI batch response parsing error: {str(e)}")
            return [None] * len(products)
    
    def _update_stats(self, response):
        """Обновить статистику использования AI"""
        self.total_requests += 1
        
        # Получаем токены из ответа, если доступны
        if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
            tokens = response.usage.total_tokens
        else:
            tokens = 150  # Примерно 150 токенов на запрос
            
        self.total_tokens += tokens
        request_cost = tokens * self.cost_per_token
        self.total_cost += request_cost
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику использования AI"""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost,
            "total_cost_rub": self.total_cost * 75,  # Примерный курс доллара
            "cost_per_request_rub": (self.total_cost * 75) / max(1, self.total_requests),
            "cache_size": len(self.cache)
        }

    # ---------------------------------------------------------------------
    # Internal helpers for compatibility with openai <1.0 and >=1.0
    # ---------------------------------------------------------------------

    def _chat_completion(self, messages: List[Dict[str, str]], max_tokens: int) -> Any:  # noqa: ANN401
        """Выполняет chat completion с учётом версии клиента."""
        if self._use_legacy_client:
            return self._client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1,
            )

        # Новый клиент
        return self._client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1,
        )


class HybridParser:
    """Гибридный парсер: regex + AI fallback"""
    
    def __init__(self, regex_parser, ai_parser: Optional[AIFallbackParser] = None):
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


def main():
    """Тестовая функция"""
    import json
    from regex_parser import RegexParser
    
    # Загрузить тестовые данные
    with open('price_sample.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    # Создать парсеры
    regex_parser = RegexParser()
    
    # Проверить доступность AI
    ai_parser = None
    if os.getenv('OPENAI_API_KEY'):
        try:
            ai_parser = AIFallbackParser()
            print("✅ AI fallback парсер активирован")
        except Exception as e:
            print(f"⚠️ AI fallback недоступен: {str(e)}")
    else:
        print("⚠️ AI fallback недоступен: нет OPENAI_API_KEY")
    
    # Создать гибридный парсер
    hybrid_parser = HybridParser(regex_parser, ai_parser)
    
    # Тестировать парсер
    results = []
    
    # Батчинг для экономии запросов
    batch_size = 5
    for i in range(0, len(products), batch_size):
        batch = products[i:i+batch_size]
        batch_results = hybrid_parser.parse_batch(batch)
        results.extend(batch_results)
        print(f"Обработан батч {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size}")
    
    # Вывести статистику
    stats = hybrid_parser.get_stats()
    print(f"\n📊 СТАТИСТИКА:")
    print(f"Всего товаров: {stats['total_products']}")
    print(f"Regex успешно: {stats['regex_success']} ({stats['regex_success_rate']:.1f}%)")
    print(f"AI fallback: {stats['ai_fallback']} ({stats['ai_fallback_rate']:.1f}%)")
    print(f"Не обработано: {stats['total_failed']} ({100 - stats['total_success_rate']:.1f}%)")
    print(f"Общий успех: {stats['total_success_rate']:.1f}%")
    
    if 'ai_stats' in stats:
        ai_stats = stats['ai_stats']
        print(f"\n💰 AI ЭКОНОМИКА:")
        print(f"Запросов к AI: {ai_stats['total_requests']}")
        print(f"Всего токенов: {ai_stats['total_tokens']}")
        print(f"Примерная стоимость: {ai_stats['total_cost_rub']:.2f} ₽")
        print(f"Стоимость за запрос: {ai_stats['cost_per_request_rub']:.2f} ₽")
        print(f"Размер кеша: {ai_stats['cache_size']} товаров")
    
    # Сохранить результаты
    with open('ai_fallback_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Результаты сохранены в: ai_fallback_results.json")


if __name__ == "__main__":
    main() 