"""
API endpoints для batch processing материалов.
Этап 8.5: API endpoints для асинхронной обработки материалов.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from core.schemas.processing_models import (
    BatchMaterialsRequest,
    BatchProcessingResponse,
    BatchValidationError,
    ProcessingStatusResponse,
    ProcessingResultsResponse,
    ProcessingStatus,
    ProcessingProgress,
    MaterialProcessingResult,
    ProcessingStatistics,
    BatchResponse
)
from services.batch_processing_service import get_batch_processing_service
from core.logging import get_logger

# Создаем router
router = APIRouter(
    prefix="/api/v1/materials",
    tags=["Enhanced Processing"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

logger = get_logger(__name__)


@router.post(
    "/process-enhanced",
    response_model=Union[BatchProcessingResponse, BatchValidationError],
    summary="Запустить batch обработку материалов",
    description="Принимает список материалов для асинхронной обработки через полный pipeline",
    responses={
        202: {
            "description": "Запрос принят в обработку",
            "model": BatchProcessingResponse
        },
        400: {
            "description": "Ошибка валидации данных",
            "model": BatchValidationError
        },
        429: {
            "description": "Превышен лимит запросов"
        }
    }
)
async def process_materials_batch(
    request: BatchMaterialsRequest,
    background_tasks: BackgroundTasks,
    batch_service = Depends(get_batch_processing_service)
) -> BatchResponse:
    """
    Запустить batch обработку материалов.
    
    Последовательность обработки:
    1. Быстрая валидация входных данных
    2. Инициализация background job
    3. Возврат response с request_id для tracking
    
    Args:
        request: Запрос с материалами для обработки
        background_tasks: FastAPI background tasks
        batch_service: Сервис batch обработки
        
    Returns:
        Ответ о принятии запроса или ошибке валидации
    """
    try:
        # Логируем начало обработки
        logger.info(f"Received batch processing request {request.request_id} with {len(request.materials)} materials")
        
        # Проверяем лимиты
        service_stats = batch_service.get_service_stats()
        
        if len(request.materials) > batch_service.config.max_materials_per_request:
            error_response = BatchValidationError(
                errors=[f"Too many materials: {len(request.materials)} > {batch_service.config.max_materials_per_request}"],
                rejected_materials=[]
            )
            return error_response
        
        # Проверяем активные задачи
        if service_stats['active_jobs'] >= batch_service.config.max_concurrent_batches:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many active jobs: {service_stats['active_jobs']} >= {batch_service.config.max_concurrent_batches}"
            )
        
        # Запускаем background job
        job_started = await batch_service.start_processing_job(
            request.request_id,
            request.materials
        )
        
        if not job_started:
            error_response = BatchValidationError(
                errors=["Failed to start processing job"],
                rejected_materials=[]
            )
            return error_response
        
        # Вычисляем предполагаемое время завершения
        estimated_completion = datetime.utcnow() + timedelta(
            seconds=len(request.materials) * 2  # Примерно 2 секунды на материал
        )
        
        # Успешный ответ
        response = BatchProcessingResponse(
            status="accepted",
            request_id=request.request_id,
            materials_count=len(request.materials),
            estimated_completion=estimated_completion
        )
        
        logger.info(f"Started batch processing job {request.request_id}")
        return response
        
    except ValidationError as e:
        error_response = BatchValidationError(
            errors=[str(err) for err in e.errors()],
            rejected_materials=[]
        )
        logger.warning(f"Validation error for request {request.request_id}: {e}")
        return error_response
        
    except Exception as e:
        logger.error(f"Unexpected error processing batch request {request.request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during request processing"
        )


@router.get(
    "/process-enhanced/status/{request_id}",
    response_model=ProcessingStatusResponse,
    summary="Получить статус обработки",
    description="Возвращает текущий статус и прогресс обработки запроса",
    responses={
        200: {
            "description": "Статус обработки",
            "model": ProcessingStatusResponse
        },
        404: {
            "description": "Запрос не найден"
        }
    }
)
async def get_processing_status(
    request_id: str,
    batch_service = Depends(get_batch_processing_service)
) -> ProcessingStatusResponse:
    """
    Получить статус обработки запроса.
    
    Args:
        request_id: Идентификатор запроса
        batch_service: Сервис batch обработки
        
    Returns:
        Объект с текущим статусом и прогрессом
    """
    try:
        logger.debug(f"Getting processing status for request {request_id}")
        
        # Получаем прогресс обработки
        progress = await batch_service.get_processing_progress(request_id)
        
        # Проверяем, найден ли запрос
        if progress.total == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        
        # Определяем общий статус
        if progress.pending > 0:
            overall_status = ProcessingStatus.PROCESSING
        elif progress.failed > 0 and progress.completed == 0:
            overall_status = ProcessingStatus.FAILED
        elif progress.completed == progress.total:
            overall_status = ProcessingStatus.COMPLETED
        else:
            overall_status = ProcessingStatus.PROCESSING
        
        # Проверяем активные задачи
        active_jobs = batch_service.get_active_jobs()
        is_active = request_id in active_jobs
        
        # Вычисляем предполагаемое время завершения
        estimated_completion = None
        if overall_status == ProcessingStatus.PROCESSING and progress.pending > 0:
            estimated_completion = datetime.utcnow() + timedelta(
                seconds=progress.pending * 2
            )
        
        response = ProcessingStatusResponse(
            request_id=request_id,
            status=overall_status,
            progress=progress,
            estimated_completion=estimated_completion,
            started_at=None,  # Можно добавить в БД
            completed_at=None  # Можно добавить в БД
        )
        
        logger.debug(f"Processing status for {request_id}: {overall_status.value}, {progress.completed}/{progress.total}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing status for {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting processing status"
        )


@router.get(
    "/process-enhanced/results/{request_id}",
    response_model=ProcessingResultsResponse,
    summary="Получить результаты обработки",
    description="Возвращает детальные результаты обработки материалов",
    responses={
        200: {
            "description": "Результаты обработки",
            "model": ProcessingResultsResponse
        },
        404: {
            "description": "Запрос не найден"
        }
    }
)
async def get_processing_results(
    request_id: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    batch_service = Depends(get_batch_processing_service)
) -> ProcessingResultsResponse:
    """
    Получить результаты обработки запроса.
    
    Args:
        request_id: Идентификатор запроса
        limit: Максимальное количество результатов
        offset: Смещение для пагинации
        batch_service: Сервис batch обработки
        
    Returns:
        Объект с результатами обработки
    """
    try:
        logger.debug(f"Getting processing results for request {request_id}")
        
        # Получаем результаты
        results = await batch_service.get_processing_results(
            request_id,
            limit=limit,
            offset=offset
        )
        
        # Проверяем, найден ли запрос
        if not results:
            # Проверяем прогресс, чтобы убедиться, что запрос существует
            progress = await batch_service.get_processing_progress(request_id)
            if progress.total == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Request {request_id} not found"
                )
        
        # Получаем общую статистику
        progress = await batch_service.get_processing_progress(request_id)
        
        # Создаем сводку по статусам
        summary = {
            "pending": progress.pending,
            "completed": progress.completed,
            "failed": progress.failed,
            "total": progress.total
        }
        
        response = ProcessingResultsResponse(
            request_id=request_id,
            total_materials=progress.total,
            results=results,
            summary=summary
        )
        
        logger.debug(f"Retrieved {len(results)} results for request {request_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing results for {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting processing results"
        )


@router.get(
    "/process-enhanced/statistics",
    response_model=ProcessingStatistics,
    summary="Получить статистику обработки",
    description="Возвращает общую статистику сервиса batch обработки",
    responses={
        200: {
            "description": "Статистика обработки",
            "model": ProcessingStatistics
        }
    }
)
async def get_processing_statistics(
    batch_service = Depends(get_batch_processing_service)
) -> ProcessingStatistics:
    """
    Получить статистику сервиса batch обработки.
    
    Args:
        batch_service: Сервис batch обработки
        
    Returns:
        Объект со статистикой
    """
    try:
        logger.debug("Getting processing statistics")
        
        # Получаем статистику из БД
        stats = await batch_service.get_service_statistics()
        
        logger.debug(f"Processing statistics: {stats.total_requests} requests, {stats.success_rate:.2%} success rate")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting processing statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting statistics"
        )


@router.post(
    "/process-enhanced/retry",
    summary="Повторить обработку неуспешных материалов",
    description="Запускает повторную обработку материалов со статусом failed",
    responses={
        200: {
            "description": "Количество материалов для повторной обработки"
        }
    }
)
async def retry_failed_materials(
    batch_service = Depends(get_batch_processing_service)
) -> Dict[str, Any]:
    """
    Повторить обработку неуспешных материалов.
    
    Args:
        batch_service: Сервис batch обработки
        
    Returns:
        Информация о повторной обработке
    """
    try:
        logger.info("Starting retry of failed materials")
        
        # Запускаем retry
        retry_count = await batch_service.retry_failed_materials()
        
        logger.info(f"Retry started for {retry_count} materials")
        return {
            "message": f"Retry started for {retry_count} materials",
            "retry_count": retry_count
        }
        
    except Exception as e:
        logger.error(f"Error retrying failed materials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during retry"
        )


@router.delete(
    "/process-enhanced/cleanup",
    summary="Очистить старые записи обработки",
    description="Удаляет старые записи обработки для освобождения места",
    responses={
        200: {
            "description": "Количество удаленных записей"
        }
    }
)
async def cleanup_old_records(
    days_old: int = 30,
    batch_service = Depends(get_batch_processing_service)
) -> Dict[str, Any]:
    """
    Очистить старые записи обработки.
    
    Args:
        days_old: Количество дней для удаления
        batch_service: Сервис batch обработки
        
    Returns:
        Информация об очистке
    """
    try:
        logger.info(f"Starting cleanup of records older than {days_old} days")
        
        # Запускаем очистку
        deleted_count = await batch_service.cleanup_old_records(days_old)
        
        logger.info(f"Cleanup completed: {deleted_count} records deleted")
        return {
            "message": f"Cleanup completed: {deleted_count} records deleted",
            "deleted_count": deleted_count,
            "days_old": days_old
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during cleanup"
        )


# Health check endpoint
@router.get(
    "/process-enhanced/health",
    summary="Проверить состояние сервиса",
    description="Возвращает состояние сервиса batch обработки",
    responses={
        200: {
            "description": "Состояние сервиса"
        }
    }
)
async def get_service_health(
    batch_service = Depends(get_batch_processing_service)
) -> Dict[str, Any]:
    """
    Проверить состояние сервиса batch обработки.
    
    Args:
        batch_service: Сервис batch обработки
        
    Returns:
        Информация о состоянии сервиса
    """
    try:
        # Получаем статистику сервиса
        service_stats = batch_service.get_service_stats()
        
        # Проверяем состояние
        health_status = "healthy"
        if service_stats['active_jobs'] >= service_stats['config']['max_concurrent_batches']:
            health_status = "overloaded"
        elif service_stats['failed_jobs'] > service_stats['completed_jobs']:
            health_status = "degraded"
        
        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "service_stats": service_stats,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting service health: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        } 