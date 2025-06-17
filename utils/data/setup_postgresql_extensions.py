#!/usr/bin/env python3
"""
Утилита для установки необходимых PostgreSQL расширений.

Устанавливает расширения pg_trgm, btree_gin, uuid-ossp для полноценной работы с базой данных.
"""
import asyncio
import asyncpg
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_settings


async def create_extensions():
    """Создает необходимые PostgreSQL расширения."""
    print("🔧 Установка PostgreSQL расширений...")
    
    settings = get_settings()
    
    try:
        # Подключаемся к PostgreSQL через SSH туннель
        conn = await asyncpg.connect(
            host='localhost',
            port=5435,
            user='superadmin',
            password=settings.POSTGRESQL_PASSWORD,
            database='stbr_rag1'
        )
        
        print("✅ Подключение к PostgreSQL установлено")
        
        # Список необходимых расширений
        extensions = [
            ('pg_trgm', 'Trigram similarity for fuzzy search'),
            ('btree_gin', 'GIN btree support for indexes'),
            ('uuid-ossp', 'UUID generation functions')
        ]
        
        success_count = 0
        
        for ext_name, description in extensions:
            try:
                await conn.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext_name}";')
                print(f'✅ Extension {ext_name} created/enabled - {description}')
                success_count += 1
            except Exception as e:
                print(f'⚠️ Extension {ext_name} failed: {e}')
        
        # Проверяем установленные расширения
        extensions_query = """
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname IN ('pg_trgm', 'btree_gin', 'uuid-ossp')
        ORDER BY extname;
        """
        
        installed_extensions = await conn.fetch(extensions_query)
        
        print(f"\n📋 Установленные расширения ({len(installed_extensions)} из {len(extensions)}):")
        for ext in installed_extensions:
            print(f"   ✅ {ext['extname']} v{ext['extversion']}")
        
        await conn.close()
        
        if success_count == len(extensions):
            print('\n🎉 Все расширения PostgreSQL успешно установлены!')
            return True
        else:
            print(f'\n⚠️ Установлено {success_count} из {len(extensions)} расширений')
            return False
        
    except Exception as e:
        print(f'❌ Ошибка при установке расширений: {e}')
        return False


async def main():
    """Основная функция."""
    print("🚀 PostgreSQL Extensions Setup")
    print("=" * 50)
    
    success = await create_extensions()
    
    if success:
        print("\n✅ PostgreSQL расширения готовы к использованию!")
        return True
    else:
        print("\n❌ Проблемы с установкой расширений PostgreSQL")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Операция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1) 