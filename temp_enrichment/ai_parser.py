#!/usr/bin/env python3
"""
AI парсер для обработки сложных товаров, которые не смог обработать regex парсер.
Оптимизирован для минимизации затрат на API запросы.
"""

import json
import os
import time
import hashlib
import yaml
from typing import Optional, Dict, Any, List, Tuple
import openai
from dataclasses import dataclass
from packaging import version
from config import load_project_config


@dataclass
class AIParseResult:
    """Результат обработки товара через AI"""
    metric_unit: str
    price_coefficient: float
    parsing_method: str = "ai_fallback"
    confidence: float = 0.85


class AIParser:
    """AI парсер для сложных товаров с оптимизацией запросов"""
    
    def __init__(self, api_key: Optional[str] = None, cache_file: str = "ai_cache.json"):
        """
        Инициализация AI парсера
        
        Args:
            api_key: OpenAI API ключ (если None, берется из переменной окружения)
            cache_file: Путь к файлу кеша для хранения результатов
        """
        # Загружаем конфигурацию из .env.local файла
        if not api_key:
            load_project_config()
        
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
        
        # Статистика использования
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
                
                # Парсить ответ
                batch_results = self._parse_batch_response(response.choices[0].message.content, uncached_products)
                
                # Обновить результаты и кеш
                uncached_idx = 0
                for i, (product, result) in enumerate(results):
                    if result is None:  # Не был в кеше
                        parsed_result = batch_results[uncached_idx] if uncached_idx < len(batch_results) else None
                        results[i] = (product, parsed_result)
                        
                        # Сохранить в кеш
                        if parsed_result:
                            name = product.get('name', '')
                            price = float(product.get('price', 0))
                            unit = product.get('unit', 'шт')
                            cache_key = self._get_cache_key(name, price, unit)
                            self.cache[cache_key] = {
                                'metric_unit': parsed_result.metric_unit,
                                'price_coefficient': parsed_result.price_coefficient,
                                'confidence': parsed_result.confidence
                            }
                        
                        uncached_idx += 1
                
                # Сохранить кеш
                self._save_cache()
                
            except Exception as e:
                print(f"❌ Batch AI parsing error: {str(e)}")
                # Оставить None для всех некешированных товаров
        
        return results
    
    def _create_prompt(self, name: str, price: float, unit: str) -> str:
        """Создает промпт для одного товара"""
        return self._prompts["single"].format(name=name, price=price, unit=unit)
    
    def _create_batch_prompt(self, products: List[Dict]) -> str:
        """Создает промпт для батча товаров"""
        prompt = self._prompts["batch_intro"] + "\n"
        for idx, product in enumerate(products, 1):
            name = product.get('name', '')
            price = product.get('price', 0)
            unit = product.get('unit', 'шт')
            prompt += self._prompts["batch_item"].format(idx=idx, name=name, price=price, unit=unit) + "\n"
        return prompt
    
    def _parse_ai_response(self, response: str, name: str, price: float, unit: str) -> Optional[AIParseResult]:
        """Парсит ответ AI для одного товара"""
        try:
            # Пытаемся извлечь JSON из ответа
            response_clean = response.strip()
            
            # Ищем JSON в ответе
            if '{' in response_clean:
                start = response_clean.find('{')
                end = response_clean.rfind('}') + 1
                json_str = response_clean[start:end]
                
                data = json.loads(json_str)
                
                # Проверяем обязательные поля
                if 'metric_unit' in data and 'price_coefficient' in data:
                    metric_unit = data['metric_unit']
                    price_coefficient = float(data['price_coefficient'])
                    
                    # Проверяем валидность
                    if metric_unit and price_coefficient > 0:
                        return AIParseResult(
                            metric_unit=metric_unit,
                            price_coefficient=price_coefficient,
                            confidence=0.85
                        )
            
            # Fallback парсинг
            lines = response_clean.split('\n')
            metric_unit = None
            price_coefficient = None
            
            for line in lines:
                if 'metric_unit' in line.lower():
                    metric_unit = line.split(':')[-1].strip().strip('"')
                elif 'price_coefficient' in line.lower():
                    price_coefficient = float(line.split(':')[-1].strip())
            
            if metric_unit and price_coefficient and price_coefficient > 0:
                return AIParseResult(
                    metric_unit=metric_unit,
                    price_coefficient=price_coefficient,
                    confidence=0.75
                )
            
        except Exception as e:
            print(f"❌ Error parsing AI response for '{name}': {str(e)}")
            print(f"Response: {response}")
        
        return None
    
    def _parse_batch_response(self, response: str, products: List[Dict]) -> List[Optional[AIParseResult]]:
        """Парсит ответ AI для батча товаров"""
        try:
            # Пытаемся извлечь JSON массив из ответа
            response_clean = response.strip()
            
            # Ищем JSON массив в ответе
            if '[' in response_clean:
                start = response_clean.find('[')
                end = response_clean.rfind(']') + 1
                json_str = response_clean[start:end]
                
                data = json.loads(json_str)
                
                results = []
                for item in data:
                    if isinstance(item, dict) and 'metric_unit' in item and 'price_coefficient' in item:
                        metric_unit = item['metric_unit']
                        price_coefficient = float(item['price_coefficient'])
                        
                        if metric_unit and price_coefficient > 0:
                            results.append(AIParseResult(
                                metric_unit=metric_unit,
                                price_coefficient=price_coefficient,
                                confidence=0.85
                            ))
                        else:
                            results.append(None)
                    else:
                        results.append(None)
                
                return results
            
            # Fallback: попытка парсинга по строкам
            lines = response_clean.split('\n')
            results = []
            current_result = {}
            
            for line in lines:
                if line.strip().startswith('{') and line.strip().endswith('}'):
                    try:
                        item = json.loads(line.strip())
                        if 'metric_unit' in item and 'price_coefficient' in item:
                            metric_unit = item['metric_unit']
                            price_coefficient = float(item['price_coefficient'])
                            
                            if metric_unit and price_coefficient > 0:
                                results.append(AIParseResult(
                                    metric_unit=metric_unit,
                                    price_coefficient=price_coefficient,
                                    confidence=0.80
                                ))
                            else:
                                results.append(None)
                        else:
                            results.append(None)
                    except:
                        results.append(None)
            
            # Дополняем результаты до нужного количества
            while len(results) < len(products):
                results.append(None)
            
            return results[:len(products)]
            
        except Exception as e:
            print(f"❌ Error parsing batch AI response: {str(e)}")
            print(f"Response: {response}")
        
        # Возвращаем None для всех товаров в случае ошибки
        return [None] * len(products)
    
    def _update_stats(self, response):
        """Обновляет статистику использования API"""
        self.total_requests += 1
        if hasattr(response, 'usage') and response.usage:
            tokens = response.usage.total_tokens
            self.total_tokens += tokens
            self.total_cost += tokens * self.cost_per_token
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику использования AI"""
        cost_rub = self.total_cost * 75  # Примерный курс USD to RUB
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "total_cost_rub": cost_rub,
            "cost_per_request": self.total_cost / max(1, self.total_requests),
            "cost_per_request_rub": cost_rub / max(1, self.total_requests),
            "cache_size": len(self.cache)
        }
    
    def _chat_completion(self, messages: List[Dict[str, str]], max_tokens: int) -> Any:  # noqa: ANN401
        """Отправляет запрос к OpenAI API"""
        if self._use_legacy_client:
            return self._client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1
            )
        else:
            return self._client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1
            ) 