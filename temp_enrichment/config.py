#!/usr/bin/env python3
"""
Модуль для загрузки конфигурации из .env.local файла основного проекта
"""

import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed. Run 'pip install python-dotenv'")
    load_dotenv = None


def load_project_config() -> bool:
    """
    Загружает переменные окружения из .env.local файла основного проекта
    
    Returns:
        bool: True если файл найден и загружен, False иначе
    """
    if load_dotenv is None:
        print("❌ python-dotenv не установлен. Установите: pip install python-dotenv")
        return False
    
    # Путь к .env.local файлу в корне проекта
    current_dir = Path(__file__).parent
    project_root = current_dir.parent  # Поднимаемся на один уровень вверх
    env_file = project_root / '.env.local'
    
    if env_file.exists():
        print(f"✅ Загружаю конфигурацию из: {env_file}")
        load_dotenv(env_file)
        return True
    else:
        print(f"❌ Файл конфигурации не найден: {env_file}")
        print("   Убедитесь, что файл .env.local существует в корне проекта")
        return False


def get_openai_api_key() -> Optional[str]:
    """
    Получает OpenAI API ключ из переменных окружения
    
    Returns:
        str: API ключ или None если не найден
    """
    return os.getenv('OPENAI_API_KEY')


def check_required_env_vars() -> dict:
    """
    Проверяет наличие необходимых переменных окружения
    
    Returns:
        dict: Статус переменных окружения
    """
    required_vars = {
        'OPENAI_API_KEY': get_openai_api_key(),
    }
    
    optional_vars = {
        'OPENAI_MODEL': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
        'OPENAI_TIMEOUT': os.getenv('OPENAI_TIMEOUT', '30'),
        'OPENAI_MAX_RETRIES': os.getenv('OPENAI_MAX_RETRIES', '3'),
    }
    
    return {
        'required': required_vars,
        'optional': optional_vars,
        'missing_required': [k for k, v in required_vars.items() if not v]
    }


def print_env_status():
    """Выводит статус переменных окружения"""
    status = check_required_env_vars()
    
    print("🔧 СТАТУС ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    print("-" * 40)
    
    # Обязательные переменные
    print("📋 Обязательные переменные:")
    for var, value in status['required'].items():
        if value:
            print(f"   ✅ {var}: {'*' * min(len(value), 20)}...")
        else:
            print(f"   ❌ {var}: НЕ НАЙДЕНА")
    
    # Опциональные переменные
    print("\n⚙️  Опциональные переменные:")
    for var, value in status['optional'].items():
        print(f"   ℹ️  {var}: {value}")
    
    # Недостающие переменные
    if status['missing_required']:
        print(f"\n❌ Недостающие обязательные переменные: {', '.join(status['missing_required'])}")
        return False
    else:
        print(f"\n✅ Все обязательные переменные настроены")
        return True


if __name__ == "__main__":
    # Тест загрузки конфигурации
    print("🧪 ТЕСТ ЗАГРУЗКИ КОНФИГУРАЦИИ")
    print("=" * 50)
    
    config_loaded = load_project_config()
    if config_loaded:
        print_env_status()
    else:
        print("❌ Не удалось загрузить конфигурацию") 