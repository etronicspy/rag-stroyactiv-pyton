#!/usr/bin/env python3
"""
Утилита для перегенерации эмбеддингов существующих материалов
с использованием реальных OpenAI API вместо mock векторов.
"""

import asyncio
import time
from typing import List, Dict, Any
import logging

from services.materials import MaterialsService
from core.database.factories import DatabaseFactory, AIClientFactory
from core.database.exceptions import DatabaseError

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingRegenerator:
    """Класс для перегенерации эмбеддингов существующих материалов."""
    
    def __init__(self):
        """Инициализация регенератора."""
        self.vector_db = None
        self.ai_client = None
        self.materials_service = None
        self.collection_name = "materials"
        
    async def setup(self):
        """Настройка подключений к БД и AI клиенту."""
        try:
            logger.info("🔧 Настройка подключений...")
            
            # Создаем клиенты
            self.vector_db = DatabaseFactory.create_vector_database()
            self.ai_client = AIClientFactory.create_ai_client()
            self.materials_service = MaterialsService(
                vector_db=self.vector_db,
                ai_client=self.ai_client
            )
            
            logger.info("✅ Подключения настроены успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки: {e}")
            raise
    
    async def get_all_materials(self) -> List[Dict[str, Any]]:
        """Получить все материалы из векторной БД."""
        try:
            logger.info("📋 Получаем список всех материалов...")
            
            # Проверяем существование коллекции
            collection_exists = await self.vector_db.collection_exists(self.collection_name)
            if not collection_exists:
                logger.warning(f"⚠️  Коллекция {self.collection_name} не существует")
                return []
            
            # Получаем все векторы через scroll_all
            results = await self.vector_db.scroll_all(
                collection_name=self.collection_name,
                with_payload=True,
                with_vectors=True
            )
            
            logger.info(f"📊 Найдено материалов в коллекции: {len(results)}")
            logger.info(f"📦 Загружено материалов для обработки: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения материалов: {e}")
            raise
    
    async def regenerate_single_material(self, material_data: Dict[str, Any]) -> bool:
        """Перегенерировать эмбеддинг для одного материала."""
        try:
            material_id = material_data.get("id")
            payload = material_data.get("payload", {})
            
            name = payload.get("name", "")
            description = payload.get("description", "")
            use_category = payload.get("use_category", "")
            
            logger.info(f"🔄 Обрабатываю: {name}")
            
            # Создаем текст для эмбеддинга (как в MaterialsService)
            text_for_embedding = f"{name} {use_category} {description}".strip()
            
            # Генерируем новый эмбеддинг через AI клиент
            if hasattr(self.ai_client, 'embeddings'):
                logger.debug(f"   🧠 Генерирую OpenAI эмбеддинг...")
                response = await self.ai_client.embeddings.create(
                    input=text_for_embedding,
                    model="text-embedding-3-small",
                    dimensions=1536
                )
                new_embedding = response.data[0].embedding
            elif hasattr(self.ai_client, 'get_embedding'):
                logger.debug(f"   🔧 Используя mock AI клиент...")
                new_embedding = await self.ai_client.get_embedding(text_for_embedding)
            else:
                raise ValueError("AI клиент не поддерживает генерацию эмбеддингов")
            
            # Обновляем вектор в базе данных
            vector_data = {
                "id": material_id,
                "vector": new_embedding,
                "payload": payload
            }
            
            await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[vector_data]
            )
            
            logger.debug(f"   ✅ Эмбеддинг обновлен для: {name}")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Ошибка обработки материала {material_id}: {e}")
            return False
    
    async def regenerate_all_embeddings(self, batch_size: int = 10) -> Dict[str, Any]:
        """Перегенерировать эмбеддинги для всех материалов."""
        logger.info("🚀 Начинаю перегенерацию эмбеддингов...")
        
        start_time = time.time()
        stats = {
            "total_materials": 0,
            "processed_successfully": 0,
            "failed": 0,
            "processing_time": 0,
            "avg_time_per_material": 0
        }
        
        try:
            # Получаем все материалы
            materials = await self.get_all_materials()
            stats["total_materials"] = len(materials)
            
            if not materials:
                logger.warning("⚠️  Нет материалов для обработки")
                return stats
            
            logger.info(f"📋 Обрабатываю {len(materials)} материалов батчами по {batch_size}...")
            
            # Обрабатываем батчами для контроля нагрузки
            for i in range(0, len(materials), batch_size):
                batch = materials[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(materials) + batch_size - 1) // batch_size
                
                logger.info(f"📦 Батч {batch_num}/{total_batches}: обрабатываю {len(batch)} материалов...")
                
                # Обрабатываем материалы в батче параллельно
                tasks = [
                    self.regenerate_single_material(material) 
                    for material in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Подсчитываем результаты батча
                for result in batch_results:
                    if isinstance(result, Exception):
                        stats["failed"] += 1
                        logger.error(f"   ❌ Ошибка в батче: {result}")
                    elif result:
                        stats["processed_successfully"] += 1
                    else:
                        stats["failed"] += 1
                
                # Пауза между батчами для снижения нагрузки на API
                if i + batch_size < len(materials):
                    await asyncio.sleep(1)
                    
                logger.info(f"   ✅ Батч {batch_num} завершен")
            
            # Вычисляем статистики
            stats["processing_time"] = time.time() - start_time
            if stats["processed_successfully"] > 0:
                stats["avg_time_per_material"] = stats["processing_time"] / stats["processed_successfully"]
            
            # Выводим итоговую статистику
            logger.info("\n" + "=" * 60)
            logger.info("📊 ИТОГОВАЯ СТАТИСТИКА ПЕРЕГЕНЕРАЦИИ")
            logger.info("=" * 60)
            logger.info(f"✅ Всего материалов: {stats['total_materials']}")
            logger.info(f"✅ Успешно обработано: {stats['processed_successfully']}")
            logger.info(f"❌ Ошибок: {stats['failed']}")
            logger.info(f"⏱️  Общее время: {stats['processing_time']:.1f}с")
            logger.info(f"⚡ Среднее время на материал: {stats['avg_time_per_material']:.2f}с")
            
            success_rate = (stats['processed_successfully'] / stats['total_materials']) * 100
            logger.info(f"📈 Успешность: {success_rate:.1f}%")
            
            if success_rate >= 90:
                logger.info("🌟 Перегенерация завершена успешно!")
            elif success_rate >= 70:
                logger.info("👍 Перегенерация завершена с предупреждениями")
            else:
                logger.warning("⚠️  Перегенерация завершена с ошибками")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка перегенерации: {e}")
            stats["processing_time"] = time.time() - start_time
            raise
    
    async def verify_embeddings_quality(self, sample_size: int = 5) -> Dict[str, Any]:
        """Проверить качество новых эмбеддингов."""
        logger.info(f"🔍 Проверяю качество эмбеддингов на выборке из {sample_size} материалов...")
        
        try:
            # Получаем образцы материалов
            materials = await self.get_all_materials()
            sample_materials = materials[:sample_size]
            
            quality_stats = {
                "sample_size": len(sample_materials),
                "vector_dimensions": [],
                "vector_norms": [],
                "non_zero_components": []
            }
            
            for material in sample_materials:
                vector = material.get("vector", [])
                payload = material.get("payload", {})
                name = payload.get("name", "Unknown")
                
                if vector:
                    # Анализируем вектор
                    dimensions = len(vector)
                    vector_norm = sum(x*x for x in vector) ** 0.5
                    non_zero_count = sum(1 for x in vector if abs(x) > 1e-8)
                    
                    quality_stats["vector_dimensions"].append(dimensions)
                    quality_stats["vector_norms"].append(vector_norm)
                    quality_stats["non_zero_components"].append(non_zero_count)
                    
                    logger.info(f"   📊 {name}: размерность={dimensions}, норма={vector_norm:.4f}, ненулевых={non_zero_count}")
            
            # Анализируем качество
            if quality_stats["vector_dimensions"]:
                avg_norm = sum(quality_stats["vector_norms"]) / len(quality_stats["vector_norms"])
                avg_non_zero = sum(quality_stats["non_zero_components"]) / len(quality_stats["non_zero_components"])
                
                logger.info(f"📈 Средняя норма векторов: {avg_norm:.4f}")
                logger.info(f"📈 Среднее количество ненулевых компонент: {avg_non_zero:.0f}")
                
                # Проверки качества
                all_1536_dims = all(d == 1536 for d in quality_stats["vector_dimensions"])
                reasonable_norms = all(0.1 < norm < 10.0 for norm in quality_stats["vector_norms"])
                diverse_vectors = all(nz > 100 for nz in quality_stats["non_zero_components"])
                
                if all_1536_dims and reasonable_norms and diverse_vectors:
                    logger.info("✅ Качество эмбеддингов: ОТЛИЧНОЕ")
                elif all_1536_dims and reasonable_norms:
                    logger.info("👍 Качество эмбеддингов: ХОРОШЕЕ")
                else:
                    logger.warning("⚠️  Качество эмбеддингов: ТРЕБУЕТ ВНИМАНИЯ")
                
                quality_stats["avg_norm"] = avg_norm
                quality_stats["avg_non_zero"] = avg_non_zero
                quality_stats["quality_checks"] = {
                    "correct_dimensions": all_1536_dims,
                    "reasonable_norms": reasonable_norms,
                    "diverse_vectors": diverse_vectors
                }
            
            return quality_stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки качества: {e}")
            raise


async def main():
    """Основная функция для запуска перегенерации эмбеддингов."""
    print("🚀 ПЕРЕГЕНЕРАЦИЯ ЭМБЕДДИНГОВ МАТЕРИАЛОВ")
    print("=" * 50)
    print("Эта утилита заменит mock эмбеддинги на реальные OpenAI векторы")
    print("для улучшения качества семантического поиска.")
    print("")
    
    # Подтверждение от пользователя
    confirm = input("❓ Продолжить перегенерацию? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Операция отменена")
        return
    
    regenerator = EmbeddingRegenerator()
    
    try:
        # Настройка
        await regenerator.setup()
        
        # Проверка качества до
        print("\n📋 Проверка качества эмбеддингов ДО перегенерации:")
        await regenerator.verify_embeddings_quality()
        
        # Перегенерация
        print(f"\n🔄 Начинаю перегенерацию эмбеддингов...")
        stats = await regenerator.regenerate_all_embeddings(batch_size=5)
        
        # Проверка качества после
        if stats["processed_successfully"] > 0:
            print("\n📋 Проверка качества эмбеддингов ПОСЛЕ перегенерации:")
            await regenerator.verify_embeddings_quality()
            
            print(f"\n🎉 Перегенерация завершена!")
            print(f"✅ Обработано: {stats['processed_successfully']}/{stats['total_materials']} материалов")
            print(f"⏱️  Время: {stats['processing_time']:.1f} секунд")
            
            print(f"\n💡 Теперь запустите тест качества поиска:")
            print(f"   python3 test_search_quality.py")
        else:
            print(f"\n❌ Не удалось обработать ни одного материала")
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print(f"💡 Проверьте:")
        print(f"   - Наличие OpenAI API ключа в .env.local")
        print(f"   - Подключение к Qdrant")
        print(f"   - Наличие материалов в коллекции")


if __name__ == "__main__":
    asyncio.run(main()) 