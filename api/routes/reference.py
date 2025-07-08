from typing import List
from fastapi import APIRouter, Depends
from core.schemas.materials import Category, Unit
from core.schemas.colors import ColorReference, ColorCreate
from services.materials import CategoryService, UnitService, ColorService
from core.database.interfaces import IVectorDatabase
from core.dependencies.database import get_vector_db_dependency, get_ai_client_dependency
from core.schemas.response_models import ERROR_RESPONSES

router = APIRouter(responses=ERROR_RESPONSES)

def get_category_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency)
) -> CategoryService:
    """Get CategoryService with dependency injection."""
    return CategoryService(vector_db=vector_db)

def get_unit_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency)
) -> UnitService:
    """Get UnitService with dependency injection."""
    return UnitService(vector_db=vector_db)

def get_color_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency),
    ai_client = Depends(get_ai_client_dependency)
) -> ColorService:
    """Get ColorService with dependency injection."""
    return ColorService(vector_db=vector_db, ai_client=ai_client)

@router.post(
    "/categories/",
    response_model=Category,
    summary="🏷️ Create Category – Создание категории",
    response_description="Созданная категория",
    status_code=201
)
async def create_category(
    category: Category,
    service: CategoryService = Depends(get_category_service)
):
    """
    🏷️ **Create Category** - Создание новой категории материалов
    
    Создает новую категорию использования материалов для классификации и фильтрации.
    Категории помогают организовать материалы по функциональному назначению.
    
    **Особенности:**
    - 🆔 Автогенерация UUID для категории
    - 🔍 Индексация для быстрого поиска
    - ⏰ Автоматические временные метки
    - 📝 Валидация уникальности названия
    - 🗄️ Сохранение в векторную БД
    
    **Required Fields:**
    - `name`: Название категории (уникальное)
    
    **Optional Fields:**
    - `description`: Описание категории
    
    **Request Body Example:**
    ```json
    {
        "name": "Цемент",
        "description": "Вяжущие материалы на основе портландцемента для создания бетонных смесей"
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Цемент",
        "description": "Вяжущие материалы на основе портландцемента для создания бетонных смесей",
        "created_at": "2025-06-16T17:30:15.123456Z",
        "updated_at": "2025-06-16T17:30:15.123456Z"
    }
    ```
    
    **Response Status Codes:**
    - **201 Created**: Категория успешно создана
    - **400 Bad Request**: Ошибка валидации (дубликат названия)
    - **500 Internal Server Error**: Ошибка сохранения в БД
    
    **Common Categories:**
    - Цемент, Кирпич, Арматура, Бетон, Песок, Щебень
    - Утеплители, Гидроизоляция, Металлопрокат
    - Лакокрасочные материалы, Сухие смеси
    
    **Use Cases:**
    - Создание системы классификации материалов
    - Настройка фильтров для поиска
    - Организация каталога продукции
    - Стандартизация номенклатуры
    """
    return await service.create_category(category.name, category.description)

@router.get(
    "/categories/",
    response_model=List[Category],
    summary="📋 List Categories – Список категорий",
    response_description="Список категорий материалов"
)
async def get_categories(
    service: CategoryService = Depends(get_category_service)
):
    """
    📋 **List Categories** - Получение всех категорий материалов
    
    Возвращает полный список всех доступных категорий материалов в системе.
    Используется для создания выпадающих списков и фильтров в интерфейсах.
    
    **Особенности:**
    - 📊 Полный список без пагинации
    - ⚡ Быстрая загрузка (кэшируется)
    - 🔤 Сортировка по алфавиту
    - 📈 Счетчики использования
    - 🎯 Готово к использованию в UI
    
    **Response Example:**
    ```json
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Арматура",
            "description": "Стальные стержни для армирования железобетонных конструкций",
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "Кирпич",
            "description": "Керамические и силикатные изделия для кладки стен",
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "name": "Цемент",
            "description": "Вяжущие материалы на основе портландцемента",
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        }
    ]
    ```
    
    **Response Status Codes:**
    - **200 OK**: Список возвращен успешно (может быть пустым)
    - **500 Internal Server Error**: Ошибка получения данных
    
    **Use Cases:**
    - Создание выпадающих списков в формах
    - Фильтрация материалов по категориям
    - Административные интерфейсы
    - API для мобильных приложений
    - Синхронизация с внешними системами
    """
    return await service.get_categories()

