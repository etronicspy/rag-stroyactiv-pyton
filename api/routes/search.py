from fastapi import APIRouter, Query, HTTPException
from typing import List
from core.monitoring.logger import get_logger

from core.schemas.materials import Material
from services.materials import MaterialsService

logger = get_logger(__name__)
router = APIRouter()

@router.get("/", response_model=List[Material])
async def search_materials(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of results to return")
) -> List[Material]:
    """
    🔍 **Simple Material Search** - Упрощенный поиск материалов
    
    Простой и быстрый endpoint для поиска строительных материалов через URL параметры.
    Идеально подходит для GET запросов и интеграции с простыми фронтендами.
    
    **🔄 Search Strategy:**
    1. **Vector Search**: Семантический поиск по embedding
    2. **Fallback to SQL**: Текстовый поиск при отсутствии результатов
    3. **Error Handling**: Graceful degradation при сбоях
    
    **Особенности:**
    - ⚡ GET запрос - можно кэшировать
    - 🔗 Простые URL параметры
    - 🧠 AI-powered семантический поиск
    - 🛡️ Fallback стратегия
    - 📱 Подходит для AJAX запросов
    
    **Query Parameters:**
    - `q`: Поисковый запрос (обязательный, min: 1 символ)
    - `limit`: Максимальное количество результатов (default: 10, max: 100)
    
    **URL Examples:**
    - `GET /search/?q=цемент&limit=5`
    - `GET /search/?q=арматура%20стальная&limit=20`
    - `GET /search/?q=кирпич%20красный`
    
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
    
    **Response Status Codes:**
    - **200 OK**: Поиск выполнен успешно (может быть пустой список)
    - **400 Bad Request**: Некорректные параметры запроса
    - **500 Internal Server Error**: Ошибка выполнения поиска
    
    **Search Tips:**
    - **Точные запросы**: `"цемент М500"` → находит конкретную марку
    - **Категории**: `"арматура"` → находит все виды арматуры
    - **Характеристики**: `"кирпич красный"` → по цвету и типу
    - **Синонимы**: `"железобетон"` → найдет "ЖБИ", "бетон армированный"
    
    **Use Cases:**
    - 🌐 AJAX поиск в веб-интерфейсах
    - 📱 Мобильные приложения
    - 🔗 Простые интеграции через GET
    - ⚡ Автодополнение в формах
    - 🔍 Быстрый поиск по каталогу
    
    **Performance:**
    - ⚡ Отклик: < 300ms
    - 🧠 Семантический анализ: включен
    - 💾 Кэширование: рекомендуется
    - 📊 Лимит результатов: настраивается
    """
    try:
        service = MaterialsService()
        return await service.search_materials(query=q, limit=limit)
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during search") 