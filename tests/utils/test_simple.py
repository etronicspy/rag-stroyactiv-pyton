#!/usr/bin/env python3
"""
Простые тесты для утилит без зависимостей от внешних сервисов
"""

import pytest
import os
import tempfile
import json
from pathlib import Path


class TestBasicUtilities:
    """Базовые тесты утилит"""
    
    def test_pathlib_operations(self):
        """Тест базовых операций с путями"""
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {"test": "data"}
            json.dump(test_data, f)
            temp_file = f.name
        
        # Проверяем что файл существует
        assert os.path.exists(temp_file)
        
        # Проверяем Path операции
        path = Path(temp_file)
        assert path.exists()
        assert path.suffix == '.json'
        
        # Читаем данные
        with open(temp_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_data
        
        # Удаляем временный файл
        os.unlink(temp_file)
    
    def test_json_processing(self):
        """Тест обработки JSON данных"""
        materials_data = [
            {"article": "TEST001", "name": "Тестовый материал 1"},
            {"article": "TEST002", "name": "Тестовый материал 2"},
        ]
        
        # Проверяем структуру данных
        assert len(materials_data) == 2
        assert all('article' in item for item in materials_data)
        assert all('name' in item for item in materials_data)
        
        # Проверяем конкретные значения
        assert materials_data[0]['article'] == 'TEST001'
        assert materials_data[1]['name'] == 'Тестовый материал 2'
    
    def test_string_operations(self):
        """Тест строковых операций для обработки материалов"""
        material_names = [
            "Цемент М400",
            "Песок речной",
            "Кирпич красный керамический"
        ]
        
        # Тест определения категорий по ключевым словам
        def infer_category(name):
            name_lower = name.lower()
            if 'цемент' in name_lower:
                return 'Цемент'
            elif 'песок' in name_lower:
                return 'Песок'
            elif 'кирпич' in name_lower:
                return 'Кирпич'
            else:
                return 'Стройматериалы'
        
        categories = [infer_category(name) for name in material_names]
        
        assert categories[0] == 'Цемент'
        assert categories[1] == 'Песок'
        assert categories[2] == 'Кирпич'
    
    def test_environment_setup(self):
        """Тест настройки окружения для тестов"""
        # Проверяем что мы можем читать переменные окружения
        test_var = os.getenv('TEST_VAR', 'default_value')
        assert test_var == 'default_value'
        
        # Проверяем что мы можем устанавливать переменные
        os.environ['TEST_TEMP_VAR'] = 'test_value'
        assert os.getenv('TEST_TEMP_VAR') == 'test_value'
        
        # Очищаем после теста
        del os.environ['TEST_TEMP_VAR']
    
    @pytest.mark.asyncio
    async def test_async_basic(self):
        """Базовый тест асинхронной функциональности"""
        import asyncio
        
        async def simple_async_task():
            await asyncio.sleep(0.001)  # Очень короткая задержка
            return "async_result"
        
        result = await simple_async_task()
        assert result == "async_result"
    
    def test_fixtures_basic(self, temp_materials_data):
        """Тест использования фикстур"""
        # temp_materials_data должна быть доступна из conftest.py
        assert isinstance(temp_materials_data, list)
        assert len(temp_materials_data) >= 1
        
        # Проверяем структуру тестовых данных
        first_material = temp_materials_data[0]
        assert 'article' in first_material
        assert 'name' in first_material
        assert 'use_category' in first_material
        assert 'unit' in first_material


class TestUtilityHelpers:
    """Тесты вспомогательных функций"""
    
    def test_format_confidence(self):
        """Тест форматирования уровня уверенности"""
        def format_confidence(score):
            """Форматирует уровень уверенности в процентах"""
            return f"{score * 100:.1f}%"
        
        assert format_confidence(0.95) == "95.0%"
        assert format_confidence(0.123) == "12.3%"
        assert format_confidence(1.0) == "100.0%"
    
    def test_truncate_text(self):
        """Тест обрезки текста"""
        def truncate_text(text, max_length=50):
            """Обрезает текст до указанной длины"""
            if len(text) <= max_length:
                return text
            return text[:max_length-3] + "..."
        
        short_text = "Короткий текст"
        long_text = "Очень длинный текст который нужно обрезать потому что он слишком длинный для отображения"
        
        assert truncate_text(short_text) == short_text
        assert len(truncate_text(long_text)) == 50
        assert truncate_text(long_text).endswith("...")
    
    def test_generate_id(self):
        """Тест генерации уникальных ID"""
        import uuid
        
        # Простая генерация ID
        def generate_unique_id():
            return str(uuid.uuid4())
        
        id1 = generate_unique_id()
        id2 = generate_unique_id()
        
        assert id1 != id2
        assert len(id1) == 36  # UUID длина
        assert '-' in id1


if __name__ == "__main__":
    # Запуск тестов напрямую
    pytest.main([__file__, "-v"]) 