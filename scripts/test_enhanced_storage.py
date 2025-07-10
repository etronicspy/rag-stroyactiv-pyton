#!/usr/bin/env python3
"""
Test Enhanced Storage - Тест расширенного сохранения материалов

Этот скрипт тестирует сохранение материалов с новыми полями:
- color
- normalized_color  
- normalized_parsed_unit
- unit_coefficient
"""

import sys
import os
import asyncio
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logging import get_logger
from core.schemas.materials import MaterialCreate
from core.database.factories import DatabaseFactory, AIClientFactory
from services.materials import MaterialsService

logger = get_logger(__name__)

class EnhancedStorageTest:
    """Тест расширенного сохранения материалов"""
    
    def __init__(self):
        self.materials_service = None
        self.test_materials = []
    
    async def initialize(self):
        """Инициализация сервисов"""
        try:
            # Initialize database clients
            vector_db = DatabaseFactory.create_vector_database()
            ai_client = AIClientFactory.create_ai_client()
            
            # Initialize service
            self.materials_service = MaterialsService(vector_db=vector_db, ai_client=ai_client)
            await self.materials_service.initialize()
            
            logger.info("✅ Сервисы инициализированы успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
    def prepare_test_materials(self):
        """Подготовка тестовых материалов с расширенными полями"""
        
        self.test_materials = [
            MaterialCreate(
                name="Кирпич керамический рядовой красный",
                use_category="Кирпич",
                unit="шт",
                sku="BRK0101",
                description="Керамический рядовой кирпич для кладки стен",
                color="красный",
                normalized_color="красный",
                normalized_parsed_unit="штука",
                unit_coefficient=1.0
            ),
            MaterialCreate(
                name="Цемент портландский М500 белый",
                use_category="Цемент",
                unit="мешок",
                sku="CEM0201",
                description="Белый портландцемент высокой марки",
                color="белый",
                normalized_color="белый",
                normalized_parsed_unit="мешок",
                unit_coefficient=1.0
            ),
            MaterialCreate(
                name="Песок строительный речной",
                use_category="Песок",
                unit="м³",
                sku="SND0301",
                description="Речной песок для строительных работ",
                color=None,  # Без цвета
                normalized_color="без_цвета",
                normalized_parsed_unit="кубический_метр",
                unit_coefficient=1.0
            ),
            MaterialCreate(
                name="Плитка керамическая напольная серая 300x300",
                use_category="Плитка",
                unit="м²",
                sku="TLE0401",
                description="Керамическая плитка для пола",
                color="серая",
                normalized_color="серый",
                normalized_parsed_unit="квадратный_метр",
                unit_coefficient=1.0
            ),
            MaterialCreate(
                name="Краска водоэмульсионная 10л",
                use_category="Краска",
                unit="л",
                sku="PNT0501",
                description="Водоэмульсионная краска для внутренних работ",
                color="белая",
                normalized_color="белый",
                normalized_parsed_unit="литр",
                unit_coefficient=1.0
            )
        ]
        
        logger.info(f"📋 Подготовлено {len(self.test_materials)} тестовых материалов")
    
    async def test_individual_creation(self):
        """Тест создания отдельных материалов"""
        logger.info("🔍 Тестирование создания отдельных материалов...")
        
        created_materials = []
        
        for i, material in enumerate(self.test_materials, 1):
            try:
                logger.info(f"📝 Создание материала {i}/{len(self.test_materials)}: {material.name}")
                
                # Создаем материал
                created_material = await self.materials_service.create_material(material)
                created_materials.append(created_material)
                
                # Проверяем новые поля
                assert created_material.color == material.color
                assert created_material.normalized_color == material.normalized_color
                assert created_material.normalized_parsed_unit == material.normalized_parsed_unit
                assert created_material.unit_coefficient == material.unit_coefficient
                
                logger.info(f"✅ Материал создан успешно: {created_material.id}")
                logger.info(f"   Цвет: {created_material.color} → {created_material.normalized_color}")
                logger.info(f"   Единица: {created_material.unit} → {created_material.normalized_parsed_unit}")
                logger.info(f"   Коэффициент: {created_material.unit_coefficient}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка создания материала {material.name}: {e}")
                raise
        
        logger.info(f"✅ Все {len(created_materials)} материалов созданы успешно")
        return created_materials
    
    async def test_batch_creation(self):
        """Тест batch создания материалов"""
        logger.info("🔄 Тестирование batch создания...")
        
        # Создаем дополнительные материалы для batch теста
        batch_materials = [
            MaterialCreate(
                name="Гипсокартон стандартный 12.5мм",
                use_category="Гипсокартон",
                unit="лист",
                sku="GYP0601",
                description="Гипсокартонный лист стандартный",
                color="серый",
                normalized_color="серый",
                normalized_parsed_unit="лист",
                unit_coefficient=1.0
            ),
            MaterialCreate(
                name="Утеплитель минеральная вата 50мм",
                use_category="Утеплитель",
                unit="м²",
                sku="INS0701",
                description="Минеральная вата для утепления",
                color="желтый",
                normalized_color="желтый",
                normalized_parsed_unit="квадратный_метр",
                unit_coefficient=1.0
            )
        ]
        
        try:
            # Создаем batch
            batch_result = await self.materials_service.create_materials_batch(batch_materials)
            
            # Проверяем результаты
            assert batch_result.success is True
            assert len(batch_result.successful_materials) == len(batch_materials)
            assert len(batch_result.failed_materials) == 0
            
            logger.info(f"✅ Batch создание успешно: {batch_result.total_processed} материалов")
            
            # Проверяем новые поля в созданных материалах
            for material in batch_result.successful_materials:
                assert material.normalized_color is not None
                assert material.normalized_parsed_unit is not None
                assert material.unit_coefficient is not None
                
            return batch_result.successful_materials
            
        except Exception as e:
            logger.error(f"❌ Ошибка batch создания: {e}")
            raise
    
    async def test_search_with_enhanced_fields(self):
        """Тест поиска с учетом расширенных полей"""
        logger.info("🔍 Тестирование поиска с расширенными полями...")
        
        test_queries = [
            "красный кирпич",
            "белый цемент",
            "серая плитка",
            "белая краска",
            "желтый утеплитель"
        ]
        
        for query in test_queries:
            try:
                logger.info(f"🔎 Поиск: '{query}'")
                
                results = await self.materials_service.search_materials(query, limit=5)
                
                logger.info(f"   Найдено результатов: {len(results)}")
                
                for result in results:
                    logger.info(f"   - {result.name}")
                    logger.info(f"     Цвет: {result.color} → {result.normalized_color}")
                    logger.info(f"     Единица: {result.unit} → {result.normalized_parsed_unit}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка поиска '{query}': {e}")
                # Не прерываем тест, просто логируем
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        start_time = datetime.now()
        logger.info("🚀 Запуск тестов расширенного сохранения...")
        
        try:
            # Инициализация
            await self.initialize()
            
            # Подготовка данных
            self.prepare_test_materials()
            
            # Тест 1: Создание отдельных материалов
            created_individuals = await self.test_individual_creation()
            
            # Тест 2: Batch создание
            created_batch = await self.test_batch_creation()
            
            # Тест 3: Поиск с расширенными полями
            await self.test_search_with_enhanced_fields()
            
            # Итоговая статистика
            total_created = len(created_individuals) + len(created_batch)
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            logger.info("="*60)
            logger.info("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            logger.info(f"📊 Всего создано материалов: {total_created}")
            logger.info(f"⏱️ Время выполнения: {elapsed_time:.2f} секунд")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ ТЕСТ ПРОВАЛЕН: {e}")
            raise

async def main():
    """Основная функция"""
    test = EnhancedStorageTest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 