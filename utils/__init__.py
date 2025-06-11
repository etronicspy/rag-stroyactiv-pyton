"""
Оптимизированные утилиты для RAG системы строительных материалов

Этот модуль содержит оптимизированные утилиты для:
- Сопоставления материалов (material_matcher) с параллельной обработкой
- Кэширования эмбеддингов и векторных операций (common)
- Создания тестовых данных (create_test_data)
- Тестирования поиска на русском языке (test_russian_search)
- Тестирования всех сервисов (test_all_services)
- Управления коллекциями (cleanup_collections, view_collection)
- Проверки подключения к БД (check_db_connection)

Ключевые улучшения:
- Кэширование эмбеддингов с TTL
- Параллельная обработка запросов
- Батчевые операции с векторной БД
- Оптимизированные утилитные функции
"""

__all__ = []

# Безопасные импорты основных утилит
try:
    from .material_matcher import MaterialMatcher, MaterialMatch
    __all__.extend(['MaterialMatcher', 'MaterialMatch'])
except ImportError:
    pass

try:
    from .common import (
        embedding_service,
        qdrant_service,
        vector_cache,
        calculate_cosine_similarity,
        calculate_cosine_similarity_batch,
        format_confidence,
        format_price,
        truncate_text,
        generate_unique_id,
        parallel_processing
    )
    __all__.extend([
        'embedding_service',
        'qdrant_service', 
        'vector_cache',
        'calculate_cosine_similarity',
        'calculate_cosine_similarity_batch',
        'format_confidence',
        'format_price',
        'truncate_text',
        'generate_unique_id',
        'parallel_processing'
    ])
except ImportError:
    pass

try:
    from .create_test_data import (
        create_categories, 
        create_units, 
        create_materials
    )
    __all__.extend([
        'create_categories',
        'create_units', 
        'create_materials'
    ])
except ImportError:
    pass

# Безопасные импорты тестовых утилит
try:
    from .test_russian_search import test_russian_search
    __all__.append('test_russian_search')
except ImportError:
    pass

try:
    from .test_all_services import test_all_services
    __all__.append('test_all_services')
except ImportError:
    pass

try:
    from .check_db_connection import check_connection
    __all__.append('check_connection')
except ImportError:
    pass

# Безопасные импорты утилит управления коллекциями
try:
    from .cleanup_collections import cleanup_all_collections
    __all__.append('cleanup_all_collections')
except ImportError:
    pass

try:
    from .view_collection import view_collection
    __all__.append('view_collection')
except ImportError:
    pass

# Безопасные импорты утилит загрузки данных
try:
    from .load_materials import MaterialsLoader
    __all__.append('MaterialsLoader')
except ImportError:
    pass

# Безопасные импорты утилит анализа данных
try:
    from .load_building_materials import load_materials
    __all__.append('load_materials')
except ImportError:
    pass

try:
    from .check_loaded_materials import check_materials
    __all__.append('check_materials')
except ImportError:
    pass

# Безопасный импорт менеджера утилит
try:
    from .run_utility import main as run_utility_manager
    __all__.append('run_utility_manager')
except ImportError:
    pass

# Безопасный импорт утилит просмотра прайсов
try:
    from .show_supplier_prices import show_supplier_prices
    __all__.append('show_supplier_prices')
except ImportError:
    pass

# Безопасный импорт утилиты экспорта прайсов
try:
    from .export_supplier_prices import export_supplier_prices_to_csv
    __all__.append('export_supplier_prices_to_csv')
except ImportError:
    pass 