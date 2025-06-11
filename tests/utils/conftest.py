"""
Конфигурация pytest для тестов утилит
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Добавляем корневую папку проекта в PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всей сессии тестирования"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env_vars():
    """Фикстура для мокирования переменных окружения"""
    original_env = os.environ.copy()
    
    # Устанавливаем тестовые значения
    test_env = {
        'OPENAI_API_KEY': 'test-openai-key',
        'QDRANT_URL': 'http://localhost:6333',
        'QDRANT_API_KEY': 'test-qdrant-key'
    }
    os.environ.update(test_env)
    
    yield test_env
    
    # Восстанавливаем оригинальные переменные
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def temp_materials_data():
    """Фикстура с тестовыми данными материалов"""
    return [
        {
            "article": "TEST001",
            "name": "Тестовый цемент М400",
            "use_category": "Цемент",
            "unit": "кг",
            "description": None
        },
        {
            "article": "TEST002", 
            "name": "Тестовый песок речной",
            "use_category": "Песок",
            "unit": "м³",
            "description": None
        },
        {
            "article": "TEST003",
            "name": "Тестовый кирпич красный",
            "use_category": "Кирпич", 
            "unit": "шт",
            "description": None
        }
    ]


@pytest.fixture
def sample_search_results():
    """Фикстура с образцами результатов поиска"""
    return [
        {
            "id": "material-1",
            "score": 0.95,
            "payload": {
                "name": "Цемент портландский М500",
                "article": "CEM001",
                "use_category": "Цемент",
                "unit": "кг"
            }
        },
        {
            "id": "material-2", 
            "score": 0.87,
            "payload": {
                "name": "Песок строительный мытый",
                "article": "SND001",
                "use_category": "Песок",
                "unit": "м³"
            }
        }
    ]


def pytest_configure(config):
    """Конфигурация pytest маркеров"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require running services)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "api: marks tests that require API server"
    )


def pytest_collection_modifyitems(config, items):
    """Модифицирует собранные тесты, добавляя маркеры"""
    # Маркируем интеграционные тесты
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Маркируем асинхронные тесты как потенциально медленные
        if hasattr(item.function, '_pytestfixturefunction'):
            continue
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.slow)


@pytest.fixture
def skip_if_no_api():
    """Пропускает тест если API недоступен"""
    def _skip_if_no_api():
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code != 200:
                pytest.skip("API server not available")
        except Exception:
            pytest.skip("API server not available")
    return _skip_if_no_api


@pytest.fixture
def skip_if_no_qdrant():
    """Пропускает тест если Qdrant недоступен"""
    def _skip_if_no_qdrant():
        try:
            import requests
            response = requests.get("http://localhost:6333", timeout=2)
            if response.status_code != 200:
                pytest.skip("Qdrant server not available")
        except Exception:
            pytest.skip("Qdrant server not available")
    return _skip_if_no_qdrant 