@router.delete(
    "/categories/{category_id}",
    summary="🗑️ Delete Category – Удаление категории",
    response_description="Результат удаления категории",
    responses={
        200: {"description": "Категория успешно удалена"},
        404: {"description": "Категория не найдена"},
        400: {"description": "Некорректный UUID"}
    }
)
async def delete_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service)
):
    """
    🗑️ **Delete Category** - Удаление категории материалов
    
    Удаляет категорию из системы. Операция необратимая, требует осторожности.
    
    **⚠️ ВНИМАНИЕ:** Убедитесь, что категория не используется материалами!
    
    **Особенности:**
    - 🔥 Полное удаление из векторной БД
    - ⚠️ Проверка зависимостей не выполняется
    - ⚡ Мгновенное выполнение
    - 📊 Обновление индексов
    
    **Path Parameters:**
    - `category_id`: UUID категории для удаления
    
    **Response Example:**
    ```json
    {
        "success": true,
        "message": "Category deleted successfully",
        "deleted_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Категория успешно удалена
    - **404 Not Found**: Категория с указанным ID не найдена
    - **400 Bad Request**: Некорректный формат UUID
    - **500 Internal Server Error**: Ошибка удаления
    
    **⚠️ Рекомендации:**
    - Проверьте использование категории в материалах
    - Создайте резервную копию перед удалением
    - Рассмотрите архивацию вместо удаления
    
    **Use Cases:**
    - Удаление устаревших категорий
    - Очистка тестовых данных
    - Реорганизация системы классификации
    """
    success = await service.delete_category(category_id)
    return {"success": success}

@router.post(
    "/units/",
    response_model=Unit,
    summary="📏 Create Unit – Создание единицы измерения",
    response_description="Созданная единица измерения",
    status_code=201
)
async def create_unit(
    unit: Unit,
    service: UnitService = Depends(get_unit_service)
):
    """
    📏 **Create Unit** - Создание новой единицы измерения
    
    Создает новую единицу измерения для материалов. Единицы измерения используются
    для точного указания количества и объемов строительных материалов.
    
    **Особенности:**
    - 🆔 Автогенерация UUID для единицы
    - 📝 Валидация уникальности названия
    - 🔍 Индексация для быстрого поиска
    - ⏰ Автоматические временные метки
    - 🗄️ Сохранение в векторную БД
    
    **Required Fields:**
    - `name`: Название единицы измерения (уникальное)
    
    **Optional Fields:**
    - `description`: Описание единицы измерения
    
    **Request Body Example:**
    ```json
    {
        "name": "м³",
        "description": "Кубический метр - единица измерения объема сыпучих материалов"
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "м³",
        "description": "Кубический метр - единица измерения объема сыпучих материалов",
        "created_at": "2025-06-16T17:30:15.123456Z",
        "updated_at": "2025-06-16T17:30:15.123456Z"
    }
    ```
    
    **Response Status Codes:**
    - **201 Created**: Единица измерения успешно создана
    - **400 Bad Request**: Ошибка валидации (дубликат названия)
    - **500 Internal Server Error**: Ошибка сохранения в БД
    
    **Common Units:**
    - **Объем**: м³, л, дм³
    - **Масса**: кг, т, г
    - **Площадь**: м², см², мм²
    - **Длина**: м, см, мм
    - **Штучные**: шт, упак, мешок, паллета
    - **Специальные**: п.м. (погонный метр), м.п. (метр погонный)
    
    **Use Cases:**
    - Стандартизация единиц измерения
    - Создание выпадающих списков в формах
    - Расчет количества материалов
    - Формирование смет и спецификаций
    """
    return await service.create_unit(unit.name, unit.description)

@router.get(
    "/units/",
    response_model=List[Unit],
    summary="📐 List Units – Список единиц измерения",
    response_description="Список единиц измерения"
)
async def get_units(
    service: UnitService = Depends(get_unit_service)
):
    """
    📋 **List Units** - Получение всех единиц измерения
    
    Возвращает полный список всех доступных единиц измерения в системе.
    Используется для создания выпадающих списков и валидации данных.
    
    **Особенности:**
    - 📊 Полный список без пагинации
    - ⚡ Быстрая загрузка (кэшируется)
    - 🔤 Сортировка по популярности
    - 📈 Готово к использованию в UI
    - 🌐 Поддержка международных стандартов
    
    **Response Example:**
    ```json
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "кг",
            "description": "Килограмм - единица измерения массы",
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "м³",
            "description": "Кубический метр - единица измерения объема",
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "name": "шт",
            "description": "Штука - единица измерения штучных изделий",
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        }
    ]
    ```
    
    **Response Status Codes:**
    - **200 OK**: Список возвращен успешно (может быть пустым)
    - **500 Internal Server Error**: Ошибка получения данных
    
    **Unit Categories:**
    - **Объем**: м³, л, дм³
    - **Масса**: кг, т, г  
    - **Площадь**: м², см²
    - **Длина**: м, см, мм
    - **Количество**: шт, упак, мешок
    
    **Use Cases:**
    - Создание выпадающих списков в формах
    - Валидация единиц измерения
    - Расчеты в сметах и спецификациях
    - API для мобильных приложений
    - Интеграция с ERP системами
    """
    return await service.get_units()

