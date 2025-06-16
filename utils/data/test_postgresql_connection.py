#!/usr/bin/env python3
"""
Утилита для тестирования подключения к PostgreSQL
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_settings
from core.database.adapters.postgresql_adapter import PostgreSQLAdapter
from core.monitoring.logger import get_logger

logger = get_logger(__name__)

async def test_postgresql_connection():
    """Тестирование подключения к PostgreSQL"""
    print("🔍 Тестирование подключения к PostgreSQL...")
    
    try:
        # Получаем настройки
        settings = get_settings()
        print(f"📋 Используемые настройки:")
        print(f"   - Host: {settings.POSTGRESQL_HOST}")
        print(f"   - Port: {settings.POSTGRESQL_PORT}")
        print(f"   - Database: {settings.POSTGRESQL_DATABASE}")
        print(f"   - User: {settings.POSTGRESQL_USER}")
        print(f"   - Connection URL: {settings.POSTGRESQL_URL}")
        
        # Создаем адаптер PostgreSQL
        config = settings.get_relational_db_config()
        postgres_adapter = PostgreSQLAdapter(config)
        
        # Тестируем подключение
        print("\n🔗 Попытка подключения к PostgreSQL...")
        is_healthy = await postgres_adapter.health_check()
        
        if is_healthy:
            print("✅ Подключение к PostgreSQL успешно!")
            
            # Тестируем выполнение простого запроса
            print("\n🔍 Тестирование выполнения запроса...")
            query = "SELECT version() as version, current_database() as database, current_user as user"
            
            try:
                result = await postgres_adapter.execute_query(query)
                if result:
                    print("📊 Информация о базе данных:")
                    for row in result:
                        print(f"   - Версия PostgreSQL: {row.get('version', 'N/A')}")
                        print(f"   - Текущая БД: {row.get('database', 'N/A')}")
                        print(f"   - Текущий пользователь: {row.get('user', 'N/A')}")
                else:
                    print("⚠️ Запрос выполнен, но результат пустой")
                    
            except Exception as e:
                print(f"❌ Ошибка выполнения запроса: {e}")
                
        else:
            print("❌ Не удалось подключиться к PostgreSQL")
            
    except Exception as e:
        print(f"❌ Критическая ошибка при тестировании PostgreSQL: {e}")
        logger.error(f"PostgreSQL connection test failed: {e}")
        
    finally:
        # Закрываем соединения
        if 'postgres_adapter' in locals():
            try:
                await postgres_adapter.close()
                print("🔒 Соединения с PostgreSQL закрыты")
            except Exception as e:
                print(f"⚠️ Ошибка при закрытии соединений: {e}")

async def test_database_creation():
    """Тестирование создания базы данных и таблиц"""
    print("\n🏗️ Тестирование создания структуры базы данных...")
    
    try:
        settings = get_settings()
        config = settings.get_relational_db_config()
        postgres_adapter = PostgreSQLAdapter(config)
        
        # Проверяем существование таблиц
        print("🔍 Проверка существующих таблиц...")
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        
        tables = await postgres_adapter.execute_query(tables_query)
        if tables:
            print("📋 Существующие таблицы:")
            for table in tables:
                print(f"   - {table['table_name']}")
        else:
            print("📋 Таблицы не найдены (возможно, нужно запустить миграции)")
            
        # Проверяем версию Alembic
        print("\n🔍 Проверка миграций Alembic...")
        alembic_query = """
        SELECT version_num 
        FROM alembic_version 
        LIMIT 1;
        """
        
        try:
            alembic_version = await postgres_adapter.execute_query(alembic_query)
            if alembic_version:
                print(f"📋 Текущая версия миграций: {alembic_version[0]['version_num']}")
            else:
                print("📋 Миграции Alembic не найдены")
        except Exception as e:
            print(f"📋 Таблица alembic_version не существует: {e}")
            print("💡 Рекомендуется запустить: alembic upgrade head")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке структуры БД: {e}")
        
    finally:
        if 'postgres_adapter' in locals():
            try:
                await postgres_adapter.close()
            except:
                pass

def print_setup_instructions():
    """Выводит инструкции по настройке"""
    print("\n" + "="*60)
    print("📋 СЛЕДУЮЩИЕ ШАГИ ДЛЯ НАСТРОЙКИ PostgreSQL:")
    print("="*60)
    print("1. Скопируйте настройки из env.example в ваш .env.local файл:")
    print("   - POSTGRESQL_URL=postgresql+asyncpg://superadmin:DE3qVSbGa09RtGY2c9Ve@localhost:5432/materials")
    print("   - DISABLE_POSTGRESQL_CONNECTION=false")
    print("   - AUTO_MIGRATE=true")
    print("   - AUTO_SEED=true")
    print()
    print("2. Если база данных 'materials' не существует, создайте её:")
    print("   psql -U superadmin -h localhost -c 'CREATE DATABASE materials;'")
    print()
    print("3. Запустите миграции Alembic:")
    print("   alembic upgrade head")
    print()
    print("4. Загрузите тестовые данные:")
    print("   python load_materials.py")
    print()
    print("5. Запустите приложение:")
    print("   python main.py")
    print("="*60)

async def main():
    """Основная функция"""
    print("🚀 PostgreSQL Connection Tester")
    print("=" * 50)
    
    await test_postgresql_connection()
    await test_database_creation()
    print_setup_instructions()

if __name__ == "__main__":
    asyncio.run(main()) 