#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурационный файл pytest с фикстурами для тестирования модуля temp_enrichment
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock


@pytest.fixture
def temp_cache_file():
    """Создает временный файл кеша для тестов"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        cache_file = f.name
    yield cache_file
    if os.path.exists(cache_file):
        os.unlink(cache_file)


@pytest.fixture
def sample_products() -> List[Dict]:
    """Фикстура с образцами товаров для тестирования"""
    return [
        {"name": "Цемент М-400 50кг", "price": 300.0, "unit": "мешок"},
        {"name": "OSB-3 2500x1250x12 мм", "price": 919.0, "unit": "лист"},
        {"name": "Кирпич полнотелый М-150 (250x120x65)", "price": 13.0, "unit": "шт"},
        {"name": "Рубероид РКП-300 1x15 м", "price": 367.0, "unit": "рулон"},
        {"name": "Пена монтажная PROFFLEX 850мл", "price": 384.0, "unit": "баллон"},
        {"name": "Газобетон 600x300x200", "price": 185.0, "unit": "блок"},
        {"name": "Плитка керамическая", "price": 1200.0, "unit": "м2"},
        {"name": "Краска акриловая 2.5 л", "price": 850.0, "unit": "банка"},
        {"name": "Неизвестный товар", "price": 100.0, "unit": "шт"}
    ]


@pytest.fixture
def test_materials_data():
    """Фикстура с тестовыми данными из файла test_materials_image.json"""
    test_data_path = Path(__file__).parent / "test_materials_image.json"
    if test_data_path.exists():
        with open(test_data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


@pytest.fixture
def mock_openai_response():
    """Фикстура для мокирования ответов OpenAI API"""
    def _create_mock_response(content: str, tokens: int = 50):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = content
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = tokens
        return mock_response
    return _create_mock_response


@pytest.fixture
def regex_test_cases():
    """Фикстура с тестовыми случаями для regex парсера"""
    return [
        # Прямые объемы
        {
            "name": "Керамзитобетон 5 м³",
            "price": 15000.0,
            "unit": "м³",
            "expected": {
                "metric_unit": "м3",
                "quantity": 5.0,
                "parsing_method": "direct_volume"
            }
        },
        {
            "name": "Краска 2.5 л",
            "price": 850.0,
            "unit": "банка",
            "expected": {
                "metric_unit": "л",
                "quantity": 2.5,
                "parsing_method": "direct_volume_liters"
            }
        },
        # Прямые площади
        {
            "name": "Линолеум 15 м²",
            "price": 2250.0,
            "unit": "рулон",
            "expected": {
                "metric_unit": "м2",
                "quantity": 15.0,
                "parsing_method": "direct_area"
            }
        },
        # Прямые веса
        {
            "name": "Цемент 50кг",
            "price": 300.0,
            "unit": "меш",
            "expected": {
                "metric_unit": "кг",
                "quantity": 50.0,
                "parsing_method": "direct_weight_kg"
            }
        },
        # Площади из размеров
        {
            "name": "OSB-3 2500x1250x12 мм",
            "price": 919.0,
            "unit": "лист",
            "expected": {
                "metric_unit": "м2",
                "quantity": 3.125,
                "parsing_method": "sheet_area_dimensions"
            }
        },
        # Объемы из размеров
        {
            "name": "Газобетон 600x300x200 мм",
            "price": 185.0,
            "unit": "блок",
            "expected": {
                "metric_unit": "м3",
                "quantity": 0.036,
                "parsing_method": "volume_dimensions"
            }
        },
        # Случаи без парсинга
        {
            "name": "Неизвестный товар",
            "price": 100.0,
            "unit": "шт",
            "expected": {
                "metric_unit": None,
                "quantity": None,
                "parsing_method": "no_parsing"
            }
        }
    ]


@pytest.fixture
def ai_test_cases():
    """Фикстура с тестовыми случаями для AI парсера"""
    return [
        {
            "name": "Кирпич полнотелый М-150 (250x120x65)",
            "price": 13.0,
            "unit": "шт",
            "mock_response": '{"metric_unit": "м3", "price_coefficient": 0.00195}',
            "expected": {
                "metric_unit": "м3",
                "price_coefficient": 0.00195,
                "confidence": 0.85
            }
        },
        {
            "name": "Пена монтажная PROFFLEX 850мл",
            "price": 384.0,
            "unit": "баллон",
            "mock_response": '{"metric_unit": "л", "price_coefficient": 0.85}',
            "expected": {
                "metric_unit": "л",
                "price_coefficient": 0.85,
                "confidence": 0.85
            }
        }
    ]


@pytest.fixture
def edge_cases():
    """Фикстура с граничными случаями для тестирования"""
    return [
        {"name": "", "price": 0.0, "unit": ""},
        {"name": "Товар без цены", "price": 0.0, "unit": "шт"},
        {"name": "Товар с очень длинным названием " * 10, "price": 100.0, "unit": "шт"},
        {"name": "Товар с спецсимволами !@#$%^&*()", "price": 50.0, "unit": "шт"}
    ]


@pytest.fixture(scope="session")
def setup_test_env():
    """Настройка тестового окружения"""
    # Устанавливаем переменные окружения для тестов
    test_api_key = "test_api_key_12345"
    os.environ.setdefault('OPENAI_API_KEY', test_api_key)
    yield
    # Очистка после тестов не требуется


@pytest.fixture
def temporary_files():
    """Фикстура для создания временных файлов"""
    created_files = []
    
    def create_temp_file(content: str = "", suffix: str = ".json"):
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            temp_file = f.name
        created_files.append(temp_file)
        return temp_file
    
    yield create_temp_file
    
    # Cleanup
    for file_path in created_files:
        if os.path.exists(file_path):
            os.unlink(file_path) 