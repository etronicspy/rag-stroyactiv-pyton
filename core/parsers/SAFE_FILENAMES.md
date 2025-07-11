# Safe Filenames for Parser Module

## ✅ Проверенные безопасные имена файлов для парсеров:

### Services
- `ai_parser_service.py` - основной AI парсинг сервис
- `material_parser_service.py` - парсинг материалов
- `batch_parser_service.py` - батч обработка
- `text_parser_service.py` - парсинг текста
- `validation_parser_service.py` - валидация результатов

### Configuration
- `parser_config_manager.py` - управление конфигурацией
- `system_prompts_manager.py` - управление системными промптами
- `units_config_manager.py` - конфигурация единиц измерения
- `parser_settings_manager.py` - управление настройками

### Interfaces
- `parser_interface.py` - базовый интерфейс парсера
- `ai_parser_interface.py` - интерфейс AI парсера
- `material_parser_interface.py` - интерфейс парсера материалов
- `batch_parser_interface.py` - интерфейс батч парсера

### Utilities
- `parser_utils.py` - утилиты для парсинга
- `text_processing_utils.py` - утилиты обработки текста
- `validation_utils.py` - утилиты валидации

### Data Models
- `parser_models.py` - модели данных парсера
- `parse_result_models.py` - модели результатов парсинга
- `material_models.py` - модели материалов
- `batch_models.py` - модели батчей

## 🚨 ИЗБЕГАТЬ этих имен:

### Критические конфликты с Python stdlib:
- `parser.py` - конфликт с модулем parser
- `json.py` - конфликт с модулем json
- `ast.py` - конфликт с модулем ast
- `string.py` - конфликт с модулем string
- `re.py` - конфликт с модулем re

### Потенциально опасные:
- `config.py` - слишком общий
- `utils.py` - слишком общий
- `base.py` - слишком общий
- `models.py` - слишком общий

## 📋 Рекомендации:

1. **Всегда используйте описательные префиксы**: `parser_`, `ai_`, `material_`
2. **Добавляйте функциональные суффиксы**: `_service`, `_manager`, `_interface`
3. **Избегайте сокращений**: `config` → `config_manager`
4. **Используйте полные описания**: `ai_parser_service` вместо `ai_parser`

## 🔍 Проверка:

Для проверки безопасности имен файлов:
```bash
python scripts/check_filename_conflicts.py --strict --suggest-alternatives
``` 