"""Refactored Materials API routes using new multi-database architecture.

Рефакторенные API роуты материалов с новой мульти-БД архитектурой.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from datetime import datetime

from core.logging import get_logger
from core.schemas.materials import (
    MaterialCreate, MaterialUpdate, Material, MaterialSearchQuery, 
    MaterialBatchCreate, MaterialBatchResponse, MaterialImportRequest
)
from core.schemas.response_models import ERROR_RESPONSES
from core.database.interfaces import IVectorDatabase
from core.dependencies.database import get_vector_db_dependency, get_ai_client_dependency
from core.database.exceptions import DatabaseError
from services.materials import MaterialsService


logger = get_logger(__name__)
router = APIRouter(responses=ERROR_RESPONSES)


def get_materials_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency),
    ai_client = Depends(get_ai_client_dependency)
) -> MaterialsService:
    """Get MaterialsService with dependency injection (Qdrant-only mode).
    
    Args:
        vector_db: Vector database client (injected)
        ai_client: AI client for embeddings (injected)
        
    Returns:
        Configured MaterialsService instance
    """
    try:
        return MaterialsService(vector_db=vector_db, ai_client=ai_client)
    except Exception as e:
        logger.error(f"Failed to initialize MaterialsService: {e}")
        # For now, return None to trigger fallback behavior
        return None


@router.get(
    "/health",
    summary="Materials Health – Статус сервиса материалов",
    response_description="Информация о состоянии сервиса материалов"
)
async def health_check(
    service: MaterialsService = Depends(get_materials_service)
):
    """
    🔍 **Materials Service Health Check** - Проверка работы сервиса материалов
    
    Проверяет состояние сервиса материалов и подключения к векторной базе данных.
    Работает в режиме Qdrant-only для семантического поиска стройматериалов.
    
    **Особенности:**
    - 🗄️ Проверка Qdrant подключения
    - 📋 Список доступных endpoints
    - ⚡ Быстрая диагностика сервиса
    - 🎯 Статус инициализации
    
    **Response Status Codes:**
    - **200 OK**: Сервис работает нормально
    - **206 Partial Content**: Сервис работает с ограничениями
    - **503 Service Unavailable**: Сервис недоступен
    
    **Example Response:**
    ```json
    {
        "status": "healthy",
        "service": "MaterialsService",
        "mode": "qdrant-only",
        "service_status": "operational",
        "vector_database": {
            "status": "healthy",
            "database_type": "Qdrant",
            "collections_count": 3,
            "total_vectors": 15420,
            "response_time_ms": 156.3
        },
        "available_endpoints": {
            "search": "POST /api/v1/materials/search",
            "batch": "POST /api/v1/materials/batch",
            "import": "POST /api/v1/materials/import",
            "list": "GET /api/v1/materials/",
            "get_by_id": "GET /api/v1/materials/{id}",
            "create": "POST /api/v1/materials/",
            "update": "PUT /api/v1/materials/{id}",
            "delete": "DELETE /api/v1/materials/{id}"
        }
    }
    ```
    
    **Use Cases:**
    - Проверка работы сервиса материалов
    - Диагностика векторной БД
    - Мониторинг доступности endpoints
    """
    health_status = {
        "status": "healthy",
        "service": "MaterialsService",
        "mode": "qdrant-only",
        "available_endpoints": {
            "search": "POST /api/v1/materials/search",
            "batch": "POST /api/v1/materials/batch", 
            "import": "POST /api/v1/materials/import",
            "list": "GET /api/v1/materials/",
            "get_by_id": "GET /api/v1/materials/{id}",
            "create": "POST /api/v1/materials/",
            "update": "PUT /api/v1/materials/{id}",
            "delete": "DELETE /api/v1/materials/{id}"
        }
    }
    
    # Try to check service health
    if service is None:
        health_status.update({
            "status": "degraded",
            "service_status": "initialization_failed",
            "message": "MaterialsService failed to initialize, running in fallback mode"
        })
    else:
        try:
            # Try to check vector database health
            vector_health = await service.vector_db.health_check()
            health_status.update({
                "vector_database": vector_health,
                "service_status": "operational"
            })
        except Exception as e:
            health_status.update({
                "status": "degraded",
                "service_status": "vector_db_error",
                "vector_db_error": str(e),
                "message": "Vector database connection issues detected"
            })
    
    return health_status


@router.post(
    "/",
    response_model=Material,
    responses=ERROR_RESPONSES,
    summary="➕ Create Material – Создание материала",
    response_description="Созданный материал"
)
async def create_material(
    material: MaterialCreate,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    ➕ **Create Material** - Создание нового строительного материала
    
    Создает новый материал с автоматической генерацией семантического embedding
    для поиска. Материал сохраняется в векторную БД для последующего поиска.
    
    **Особенности:**
    - 🧠 Автогенерация 1536-мерного embedding (OpenAI)
    - 🔍 Индексация для семантического поиска
    - ✨ Автоматическое создание UUID
    - 📝 Валидация обязательных полей
    - ⏰ Автоматические временные метки
    
    **Required Fields:**
    - `name`: Название материала (2-200 символов)
    - `use_category`: Категория использования
    - `unit`: Единица измерения
    
    **Optional Fields:**
    - `sku`: Артикул/код материала (3-50 символов)
    - `description`: Описание материала
    
    **Request Body Example:**
    ```json
    {
        "name": "Портландцемент М500 Д0",
        "use_category": "Цемент",
        "unit": "мешок",
        "sku": "CEM500-001",
        "description": "Высокопрочный цемент для конструкционного бетона без минеральных добавок"
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Портландцемент М500 Д0",
        "use_category": "Цемент",
        "unit": "мешок",
        "sku": "CEM500-001",
        "description": "Высокопрочный цемент для конструкционного бетона без минеральных добавок",
        "embedding": [0.023, -0.156, 0.789, ...], // 1536 dimensions
        "created_at": "2025-06-16T16:46:29.421964Z",
        "updated_at": "2025-06-16T16:46:29.421964Z"
    }
    ```
    
    **Response Status Codes:**
    - **201 Created**: Материал успешно создан
    - **400 Bad Request**: Ошибка валидации данных
    - **500 Internal Server Error**: Ошибка создания embedding или БД
    
    **Use Cases:**
    - Добавление новых материалов в каталог
    - Импорт данных из прайс-листов
    - Создание справочников материалов
    """
    try:
        logger.info(f"Creating material: {material.name}")
        result = await service.create_material(material)
        logger.info(f"Material created successfully: {result.id}")
        return result
    except DatabaseError as e:
        logger.error(f"Database error creating material: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error creating material: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/{material_id}",
    response_model=Material,
    responses=ERROR_RESPONSES,
    summary="🔍 Get Material – Получение материала по ID",
    response_description="Данные материала"
)
async def get_material(
    material_id: str,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    🔍 **Get Material by ID** - Получение материала по идентификатору
    
    Возвращает полную информацию о материале включая embedding для анализа.
    Поиск выполняется по UUID в векторной базе данных.
    
    **Path Parameters:**
    - `material_id`: UUID материала в формате UUID4
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Портландцемент М500 Д0",
        "use_category": "Цемент",
        "unit": "мешок",
        "sku": "CEM500-001",
        "description": "Высокопрочный цемент для конструкционного бетона",
        "embedding": [0.023, -0.156, 0.789, ...], // 1536 dimensions
        "created_at": "2025-06-16T16:46:29.421964Z",
        "updated_at": "2025-06-16T16:46:29.421964Z"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Материал найден и возвращен
    - **404 Not Found**: Материал с указанным ID не найден
    - **400 Bad Request**: Некорректный формат UUID
    - **500 Internal Server Error**: Ошибка работы с БД
    
    **Use Cases:**
    - Получение полной информации о материале
    - Анализ embedding для отладки поиска
    - Проверка существования материала
    """
    try:
        logger.debug(f"Getting material: {material_id}")
        material = await service.get_material(material_id)
        if not material:
            logger.warning(f"Material not found: {material_id}")
            raise HTTPException(status_code=404, detail="Material not found")
        return material
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except DatabaseError as e:
        logger.error(f"Database error getting material: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error getting material: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 🛈 Deprecated: material-level search endpoint removed. See unified search router.


@router.get(
    "/",
    response_model=List[Material],
    summary="📋 List Materials – Список материалов",
    response_description="Список материалов с поддержкой фильтрации"
)
async def get_materials(
    skip: int = 0, 
    limit: int = 10, 
    category: Optional[str] = None,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    📋 **List Materials** - Получение списка материалов с пагинацией
    
    Возвращает список всех материалов с поддержкой пагинации и фильтрации.
    Полезно для создания каталогов и административных интерфейсов.
    
    **Query Parameters:**
    - `skip`: Количество записей для пропуска (offset) - default: 0
    - `limit`: Максимальное количество записей - default: 10, max: 100
    - `category`: Фильтр по категории использования (опционально)
    
    **Response Example:**
    ```json
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Портландцемент М500 Д0",
            "use_category": "Цемент",
            "unit": "мешок",
            "sku": "CEM500-001",
            "description": "Высокопрочный цемент для конструкционного бетона",
            "embedding": null, // Hidden in list view
            "created_at": "2025-06-16T16:46:29.421964Z",
            "updated_at": "2025-06-16T16:46:29.421964Z"
        }
    ]
    ```
    
    **Response Status Codes:**
    - **200 OK**: Список возвращен успешно (может быть пустым)
    - **400 Bad Request**: Некорректные параметры пагинации
    - **500 Internal Server Error**: Ошибка получения данных
    
    **Pagination Examples:**
    - `GET /materials/?limit=20` → первые 20 материалов
    - `GET /materials/?skip=20&limit=20` → материалы 21-40
    - `GET /materials/?category=Цемент&limit=50` → цементы (до 50 шт.)
    
    **Use Cases:**
    - Отображение каталога материалов
    - Административные интерфейсы
    - Экспорт данных
    - Создание отчетов
    """
    try:
        logger.debug(f"Getting materials: skip={skip}, limit={limit}, category={category}")
        results = await service.get_materials(skip=skip, limit=limit, category=category)
        logger.info(f"Retrieved {len(results)} materials")
        return results
    except DatabaseError as e:
        logger.error(f"Database error getting materials: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error getting materials: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put(
    "/{material_id}",
    response_model=Material,
    summary="✏️ Update Material – Обновление материала",
    response_description="Обновлённый материал"
)
async def update_material(
    material_id: str,
    material: MaterialUpdate,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    ✏️ **Update Material** - Обновление существующего материала
    
    Обновляет данные материала с пересчетом семантического embedding при изменении
    критических полей (name, description). Поддерживает частичное обновление.
    
    **Особенности:**
    - 🔄 Пересчет embedding при изменении ключевых полей
    - 📝 Частичное обновление (только указанные поля)
    - ⏰ Автоматическое обновление updated_at
    - ✅ Валидация измененных данных
    - 🔍 Проверка существования материала
    
    **Path Parameters:**
    - `material_id`: UUID материала для обновления
    
    **Updateable Fields:**
    - `name`: Название материала (триггерирует пересчет embedding)
    - `use_category`: Категория использования 
    - `unit`: Единица измерения
    - `sku`: Артикул/код материала
    - `description`: Описание (триггерирует пересчет embedding)
    
    **Request Body Example:**
    ```json
    {
        "name": "Портландцемент М500 Д0 (улучшенный)",
        "description": "Высокопрочный цемент для конструкционного бетона с улучшенными характеристиками",
        "sku": "CEM500-001-V2"
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Портландцемент М500 Д0 (улучшенный)",
        "use_category": "Цемент",
        "unit": "мешок",
        "sku": "CEM500-001-V2",
        "description": "Высокопрочный цемент для конструкционного бетона с улучшенными характеристиками",
        "embedding": [0.021, -0.134, 0.756, ...], // Updated embedding
        "created_at": "2025-06-16T16:46:29.421964Z",
        "updated_at": "2025-06-16T17:30:15.123456Z" // Updated timestamp
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Материал успешно обновлен
    - **404 Not Found**: Материал с указанным ID не найден
    - **400 Bad Request**: Ошибка валидации данных
    - **500 Internal Server Error**: Ошибка обновления или пересчета embedding
    
    **Use Cases:**
    - Исправление данных материалов
    - Обновление технических характеристик
    - Изменение категоризации
    - Актуализация артикулов
    """
    try:
        logger.info(f"Updating material: {material_id}")
        result = await service.update_material(material_id, material)
        if not result:
            logger.warning(f"Material not found for update: {material_id}")
            raise HTTPException(status_code=404, detail="Material not found")
        logger.info(f"Material updated successfully: {material_id}")
        return result
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except DatabaseError as e:
        logger.error(f"Database error updating material: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error updating material: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/{material_id}",
    summary="🗑️ Delete Material – Удаление материала",
    response_description="Результат удаления"
)
async def delete_material(
    material_id: str,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    🗑️ **Delete Material** - Удаление материала
    
    Удаляет материал из векторной базы данных по UUID. Операция необратимая,
    восстановление возможно только из резервных копий.
    
    **⚠️ ВНИМАНИЕ: Операция необратимая!**
    
    **Особенности:**
    - 🔥 Полное удаление из векторной БД
    - 🔍 Проверка существования перед удалением
    - 📊 Обновление индексов поиска
    - ⚡ Быстрое выполнение
    - 🛡️ Защита от случайного удаления
    
    **Path Parameters:**
    - `material_id`: UUID материала для удаления
    
    **Response Example:**
    ```json
    {
        "success": true,
        "message": "Material deleted successfully",
        "deleted_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2025-06-16T17:30:15.123456Z"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Материал успешно удален
    - **404 Not Found**: Материал с указанным ID не найден
    - **400 Bad Request**: Некорректный формат UUID
    - **500 Internal Server Error**: Ошибка удаления из БД
    
    **Use Cases:**
    - Удаление устаревших материалов
    - Очистка тестовых данных
    - Удаление дубликатов
    - Архивация неактуальных записей
    
    **⚠️ Рекомендации:**
    - Создавайте резервные копии перед массовым удалением
    - Проверяйте зависимости в связанных системах
    - Используйте batch операции для множественного удаления
    """
    try:
        logger.info(f"Deleting material: {material_id}")
        success = await service.delete_material(material_id)
        if not success:
            logger.warning(f"Material not found for deletion: {material_id}")
            raise HTTPException(status_code=404, detail="Material not found")
        logger.info(f"Material deleted successfully: {material_id}")
        return {
            "success": True,
            "message": "Material deleted successfully",
            "deleted_id": material_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except DatabaseError as e:
        logger.error(f"Database error deleting material: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error deleting material: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/batch",
    response_model=MaterialBatchResponse,
    summary="📦 Batch Create Materials – Массовое создание материалов",
    response_description="Результаты пакетного создания материалов"
)
async def create_materials_batch(
    batch_data: MaterialBatchCreate,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    📦 **Batch Create Materials** - Массовое создание материалов
    
    Создает множество материалов за один запрос с оптимизированной обработкой.
    Поддерживает частичный успех - часть материалов может быть создана успешно.
    
    **Особенности:**
    - ⚡ Параллельная обработка embedding'ов
    - 📊 Статистика успешных/неудачных операций
    - 🔄 Batch обработка в векторной БД
    - 🛡️ Graceful handling ошибок
    - 📈 Прогресс трекинг
    
    **Лимиты:**
    - **Минимум**: 1 материал
    - **Максимум**: 1000 материалов за запрос
    - **Batch size**: 100 материалов (настраивается)
    - **Timeout**: 5 минут на весь запрос
    
    **Request Body Example:**
    ```json
    {
        "materials": [
            {
                "name": "Портландцемент М500",
                "use_category": "Цемент",
                "unit": "мешок",
                "sku": "CEM500-001",
                "description": "Высокопрочный цемент"
            },
            {
                "name": "Кирпич керамический",
                "use_category": "Кирпич",
                "unit": "шт",
                "sku": "BRICK-001",
                "description": "Полнотелый кирпич"
            }
        ],
        "batch_size": 100
    }
    ```
    
    **Response Example:**
    ```json
    {
        "success": true,
        "total_processed": 2,
        "successful_materials": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Портландцемент М500",
                "use_category": "Цемент",
                "unit": "мешок",
                "sku": "CEM500-001",
                "description": "Высокопрочный цемент",
                "embedding": [...],
                "created_at": "2025-06-16T17:30:15.123456Z",
                "updated_at": "2025-06-16T17:30:15.123456Z"
            }
        ],
        "failed_materials": [
            {
                "index": 1,
                "material": {...},
                "error": "Duplicate SKU: BRICK-001"
            }
        ],
        "processing_time_seconds": 45.6,
        "successful_count": 1,
        "failed_count": 1,
        "success_rate": 50.0,
        "errors": []
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Batch обработан (проверьте success_rate)
    - **400 Bad Request**: Некорректные данные batch
    - **413 Payload Too Large**: Превышен лимит материалов
    - **500 Internal Server Error**: Критическая ошибка обработки
    
    **Use Cases:**
    - Импорт каталогов материалов
    - Миграция данных между системами
    - Массовое создание тестовых данных
    - Синхронизация с ERP системами
    """
    try:
        logger.info(f"Processing batch create: {len(batch_data.materials)} materials")
        result = await service.create_materials_batch(batch_data.materials, batch_data.batch_size)
        logger.info(f"Batch create completed: {result.successful_count}/{result.total_processed} successful")
        return result
    except ValueError as e:
        logger.error(f"Invalid batch data: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid batch data: {str(e)}")
    except DatabaseError as e:
        logger.error(f"Database error in batch create: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error in batch create: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/import",
    response_model=MaterialBatchResponse,
    summary="📥 Import Materials – Импорт материалов из JSON/CSV",
    response_description="Результат импорта материалов"
)
async def import_materials_from_json(
    import_data: MaterialImportRequest,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    📥 **Import Materials from JSON** - Импорт материалов из JSON файла
    
    Импортирует материалы из структурированного JSON формата с автоматическим
    заполнением значений по умолчанию. Оптимизирован для импорта прайс-листов.
    
    **Особенности:**
    - 📄 Упрощенный формат импорта (только SKU + name)
    - 🔧 Автоматические значения по умолчанию
    - 📊 Детальная статистика импорта
    - 🛡️ Валидация и дедупликация
    - ⚡ Оптимизированная обработка
    
    **Automatic Defaults:**
    - `use_category`: "Стройматериалы" (настраивается)
    - `unit`: "шт" (настраивается)
    - `description`: Генерируется из name
    - `embedding`: Автоматический расчет
    
    **Request Body Example:**
    ```json
    {
        "materials": [
            {
                "sku": "CEM500-001",
                "name": "Портландцемент М500 Д0"
            },
            {
                "sku": "BRICK-001", 
                "name": "Кирпич керамический полнотелый"
            }
        ],
        "default_use_category": "Строительные материалы",
        "default_unit": "единица",
        "batch_size": 100
    }
    ```
    
    **Response Example:**
    ```json
    {
        "success": true,
        "total_processed": 2,
        "successful_materials": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Портландцемент М500 Д0",
                "use_category": "Строительные материалы",
                "unit": "единица",
                "sku": "CEM500-001",
                "description": "Портландцемент М500 Д0",
                "embedding": [...],
                "created_at": "2025-06-16T17:30:15.123456Z",
                "updated_at": "2025-06-16T17:30:15.123456Z"
            }
        ],
        "failed_materials": [],
        "processing_time_seconds": 32.1,
        "successful_count": 2,
        "failed_count": 0,
        "success_rate": 100.0,
        "errors": []
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Импорт завершен (проверьте success_rate)
    - **400 Bad Request**: Некорректный формат данных
    - **413 Payload Too Large**: Превышен лимит импорта
    - **500 Internal Server Error**: Ошибка обработки импорта
    
    **Supported Formats:**
    - Simple JSON с минимальными полями
    - Bulk import от поставщиков
    - Export/Import между системами
    - Прайс-листы в JSON формате
    
    **Use Cases:**
    - Импорт прайс-листов поставщиков
    - Миграция из старых систем
    - Загрузка каталогов материалов
    - Синхронизация с внешними API
    """
    try:
        logger.info(f"Importing materials from JSON: {len(import_data.materials)} items")
        
        # Convert import format to standard MaterialCreate format
        materials = []
        for item in import_data.materials:
            material = MaterialCreate(
                name=item.name,
                use_category=import_data.default_use_category,
                unit=import_data.default_unit,
                sku=item.sku,
                description=item.name  # Use name as description by default
            )
            materials.append(material)
        
        result = await service.create_materials_batch(materials, import_data.batch_size)
        logger.info(f"JSON import completed: {result.successful_count}/{result.total_processed} successful")
        return result
        
    except ValueError as e:
        logger.error(f"Invalid import data: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid import data: {str(e)}")
    except DatabaseError as e:
        logger.error(f"Database error in import: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error in import: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/upload",
    response_model=MaterialBatchResponse,
    summary="📤 Upload Materials – File-based Material Upload",
    response_description="File processing and material upload results"
)
async def upload_materials(
    file: UploadFile = File(..., description="CSV/Excel file with materials"),
):
    """
    📤 **Upload Materials** - Bulk material upload from file
    
    Uploads and processes files containing construction material data. Supports
    CSV and Excel formats with automatic structure detection and data validation.
    
    **Supported Formats:**
    - 📊 **CSV**: Delimiters (,;|), encodings (UTF-8, Windows-1251)
    - 📋 **Excel**: .xlsx, .xls files with multiple sheets
    - 🔍 **Auto-detection**: Automatic format and structure detection
    
    **Required Fields:**
    - `name`: Material name (1-500 characters)
    - `description`: Material description (optional)
    - `use_category`: Usage category
    - `unit`: Measurement unit
    - `sku`: Stock keeping unit (optional, unique)
    
    **Processing Features:**
    - 🧠 AI-powered data analysis and enrichment
    - 🔍 Automatic category and unit detection
    - 📊 Data validation and cleaning
    - ⚡ Batch processing for large files
    - 🔄 Deduplication by name and SKU
    - 📈 Embedding generation for search
     
    **Request Example:**
    ```bash
    curl -X POST -F "file=@materials.csv" http://localhost:8000/api/v1/materials/upload
    ```
    
    **Response Status Codes:**
    - **200 OK**: File processed successfully (may have warnings)
    - **400 Bad Request**: Unsupported format or empty file
    - **413 Request Entity Too Large**: File size exceeded (50MB)
    - **422 Unprocessable Entity**: Data validation errors
    - **500 Internal Server Error**: File processing error
    
    **File Requirements:**
    - **Size**: Maximum 50MB
    - **Encoding**: UTF-8 (recommended), Windows-1251
    - **Structure**: First row contains column headers
    - **Data**: Minimum 1 data row required
    
    **Processing Statistics:**
    - `total_processed`: Total number of processed records
    - `successful`: Successfully uploaded materials
    - `failed`: Number of errors
    - `duplicates`: Found duplicates
    - `enriched`: AI-enriched records
    
    **Use Cases:**
    - Supplier catalog import
    - Data migration from other systems
    - Bulk material updates
    - ERP system synchronization
    - Initial database population
    """

@router.get(
    "",
    response_model=List[Material],
    summary="📋 List Materials – Complete Materials Catalog",
    response_description="Complete materials list with pagination and filtering"
)
async def list_materials(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    category: Optional[str] = Query(None, description="Filter by material category"),
    unit: Optional[str] = Query(None, description="Filter by measurement unit"),
):
    """
    📋 **List Materials** - Retrieve complete materials catalog with filtering
    
    Returns complete construction materials catalog with filtering capabilities
    by categories, measurement units, and result pagination.
    
    **Features:**
    - 📄 Pagination for large catalogs (default: 100 records)
    - 🔍 Filtering by categories and measurement units
    - 📊 Complete information for each material
    - ⚡ Optimized database queries
    - 🔄 Caching for frequently requested data
    
    **Query Parameters:**
    - `skip`: Number of records to skip (pagination)
    - `limit`: Maximum number of records (1-1000)
    - `category`: Filter by material category
    - `unit`: Filter by measurement unit
    
    **Response Example:**
    ```json
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Portland Cement PC 500-D0",
            "use_category": "Cement",
            "unit": "kg",
            "sku": "CEM-PC500-001",
            "description": "Portland cement without mineral additives",
            "embedding": null,
            "created_at": "2025-06-16T16:46:29.421964Z",
            "updated_at": "2025-06-16T16:46:29.421964Z"
        }
    ]
    ```
    
    **Response Status Codes:**
    - **200 OK**: Materials list returned successfully
    - **400 Bad Request**: Invalid filtering parameters
    - **500 Internal Server Error**: Data retrieval error
    
    **Filtering Examples:**
    - `/materials?category=Cement` - cement materials only
    - `/materials?unit=kg&limit=50` - materials in kilograms, 50 records
    - `/materials?skip=100&limit=50` - records 101-150
    
    **Performance Notes:**
    - Pagination recommended for large catalogs
    - Filtering performed at database level
    - Results cached for repeated requests
    
    **Use Cases:**
    - Complete materials catalog browsing
    - Creating dropdown lists in UI
    - Data export for analysis
    - External system synchronization
    - Materials reporting
    """

@router.get(
    "/{material_id}",
    response_model=Material,
    summary="🔍 Get Material – Retrieve Material by ID",
    response_description="Detailed information about specific material"
)
async def get_material(material_id: str):
    """
    🔍 **Get Material by ID** - Retrieve detailed material information
    
    Returns complete information about specific construction material by its
    unique identifier.
    
    **Features:**
    - 📊 Complete material information
    - 🔍 Search by UUID or SKU
    - ⚡ Fast access via indexed fields
    - 🔄 Caching for frequently requested materials
    
    **Path Parameters:**
    - `material_id`: Material UUID or SKU
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Portland Cement PC 500-D0",
        "use_category": "Cement",
        "unit": "kg",
        "sku": "CEM-PC500-001",
        "description": "Portland cement without mineral additives grade 500",
        "embedding": null,
        "created_at": "2025-06-16T16:46:29.421964Z",
        "updated_at": "2025-06-16T16:46:29.421964Z"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Material found and returned
    - **404 Not Found**: Material with specified ID not found
    - **400 Bad Request**: Invalid ID format
    - **500 Internal Server Error**: Data retrieval error
    
    **ID Formats:**
    - **UUID**: `550e8400-e29b-41d4-a716-446655440000`
    - **SKU**: `CEM-PC500-001` (if unique)
    
    **Use Cases:**
    - Material details display in interface
    - Material existence verification
    - Data retrieval for editing
    - API integration with external systems
    - Material validation in orders
    """

@router.put(
    "/{material_id}",
    response_model=Material,
    summary="✏️ Update Material – Material Update Operation",
    response_description="Updated material information"
)
async def update_material(
    material_id: str,
    material_data: MaterialCreate
):
    """
    ✏️ **Update Material** - Material information update
    
    Updates existing construction material data. Supports partial and complete
    updates with data validation.
    
    **Features:**
    - 📝 Partial and complete updates
    - 🔍 SKU uniqueness validation
    - 🧠 AI-enrichment of updated data
    - 📈 Automatic embedding updates
    - 📊 Change logging
    - 🔄 Automatic timestamp updates
    
    **Request Body Example:**
    ```json
    {
        "name": "Portland Cement PC 500-D0 Premium",
        "description": "High-quality Portland cement without additives",
        "use_category": "Cement",
        "unit": "kg",
        "sku": "CEM-PC500-PREM-001"
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Portland Cement PC 500-D0 Premium",
        "use_category": "Cement",
        "unit": "kg",
        "sku": "CEM-PC500-PREM-001",
        "description": "High-quality Portland cement without additives",
        "embedding": null,
        "created_at": "2025-06-16T16:46:29.421964Z",
        "updated_at": "2025-06-16T18:15:42.123456Z"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Material successfully updated
    - **404 Not Found**: Material with specified ID not found
    - **400 Bad Request**: Invalid data or duplicate SKU
    - **422 Unprocessable Entity**: Data validation errors
    - **500 Internal Server Error**: Update error
    
    **Validation Rules:**
    - `name`: 1-500 characters, required field
    - `sku`: Unique if specified
    - `use_category`: Must exist in reference catalog
    - `unit`: Must exist in reference catalog
    
    **Automatic Processing:**
    - New embedding generation when name/description changes
    - AI analysis and categorization of updated data
    - Related records and indexes update
    
    **Use Cases:**
    - Data error corrections
    - Description and characteristics updates
    - Material categorization changes
    - External catalog synchronization
    - Bulk updates via API
    """

@router.delete(
    "/{material_id}",
    summary="🗑️ Delete Material – Material Deletion Operation",
    response_description="Material deletion confirmation"
)
async def delete_material(material_id: str):
    """
    🗑️ **Delete Material** - Remove material from catalog
    
    Removes construction material from database. Operation is irreversible
    and requires confirmation for critical data.
    
    **Features:**
    - 🗑️ Permanent record deletion
    - 🔍 Related data verification before deletion
    - 📊 Deletion operation logging
    - 🧹 Related embeddings and indexes cleanup
    - ⚠️ Related records warnings
    
    **Response Example:**
    ```json
    {
        "message": "Material successfully deleted",
        "deleted_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Material successfully deleted
    - **404 Not Found**: Material with specified ID not found
    - **409 Conflict**: Material is used in other records
    - **500 Internal Server Error**: Deletion error
    
    **⚠️ Warnings:**
    - Operation is irreversible - recovery impossible
    - Check related data before deletion
    - Backup recommended before bulk deletion
    
    **Cleanup Operations:**
    - Vector embeddings removal from vector DB
    - Search indexes cleanup
    - Cached data removal
    - Catalog statistics update
    
    **Use Cases:**
    - Outdated materials removal
    - Duplicate records cleanup
    - Erroneously created materials removal
    - Bulk catalog cleanup
    - GDPR compliance requirements
    """

 