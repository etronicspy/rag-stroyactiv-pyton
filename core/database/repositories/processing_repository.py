"""
Repository для работы с таблицей processing_results.
Этап 8.3: Database repository для batch processing.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import text

from core.schemas.processing_models import (
    ProcessingStatus,
    MaterialProcessingResult,
    ProcessingProgress,
    ProcessingStatistics
)
from core.logging import get_logger
from core.repositories.interfaces import IBatchProcessingRepository

logger = get_logger(__name__)


class ProcessingResult:
    """SQLAlchemy модель для таблицы processing_results."""
    
    def __init__(self):
        # Будет заменено на реальную SQLAlchemy модель
        # когда будет создана в models/__init__.py
        pass


class ProcessingRepository(IBatchProcessingRepository):
    """Repository для работы с результатами batch обработки.
    Implements IBatchProcessingRepository for universal batch processing support.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger
    
    async def create_processing_records(
        self, 
        request_id: str, 
        materials: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Создать начальные записи для batch обработки.
        
        Args:
            request_id: Идентификатор запроса
            materials: Список материалов для обработки
            
        Returns:
            Список ID созданных записей
        """
        try:
            records = []
            for material in materials:
                record_data = {
                    'request_id': request_id,
                    'material_id': material['id'],
                    'original_name': material['name'],
                    'original_unit': material['unit'],
                    'processing_status': ProcessingStatus.PENDING.value,
                    'created_at': datetime.utcnow(),
                    'retry_count': 0
                }
                records.append(record_data)
            
            # Bulk insert с использованием raw SQL для производительности
            
            insert_query = text("""
                INSERT INTO processing_results 
                (request_id, material_id, original_name, original_unit, processing_status, created_at, retry_count)
                VALUES 
                """ + ", ".join([
                    f"('{record['request_id']}', '{record['material_id']}', '{record['original_name']}', "
                    f"'{record['original_unit']}', '{record['processing_status']}', "
                    f"'{record['created_at']}', {record['retry_count']})"
                    for record in records
                ]) + " RETURNING id"
            )
            
            result = await self.session.execute(insert_query)
            record_ids = [str(row[0]) for row in result.fetchall()]
            
            await self.session.commit()
            
            self.logger.info(f"Created {len(record_ids)} processing records for request {request_id}")
            return record_ids
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error creating processing records: {str(e)}")
            raise
    
    async def get_pending_materials(
        self, 
        request_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Получить материалы со статусом pending для обработки.
        
        Args:
            request_id: Идентификатор запроса
            limit: Максимальное количество записей
            
        Returns:
            Список материалов для обработки
        """
        try:
            query = text("""
                SELECT id, material_id, original_name, original_unit, retry_count
                FROM processing_results
                WHERE request_id = :request_id 
                AND processing_status = 'pending'
                ORDER BY created_at ASC
                LIMIT :limit
            """)
            
            result = await self.session.execute(
                query, 
                {'request_id': request_id, 'limit': limit}
            )
            
            materials = []
            for row in result.fetchall():
                materials.append({
                    'id': row[0],
                    'material_id': row[1],
                    'original_name': row[2],
                    'original_unit': row[3],
                    'retry_count': row[4]
                })
            
            self.logger.debug(f"Found {len(materials)} pending materials for request {request_id}")
            return materials
            
        except Exception as e:
            self.logger.error(f"Error getting pending materials: {str(e)}")
            raise
    
    async def update_processing_status(
        self, 
        record_id: str, 
        status: ProcessingStatus,
        **kwargs
    ) -> bool:
        """
        Обновить статус обработки записи.
        
        Args:
            record_id: ID записи
            status: Новый статус
            **kwargs: Дополнительные поля для обновления
            
        Returns:
            True если успешно обновлено
        """
        try:
            update_fields = {
                'processing_status': status.value,
                'updated_at': datetime.utcnow()
            }
            
            if status == ProcessingStatus.COMPLETED:
                update_fields['processed_at'] = datetime.utcnow()
            
            # Добавляем дополнительные поля
            for field, value in kwargs.items():
                if field in ['sku', 'similarity_score', 'error_message', 
                           'normalized_color', 'normalized_unit', 'unit_coefficient']:
                    update_fields[field] = value
            
            # Создаем SET часть запроса
            set_clause = ", ".join([f"{field} = :{field}" for field in update_fields.keys()])
            
            query = text(f"""
                UPDATE processing_results 
                SET {set_clause}
                WHERE id = :record_id
            """)
            
            update_fields['record_id'] = record_id
            
            result = await self.session.execute(query, update_fields)
            await self.session.commit()
            
            success = result.rowcount > 0
            if success:
                self.logger.debug(f"Updated processing record {record_id} to status {status.value}")
            else:
                self.logger.warning(f"No record found with id {record_id}")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating processing status: {str(e)}")
            raise
    
    async def get_processing_progress(self, request_id: str) -> ProcessingProgress:
        """
        Получить прогресс обработки запроса.
        
        Args:
            request_id: Идентификатор запроса
            
        Returns:
            Объект с прогрессом обработки
        """
        try:
            query = text("""
                SELECT 
                    processing_status,
                    COUNT(*) as count
                FROM processing_results
                WHERE request_id = :request_id
                GROUP BY processing_status
            """)
            
            result = await self.session.execute(query, {'request_id': request_id})
            
            status_counts = {}
            for row in result.fetchall():
                status_counts[row[0]] = row[1]
            
            total = sum(status_counts.values())
            completed = status_counts.get('completed', 0)
            failed = status_counts.get('failed', 0)
            pending = status_counts.get('pending', 0)
            
            progress = ProcessingProgress(
                total=total,
                completed=completed,
                failed=failed,
                pending=pending
            )
            
            self.logger.debug(f"Processing progress for {request_id}: {progress}")
            return progress
            
        except Exception as e:
            self.logger.error(f"Error getting processing progress: {str(e)}")
            raise
    
    async def get_processing_results(
        self, 
        request_id: str, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MaterialProcessingResult]:
        """
        Получить результаты обработки запроса.
        
        Args:
            request_id: Идентификатор запроса
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            
        Returns:
            Список результатов обработки
        """
        try:
            query_parts = ["""
                SELECT 
                    material_id, original_name, original_unit, sku,
                    similarity_score, processing_status, error_message, processed_at,
                    normalized_color, normalized_unit, unit_coefficient
                FROM processing_results
                WHERE request_id = :request_id
                ORDER BY created_at ASC
            """]
            
            params = {'request_id': request_id}
            
            if limit is not None:
                query_parts.append("LIMIT :limit")
                params['limit'] = limit
            
            if offset is not None:
                query_parts.append("OFFSET :offset")
                params['offset'] = offset
            
            query = text(" ".join(query_parts))
            result = await self.session.execute(query, params)
            
            results = []
            for row in result.fetchall():
                result_obj = MaterialProcessingResult(
                    material_id=row[0],
                    original_name=row[1],
                    original_unit=row[2],
                    sku=row[3],
                    similarity_score=row[4],
                    processing_status=ProcessingStatus(row[5]),
                    error_message=row[6],
                    processed_at=row[7],
                    normalized_color=row[8],
                    normalized_unit=row[9],
                    unit_coefficient=row[10]
                )
                results.append(result_obj)
            
            self.logger.debug(f"Found {len(results)} processing results for request {request_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting processing results: {str(e)}")
            raise
    
    async def get_failed_materials_for_retry(
        self, 
        max_retries: int = 3, 
        retry_delay_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Получить материалы для повторной обработки.
        
        Args:
            max_retries: Максимальное количество попыток
            retry_delay_minutes: Задержка между попытками в минутах
            
        Returns:
            Список материалов для retry
        """
        try:
            retry_time = datetime.utcnow() - timedelta(minutes=retry_delay_minutes)
            
            query = text("""
                SELECT id, request_id, material_id, original_name, original_unit, retry_count
                FROM processing_results
                WHERE processing_status = 'failed'
                AND retry_count < :max_retries
                AND (retry_after IS NULL OR retry_after <= :retry_time)
                ORDER BY created_at ASC
                LIMIT 100
            """)
            
            result = await self.session.execute(
                query, 
                {'max_retries': max_retries, 'retry_time': retry_time}
            )
            
            materials = []
            for row in result.fetchall():
                materials.append({
                    'id': row[0],
                    'request_id': row[1],
                    'material_id': row[2],
                    'original_name': row[3],
                    'original_unit': row[4],
                    'retry_count': row[5]
                })
            
            self.logger.debug(f"Found {len(materials)} materials for retry")
            return materials
            
        except Exception as e:
            self.logger.error(f"Error getting materials for retry: {str(e)}")
            raise
    
    async def increment_retry_count(self, record_id: str) -> bool:
        """
        Увеличить счетчик повторных попыток.
        
        Args:
            record_id: ID записи
            
        Returns:
            True если успешно обновлено
        """
        try:
            retry_after = datetime.utcnow() + timedelta(minutes=60)  # Retry через час
            
            query = text("""
                UPDATE processing_results 
                SET retry_count = retry_count + 1,
                    retry_after = :retry_after,
                    processing_status = 'pending',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :record_id
            """)
            
            result = await self.session.execute(
                query, 
                {'record_id': record_id, 'retry_after': retry_after}
            )
            await self.session.commit()
            
            success = result.rowcount > 0
            if success:
                self.logger.debug(f"Incremented retry count for record {record_id}")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error incrementing retry count: {str(e)}")
            raise
    
    async def get_processing_statistics(self) -> ProcessingStatistics:
        """
        Получить общую статистику обработки.
        
        Returns:
            Объект со статистикой
        """
        try:
            query = text("""
                SELECT 
                    COUNT(DISTINCT request_id) as total_requests,
                    COUNT(DISTINCT CASE WHEN processing_status = 'processing' THEN request_id END) as active_requests,
                    COUNT(DISTINCT CASE WHEN processing_status = 'completed' THEN request_id END) as completed_requests,
                    COUNT(DISTINCT CASE WHEN processing_status = 'failed' THEN request_id END) as failed_requests,
                    COUNT(*) as total_materials_processed,
                    AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) as avg_processing_time,
                    COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) * 1.0 / COUNT(*) as success_rate
                FROM processing_results
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
            
            result = await self.session.execute(query)
            row = result.fetchone()
            
            if row:
                stats = ProcessingStatistics(
                    total_requests=row[0] or 0,
                    active_requests=row[1] or 0,
                    completed_requests=row[2] or 0,
                    failed_requests=row[3] or 0,
                    total_materials_processed=row[4] or 0,
                    average_processing_time=row[5] or 0.0,
                    success_rate=row[6] or 0.0
                )
            else:
                stats = ProcessingStatistics(
                    total_requests=0,
                    active_requests=0,
                    completed_requests=0,
                    failed_requests=0,
                    total_materials_processed=0,
                    average_processing_time=0.0,
                    success_rate=0.0
                )
            
            self.logger.debug(f"Processing statistics: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting processing statistics: {str(e)}")
            raise
    
    async def cleanup_old_records(self, days_old: int = 30) -> int:
        """
        Очистить старые записи обработки.
        
        Args:
            days_old: Количество дней для удаления
            
        Returns:
            Количество удаленных записей
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            query = text("""
                DELETE FROM processing_results 
                WHERE created_at < :cutoff_date
                AND processing_status IN ('completed', 'failed')
            """)
            
            result = await self.session.execute(query, {'cutoff_date': cutoff_date})
            await self.session.commit()
            
            deleted_count = result.rowcount
            self.logger.info(f"Cleaned up {deleted_count} old processing records")
            
            return deleted_count
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error cleaning up old records: {str(e)}")
            raise 

    async def save_processed_material(self, record_id: str, material_data: Dict[str, Any], status: ProcessingStatus, **kwargs) -> bool:
        """
        Upsert: если запись есть — обновить, если нет — создать новую.
        Args:
            record_id: ID записи
            material_data: данные материала (dict)
            status: новый статус
            **kwargs: дополнительные поля
        Returns:
            True если успешно сохранено
        """
        # Проверяем наличие записи
        query = text("SELECT id FROM processing_results WHERE id = :record_id")
        result = await self.session.execute(query, {'record_id': record_id})
        row = result.fetchone()
        if row:
            # Обновляем существующую запись
            return await self.update_processing_status(record_id, status, **kwargs)
        else:
            # Создаём новую запись (используем create_processing_records)
            await self.create_processing_records(material_data['request_id'], [material_data])
            # После создания — обновляем статус и дополнительные поля
            return await self.update_processing_status(record_id, status, **kwargs) 