"""
Pydantic models for batch processing API.
Этап 8.1: Модели для асинхронной batch обработки материалов.
"""

from datetime import datetime
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ProcessingStatus(str, Enum):
    """Статус обработки материала или запроса."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MaterialInput(BaseModel):
    """Входные данные для обработки одного материала."""
    id: str = Field(..., description="Уникальный идентификатор материала")
    name: str = Field(..., min_length=1, max_length=500, description="Название материала")
    unit: str = Field(..., min_length=1, max_length=100, description="Единица измерения")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "mat_001",
                "name": "Кирпич керамический белый",
                "unit": "шт"
            }
        }


class BatchMaterialsRequest(BaseModel):
    """Запрос на batch обработку материалов."""
    request_id: str = Field(..., description="Уникальный идентификатор запроса")
    materials: List[MaterialInput] = Field(..., min_items=1, max_items=10000, description="Список материалов для обработки")
    
    @validator('materials')
    def validate_materials_unique_ids(cls, v):
        """Проверить уникальность ID материалов."""
        ids = [material.id for material in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Все ID материалов должны быть уникальными")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "req_12345",
                "materials": [
                    {"id": "mat_001", "name": "Кирпич керамический", "unit": "шт"},
                    {"id": "mat_002", "name": "Цемент М400", "unit": "кг"}
                ]
            }
        }


class BatchProcessingResponse(BaseModel):
    """Ответ на запрос batch обработки."""
    status: str = Field(..., description="Статус принятия запроса")
    request_id: str = Field(..., description="Идентификатор запроса")
    materials_count: int = Field(..., description="Количество материалов к обработке")
    estimated_completion: Optional[datetime] = Field(None, description="Предполагаемое время завершения")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "accepted",
                "request_id": "req_12345",
                "materials_count": 150,
                "estimated_completion": "2025-01-25T15:30:00Z"
            }
        }


class BatchValidationError(BaseModel):
    """Ошибка валидации batch запроса."""
    status: str = Field("validation_error", description="Статус ошибки")
    errors: List[str] = Field(..., description="Список ошибок валидации")
    rejected_materials: List[str] = Field(..., description="Список ID отклоненных материалов")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "validation_error",
                "errors": ["Material name is required", "Unit must be valid"],
                "rejected_materials": ["mat_003", "mat_004"]
            }
        }


class ProcessingProgress(BaseModel):
    """Прогресс обработки запроса."""
    total: int = Field(..., description="Общее количество материалов")
    completed: int = Field(..., description="Количество завершенных")
    failed: int = Field(..., description="Количество неудачных")
    pending: int = Field(..., description="Количество ожидающих обработки")
    
    class Config:
        schema_extra = {
            "example": {
                "total": 150,
                "completed": 120,
                "failed": 5,
                "pending": 25
            }
        }


class ProcessingStatusResponse(BaseModel):
    """Ответ на запрос статуса обработки."""
    request_id: str = Field(..., description="Идентификатор запроса")
    status: ProcessingStatus = Field(..., description="Общий статус обработки")
    progress: ProcessingProgress = Field(..., description="Детальный прогресс")
    estimated_completion: Optional[datetime] = Field(None, description="Предполагаемое время завершения")
    started_at: Optional[datetime] = Field(None, description="Время начала обработки")
    completed_at: Optional[datetime] = Field(None, description="Время завершения обработки")
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "req_12345",
                "status": "processing",
                "progress": {
                    "total": 150,
                    "completed": 120,
                    "failed": 5,
                    "pending": 25
                },
                "estimated_completion": "2025-01-25T15:30:00Z"
            }
        }


class MaterialProcessingResult(BaseModel):
    """Результат обработки одного материала."""
    material_id: str = Field(..., description="Идентификатор материала")
    original_name: str = Field(..., description="Исходное название")
    original_unit: str = Field(..., description="Исходная единица")
    sku: Optional[str] = Field(None, description="Найденный SKU или null")
    similarity_score: Optional[float] = Field(None, description="Коэффициент сходства")
    processing_status: ProcessingStatus = Field(..., description="Статус обработки")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    processed_at: Optional[datetime] = Field(None, description="Время обработки")
    
    # Дополнительные поля для анализа
    normalized_color: Optional[str] = Field(None, description="Нормализованный цвет")
    normalized_unit: Optional[str] = Field(None, description="Нормализованная единица")
    unit_coefficient: Optional[float] = Field(None, description="Коэффициент единицы")
    
    class Config:
        schema_extra = {
            "example": {
                "material_id": "mat_001",
                "original_name": "Кирпич керамический белый",
                "original_unit": "шт",
                "sku": "SKU_12345",
                "similarity_score": 0.85,
                "processing_status": "completed",
                "error_message": None,
                "processed_at": "2025-01-25T15:25:00Z"
            }
        }


class ProcessingResultsResponse(BaseModel):
    """Ответ с детальными результатами обработки."""
    request_id: str = Field(..., description="Идентификатор запроса")
    total_materials: int = Field(..., description="Общее количество материалов")
    results: List[MaterialProcessingResult] = Field(..., description="Результаты обработки")
    summary: Dict[str, int] = Field(..., description="Сводка по статусам")
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "req_12345",
                "total_materials": 2,
                "results": [
                    {
                        "material_id": "mat_001",
                        "sku": "SKU_12345",
                        "similarity_score": 0.85,
                        "processing_status": "completed"
                    },
                    {
                        "material_id": "mat_002",
                        "sku": None,
                        "similarity_score": 0.45,
                        "processing_status": "completed"
                    }
                ],
                "summary": {
                    "completed": 2,
                    "failed": 0,
                    "pending": 0
                }
            }
        }


class ProcessingJobConfig(BaseModel):
    """Конфигурация задачи обработки."""
    max_materials_per_request: int = Field(10000, description="Максимум материалов в запросе")
    batch_processing_size: int = Field(50, description="Размер одного batch для обработки")
    max_concurrent_batches: int = Field(5, description="Максимум параллельных batch'ей")
    request_timeout: int = Field(30, description="Timeout для API response (секунды)")
    processing_timeout: int = Field(3600, description="Timeout для background processing (секунды)")
    similarity_threshold: float = Field(0.70, description="Порог сходства для поиска SKU")
    max_retries: int = Field(3, description="Максимум попыток повторной обработки")
    retry_delay: int = Field(60, description="Задержка между попытками (секунды)")
    
    class Config:
        schema_extra = {
            "example": {
                "max_materials_per_request": 10000,
                "batch_processing_size": 50,
                "max_concurrent_batches": 5,
                "similarity_threshold": 0.70
            }
        }


class ProcessingStatistics(BaseModel):
    """Статистика обработки для мониторинга."""
    total_requests: int = Field(..., description="Общее количество запросов")
    active_requests: int = Field(..., description="Активные запросы")
    completed_requests: int = Field(..., description="Завершенные запросы")
    failed_requests: int = Field(..., description="Неудачные запросы")
    total_materials_processed: int = Field(..., description="Общее количество обработанных материалов")
    average_processing_time: float = Field(..., description="Среднее время обработки (секунды)")
    success_rate: float = Field(..., description="Процент успешности")
    
    class Config:
        schema_extra = {
            "example": {
                "total_requests": 25,
                "active_requests": 3,
                "completed_requests": 20,
                "failed_requests": 2,
                "total_materials_processed": 1250,
                "average_processing_time": 45.5,
                "success_rate": 0.92
            }
        }


# Union типы для API responses
BatchResponse = Union[BatchProcessingResponse, BatchValidationError] 