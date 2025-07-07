#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной модуль для обогащения данных о ценах строительных материалов.
Использует гибридный подход: regex парсер + AI fallback.
"""

import os
import json
import argparse
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import numpy as np
from dataclasses import asdict

from regex_parser import RegexParser
from ai_parser import AIParser
from hybrid_parser import HybridParser


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class PriceEnricher:
    """
    Класс для обогащения данных о ценах строительных материалов.
    Использует гибридный подход: regex парсер + AI fallback.
    """
    
    def __init__(self, use_ai: bool = True, batch_size: int = 5, cache_file: str = "ai_cache.json"):
        """
        Инициализация обогатителя цен
        
        Args:
            use_ai: Использовать ли AI fallback
            batch_size: Размер батча для AI запросов
            cache_file: Путь к файлу кеша для AI
        """
        self.regex_parser = RegexParser()
        
        # AI парсер только если нужен и доступен API ключ
        self.ai_parser = None
        if use_ai:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    self.ai_parser = AIParser(api_key=api_key, cache_file=cache_file)
                    logger.info("✅ AI парсер активирован")
                except Exception as e:
                    logger.warning(f"⚠️ AI парсер недоступен: {str(e)}")
            else:
                logger.warning("⚠️ AI парсер недоступен: нет OPENAI_API_KEY")
        
        # Гибридный парсер
        self.hybrid_parser = HybridParser(self.regex_parser, self.ai_parser)
        self.hybrid_parser.batch_size = batch_size
    
    def enrich_products(self, products: List[Dict]) -> List[Dict]:
        """
        Обогащает список товаров метрическими единицами и ценами за единицу
        
        Args:
            products: Список товаров в формате [{"name": str, "price": float, "unit": str}, ...]
            
        Returns:
            Список обогащенных товаров
        """
        start_time = time.time()
        logger.info(f"Начало обработки {len(products)} товаров")
        
        # Обрабатываем товары батчами для экономии API запросов
        batch_size = self.hybrid_parser.batch_size
        results = []
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            batch_results = self.hybrid_parser.parse_batch(batch)
            results.extend(batch_results)
            
            # Логируем прогресс
            processed = min(i + batch_size, len(products))
            logger.info(f"Обработано {processed}/{len(products)} товаров ({processed/len(products)*100:.1f}%)")
        
        # Добавляем эмбеддинги для оригинальных названий через OpenAI Embeddings API
        enriched_products = self._add_embeddings(results)
        
        # Выводим статистику
        stats = self.hybrid_parser.get_stats()
        duration = time.time() - start_time
        
        logger.info(f"Обработка завершена за {duration:.2f} сек")
        logger.info(f"Всего товаров: {stats['total_products']}")
        logger.info(f"Regex успешно: {stats['regex_success']} ({stats['regex_success_rate']:.1f}%)")
        logger.info(f"AI fallback: {stats['ai_fallback']} ({stats['ai_fallback_rate']:.1f}%)")
        logger.info(f"Не обработано: {stats['total_failed']} ({100 - stats['total_success_rate']:.1f}%)")
        
        if 'ai_stats' in stats:
            ai_stats = stats['ai_stats']
            logger.info(f"Запросов к AI: {ai_stats['total_requests']}")
            logger.info(f"Примерная стоимость: {ai_stats['total_cost_rub']:.2f} ₽")
        
        return enriched_products
    
    def _add_embeddings(self, products: List[Dict]) -> List[Dict]:
        """Добавляет реальные эмбеддинги через OpenAI Embeddings API с локальным кешем.

        Для минимизации стоимости запросов и соблюдения ограничений по токенам
        используется батчинг (до 100 строк за раз) и файл-кеш `embedding_cache.json`.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY не найден – эмбеддинги не будут добавлены")
            # Добавляем пустые эмбеддинги для совместимости
            enriched = []
            for prod in products:
                out = dict(prod)
                out["embedding"] = []
                enriched.append(out)
            return enriched

        import openai
        from packaging import version

        legacy = version.parse(openai.__version__) < version.parse("1.0.0")

        if not legacy:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=api_key)

        # Загружаем/инициализируем кеш
        cache_path = Path("embedding_cache.json")
        if cache_path.exists():
            try:
                with cache_path.open("r", encoding="utf-8") as f:
                    embedding_cache = json.load(f)
            except Exception:
                embedding_cache = {}
        else:
            embedding_cache = {}

        texts_to_embed: List[str] = []
        map_idx: List[int] = []  # product index -> position in texts_to_embed

        for idx, prod in enumerate(products):
            title = prod.get("original_name") or prod.get("name")
            if not title:
                continue
            if title not in embedding_cache:
                map_idx.append(idx)
                texts_to_embed.append(title)

        batch_sz = 100
        for i in range(0, len(texts_to_embed), batch_sz):
            batch_inputs = texts_to_embed[i : i + batch_sz]

            try:
                if legacy:
                    openai.api_key = api_key
                    resp = openai.Embedding.create(
                        model="text-embedding-ada-002",
                        input=batch_inputs,
                    )
                    embeddings = [d["embedding"] for d in resp["data"]]
                else:
                    resp = client.embeddings.create(
                        model="text-embedding-3-small",
                        input=batch_inputs,
                    )
                    embeddings = [d.embedding for d in resp.data]  # type: ignore[attr-defined]

                # сохраняем в кеш
                for j, emb in enumerate(embeddings):
                    embedding_cache[batch_inputs[j]] = emb
            except Exception as e:
                logger.error(f"Ошибка получения эмбеддингов: {e}")
                # fallback: пустой список, чтобы не ломать последующий код
                for inp in batch_inputs:
                    embedding_cache[inp] = []

            time.sleep(0.5)  # небольшая пауза во избежание rate limit

        # сохраняем кеш
        try:
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(embedding_cache, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Не удалось сохранить кеш эмбеддингов: {e}")

        # вставляем эмбеддинги в результаты
        enriched = []
        for prod in products:
            out = dict(prod)
            title = out.get("original_name") or out.get("name")
            out["embedding"] = embedding_cache.get(title, [])
            enriched.append(out)

        return enriched
    
    def save_results(self, products: List[Dict], output_file: str) -> None:
        """
        Сохраняет результаты в JSON файл
        
        Args:
            products: Список обогащенных товаров
            output_file: Путь к выходному файлу
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Результаты сохранены в: {output_file}")
    
    def generate_report(self, products: List[Dict], output_file: str) -> None:
        """
        Генерирует отчет о результатах обработки
        
        Args:
            products: Список обогащенных товаров
            output_file: Путь к выходному файлу
        """
        # Собираем статистику по методам парсинга
        methods = {}
        units = {}
        success = 0
        
        for product in products:
            method = product.get('parsing_method', 'unknown')
            unit = product.get('metric_unit', 'unknown')
            
            methods[method] = methods.get(method, 0) + 1
            units[unit] = units.get(unit, 0) + 1
            
            if method != 'no_parsing':
                success += 1
        
        # Формируем отчет
        report = {
            "summary": {
                "total_products": len(products),
                "successfully_parsed": success,
                "success_rate": success / len(products) * 100 if products else 0,
                "parsing_methods": methods,
                "metric_units": units
            },
            "details": {
                "hybrid_stats": self.hybrid_parser.get_stats(),
                "products": products
            }
        }
        
        # Сохраняем отчет
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Отчет сохранен в: {output_file}")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Обогащение данных о ценах строительных материалов")
    parser.add_argument("input", help="Путь к входному JSON файлу с товарами")
    parser.add_argument("--output", "-o", default="enriched_materials.json", help="Путь к выходному JSON файлу")
    parser.add_argument("--report", "-r", default="enrichment_report.json", help="Путь к файлу отчета")
    parser.add_argument("--no-ai", action="store_true", help="Отключить AI fallback")
    parser.add_argument("--batch-size", "-b", type=int, default=5, help="Размер батча для AI запросов")
    parser.add_argument("--cache", default="ai_cache.json", help="Путь к файлу кеша для AI")
    
    args = parser.parse_args()
    
    # Проверяем существование входного файла
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Входной файл не найден: {args.input}")
        return 1
    
    try:
        # Загружаем входные данные
        with open(input_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        logger.info(f"Загружено {len(products)} товаров из {args.input}")
        
        # Создаем обогатитель
        enricher = PriceEnricher(
            use_ai=not args.no_ai,
            batch_size=args.batch_size,
            cache_file=args.cache
        )
        
        # Обогащаем товары
        enriched_products = enricher.enrich_products(products)
        
        # Сохраняем результаты
        enricher.save_results(enriched_products, args.output)
        
        # Генерируем отчет
        enricher.generate_report(enriched_products, args.report)
        
        return 0
        
    except Exception as e:
        logger.exception(f"Ошибка при обработке: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main()) 