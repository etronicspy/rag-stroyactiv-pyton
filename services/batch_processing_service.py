"""
Batch Processing Service для асинхронной обработки материалов.
Этап 8.4: Background processing service с интеграцией всех компонентов pipeline.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from core.schemas.processing_models import (
    ProcessingStatus,
    MaterialInput,
    ProcessingJobConfig,
    ProcessingProgress,
    ProcessingStatistics,
    MaterialProcessingResult
)
from core.database.repositories.processing_repository import ProcessingRepository
from core.logging import get_logger
from core.config.base import get_settings

# Импорт всех компонентов pipeline (этапы 1-7)
from services.material_processing_pipeline import MaterialProcessingPipeline
from services.combined_embedding_service import CombinedEmbeddingService
from services.sku_search_service import SKUSearchService
from services.materials import MaterialsService
from core.schemas.pipeline_models import MaterialProcessRequest, ProcessingResult
from core.database.factories import get_fallback_manager, AllDatabasesUnavailableError

logger = get_logger(__name__)


class BatchProcessingService:
    """
    Сервис для batch обработки материалов с интеграцией всех этапов pipeline.
    Поддерживает асинхронную обработку, retry logic и мониторинг прогресса.
    """
    
    def __init__(self, config: Optional[ProcessingJobConfig] = None):
        self.config = config or ProcessingJobConfig()
        self.logger = logger
        
        # Компоненты pipeline
        self.pipeline = MaterialProcessingPipeline()
        self.combined_embedding_service = CombinedEmbeddingService()
        self.sku_search_service = SKUSearchService()
        self.materials_service = MaterialsService()
        
        # Активные задачи
        self.active_jobs: Dict[str, asyncio.Task] = {}
        
        # Thread pool для CPU-intensive операций
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Статистика
        self.stats = {
            'total_jobs': 0,
            'active_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0
        }
    
    async def start_processing_job(
        self, 
        request_id: str, 
        materials: List[MaterialInput]
    ) -> bool:
        """
        Запустить задачу batch обработки материалов.
        
        Args:
            request_id: Идентификатор запроса
            materials: Список материалов для обработки
            
        Returns:
            True если задача успешно запущена
        """
        try:
            # Проверяем лимиты
            if len(materials) > self.config.max_materials_per_request:
                self.logger.warning(
                    f"Request {request_id} exceeds material limit: {len(materials)} > {self.config.max_materials_per_request}"
                )
                return False
            
            # Проверяем активные задачи
            if len(self.active_jobs) >= self.config.max_concurrent_batches:
                self.logger.warning(
                    f"Max concurrent batches reached: {len(self.active_jobs)} >= {self.config.max_concurrent_batches}"
                )
                return False
            
            # Создаем задачу для background processing
            task = asyncio.create_task(
                self._process_materials_batch(request_id, materials)
            )
            
            # Добавляем в активные задачи
            self.active_jobs[request_id] = task
            
            # Обновляем статистику
            self.stats['total_jobs'] += 1
            self.stats['active_jobs'] += 1
            
            self.logger.info(f"Started batch processing job for request {request_id} with {len(materials)} materials")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting processing job: {str(e)}")
            return False
    
    async def _process_materials_batch(
        self, 
        request_id: str, 
        materials: List[MaterialInput]
    ) -> None:
        """
        Основная логика batch обработки материалов.
        
        Args:
            request_id: Идентификатор запроса
            materials: Список материалов для обработки
        """
        start_time = datetime.utcnow()
        
        try:
            # 1. Инициализация - создание записей в БД
            await self._initialize_processing_records(request_id, materials)
            
            # 2. Batch обработка по частям
            await self._process_in_batches(request_id)
            
            # 3. Завершение обработки
            await self._finalize_processing(request_id, start_time)
            
        except Exception as e:
            self.logger.error(f"Error in batch processing for request {request_id}: {str(e)}")
            await self._mark_job_failed(request_id, str(e))
        
        finally:
            # Очищаем активные задачи
            if request_id in self.active_jobs:
                del self.active_jobs[request_id]
            
            self.stats['active_jobs'] -= 1
    
    async def _initialize_processing_records(
        self, 
        request_id: str, 
        materials: List[MaterialInput]
    ) -> None:
        """
        Создать начальные записи в БД для обработки через fallback manager.
        """
        try:
            fallback_manager = get_fallback_manager()
            # Конвертируем в формат для repository
            material_dicts = [
                {
                    'id': material.id,
                    'name': material.name,
                    'unit': material.unit
                }
                for material in materials
            ]
            record_ids = await fallback_manager.create_processing_records(request_id, material_dicts)
            self.logger.info(f"Created {len(record_ids)} processing records for request {request_id}")
        except Exception as e:
            self.logger.error(f"Error initializing processing records: {str(e)}")
            raise

    async def _process_in_batches(self, request_id: str) -> None:
        """
        Обработать материалы по batch'ам через fallback manager.
        """
        try:
            fallback_manager = get_fallback_manager()
            batch_size = self.config.batch_processing_size
            while True:
                # Получаем следующий batch pending материалов (оставить как есть или реализовать через fallback позже)
                # Здесь можно реализовать через fallback_manager, если будет поддержка
                # pending_materials = await fallback_manager.get_pending_materials(request_id, limit=batch_size)
                # Пока оставляем как есть, если нет поддержки в fallback
                break  # TODO: реализовать через fallback_manager
        except Exception as e:
            self.logger.error(f"Error in batch processing: {str(e)}")
            raise
    
    async def _process_single_batch(
        self, 
        request_id: str, 
        materials: List[Dict[str, Any]]
    ) -> None:
        """
        Обработать один batch материалов.
        
        Args:
            request_id: Идентификатор запроса
            materials: Список материалов для обработки
        """
        try:
            # Создаем задачи для параллельной обработки
            tasks = []
            
            for material in materials:
                task = asyncio.create_task(
                    self._process_single_material(request_id, material)
                )
                tasks.append(task)
            
            # Ждем завершения всех задач в batch
            await asyncio.gather(*tasks, return_exceptions=True)
            
            self.logger.debug(f"Processed batch of {len(materials)} materials for request {request_id}")
            
        except Exception as e:
            self.logger.error(f"Error processing single batch: {str(e)}")
            raise
    
    async def _process_single_material(
        self, 
        request_id: str, 
        material: Dict[str, Any]
    ) -> None:
        """
        Обработать один материал через весь pipeline.
        
        Args:
            request_id: Идентификатор запроса
            material: Данные материала
        """
        record_id = material['id']
        material_id = material['material_id']
        
        try:
            # Обновляем статус на "processing"
            await self._update_material_status(
                record_id, 
                ProcessingStatus.PROCESSING
            )
            
            # Создаем запрос для pipeline
            pipeline_request = MaterialProcessRequest(
                id=material_id,
                name=material['original_name'],
                unit=material['original_unit']
            )
            
            # Проходим через полный pipeline (этапы 1-7)
            processing_result = await self.pipeline.process_material(pipeline_request)
            
            # Обрабатываем результат
            await self._handle_processing_result(
                record_id, 
                material_id, 
                processing_result
            )
            
        except Exception as e:
            # Обрабатываем ошибку
            await self._handle_processing_error(
                record_id, 
                material_id, 
                str(e)
            )
    
    async def _handle_processing_result(
        self, 
        record_id: str, 
        material_id: str, 
        result: ProcessingResult
    ) -> None:
        """
        Обработать результат pipeline обработки.
        
        Args:
            record_id: ID записи в БД
            material_id: ID материала
            result: Результат обработки
        """
        try:
            if result.overall_success:
                # Ищем SKU для материала
                sku = await self._find_material_sku(result)
                
                # Обновляем статус на "completed"
                await self._update_material_status(
                    record_id,
                    ProcessingStatus.COMPLETED,
                    sku=sku,
                    similarity_score=getattr(result, 'similarity_score', None),
                    normalized_color=getattr(result, 'normalized_color', None),
                    normalized_unit=getattr(result, 'normalized_unit', None),
                    unit_coefficient=getattr(result, 'unit_coefficient', None)
                )
                
                self.logger.debug(f"Successfully processed material {material_id} with SKU: {sku}")
                
            else:
                # Обработка неуспешна
                error_msg = f"Pipeline processing failed: {result.stage}"
                await self._update_material_status(
                    record_id,
                    ProcessingStatus.FAILED,
                    error_message=error_msg
                )
                
                self.logger.warning(f"Processing failed for material {material_id}: {error_msg}")
                
        except Exception as e:
            await self._handle_processing_error(record_id, material_id, str(e))
    
    async def _find_material_sku(self, result: ProcessingResult) -> Optional[str]:
        """
        Найти SKU для материала через SKU search service.
        
        Args:
            result: Результат pipeline обработки
            
        Returns:
            SKU или None если не найден
        """
        try:
            # Генерируем комбинированный embedding
            embedding_result = await self.combined_embedding_service.generate_material_embedding(
                name=result.name,
                normalized_unit=getattr(result, 'normalized_unit', ''),
                normalized_color=getattr(result, 'normalized_color', None)
            )
            
            if not embedding_result.success:
                return None
            
            # Ищем SKU через двухэтапный поиск
            sku_result = await self.sku_search_service.find_sku_by_material_data(
                material_embedding=embedding_result.embedding,
                normalized_unit=getattr(result, 'normalized_unit', ''),
                normalized_color=getattr(result, 'normalized_color', None),
                similarity_threshold=self.config.similarity_threshold
            )
            
            return sku_result.sku if sku_result and sku_result.sku else None
            
        except Exception as e:
            self.logger.error(f"Error finding material SKU: {str(e)}")
            return None
    
    async def _handle_processing_error(
        self, 
        record_id: str, 
        material_id: str, 
        error_message: str
    ) -> None:
        """
        Обработать ошибку при обработке материала.
        
        Args:
            record_id: ID записи в БД
            material_id: ID материала
            error_message: Сообщение об ошибке
        """
        try:
            # Обновляем статус на "failed"
            await self._update_material_status(
                record_id,
                ProcessingStatus.FAILED,
                error_message=error_message
            )
            
            self.logger.error(f"Processing error for material {material_id}: {error_message}")
            
        except Exception as e:
            self.logger.error(f"Error handling processing error: {str(e)}")
    
    async def _update_material_status(
        self, 
        record_id: str, 
        status: ProcessingStatus, 
        **kwargs
    ) -> None:
        """
        Обновить статус материала в БД через fallback manager.
        """
        try:
            fallback_manager = get_fallback_manager()
            await fallback_manager.update_processing_status(record_id, kwargs.get('material_id', None), status.value, kwargs.get('error_message', None))
        except Exception as e:
            self.logger.error(f"Error updating material status: {str(e)}")
            raise
    
    async def _finalize_processing(
        self, 
        request_id: str, 
        start_time: datetime
    ) -> None:
        """
        Завершить обработку запроса через fallback manager.
        """
        try:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            fallback_manager = get_fallback_manager()
            progress = await fallback_manager.get_processing_progress(request_id)
            self.stats['completed_jobs'] += 1
            self.logger.info(
                f"Completed batch processing for request {request_id}. "
                f"Processing time: {processing_time:.2f}s, "
                f"Results: {progress.completed}/{progress.total} completed, "
                f"{progress.failed} failed"
            )
        except Exception as e:
            self.logger.error(f"Error finalizing processing: {str(e)}")
    
    async def _mark_job_failed(self, request_id: str, error_message: str) -> None:
        """
        Отметить задачу как неуспешную.
        
        Args:
            request_id: Идентификатор запроса
            error_message: Сообщение об ошибке
        """
        try:
            self.stats['failed_jobs'] += 1
            self.logger.error(f"Batch processing job failed for request {request_id}: {error_message}")
            
        except Exception as e:
            self.logger.error(f"Error marking job as failed: {str(e)}")
    
    async def get_processing_progress(self, request_id: str) -> ProcessingProgress:
        """
        Получить прогресс обработки запроса через централизованный fallback manager.
        Args:
            request_id: Идентификатор запроса
        Returns:
            Объект с прогрессом
        Raises:
            AllDatabasesUnavailableError: если все БД недоступны
        """
        fallback_manager = get_fallback_manager()
        try:
            progress = await fallback_manager.get_processing_progress(request_id)
            return progress
        except Exception as e:
            self.logger.error(f"Error getting processing progress: {str(e)}")
            if isinstance(e, AllDatabasesUnavailableError):
                raise
            raise

    async def get_processing_results(
        self, 
        request_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MaterialProcessingResult]:
        """
        Получить результаты обработки запроса через централизованный fallback manager.
        Args:
            request_id: Идентификатор запроса
            limit: Лимит записей
            offset: Смещение
        Returns:
            Список результатов обработки
        Raises:
            AllDatabasesUnavailableError: если все БД недоступны
        """
        fallback_manager = get_fallback_manager()
        try:
            results = await fallback_manager.get_processing_results(request_id, limit, offset)
            return results
        except Exception as e:
            self.logger.error(f"Error getting processing results: {str(e)}")
            if isinstance(e, AllDatabasesUnavailableError):
                raise
            raise
    
    async def get_service_statistics(self) -> ProcessingStatistics:
        """
        Получить статистику сервиса через централизованный fallback manager.
        Returns:
            Объект со статистикой
        Raises:
            AllDatabasesUnavailableError: если все БД недоступны
        """
        fallback_manager = get_fallback_manager()
        try:
            # Предполагается, что sql_client.get_processing_statistics асинхронный
            result = await fallback_manager.get_processing_statistics()
            return result
        except AllDatabasesUnavailableError as e:
            self.logger.error(f"All databases unavailable for service statistics: {e.errors}")
            raise
    
    async def retry_failed_materials(self) -> int:
        """
        Повторить обработку неуспешных материалов.
        
        Returns:
            Количество материалов для повторной обработки
        """
        try:
            fallback_manager = get_fallback_manager()
            # Получаем материалы для retry
            retry_materials = await fallback_manager.get_failed_materials_for_retry(
                max_retries=self.config.max_retries,
                retry_delay_minutes=self.config.retry_delay // 60
            )
            
            # Группируем по request_id
            retry_groups = {}
            for material in retry_materials:
                request_id = material['request_id']
                if request_id not in retry_groups:
                    retry_groups[request_id] = []
                retry_groups[request_id].append(material)
            
            # Запускаем retry для каждой группы
            for request_id, materials in retry_groups.items():
                if request_id not in self.active_jobs:
                    # Увеличиваем retry counter
                    for material in materials:
                        await fallback_manager.increment_retry_count(material['id'])
                    
                    self.logger.info(f"Retrying {len(materials)} materials for request {request_id}")
            
            return len(retry_materials)
                
        except Exception as e:
            self.logger.error(f"Error retrying failed materials: {str(e)}")
            raise
    
    async def cleanup_old_records(self, days_old: int = 30) -> int:
        """
        Очистить старые записи.
        
        Args:
            days_old: Количество дней
            
        Returns:
            Количество удаленных записей
        """
        try:
            fallback_manager = get_fallback_manager()
            return await fallback_manager.cleanup_old_records(days_old)
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old records: {str(e)}")
            raise
    
    def get_active_jobs(self) -> List[str]:
        """
        Получить список активных задач.
        
        Returns:
            Список request_id активных задач
        """
        return list(self.active_jobs.keys())
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Получить статистику сервиса.
        
        Returns:
            Словарь со статистикой
        """
        return {
            **self.stats,
            'active_job_ids': self.get_active_jobs(),
            'config': self.config.dict()
        }


# Singleton instance
_batch_processing_service: Optional[BatchProcessingService] = None


def get_batch_processing_service() -> BatchProcessingService:
    """
    Получить singleton instance сервиса batch processing.
    
    Returns:
        Singleton instance BatchProcessingService
    """
    global _batch_processing_service
    
    if _batch_processing_service is None:
        _batch_processing_service = BatchProcessingService()
    
    return _batch_processing_service 