@router.delete(
    "/units/{unit_id}",
    summary="🗑️ Delete Unit – Удаление единицы измерения",
    response_description="Результат удаления единицы",
    responses={
        200: {"description": "Единица измерения успешно удалена"},
        404: {"description": "Единица измерения не найдена"},
        400: {"description": "Некорректный UUID"}
    }
)
async def delete_unit(
    unit_id: str,
    service: UnitService = Depends(get_unit_service)
):
    """
    🗑️ **Delete Unit** - Удаление единицы измерения
    
    Удаляет единицу измерения из системы. Операция необратимая, требует осторожности.
    
    **⚠️ ВНИМАНИЕ:** Убедитесь, что единица не используется материалами!
    
    **Особенности:**
    - 🔥 Полное удаление из векторной БД
    - ⚠️ Проверка зависимостей не выполняется
    - ⚡ Мгновенное выполнение
    - 📊 Обновление индексов
    
    **Path Parameters:**
    - `unit_id`: UUID единицы измерения для удаления
    
    **Response Example:**
    ```json
    {
        "success": true,
        "message": "Unit deleted successfully", 
        "deleted_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Единица измерения успешно удалена
    - **404 Not Found**: Единица с указанным ID не найдена
    - **400 Bad Request**: Некорректный формат UUID
    - **500 Internal Server Error**: Ошибка удаления
    
    **⚠️ Рекомендации:**
    - Проверьте использование единицы в материалах
    - Создайте резервную копию перед удалением
    - Рассмотрите архивацию вместо удаления
    - Используйте стандартные единицы СИ
    
    **Use Cases:**
    - Удаление устаревших единиц измерения
    - Очистка тестовых данных
    - Стандартизация системы измерений
    - Исправление ошибок ввода
    """
    success = await service.delete_unit(unit_id)
    return {"success": success}

@router.post(
    "/colors/",
    response_model=ColorReference,
    summary="🎨 Create Color – Создание цвета",
    response_description="Созданный цвет",
    status_code=201
)
async def create_color(
    color: ColorCreate,
    service: ColorService = Depends(get_color_service)
):
    """
    🎨 **Create Color** - Создание нового справочного цвета
    
    Создает новый цвет в справочнике для классификации материалов.
    Цвета используются для визуального поиска и фильтрации стройматериалов.
    
    **Особенности:**
    - 🆔 Автогенерация UUID для цвета
    - 🤖 Генерация AI embedding для семантического поиска
    - 🌈 Поддержка HEX и RGB форматов
    - 🏷️ Система синонимов для точного поиска
    - ⏰ Автоматические временные метки
    - 🗄️ Сохранение в векторную БД
    
    **Required Fields:**
    - `name`: Название цвета на русском языке
    
    **Optional Fields:**
    - `hex_code`: HEX код цвета (например, "#FFFFFF")
    - `rgb_values`: RGB значения [R, G, B] (0-255)
    - `aliases`: Синонимы и альтернативные названия
    
    **Request Body Example:**
    ```json
    {
        "name": "белый",
        "hex_code": "#FFFFFF",
        "rgb_values": [255, 255, 255],
        "aliases": ["светлый", "молочный", "снежный", "кремовый"]
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "белый",
        "hex_code": "#FFFFFF",
        "rgb_values": [255, 255, 255],
        "aliases": ["светлый", "молочный", "снежный", "кремовый"],
        "embedding": [0.1, 0.2, 0.3, "...", "(1536 dimensions)"],
        "created_at": "2025-06-16T17:30:15.123456Z",
        "updated_at": "2025-06-16T17:30:15.123456Z"
    }
    ```
    
    **Response Status Codes:**
    - **201 Created**: Цвет успешно создан
    - **400 Bad Request**: Ошибка валидации (некорректный HEX/RGB)
    - **500 Internal Server Error**: Ошибка сохранения в БД
    
    **Common Colors:**
    - **Базовые**: белый, черный, серый, коричневый
    - **Основные**: красный, синий, зеленый, желтый
    - **Природные**: бежевый, песочный, терракотовый, охра
    - **Металлики**: серебристый, золотистый, медный
    - **Специальные**: прозрачный, матовый, глянцевый
    
    **Use Cases:**
    - Создание цветового справочника материалов
    - Фильтрация по цветам в каталогах
    - Визуальный поиск стройматериалов
    - Стандартизация цветовой номенклатуры
    - RAG нормализация цветовых описаний
    """
    return await service.create_color(color)

