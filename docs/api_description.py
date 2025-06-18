"""
API description and metadata for FastAPI application.

Centralized API documentation to reduce main.py size and improve maintainability.
"""

from typing import List, Dict, Any


def get_api_description() -> str:
    """
    Get comprehensive API description for FastAPI documentation.
    
    Returns:
        API description string with Markdown formatting
    """
    return """
    🏗️ **RAG Construction Materials API** - Система управления и семантического поиска строительных материалов

    ## 🚀 Возможности API

    ### 🔍 **Интеллектуальный поиск**
    - **Семантический поиск** с AI-эмбеддингами (OpenAI)
    - **Гибридный поиск** (векторный + SQL + нечеткий)
    - **Автодополнение** и предложения
    - **Фильтрация** по категориям и единицам измерения

    ### 📦 **Управление материалами**
    - CRUD операции с материалами
    - **Пакетная загрузка** и импорт из JSON
    - **Автоматическая векторизация** описаний
    - **Категоризация** и стандартизация единиц

    ### 💰 **Обработка прайс-листов**
    - **Загрузка CSV/Excel** прайс-листов
    - **Автоматическая обработка** и индексация
    - **Трекинг** статуса обработки продуктов
    - **Управление** несколькими поставщиками

    ### 🏥 **Мониторинг и диагностика**
    - **Полная диагностика** всех систем
    - **Статус баз данных** (Qdrant, PostgreSQL, Redis)
    - **Мониторинг пулов** подключений
    - **SSH туннель** для PostgreSQL

    ### 🔧 **Техническая архитектура**
    - **Multi-database**: Qdrant Cloud + PostgreSQL + Redis
    - **Fallback стратегия** при недоступности БД  
    - **Rate limiting** и безопасность
    - **Автоматическое масштабирование** пулов подключений

    ## 📚 **Документация**
    - **Interactive Docs**: `/docs` (Swagger UI)
    - **ReDoc**: `/redoc` 
    - **OpenAPI Schema**: `/openapi.json`

    ## 🎯 **Версионирование**
    - Текущая версия: **v1**
    - Базовый путь: `/api/v1/`
    - Стабильный API без устаревших эндпоинтов

    ---
    **Разработано с ❤️ для эффективного управления строительными материалами**
    """


def get_contact_info() -> Dict[str, str]:
    """
    Get API contact information.
    
    Returns:
        Contact information dictionary
    """
    return {
        "name": "RAG Construction Materials API",
        "url": "https://github.com/your-repo/rag-construction-materials",
    }


def get_license_info() -> Dict[str, str]:
    """
    Get API license information.
    
    Returns:
        License information dictionary
    """
    return {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }


def get_servers_config() -> List[Dict[str, str]]:
    """
    Get API servers configuration.
    
    Returns:
        List of server configurations
    """
    return [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.construction-materials.com",
            "description": "Production server"
        }
    ]


def get_tags_metadata() -> List[Dict[str, str]]:
    """
    Get API tags metadata for documentation.
    
    Returns:
        List of tag metadata dictionaries
    """
    return [
        {
            "name": "health",
            "description": "🏥 **Health & Monitoring** - Проверка состояния системы, диагностика баз данных и мониторинг"
        },
        {
            "name": "materials",
            "description": "📦 **Materials Management** - CRUD операции с материалами, пакетная загрузка, импорт и векторизация"
        },
        {
            "name": "search",
            "description": "🔍 **Search & Discovery** - Семантический поиск, автодополнение, фильтрация по категориям"
        },
        {
            "name": "prices",
            "description": "💰 **Price Lists** - Загрузка и обработка прайс-листов, управление поставщиками"
        },
        {
            "name": "reference",
            "description": "📚 **Reference Data** - Управление справочниками категорий и единиц измерения"
        },
        {
            "name": "tunnel",
            "description": "🔌 **SSH Tunnel** - Управление SSH туннелем для безопасного подключения к PostgreSQL"
        }
    ]


def get_fastapi_config(settings) -> Dict[str, Any]:
    """
    Get complete FastAPI configuration.
    
    Args:
        settings: Application settings
        
    Returns:
        FastAPI configuration dictionary
    """
    return {
        "title": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": get_api_description(),
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "contact": get_contact_info(),
        "license_info": get_license_info(),
        "servers": get_servers_config(),
        "tags_metadata": get_tags_metadata()
    } 