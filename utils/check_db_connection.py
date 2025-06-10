#!/usr/bin/env python3
"""
Скрипт для быстрой проверки подключения к базам данных
Использует настройки из .env.local
"""

import sys
import os
# Добавляем корневую папку проекта в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from core.config import settings
import time

def check_qdrant_connection():
    """Проверка подключения к Qdrant"""
    print("🔄 Проверка подключения к Qdrant...")
    try:
        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=10
        )
        
        # Получаем список коллекций
        collections = client.get_collections()
        
        print(f"✅ Qdrant подключен успешно!")
        print(f"📊 URL: {settings.QDRANT_URL}")
        print(f"📚 Количество коллекций: {len(collections.collections)}")
        
        if collections.collections:
            print("📋 Существующие коллекции:")
            for collection in collections.collections:
                try:
                    info = client.get_collection(collection.name)
                    print(f"  • {collection.name}: {info.points_count} точек")
                except Exception as e:
                    print(f"  • {collection.name}: (ошибка получения информации)")
        else:
            print("📋 Коллекций пока нет")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Qdrant: {e}")
        return False

def check_openai_key():
    """Проверка ключа OpenAI"""
    print("\n🔄 Проверка ключа OpenAI...")
    
    if settings.OPENAI_API_KEY:
        key_preview = settings.OPENAI_API_KEY[:20] + "..." + settings.OPENAI_API_KEY[-10:]
        print(f"✅ OpenAI ключ настроен: {key_preview}")
        return True
    else:
        print("❌ OpenAI ключ не настроен")
        return False

def main():
    """Основная функция проверки"""
    print("🔍 Проверка подключения к базам данных")
    print("=" * 50)
    
    print(f"📁 Конфигурация из: {os.path.abspath('.env.local')}")
    print()
    
    # Проверяем все подключения
    results = []
    
    # Qdrant
    results.append(check_qdrant_connection())
    
    # OpenAI
    results.append(check_openai_key())
    
    # Итоги
    print("\n" + "=" * 50)
    print("📋 Итоги проверки:")
    
    services = ["Qdrant", "OpenAI"]
    for i, (service, result) in enumerate(zip(services, results)):
        status = "✅ Готов" if result else "❌ Проблема"
        print(f"  {service}: {status}")
    
    all_good = all(results)
    if all_good:
        print("\n🎉 Все сервисы готовы к работе!")
        print("🚀 Можно запускать тесты и приложение")
    else:
        print("\n⚠️ Некоторые сервисы требуют внимания")
        
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main()) 