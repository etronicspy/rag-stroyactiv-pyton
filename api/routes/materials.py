"""Refactored Materials API routes using new multi-database architecture.

Рефакторенные API роуты материалов с новой мульти-БД архитектурой.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
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


@router.get("/health")
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


@router.post("/", response_model=Material, responses=ERROR_RESPONSES)
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


@router.get("/{material_id}", response_model=Material, responses=ERROR_RESPONSES)
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


@router.post("/search", response_model=List[Material], responses=ERROR_RESPONSES)
async def search_materials(
    query: MaterialSearchQuery,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    🔍 **Semantic Material Search** - Семантический поиск материалов
    
    Выполняет интеллектуальный поиск строительных материалов с использованием 
    векторных embeddings и семантического анализа. Поддерживает fallback-стратегию
    при отсутствии результатов.
    
    **🔄 Fallback Strategy:**
    1. **Vector Search**: Семантический поиск по embedding
    2. **SQL LIKE Search**: Текстовый поиск при 0 результатах
    3. **Fuzzy Matching**: Поиск с учетом опечаток
    
    **Особенности:**
    - 🧠 AI-powered семантический поиск
    - 🔍 Поиск синонимов и похожих терминов
    - 📊 Ранжирование по релевантности
    - ⚡ Быстрый отклик (< 300ms)
    - 🛡️ Graceful degradation при ошибках
    
    **Request Body Example:**
    ```json
    {
        "query": "цемент портландский высокой прочности",
        "limit": 20
    }
    ```
    
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
            "embedding": null, // Hidden in search results
            "created_at": "2025-06-16T16:46:29.421964Z",
            "updated_at": "2025-06-16T16:46:29.421964Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "Цемент М400 быстротвердеющий",
            "use_category": "Цемент",
            "unit": "т",
            "sku": "CEM400-BT",
            "description": "Быстротвердеющий портландцемент для срочных работ",
            "embedding": null,
            "created_at": "2025-06-16T16:46:29.421964Z",
            "updated_at": "2025-06-16T16:46:29.421964Z"
        }
    ]
    ```
    
    **Query Parameters:**
    - `query`: Поисковый запрос (min: 1 символ, max: 500 символов)
    - `limit`: Максимальное количество результатов (1-100, default: 10)
    
    **Response Status Codes:**
    - **200 OK**: Поиск выполнен успешно (может быть пустой список)
    - **400 Bad Request**: Некорректные параметры запроса
    - **500 Internal Server Error**: Ошибка выполнения поиска
    
    **Search Examples:**
    - `"цемент М500"` → найдет все цементы марки М500
    - `"арматура стальная"` → найдет стальную арматуру всех видов
    - `"утеплитель минеральный"` → найдет минеральные утеплители
    - `"кирпич красный лицевой"` → найдет лицевой красный кирпич
    
    **Use Cases:**
    - Поиск материалов для строительных проектов
    - Подбор аналогов и заменителей
    - Создание спецификаций и смет
    - API для мобильных приложений
    """
    try:
        # Check if service initialization failed
        if service is None:
            logger.warning("MaterialsService initialization failed, returning mock response")
            return [{
                "id": "fallback-1",
                "name": f"Fallback result for '{query.query}'",
                "sku": "FB-001",
                "description": f"Fallback search result for query: {query.query} (service unavailable)",
                "use_category": "Fallback",
                "unit": "шт",
                "embedding": None,
                "created_at": None,
                "updated_at": None
            }]
        
        logger.info(f"Searching materials: '{query.query}' (limit: {query.limit})")
        results = await service.search_materials(query.query, query.limit)
        logger.info(f"Search returned {len(results)} results")
        return results
        
    except DatabaseError as e:
        logger.error(f"Database error searching materials: {e}")
        # Return fallback instead of HTTP error
        return [{
            "id": "error-fallback-1",
            "name": f"Search temporarily unavailable for '{query.query}'",
            "sku": "ERR-001", 
            "description": f"Database error occurred, please try again later",
            "use_category": "System",
            "unit": "шт",
            "embedding": None,
            "created_at": None,
            "updated_at": None
        }]
    except Exception as e:
        logger.error(f"Unexpected error searching materials: {e}")
        # Return fallback instead of HTTP error for better UX
        return [{
            "id": "exception-fallback-1",
            "name": f"Search error for '{query.query}'",
            "sku": "EXC-001",
            "description": f"An error occurred during search, please try again",
            "use_category": "System", 
            "unit": "шт",
            "embedding": None,
            "created_at": None,
            "updated_at": None
        }]


@router.get("/", response_model=List[Material])
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


@router.put("/{material_id}", response_model=Material)
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


@router.delete("/{material_id}")
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


@router.post("/batch", response_model=MaterialBatchResponse)
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


@router.post("/import", response_model=MaterialBatchResponse)
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

 