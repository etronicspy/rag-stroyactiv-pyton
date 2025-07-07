#!/usr/bin/env python3
"""
Единый CLI интерфейс для гибридного парсера цен строительных материалов
"""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

from regex_parser import RegexParser
from ai_parser import AIParser
from hybrid_parser import HybridParser
from price_enricher import PriceEnricher
from config import load_project_config, check_required_env_vars, print_env_status


def load_materials_from_file(file_path: str) -> List[Dict]:
    """Загружает материалы из файла"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_results(results: List[Dict]) -> Dict:
    """Анализирует результаты парсинга"""
    stats = {
        'total': len(results),
        'parsed': 0,
        'unparsed': 0,
        'by_unit': {},
        'by_method': {},
        'by_source': {
            'regex': 0,
            'ai': 0,
            'none': 0
        }
    }
    
    for result in results:
        if result.get('metric_unit'):
            stats['parsed'] += 1
            unit = result.get('metric_unit')
            stats['by_unit'][unit] = stats['by_unit'].get(unit, 0) + 1
            
            # Определяем источник парсинга
            method = result.get('parsing_method', '')
            if method == 'ai_fallback':
                stats['by_source']['ai'] += 1
            elif method != 'no_parsing':
                stats['by_source']['regex'] += 1
        else:
            stats['unparsed'] += 1
            stats['by_source']['none'] += 1
        
        method = result.get('parsing_method', '')
        stats['by_method'][method] = stats['by_method'].get(method, 0) + 1
    
    return stats


def format_result(result: Dict, index: int) -> str:
    """Форматирует результат для вывода"""
    name = result.get('original_name', '')[:50]
    
    if result.get('metric_unit'):
        return (f"✅ {index:2d}. {name:<50} → "
                f"{result.get('quantity', 0):>8.3f} {result.get('metric_unit', ''):<3} | "
                f"{result.get('price_per_unit', 0):>8.2f} ₽/{result.get('metric_unit', '')} | "
                f"{result.get('parsing_method', '')}")
    else:
        return (f"❌ {index:2d}. {name:<50} → "
                f"{'не распарсено':<20} | {result.get('parsing_method', '')}")


def print_statistics(stats: Dict, ai_stats: Optional[Dict] = None, processing_time: float = 0):
    """Выводит статистику обработки"""
    print(f"⏱️  Время обработки: {processing_time:.2f} секунд")
    print(f"🎯 Общая эффективность: {stats['parsed']}/{stats['total']} ({stats['parsed']/stats['total']*100:.1f}%)")
    print(f"❌ Не распарсено: {stats['unparsed']} материалов ({stats['unparsed']/stats['total']*100:.1f}%)")
    print()
    
    # Распределение по источникам
    print("🔍 ИСТОЧНИКИ ПАРСИНГА:")
    print(f"   RegEx: {stats['by_source']['regex']} материалов ({stats['by_source']['regex']/stats['total']*100:.1f}%)")
    print(f"   AI:    {stats['by_source']['ai']} материалов ({stats['by_source']['ai']/stats['total']*100:.1f}%)")
    print(f"   None:  {stats['by_source']['none']} материалов ({stats['by_source']['none']/stats['total']*100:.1f}%)")
    print()
    
    # Распределение по единицам
    if stats['by_unit']:
        print("📊 РАСПРЕДЕЛЕНИЕ ПО ЕДИНИЦАМ ИЗМЕРЕНИЯ:")
        for unit, count in sorted(stats['by_unit'].items()):
            print(f"   {unit:<3}: {count:>2} материалов ({count/stats['total']*100:.1f}%)")
        print()
    
    # Распределение по методам
    print("🔧 МЕТОДЫ ПАРСИНГА:")
    for method, count in sorted(stats['by_method'].items()):
        print(f"   {method:<25}: {count:>2} материалов")
    print()
    
    # Статистика использования AI
    if ai_stats:
        print("💰 СТАТИСТИКА ИСПОЛЬЗОВАНИЯ AI:")
        print(f"   Запросов к API: {ai_stats.get('total_requests', 0)}")
        print(f"   Использовано токенов: {ai_stats.get('total_tokens', 0)}")
        total_cost = ai_stats.get('total_cost_rub', 0)
        print(f"   Примерная стоимость: {total_cost:.2f}₽")
        print()


def print_detailed_results(results: List[Dict], show_failed: bool = True):
    """Выводит детальные результаты"""
    print("📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ПАРСИНГА:")
    print("=" * 120)
    print(f"{'№':<3} {'Наименование':<50} {'Результат':<20} {'Цена/единицу':<15} {'Метод'}")
    print("-" * 120)
    
    # Сначала успешные
    success_results = [(i+1, r) for i, r in enumerate(results) if r.get('metric_unit')]
    for index, result in success_results:
        print(format_result(result, index))
    
    # Потом неуспешные
    if show_failed:
        failed_results = [(i+1, r) for i, r in enumerate(results) if not r.get('metric_unit')]
        if failed_results:
            print("\n❌ НЕ УДАЛОСЬ РАСПАРСИТЬ:")
            for index, result in failed_results:
                print(format_result(result, index))


def save_results(results: List[Dict], stats: Dict, ai_stats: Optional[Dict], 
                 processing_time: float, output_file: str):
    """Сохраняет результаты в файл"""
    output_data = {
        'metadata': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_materials': stats['total'],
            'parsed_count': stats['parsed'],
            'success_rate': f"{stats['parsed']/stats['total']*100:.1f}%",
            'processing_time_seconds': round(processing_time, 2),
        },
        'statistics': stats,
        'results': results
    }
    
    # Добавляем AI статистику если есть
    if ai_stats:
        output_data['metadata'].update({
            'ai_requests': ai_stats.get('total_requests', 0),
            'ai_tokens': ai_stats.get('total_tokens', 0),
            'ai_cost_rub': round(ai_stats.get('total_cost_rub', 0), 2)
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


def cmd_regex_only(args):
    """Обработка только RegEx парсером"""
    print("🚀 ОБРАБОТКА ТОЛЬКО REGEX ПАРСЕРОМ")
    print("=" * 80)
    
    # Загружаем данные
    materials = load_materials_from_file(args.input)
    print(f"📋 Загружено {len(materials)} материалов")
    
    # Создаем парсер
    parser = RegexParser()
    start_time = time.time()
    
    # Обрабатываем материалы
    results = []
    for material in materials:
        name = material.get('name', 'Unknown')
        price = float(material.get('price', 0))
        unit = material.get('unit', 'шт')
        
        result = parser.parse_product(name, price, unit)
        # Конвертируем в словарь для единообразия
        result_dict = {
            'original_name': result.original_name,
            'original_price': result.original_price,
            'original_unit': result.original_unit,
            'metric_unit': result.metric_unit,
            'quantity': result.quantity,
            'price_per_unit': result.price_per_unit,
            'price_coefficient': result.price_coefficient,
            'parsing_method': result.parsing_method,
            'confidence': result.confidence
        }
        results.append(result_dict)
    
    processing_time = time.time() - start_time
    
    # Анализируем результаты
    stats = analyze_results(results)
    
    # Выводим статистику
    print_statistics(stats, processing_time=processing_time)
    
    # Детальные результаты
    if args.verbose:
        print_detailed_results(results, show_failed=not args.hide_failed)
    
    # Сохраняем результаты
    if args.output:
        save_results(results, stats, None, processing_time, args.output)
        print(f"💾 Результаты сохранены в файл: {args.output}")
    
    print("\n🎉 ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!")


def cmd_hybrid(args):
    """Обработка гибридным парсером (RegEx + AI)"""
    print("🚀 ОБРАБОТКА ГИБРИДНЫМ ПАРСЕРОМ (REGEX + AI)")
    print("=" * 80)
    
    # Загружаем конфигурацию из .env.local файла
    load_project_config()
    
    # Проверяем наличие API ключа
    env_status = check_required_env_vars()
    if env_status['missing_required']:
        print("❌ Не найден API ключ OpenAI. Установите переменную окружения OPENAI_API_KEY")
        print("   Пример: export OPENAI_API_KEY='your-api-key'")
        print("   Или убедитесь, что файл .env.local содержит корректный OPENAI_API_KEY")
        return
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Загружаем данные
    materials = load_materials_from_file(args.input)
    print(f"📋 Загружено {len(materials)} материалов")
    
    # Создаем парсеры
    regex_parser = RegexParser()
    ai_parser = AIParser(api_key=api_key, cache_file=args.cache)
    hybrid_parser = HybridParser(regex_parser=regex_parser, ai_parser=ai_parser)
    hybrid_parser.batch_size = args.batch_size
    
    start_time = time.time()
    
    # Обрабатываем материалы
    results = hybrid_parser.parse_batch(materials)
    
    processing_time = time.time() - start_time
    
    # Анализируем результаты
    stats = analyze_results(results)
    
    # Получаем статистику использования AI
    ai_stats = ai_parser.get_stats()
    
    # Выводим статистику
    print_statistics(stats, ai_stats, processing_time)
    
    # Детальные результаты
    if args.verbose:
        print_detailed_results(results, show_failed=not args.hide_failed)
    
    # Сохраняем результаты
    if args.output:
        save_results(results, stats, ai_stats, processing_time, args.output)
        print(f"💾 Результаты сохранены в файл: {args.output}")
    
    print("\n🎉 ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!")


def cmd_enricher(args):
    """Обработка через price_enricher с эмбеддингами"""
    print("🚀 ОБРАБОТКА ЧЕРЕЗ PRICE ENRICHER С ЭМБЕДДИНГАМИ")
    print("=" * 80)
    
    # Загружаем данные
    materials = load_materials_from_file(args.input)
    print(f"📋 Загружено {len(materials)} материалов")
    
    # Создаем enricher
    enricher = PriceEnricher(
        use_ai=not args.no_ai,
        batch_size=args.batch_size,
        cache_file=args.cache
    )
    
    start_time = time.time()
    
    # Обрабатываем материалы
    results = enricher.enrich_products(materials)
    
    processing_time = time.time() - start_time
    
    # Анализируем результаты
    stats = analyze_results(results)
    
    # Получаем статистику
    hybrid_stats = enricher.hybrid_parser.get_stats()
    ai_stats = hybrid_stats.get('ai_stats')
    
    # Выводим статистику
    print_statistics(stats, ai_stats, processing_time)
    
    # Детальные результаты
    if args.verbose:
        print_detailed_results(results, show_failed=not args.hide_failed)
    
    # Сохраняем результаты
    if args.output:
        enricher.save_results(results, args.output)
        print(f"💾 Результаты сохранены в файл: {args.output}")
    
    # Генерируем отчет
    if args.report:
        enricher.generate_report(results, args.report)
        print(f"📊 Отчет сохранен в файл: {args.report}")
    
    print("\n🎉 ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!")


def main():
    """Основная функция CLI"""
    parser = argparse.ArgumentParser(
        description='Гибридный парсер цен строительных материалов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Только RegEx парсер
  python main.py regex-only test_materials_image.json -o results_regex.json
  
  # Гибридный парсер (RegEx + AI)
  python main.py hybrid test_materials_image.json -o results_hybrid.json
  
  # Полный enricher с эмбеддингами
  python main.py enricher test_materials_image.json -o results_enriched.json -r report.json
  
  # Подробный вывод без показа неудачных результатов
  python main.py hybrid test_materials_image.json -v --hide-failed
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда regex-only
    regex_parser = subparsers.add_parser('regex-only', help='Обработка только RegEx парсером')
    regex_parser.add_argument('input', help='Входной JSON файл с материалами')
    regex_parser.add_argument('-o', '--output', help='Выходной JSON файл')
    regex_parser.add_argument('-v', '--verbose', action='store_true', help='Подробный вывод')
    regex_parser.add_argument('--hide-failed', action='store_true', help='Скрыть неудачные результаты')
    
    # Команда hybrid
    hybrid_parser = subparsers.add_parser('hybrid', help='Гибридный парсер (RegEx + AI)')
    hybrid_parser.add_argument('input', help='Входной JSON файл с материалами')
    hybrid_parser.add_argument('-o', '--output', help='Выходной JSON файл')
    hybrid_parser.add_argument('-c', '--cache', default='ai_cache.json', help='Файл кеша для AI')
    hybrid_parser.add_argument('-b', '--batch-size', type=int, default=5, help='Размер батча для AI')
    hybrid_parser.add_argument('-v', '--verbose', action='store_true', help='Подробный вывод')
    hybrid_parser.add_argument('--hide-failed', action='store_true', help='Скрыть неудачные результаты')
    
    # Команда enricher
    enricher_parser = subparsers.add_parser('enricher', help='Полный enricher с эмбеддингами')
    enricher_parser.add_argument('input', help='Входной JSON файл с материалами')
    enricher_parser.add_argument('-o', '--output', help='Выходной JSON файл')
    enricher_parser.add_argument('-r', '--report', help='Файл отчета')
    enricher_parser.add_argument('-c', '--cache', default='ai_cache.json', help='Файл кеша для AI')
    enricher_parser.add_argument('-b', '--batch-size', type=int, default=5, help='Размер батча для AI')
    enricher_parser.add_argument('--no-ai', action='store_true', help='Отключить AI парсер')
    enricher_parser.add_argument('-v', '--verbose', action='store_true', help='Подробный вывод')
    enricher_parser.add_argument('--hide-failed', action='store_true', help='Скрыть неудачные результаты')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'regex-only':
            cmd_regex_only(args)
        elif args.command == 'hybrid':
            cmd_hybrid(args)
        elif args.command == 'enricher':
            cmd_enricher(args)
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 