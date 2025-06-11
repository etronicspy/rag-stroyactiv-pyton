#!/usr/bin/env python3
"""
Утилита для экспорта прайсов поставщика в CSV с полными векторами
"""

import sys
import os
import csv
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Добавляем корневую папку проекта в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

def get_qdrant_client():
    """Получить клиент Qdrant"""
    # Загружаем переменные окружения из .env.local
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    
    return QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

def get_collection_name(supplier_id: str) -> str:
    """Генерировать имя коллекции для поставщика"""
    return f"supplier_{supplier_id}_prices"

def export_supplier_prices_to_csv(
    supplier_id: str,
    output_file: Optional[str] = None,
    include_vectors: bool = True,
    vector_format: str = "json",
    limit: Optional[int] = None
) -> str:
    """
    Экспортировать прайсы поставщика в CSV
    
    Args:
        supplier_id: ID поставщика
        output_file: Путь к выходному файлу (опционально)
        include_vectors: Включать ли векторы в экспорт
        vector_format: Формат векторов ("json", "columns", "compact")
        limit: Ограничение количества записей
    
    Returns:
        Путь к созданному файлу
    """
    
    print(f"🔄 Экспорт прайса поставщика: {supplier_id}")
    
    # Подключение к Qdrant
    client = get_qdrant_client()
    collection_name = get_collection_name(supplier_id)
    
    # Проверка существования коллекции
    try:
        collections = client.get_collections()
        if not any(c.name == collection_name for c in collections.collections):
            print(f"❌ Коллекция '{collection_name}' не найдена")
            return None
    except Exception as e:
        print(f"❌ Ошибка подключения к Qdrant: {e}")
        return None
    
    # Получение данных из коллекции
    print("📥 Загрузка данных из коллекции...")
    
    all_points = []
    offset = None
    batch_size = 100
    
    while True:
        try:
            if limit and len(all_points) >= limit:
                all_points = all_points[:limit]
                break
                
            current_limit = min(batch_size, limit - len(all_points)) if limit else batch_size
            
            result = client.scroll(
                collection_name=collection_name,
                limit=current_limit,
                offset=offset,
                with_payload=True,
                with_vectors=include_vectors
            )
            
            if isinstance(result, tuple):
                points, next_offset = result
            else:
                points = result
                next_offset = None
            
            if not points:
                break
                
            all_points.extend(points)
            print(f"   📦 Загружено: {len(all_points)} записей")
            
            if next_offset is None:
                break
                
            offset = next_offset
            
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return None
    
    if not all_points:
        print("📭 Нет данных для экспорта")
        return None
    
    print(f"✅ Загружено {len(all_points)} записей")
    
    # Определение выходного файла
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        vector_suffix = "_with_vectors" if include_vectors else "_no_vectors"
        output_file = f"export_{supplier_id}_{timestamp}{vector_suffix}.csv"
    
    # Анализ структуры данных
    sample_point = all_points[0]
    
    # Определение формата данных
    is_extended_format = any(key in sample_point.payload for key in ["sku", "unit_price", "pricelistid"])
    
    print(f"📊 Формат данных: {'Расширенный' if is_extended_format else 'Базовый (legacy)'}")
    
    # Подготовка заголовков CSV
    if is_extended_format:
        base_headers = [
            "id", "name", "sku", "use_category", "upload_date",
            "unit_price", "unit_price_currency", "unit_calc_price", "unit_calc_price_currency",
            "buy_price", "buy_price_currency", "sale_price", "sale_price_currency",
            "calc_unit", "count", "pricelistid", "is_processed", "date_price_change",
            "created", "modified", "supplier_id"
        ]
    else:
        base_headers = [
            "id", "name", "use_category", "unit", "price", "description", 
            "upload_date", "supplier_id"
        ]
    
    # Добавление векторных полей
    headers = base_headers.copy()
    vector_headers = []
    
    if include_vectors and sample_point.vector:
        if vector_format == "json":
            headers.append("embedding_vector")
        elif vector_format == "columns":
            vector_size = len(sample_point.vector)
            vector_headers = [f"vec_{i:04d}" for i in range(vector_size)]
            headers.extend(vector_headers)
        elif vector_format == "compact":
            headers.extend(["vector_norm", "vector_mean", "vector_std", "vector_min", "vector_max"])
    
    # Запись в CSV
    print(f"💾 Сохранение в файл: {output_file}")
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Записываем заголовки
            writer.writerow(headers)
            
            # Записываем данные
            for i, point in enumerate(all_points, 1):
                if i % 100 == 0:
                    print(f"   💾 Обработано: {i}/{len(all_points)} записей")
                
                row = []
                
                # Базовые поля
                for header in base_headers:
                    if header == "id":
                        row.append(str(point.id))
                    elif header == "supplier_id":
                        row.append(supplier_id)
                    else:
                        value = point.payload.get(header, "")
                        if value is None:
                            value = ""
                        row.append(str(value))
                
                # Векторные поля
                if include_vectors and point.vector:
                    if vector_format == "json":
                        row.append(json.dumps(point.vector))
                    elif vector_format == "columns":
                        row.extend(point.vector)
                    elif vector_format == "compact":
                        import numpy as np
                        vec_array = np.array(point.vector)
                        row.extend([
                            float(np.linalg.norm(vec_array)),  # норма
                            float(np.mean(vec_array)),         # среднее
                            float(np.std(vec_array)),          # стандартное отклонение
                            float(np.min(vec_array)),          # минимум
                            float(np.max(vec_array))           # максимум
                        ])
                elif include_vectors:
                    # Заполняем пустыми значениями если вектор отсутствует
                    if vector_format == "json":
                        row.append("")
                    elif vector_format == "columns":
                        row.extend([""] * len(vector_headers))
                    elif vector_format == "compact":
                        row.extend(["", "", "", "", ""])
                
                writer.writerow(row)
    
    except Exception as e:
        print(f"❌ Ошибка записи в файл: {e}")
        return None
    
    # Статистика
    file_size = os.path.getsize(output_file)
    file_size_mb = file_size / (1024 * 1024)
    
    print("=" * 60)
    print("✅ ЭКСПОРТ ЗАВЕРШЕН")
    print("=" * 60)
    print(f"📁 Файл: {output_file}")
    print(f"📊 Записей: {len(all_points)}")
    print(f"📏 Колонок: {len(headers)}")
    print(f"💾 Размер файла: {file_size_mb:.2f} MB")
    print(f"🔢 Формат векторов: {vector_format if include_vectors else 'без векторов'}")
    
    if include_vectors and vector_format == "columns":
        print(f"🎯 Размер вектора: {len(vector_headers)} измерений")
    
    return output_file

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(
        description="Экспорт прайсов поставщика в CSV с векторами",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Базовый экспорт с векторами в JSON
  python utils/export_supplier_prices.py СтройТорг_Мега

  # Экспорт без векторов
  python utils/export_supplier_prices.py СтройТорг_Мега --no-vectors

  # Экспорт с векторами в отдельных колонках  
  python utils/export_supplier_prices.py СтройТорг_Мега --vector-format columns

  # Экспорт с компактным представлением векторов
  python utils/export_supplier_prices.py СтройТорг_Мега --vector-format compact

  # Ограниченный экспорт
  python utils/export_supplier_prices.py СтройТорг_Мега --limit 100

  # Экспорт в конкретный файл
  python utils/export_supplier_prices.py СтройТорг_Мега -o my_export.csv
        """
    )
    
    parser.add_argument(
        "supplier_id",
        nargs='?',
        help="ID поставщика для экспорта"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Путь к выходному CSV файлу (опционально)"
    )
    
    parser.add_argument(
        "--no-vectors",
        action="store_true",
        help="Исключить векторы из экспорта"
    )
    
    parser.add_argument(
        "--vector-format",
        choices=["json", "columns", "compact"],
        default="json",
        help="Формат представления векторов (по умолчанию: json)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Ограничить количество экспортируемых записей"
    )
    
    parser.add_argument(
        "--list-suppliers",
        action="store_true", 
        help="Показать список доступных поставщиков"
    )
    
    args = parser.parse_args()
    
    # Показать список поставщиков
    if args.list_suppliers:
        print("🔍 Поиск доступных поставщиков...")
        try:
            client = get_qdrant_client()
            collections = client.get_collections()
            
            supplier_collections = [
                c.name for c in collections.collections 
                if c.name.startswith("supplier_") and c.name.endswith("_prices")
            ]
            
            if supplier_collections:
                print("\n📋 Доступные поставщики:")
                for collection in sorted(supplier_collections):
                    # Извлекаем ID поставщика из имени коллекции
                    supplier_id = collection.replace("supplier_", "").replace("_prices", "")
                    
                    # Получаем количество записей
                    try:
                        info = client.get_collection(collection)
                        count = info.points_count if hasattr(info, 'points_count') else '?'
                    except:
                        count = '?'
                    
                    print(f"  • {supplier_id} ({count} записей)")
            else:
                print("📭 Поставщики не найдены")
                
        except Exception as e:
            print(f"❌ Ошибка получения списка: {e}")
        return
    
    # Проверяем, что supplier_id указан для экспорта
    if not args.supplier_id:
        print("❌ Ошибка: Необходимо указать ID поставщика для экспорта")
        print("Используйте --list-suppliers для просмотра доступных поставщиков")
        sys.exit(1)
    
    # Выполнить экспорт
    include_vectors = not args.no_vectors
    
    result = export_supplier_prices_to_csv(
        supplier_id=args.supplier_id,
        output_file=args.output,
        include_vectors=include_vectors,
        vector_format=args.vector_format,
        limit=args.limit
    )
    
    if result:
        print(f"\n🎉 Экспорт успешно завершен: {result}")
    else:
        print("\n💥 Экспорт не удался")
        sys.exit(1)

if __name__ == "__main__":
    main() 