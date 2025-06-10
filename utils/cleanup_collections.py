#!/usr/bin/env python3
"""
Утилита для очистки коллекций Qdrant
Удаляет все материалы и связанные данные
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_vector_db_client, settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_materials_collection():
    """Очистка коллекции materials"""
    try:
        client = get_vector_db_client()
        db_config = settings.get_vector_db_config()
        collection_name = db_config["collection_name"]
        
        logger.info(f"🗑️  Очистка коллекции: {collection_name}")
        
        # Проверяем существование коллекции
        collections = client.get_collections()
        if any(c.name == collection_name for c in collections.collections):
            # Удаляем коллекцию полностью
            client.delete_collection(collection_name=collection_name)
            logger.info(f"✅ Коллекция {collection_name} удалена")
        else:
            logger.info(f"ℹ️  Коллекция {collection_name} не существует")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке коллекции materials: {e}")
        return False
    return True

def cleanup_price_collections():
    """Очистка всех коллекций с прайсами"""
    try:
        client = get_vector_db_client()
        
        logger.info("🗑️  Поиск коллекций с прайсами...")
        
        # Получаем все коллекции
        collections = client.get_collections()
        price_collections = [c.name for c in collections.collections if "supplier_" in c.name and "_prices" in c.name]
        
        if not price_collections:
            logger.info("ℹ️  Коллекции с прайсами не найдены")
            return True
            
        logger.info(f"📋 Найдено коллекций с прайсами: {len(price_collections)}")
        for collection_name in price_collections:
            logger.info(f"  • {collection_name}")
        
        # Подтверждение от пользователя
        response = input("\n❓ Удалить все коллекции с прайсами? (y/N): ").strip().lower()
        if response not in ['y', 'yes', 'да']:
            logger.info("🚫 Операция отменена пользователем")
            return True
            
        # Удаляем коллекции
        for collection_name in price_collections:
            try:
                client.delete_collection(collection_name=collection_name)
                logger.info(f"✅ Коллекция {collection_name} удалена")
            except Exception as e:
                logger.error(f"❌ Ошибка удаления {collection_name}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке коллекций с прайсами: {e}")
        return False
    return True

def cleanup_all_collections():
    """Очистка всех коллекций"""
    try:
        client = get_vector_db_client()
        
        logger.info("🗑️  Получение списка всех коллекций...")
        
        # Получаем все коллекции
        collections = client.get_collections()
        all_collections = [c.name for c in collections.collections]
        
        if not all_collections:
            logger.info("ℹ️  Коллекции не найдены")
            return True
            
        logger.info(f"📋 Найдено коллекций: {len(all_collections)}")
        for collection_name in all_collections:
            logger.info(f"  • {collection_name}")
        
        # Подтверждение от пользователя
        response = input("\n⚠️  ВНИМАНИЕ! Удалить ВСЕ коллекции? (y/N): ").strip().lower()
        if response not in ['y', 'yes', 'да']:
            logger.info("🚫 Операция отменена пользователем")
            return True
            
        # Удаляем все коллекции
        for collection_name in all_collections:
            try:
                client.delete_collection(collection_name=collection_name)
                logger.info(f"✅ Коллекция {collection_name} удалена")
            except Exception as e:
                logger.error(f"❌ Ошибка удаления {collection_name}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке всех коллекций: {e}")
        return False
    return True

def recreate_materials_collection():
    """Пересоздание коллекции materials с правильными параметрами"""
    try:
        from qdrant_client.models import Distance, VectorParams
        
        client = get_vector_db_client()
        db_config = settings.get_vector_db_config()
        collection_name = db_config["collection_name"]
        
        logger.info(f"🔄 Пересоздание коллекции: {collection_name}")
        
        # Создаем коллекцию заново
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=db_config["vector_size"], 
                distance=Distance.COSINE
            ),
        )
        
        logger.info(f"✅ Коллекция {collection_name} создана заново")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при пересоздании коллекции materials: {e}")
        return False
    return True

def main():
    """Главная функция"""
    logger.info("🧹 Утилита очистки коллекций Qdrant")
    logger.info("=" * 50)
    
    print("\nВыберите операцию:")
    print("1. Очистить только коллекцию materials")
    print("2. Очистить коллекции с прайсами") 
    print("3. Очистить ВСЕ коллекции")
    print("4. Пересоздать коллекцию materials")
    print("0. Выход")
    
    choice = input("\nВведите номер операции: ").strip()
    
    if choice == "1":
        logger.info("\n🎯 Очистка коллекции materials...")
        if cleanup_materials_collection():
            logger.info("✅ Операция завершена успешно")
        else:
            logger.error("❌ Операция завершена с ошибками")
            
    elif choice == "2":
        logger.info("\n🎯 Очистка коллекций с прайсами...")
        if cleanup_price_collections():
            logger.info("✅ Операция завершена успешно")
        else:
            logger.error("❌ Операция завершена с ошибками")
            
    elif choice == "3":
        logger.info("\n🎯 Очистка всех коллекций...")
        if cleanup_all_collections():
            logger.info("✅ Операция завершена успешно")
        else:
            logger.error("❌ Операция завершена с ошибками")
            
    elif choice == "4":
        logger.info("\n🎯 Пересоздание коллекции materials...")
        # Сначала удаляем
        if cleanup_materials_collection():
            # Затем создаем заново
            if recreate_materials_collection():
                logger.info("✅ Операция завершена успешно")
            else:
                logger.error("❌ Ошибка при пересоздании коллекции")
        else:
            logger.error("❌ Ошибка при удалении коллекции")
            
    elif choice == "0":
        logger.info("👋 Выход из программы")
    else:
        logger.error("❌ Неверный выбор")

if __name__ == "__main__":
    main() 