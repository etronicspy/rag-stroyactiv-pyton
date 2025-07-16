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
from core.schemas.pipeline_models import MaterialProcessRequest, ProcessingResult
from core.database.repositories.processing_repository import ProcessingRepository
from core.logging import get_logger
from core.config.base import get_settings

# Импорт всех компонентов pipeline (этапы 1-7)
from services.material_processing_pipeline import MaterialProcessingPipeline
from services.combined_embedding_service import CombinedEmbeddingService
from services.sku_search_service import SKUSearchService
from services.materials import MaterialsService
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
            self.logger.info(f"Starting _process_materials_batch for request {request_id}")
            
            # 1. Инициализация - создание записей в БД
            self.logger.info(f"Step 1: Initializing processing records for request {request_id}")
            await self._initialize_processing_records(request_id, materials)
            
            # 2. Batch обработка по частям
            self.logger.info(f"Step 2: Starting batch processing for request {request_id}")
            await self._process_in_batches(request_id)
            
            # 3. Завершение обработки
            self.logger.info(f"Step 3: Finalizing processing for request {request_id}")
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
                    'material_id': material.id,  # исправлено!
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
            self.logger.info(f"Starting batch processing for request {request_id}")
            fallback_manager = get_fallback_manager()
            batch_size = self.config.batch_processing_size
            
            # Получаем все записи для данного request_id
            all_records = await fallback_manager.get_processing_results(request_id)
            self.logger.info(f"Retrieved {len(all_records)} total records for request {request_id}")
            
            pending_materials = [
                record for record in all_records 
                if record.get('status') == 'pending'
            ]
            
            self.logger.info(f"Found {len(pending_materials)} pending materials for request {request_id}")
            
            if not pending_materials:
                self.logger.warning(f"No pending materials found for request {request_id}")
                return
            
            # Обрабатываем материалы по batch'ам
            for i in range(0, len(pending_materials), batch_size):
                batch = pending_materials[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1} with {len(batch)} materials")
                
                # Обрабатываем каждый материал в batch
                for material_record in batch:
                    self.logger.info(f"Processing material {material_record.get('material_id')} from record")
                    await self._process_single_material_from_record(request_id, material_record)
                
        except Exception as e:
            self.logger.error(f"Error in batch processing: {str(e)}")
            raise
    
    async def _process_single_material_from_record(self, request_id: str, material_record: dict) -> None:
        """
        Обработать один материал из записи в БД.
        
        Args:
            request_id: Идентификатор запроса
            material_record: Запись материала из БД
        """
        material_id = material_record.get('material_id')
        self.logger.info(f"Starting processing for material {material_id}")
        self.logger.debug(f"Material record for processing: {material_record}")
        try:
            # Обновляем статус на "processing"
            self.logger.info(f"Updating status to PROCESSING for material {material_id}")
            await self._update_material_status(
                material_id, 
                ProcessingStatus.PROCESSING
            )
            
            # Создаем запрос для pipeline
            pipeline_request = MaterialProcessRequest(
                id=material_id,
                name=material_record.get('original_name', 'Unknown Material'),
                unit=material_record.get('original_unit', 'шт'),
                price=0.0,  # Добавляем обязательное поле price
                enable_color_extraction=True,
                enable_unit_normalization=True,
                enable_sku_search=True,
                parsing_method="ai_gpt"  # Исправлено!
            )
            self.logger.info(f"Created pipeline request for material {material_id}: {pipeline_request.name}")
            self.logger.debug(f"Pipeline request: {pipeline_request.dict()}")
            
            # Проходим через полный pipeline
            self.logger.info(f"Starting pipeline processing for material {material_id}")
            processing_result = await self.pipeline.process_material(pipeline_request)
            self.logger.info(f"Pipeline completed for material {material_id}, success: {processing_result.overall_success}")
            
            # Обрабатываем результат
            await self._handle_processing_result(
                material_id, 
                material_id, 
                processing_result
            )
            
        except Exception as e:
            self.logger.error(f"Error processing material {material_id}: {str(e)}")
            # Обрабатываем ошибку
            await self._handle_processing_error(
                material_id, 
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
                error_msg = f"Pipeline processing failed: overall_success=False"
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
            self.logger.error(f"_handle_processing_error called for material {material_id} with error: {error_message}")
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
            self.logger.info(f"_update_material_status called for {record_id} to {status}")
            fallback_manager = get_fallback_manager()
            # Подготавливаем дополнительные поля для передачи
            additional_fields = {}
            if 'sku' in kwargs:
                additional_fields['sku'] = kwargs['sku']
            if 'similarity_score' in kwargs:
                additional_fields['similarity_score'] = kwargs['similarity_score']
            if 'normalized_color' in kwargs:
                additional_fields['normalized_color'] = kwargs['normalized_color']
            if 'normalized_unit' in kwargs:
                additional_fields['normalized_unit'] = kwargs['normalized_unit']
            if 'unit_coefficient' in kwargs:
                additional_fields['unit_coefficient'] = kwargs['unit_coefficient']
            if 'processed_at' in kwargs:
                additional_fields['processed_at'] = kwargs['processed_at']

            # Гарантируем, что material_id всегда str и не None
            assert record_id is not None and isinstance(record_id, str), f"material_id (record_id) must be str, got {record_id} ({type(record_id)})"
            self.logger.debug(f"Calling update_processing_status with material_id={record_id} (type={type(record_id)}), status={status}, additional_fields={additional_fields}")
            await fallback_manager.update_processing_status(
                record_id,  # request_id
                record_id,  # material_id
                status.value,
                kwargs.get('error_message', None),
                **additional_fields
            )
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
                f"Results: {progress['completed']}/{progress['total']} completed, "
                f"{progress['failed']} failed"
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
                    self.logger.info(f"Retrying {len(materials)} materials for request {request_id}")
                    
                    # Обрабатываем каждый материал
                    for material in materials:
                        # Увеличиваем retry counter
                        await fallback_manager.increment_retry_count(material['id'])
                        
                        # Фактически обрабатываем материал
                        await self._process_single_material_from_record(request_id, material)
            
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