@router.get(
    "/colors/",
    response_model=List[ColorReference],
    summary="🌈 List Colors – Список цветов",
    response_description="Список цветов материалов"
)
async def get_colors(
    service: ColorService = Depends(get_color_service)
):
    """
    🌈 **List Colors** - Получение всех цветов из справочника
    
    Возвращает полный список всех доступных цветов в системе.
    Используется для создания цветовых палитр и фильтров в интерфейсах.
    
    **Особенности:**
    - 🎨 Полный список цветов с embeddings
    - 🌈 Поддержка HEX и RGB форматов
    - 🏷️ Синонимы для каждого цвета
    - ⚡ Быстрая загрузка (кэшируется)
    - 🔤 Сортировка по популярности
    - 📈 Готово к использованию в UI
    
    **Response Example:**
    ```json
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "белый",
            "hex_code": "#FFFFFF",
            "rgb_values": [255, 255, 255],
            "aliases": ["светлый", "молочный", "снежный"],
            "embedding": [0.1, 0.2, 0.3, "...", "(1536 dimensions)"],
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "красный",
            "hex_code": "#FF0000",
            "rgb_values": [255, 0, 0],
            "aliases": ["алый", "кирпичный", "багряный"],
            "embedding": [0.4, 0.5, 0.6, "...", "(1536 dimensions)"],
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        }
    ]
    ```
    
    **Response Status Codes:**
    - **200 OK**: Список возвращен успешно (может быть пустым)
    - **500 Internal Server Error**: Ошибка получения данных
    
    **Color Categories:**
    - **Нейтральные**: белый, черный, серый
    - **Теплые**: красный, оранжевый, желтый
    - **Холодные**: синий, зеленый, фиолетовый
    - **Природные**: коричневый, бежевый, терракотовый
    - **Металлические**: серебристый, золотистый, медный
    
    **Use Cases:**
    - Создание цветовых палитр в UI
    - Фильтрация материалов по цветам
    - RAG нормализация цветовых описаний
    - API для мобильных приложений
    - Интеграция с каталогами поставщиков
    """
    return await service.get_colors()

@router.delete(
    "/colors/{color_id}",
    summary="🗑️ Delete Color – Удаление цвета",
    response_description="Результат удаления цвета",
    responses={
        200: {"description": "Цвет успешно удален"},
        404: {"description": "Цвет не найден"},
        400: {"description": "Некорректный UUID"}
    }
)
async def delete_color(
    color_id: str,
    service: ColorService = Depends(get_color_service)
):
    """
    🗑️ **Delete Color** - Удаление цвета из справочника
    
    Удаляет цвет из системы. Операция необратимая, требует осторожности.
    
    **⚠️ ВНИМАНИЕ:** Убедитесь, что цвет не используется в материалах!
    
    **Особенности:**
    - 🔥 Полное удаление из векторной БД
    - ⚠️ Проверка зависимостей не выполняется
    - ⚡ Мгновенное выполнение
    - 📊 Обновление индексов
    - 🤖 Удаление AI embeddings
    
    **Path Parameters:**
    - `color_id`: UUID цвета для удаления
    
    **Response Example:**
    ```json
    {
        "success": true,
        "message": "Color deleted successfully",
        "deleted_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Цвет успешно удален
    - **404 Not Found**: Цвет с указанным ID не найден
    - **400 Bad Request**: Некорректный формат UUID
    - **500 Internal Server Error**: Ошибка удаления
    
    **⚠️ Рекомендации:**
    - Проверьте использование цвета в материалах
    - Создайте резервную копию перед удалением
    - Рассмотрите архивацию вместо удаления
    - Используйте стандартные цвета из палитры
    
    **Use Cases:**
    - Удаление устаревших цветов
    - Очистка тестовых данных
    - Стандартизация цветовой палитры
    - Исправление ошибок ввода
    - Реорганизация справочника цветов
    """
    success = await service.delete_color(color_id)
    return {"success": success}

 