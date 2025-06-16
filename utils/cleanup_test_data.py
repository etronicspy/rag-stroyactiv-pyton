#!/usr/bin/env python3
"""
Утилита для очистки тестовых данных и добавления качественных строительных материалов
для улучшения семантического поиска.
"""

import asyncio
import logging
import json
from typing import List, Dict, Any

from services.materials import MaterialsService
from core.database.factories import DatabaseFactory, AIClientFactory

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCleanupManager:
    """Класс для очистки тестовых данных и добавления качественных материалов."""
    
    def __init__(self):
        """Инициализация менеджера очистки данных."""
        self.vector_db = None
        self.materials_service = None
        self.collection_name = "materials"
        
    async def setup(self):
        """Настройка подключений."""
        try:
            logger.info("🔧 Настройка подключений...")
            
            self.vector_db = DatabaseFactory.create_vector_database()
            ai_client = AIClientFactory.create_ai_client()
            self.materials_service = MaterialsService(
                vector_db=self.vector_db,
                ai_client=ai_client
            )
            
            logger.info("✅ Подключения настроены успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки: {e}")
            raise
    
    async def cleanup_test_materials(self) -> Dict[str, int]:
        """Удалить тестовые и низкокачественные материалы."""
        logger.info("🧹 Начинаю очистку тестовых данных...")
        
        stats = {
            "total_checked": 0,
            "deleted": 0,
            "kept": 0
        }
        
        try:
            # Получаем все материалы
            materials = await self.vector_db.scroll_all(
                collection_name=self.collection_name,
                with_payload=True,
                with_vectors=False
            )
            
            stats["total_checked"] = len(materials)
            logger.info(f"📋 Проверяю {len(materials)} материалов...")
            
            # Критерии для удаления
            delete_patterns = [
                "string",
                "test",
                "тест",
                "Test",
                "Тест"
            ]
            
            for material in materials:
                material_id = material.get("id")
                payload = material.get("payload", {})
                name = payload.get("name", "").lower()
                description = payload.get("description", "").lower()
                
                should_delete = False
                
                # Проверяем на тестовые данные
                for pattern in delete_patterns:
                    if (pattern.lower() in name or 
                        pattern.lower() in description or
                        name == pattern.lower()):
                        should_delete = True
                        break
                
                # Удаляем низкокачественные записи
                if (name == "" or 
                    name == "unknown" or
                    len(name) < 3 or
                    description == name):  # Описание дублирует название
                    should_delete = True
                
                if should_delete:
                    try:
                        await self.vector_db.delete(self.collection_name, material_id)
                        logger.info(f"   🗑️  Удален: {payload.get('name', 'Unknown')}")
                        stats["deleted"] += 1
                    except Exception as e:
                        logger.error(f"   ❌ Ошибка удаления {material_id}: {e}")
                else:
                    stats["kept"] += 1
            
            logger.info(f"✅ Очистка завершена: удалено {stats['deleted']}, оставлено {stats['kept']}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных: {e}")
            raise
    
    async def load_materials_from_json(self, json_file_path: str) -> List[Dict[str, Any]]:
        """Загрузить материалы из JSON файла и обогатить их данными."""
        logger.info(f"📋 Загружаю материалы из файла: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                raw_materials = json.load(f)
            
            logger.info(f"📦 Загружено {len(raw_materials)} материалов из JSON")
            
            # Обогащаем данные материалов
            enriched_materials = []
            
            for material in raw_materials:
                sku = material.get("sku", "")
                name = material.get("name", "")
                
                # Определяем категорию и характеристики по SKU и названию
                category, description, unit, price = self._enrich_material_data(sku, name)
                
                enriched_material = {
                    "sku": sku,
                    "name": name,
                    "description": description,
                    "use_category": category,
                    "unit": unit,
                    "price": price
                }
                
                enriched_materials.append(enriched_material)
                logger.debug(f"   📝 Обогащен: {name} [{category}]")
            
            logger.info(f"✅ Обогащено {len(enriched_materials)} материалов")
            return enriched_materials
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки материалов из JSON: {e}")
            raise
    
    def _enrich_material_data(self, sku: str, name: str) -> tuple:
        """Обогатить данные материала на основе SKU и названия."""
        
        # Словарь для определения категорий, описаний и характеристик
        enrichment_rules = {
            # ЦЕМЕНТЫ
            "CEM": {
                "category": "Цемент",
                "unit": "кг",
                "base_price": 300,
                "descriptions": {
                    "М400": "Портландцемент марки М400, универсальный состав для строительных работ",
                    "М500": "Портландцемент марки М500, высокая прочность и быстрое твердение"
                }
            },
            
            # ПЕСОК И ЩЕБЕНЬ
            "SND": {
                "category": "Песок",
                "unit": "м3",
                "base_price": 800,
                "descriptions": {
                    "мытый": "Строительный песок мытый, фракция 0-5мм, для бетонных работ",
                    "речной": "Песок речной природный, чистый, для штукатурных и кладочных работ"
                }
            },
            "GRV": {
                "category": "Щебень",
                "unit": "м3", 
                "base_price": 1200,
                "descriptions": {
                    "5-20мм": "Щебень гранитный фракции 5-20мм для бетона и дорожных работ",
                    "20-40мм": "Щебень гранитный фракции 20-40мм для фундаментов и дренажа"
                }
            },
            
            # КИРПИЧИ
            "BRK": {
                "category": "Кирпич",
                "unit": "шт",
                "base_price": 20,
                "descriptions": {
                    "рядовой": "Кирпич керамический рядовой полнотелый, размер 250x120x65мм",
                    "силикатный": "Кирпич силикатный белый для внутренних стен, размер 250x120x65мм",
                    "облицовочный": "Кирпич облицовочный красный для фасадных работ, размер 250x120x65мм"
                }
            },
            
            # БЛОКИ
            "BLK": {
                "category": "Блоки",
                "unit": "шт",
                "base_price": 150,
                "descriptions": {
                    "газобетонный D400": "Блок газобетонный автоклавный плотностью D400, размер 600x300x200мм",
                    "газобетонный D500": "Блок газобетонный автоклавный плотностью D500, размер 600x300x200мм",
                    "керамзитобетонный": "Блок керамзитобетонный стеновой, размер 390x190x188мм",
                    "пенобетонный D300": "Блок пенобетонный плотностью D300, размер 600x300x200мм"
                }
            },
            
            # АРМАТУРА
            "ARM": {
                "category": "Арматура",
                "unit": "м",
                "base_price": 50,
                "descriptions": {
                    "Ø12мм": "Арматура стальная периодического профиля А500С диаметром 12мм",
                    "Ø14мм": "Арматура стальная периодического профиля А500С диаметром 14мм", 
                    "Ø16мм": "Арматура стальная периодического профиля А500С диаметром 16мм",
                    "Ø20мм": "Арматура стальная периодического профиля А500С диаметром 20мм"
                }
            },
            
            # МЕТАЛЛИЧЕСКИЕ ИЗДЕЛИЯ
            "MTL": {
                "category": "Металлоизделия",
                "unit": "м2",
                "base_price": 200,
                "descriptions": {
                    "арматурная": "Сетка арматурная сварная из проволоки ВР-1, ячейка 100x100мм",
                    "кладочная": "Сетка кладочная из проволоки ВР-1, ячейка 50x50мм для армирования кладки"
                }
            },
            
            # УТЕПЛИТЕЛИ
            "INS": {
                "category": "Утеплитель",
                "unit": "м2",
                "base_price": 180,
                "descriptions": {
                    "минеральная вата 50мм": "Утеплитель минераловатный плотностью 50кг/м3, толщина 50мм",
                    "минеральная вата 100мм": "Утеплитель минераловатный плотностью 50кг/м3, толщина 100мм",
                    "экструдированный 50мм": "Пенополистирол экструдированный толщиной 50мм для утепления цоколей",
                    "обычный 100мм": "Пенополистирол обычный толщиной 100мм для утепления стен"
                }
            },
            
            # КРОВЕЛЬНЫЕ МАТЕРИАЛЫ
            "ROF": {
                "category": "Кровля",
                "unit": "м2",
                "base_price": 350,
                "descriptions": {
                    "металлическая": "Черепица металлическая с полимерным покрытием для скатных кровель",
                    "керамическая": "Черепица керамическая натуральная для скатных кровель",
                    "асбестоцементный": "Шифер асбестоцементный волнистый 8-волновой",
                    "С21": "Профнастил оцинкованный С21 для кровли и ограждений",
                    "Ондулин": "Ондулин битумные волнистые листы для кровли",
                    "РКК-350": "Рубероид кровельный РКК-350 на картонной основе"
                }
            },
            
            # ПИЛОМАТЕРИАЛЫ
            "WOD": {
                "category": "Пиломатериалы",
                "unit": "м3",
                "base_price": 15000,
                "descriptions": {
                    "50х150мм": "Доска обрезная сосновая 50x150мм, длина 6м, сорт 1-2",
                    "40х150мм": "Доска обрезная сосновая 40x150мм, длина 6м, сорт 1-2",
                    "100х100мм": "Брус строительный сосновый 100x100мм, длина 6м, сорт 1",
                    "150х150мм": "Брус строительный сосновый 150x150мм, длина 6м, сорт 1",
                    "Вагонка": "Вагонка деревянная сосновая, профиль стандарт, сорт А"
                }
            },
            
            # ЛИСТОВЫЕ МАТЕРИАЛЫ
            "PLY": {
                "category": "Фанера",
                "unit": "лист",
                "base_price": 800,
                "descriptions": {
                    "березовая 12мм": "Фанера березовая ФК 12мм, размер 1525x1525мм, сорт 2/3",
                    "хвойная 18мм": "Фанера хвойная ФСФ 18мм, размер 1220x2440мм, сорт 3/4"
                }
            },
            "OSB": {
                "category": "OSB",
                "unit": "лист",
                "base_price": 600,
                "descriptions": {
                    "12мм": "Плита OSB-3 влагостойкая 12мм, размер 1220x2440мм",
                    "18мм": "Плита OSB-3 влагостойкая 18мм, размер 1220x2440мм"
                }
            },
            "GYP": {
                "category": "Гипсокартон",
                "unit": "лист",
                "base_price": 300,
                "descriptions": {
                    "обычный": "Гипсокартон обычный ГКЛ 12.5мм, размер 1200x2500мм",
                    "влагостойкий": "Гипсокартон влагостойкий ГКЛВ 12.5мм, размер 1200x2500мм"
                }
            },
            
            # НАПОЛЬНЫЕ ПОКРЫТИЯ
            "TIL": {
                "category": "Плитка",
                "unit": "м2",
                "base_price": 800,
                "descriptions": {
                    "напольная": "Плитка керамическая напольная противоскользящая, размер 300x300мм",
                    "настенная": "Плитка керамическая настенная глазурованная, размер 200x300мм",
                    "Керамогранит": "Керамогранит полированный технический, размер 600x600мм"
                }
            },
            "LAM": {
                "category": "Ламинат",
                "unit": "м2",
                "base_price": 600,
                "descriptions": {
                    "32 класс": "Ламинат 32 класс износостойкости для жилых помещений",
                    "33 класс": "Ламинат 33 класс износостойкости для коммерческих помещений"
                }
            },
            "PAR": {
                "category": "Паркет",
                "unit": "м2",
                "base_price": 1500,
                "descriptions": {
                    "дубовый": "Паркет штучный дубовый, размер 420x70x15мм, сорт Рустик"
                }
            },
            "LIN": {
                "category": "Линолеум",
                "unit": "м2",
                "base_price": 400,
                "descriptions": {
                    "бытовой": "Линолеум бытовой гетерогенный, толщина 2.5мм, ширина 2м",
                    "коммерческий": "Линолеум коммерческий гомогенный, толщина 2мм, ширина 2м"
                }
            },
            
            # ЛАКОКРАСОЧНЫЕ МАТЕРИАЛЫ
            "PNT": {
                "category": "Краски",
                "unit": "кг",
                "base_price": 200,
                "descriptions": {
                    "водоэмульсионная": "Краска водоэмульсионная белая матовая для внутренних работ",
                    "масляная": "Краска масляная белая глянцевая для наружных и внутренних работ"
                }
            }
        }
        
        # Определяем префикс SKU
        sku_prefix = sku[:3] if len(sku) >= 3 else ""
        
        # Получаем правила обогащения
        rules = enrichment_rules.get(sku_prefix, {
            "category": "Стройматериалы",
            "unit": "шт",
            "base_price": 100,
            "descriptions": {}
        })
        
        category = rules["category"]
        unit = rules["unit"]
        base_price = rules["base_price"]
        
        # Подбираем описание
        description = name
        for key, desc in rules.get("descriptions", {}).items():
            if key.lower() in name.lower():
                description = desc
                break
        
        # Если описание не найдено, создаем базовое
        if description == name:
            description = f"{name} - качественный строительный материал"
        
        # Вариация цены (±20%)
        import random
        price_variation = random.uniform(0.8, 1.2)
        price = round(base_price * price_variation, 2)
        
        return category, description, unit, price

    async def add_quality_materials(self, json_file_path: str = None) -> Dict[str, int]:
        """Добавить качественные строительные материалы из JSON файла."""
        logger.info("📦 Добавляю качественные строительные материалы...")
        
        if json_file_path:
            # Загружаем материалы из JSON файла
            quality_materials = await self.load_materials_from_json(json_file_path)
        else:
            # Используем встроенный список (fallback)
            quality_materials = []
        
        stats = {
            "added": 0,
            "failed": 0
        }
        
        for material_data in quality_materials:
            try:
                result = await self.materials_service.create_material(material_data)
                if result.get("success"):
                    logger.info(f"   ✅ Добавлен: {material_data['name']}")
                    stats["added"] += 1
                else:
                    logger.error(f"   ❌ Не удалось добавить: {material_data['name']}")
                    stats["failed"] += 1
                    
            except Exception as e:
                logger.error(f"   ❌ Ошибка добавления {material_data['name']}: {e}")
                stats["failed"] += 1
        
        logger.info(f"✅ Добавление завершено: добавлено {stats['added']}, ошибок {stats['failed']}")
        return stats


async def main():
    """Основная функция для очистки данных и добавления качественных материалов."""
    print("🧹 ОЧИСТКА ДАННЫХ И ДОБАВЛЕНИЕ КАЧЕСТВЕННЫХ МАТЕРИАЛОВ")
    print("=" * 60)
    print("Эта утилита:")
    print("1. 🗑️  Удалит тестовые и низкокачественные данные")
    print("2. 📦 Добавит качественные строительные материалы")
    print("3. 🎯 Улучшит качество семантического поиска")
    print("")
    
    # Подтверждение от пользователя
    confirm = input("❓ Продолжить? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Операция отменена")
        return
    
    manager = DataCleanupManager()
    
    try:
        # Настройка
        await manager.setup()
        
        # Очистка тестовых данных
        print("\n🧹 ЭТАП 1: Очистка тестовых данных")
        cleanup_stats = await manager.cleanup_test_materials()
        
        # Добавление качественных материалов
        print(f"\n📦 ЭТАП 2: Добавление качественных материалов")
        json_file_path = "tests/data/building_materials.json"
        add_stats = await manager.add_quality_materials(json_file_path)
        
        # Итоговая статистика
        print(f"\n🎉 ОПЕРАЦИЯ ЗАВЕРШЕНА!")
        print(f"=" * 40)
        print(f"🗑️  Удалено тестовых записей: {cleanup_stats['deleted']}")
        print(f"📋 Оставлено существующих: {cleanup_stats['kept']}")
        print(f"📦 Добавлено новых материалов: {add_stats['added']}")
        print(f"❌ Ошибок при добавлении: {add_stats['failed']}")
        
        total_materials = cleanup_stats['kept'] + add_stats['added']
        print(f"\n📊 Итого материалов в базе: {total_materials}")
        
        print(f"\n💡 Теперь запустите тест качества поиска:")
        print(f"   python3 test_search_quality.py")
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 