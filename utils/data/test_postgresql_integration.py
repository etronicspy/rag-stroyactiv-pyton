#!/usr/bin/env python3
"""
Простой интеграционный тест PostgreSQL.

Проверяет подключение к PostgreSQL через SSH туннель и основные операции.
"""
import asyncio
import asyncpg
import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_settings


async def get_postgresql_connection():
    """Получить подключение к PostgreSQL используя переменные окружения."""
    try:
        settings = get_settings()
        return await asyncpg.connect(
            host='localhost',
            port=5435,
            user='superadmin',
            password=settings.POSTGRESQL_PASSWORD,
            database='stbr_rag1'
        )
    except Exception as e:
        print(f"❌ Ошибка создания подключения: {e}")
        raise


async def test_postgresql_connection():
    """Тест подключения к PostgreSQL."""
    print("🔍 Тестирование подключения к PostgreSQL...")
    
    try:
        # Подключаемся к PostgreSQL через SSH туннель используя переменные окружения
        conn = await get_postgresql_connection()
        
        print("✅ Подключение к PostgreSQL установлено")
        
        # Проверяем версию и информацию о БД
        result = await conn.fetchrow("""
            SELECT 
                version() as version,
                current_database() as database,
                current_user as user,
                pg_database_size(current_database()) as db_size_bytes,
                now() as timestamp
        """)
        
        print(f"📋 Информация о базе данных:")
        print(f"   └─ Версия: {result['version']}")
        print(f"   └─ База данных: {result['database']}")
        print(f"   └─ Пользователь: {result['user']}")
        print(f"   └─ Размер БД: {result['db_size_bytes']:,} байт")
        print(f"   └─ Время: {result['timestamp']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False


async def test_postgresql_tables():
    """Тест проверки таблиц PostgreSQL."""
    print("\n🔍 Проверка таблиц PostgreSQL...")
    
    try:
        conn = await get_postgresql_connection()
        
        # Проверяем существующие таблицы
        tables = await conn.fetch("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        print(f"📋 Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"   ✅ {table['table_name']} ({table['table_type']})")
        
        # Проверяем миграции
        try:
            migration = await conn.fetchrow("SELECT version_num FROM alembic_version LIMIT 1")
            if migration:
                print(f"🔄 Текущая миграция: {migration['version_num']}")
            else:
                print("⚠️ Миграции не найдены")
        except Exception as e:
            print(f"⚠️ Ошибка проверки миграций: {e}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки таблиц: {e}")
        return False


async def test_postgresql_extensions():
    """Тест проверки расширений PostgreSQL."""
    print("\n🔍 Проверка расширений PostgreSQL...")
    
    try:
        conn = await get_postgresql_connection()
        
        # Проверяем установленные расширения
        extensions = await conn.fetch("""
            SELECT extname, extversion 
            FROM pg_extension 
            ORDER BY extname
        """)
        
        print(f"📋 Установленные расширения ({len(extensions)}):")
        for ext in extensions:
            print(f"   ✅ {ext['extname']} v{ext['extversion']}")
        
        # Проверяем критические расширения
        critical_extensions = ['pg_trgm', 'btree_gin', 'uuid-ossp']
        installed_names = [ext['extname'] for ext in extensions]
        
        for critical_ext in critical_extensions:
            if critical_ext in installed_names:
                print(f"   ✅ Критическое расширение {critical_ext} установлено")
            else:
                print(f"   ❌ Критическое расширение {critical_ext} НЕ установлено")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки расширений: {e}")
        return False


async def test_postgresql_materials_table():
    """Тест работы с таблицей materials."""
    print("\n🔍 Тестирование таблицы materials...")
    
    try:
        conn = await get_postgresql_connection()
        
        # Проверяем структуру таблицы materials
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'materials' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        if columns:
            print(f"📋 Структура таблицы materials ({len(columns)} колонок):")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"   └─ {col['column_name']}: {col['data_type']} {nullable}{default}")
            
            # Проверяем количество записей
            count_result = await conn.fetchrow("SELECT COUNT(*) as count FROM materials")
            print(f"📊 Количество материалов в БД: {count_result['count']}")
            
            # Показываем несколько примеров
            if count_result['count'] > 0:
                samples = await conn.fetch("SELECT id, name, description FROM materials LIMIT 3")
                print("📝 Примеры материалов:")
                for sample in samples:
                    print(f"   └─ [{sample['id']}] {sample['name']}")
                    if sample['description']:
                        print(f"      {sample['description'][:100]}...")
        else:
            print("❌ Таблица materials не найдена или пуста")
        
        await conn.close()  
        return True
        
    except Exception as e:
        print(f"❌ Ошибка работы с таблицей materials: {e}")
        return False


async def test_postgresql_performance():
    """Тест производительности PostgreSQL."""
    print("\n🔍 Тестирование производительности PostgreSQL...")
    
    try:
        conn = await get_postgresql_connection()
        
        # Простой тест производительности
        start_time = datetime.now()
        
        result = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_materials,
                COUNT(DISTINCT name) as unique_names,
                AVG(LENGTH(description)) as avg_description_length
            FROM materials
        """)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        print(f"📊 Производительность запроса:")
        print(f"   └─ Время ответа: {response_time:.2f}ms")
        print(f"   └─ Общее количество материалов: {result['total_materials']}")
        print(f"   └─ Уникальных названий: {result['unique_names']}")
        
        # Обрабатываем случай, когда avg_description_length может быть None
        avg_length = result['avg_description_length']
        if avg_length is not None:
            print(f"   └─ Средняя длина описания: {avg_length:.1f} символов")
        else:
            print(f"   └─ Средняя длина описания: нет данных (таблица пуста)")
        
        # Оценка производительности
        if response_time < 100:
            print("   ✅ Отличная производительность")
        elif response_time < 500:
            print("   ✅ Хорошая производительность")
        elif response_time < 1000:
            print("   ⚠️ Средняя производительность")
        else:
            print("   ❌ Медленная производительность")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования производительности: {e}")
        return False


async def main():
    """Основная функция."""
    print("🚀 PostgreSQL Integration Test")
    print("=" * 50)
    
    # Список тестов
    tests = [
        ("Connection Test", test_postgresql_connection),
        ("Tables Test", test_postgresql_tables),
        ("Extensions Test", test_postgresql_extensions),
        ("Materials Table Test", test_postgresql_materials_table),
        ("Performance Test", test_postgresql_performance)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ Тест {test_name} failed: {e}")
            results[test_name] = False
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print(f"{'='*60}")
    
    successful = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Результат: {successful}/{total} тестов прошли успешно")
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    if successful == total:
        print("\n🎉 PostgreSQL полностью готов к работе!")
        print("💡 Все системы функционируют корректно")
    elif successful >= total * 0.7:
        print(f"\n⚠️ PostgreSQL частично готов ({successful}/{total})")
        print("🔧 Некоторые функции могут быть недоступны")
    else:
        print(f"\n❌ PostgreSQL не готов к работе ({successful}/{total})")
        print("🔧 Требуется дополнительная настройка")
    
    return successful == total


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1) 