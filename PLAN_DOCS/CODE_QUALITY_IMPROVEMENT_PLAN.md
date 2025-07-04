# Code Quality Improvement Plan

_Дата: 2025-06-23_

Цель — повысить читаемость, надёжность и тестируемость кода без изменения бизнес-логики приложения.

## 1. Статический анализ
✅ Выполнено — конфигурация `mypy --strict`, `ruff`, плагины flake8 и pre-commit добавлены (2025-06-23).

## 2. Тестовое покрытие
- Расширить unit-тесты для `core/database` adapters и middleware (граничные случаи, исключения).
- Добавить интеграционные тесты для health-checks и fallback-стратегии (**vector → SQL**).

## 3. Контрактность и валидация
- Использовать `field_validator` во всех Pydantic-настройках `.env`.
- Добавить runtime-assertions в критичных точках (ID, типы коллекций).

## 4. Документация API
- Проверить docstrings (Google style) для всех публичных классов/функций.
- Расширить OpenAPI: документировать все нестандартные 4xx/5xx ответы.

## 5. Модульный рефакторинг
- Декомпозировать файлы > 500 строк (`core/logging/*`, `services/price_processor.py`).
- Выделить интерфейсы (ABC) для кешей и внешних API, внедрять через DI.

## 6. Исключение глобальных синглтонов
- Перейти на FastAPI `Depends` для логгеров и метрик.
- Ограничить использование `lru_cache` только действительно тяжёлыми фабриками.

## 7. Производительность
- Заменить блокирующие вызовы (`psutil.cpu_percent(interval=1)`) на асинхронные или кэшированные.
- В middleware/compression вычислять приоритет алгоритма один раз на старте.

## 8. CI/CD
- Добавить `pre-commit` шаг `ruff --fix`.
- Настроить CI (GitHub/Bitbucket): ruff, mypy, pytest, safety.

## 9. Обработка ошибок
- Ловить конкретные исключения (например, `QdrantClientException`, `RedisError`).
- Использовать фабрику ошибок для генерации пользовательских сообщений.

## 10. Улучшение типизации
- Заменить `Dict[str, Any]` на `TypedDict` или `Protocol`.
- Применять `Literal["qdrant", "weaviate", "pinecone"]` для `database_type`.

## 11. Логирование и мониторинг
- Перейти на структурированные JSON-логи для всех сервисов (middleware, DB, external API).
- Выравнять уровни логирования по стандарту (DEBUG, INFO, WARNING, ERROR, CRITICAL) и удалить кастомные уровни.
- Интегрировать трассировку `OpenTelemetry` для медленных запросов и профилирования.
- Добавить метрики latency для vector search и fallback SQL-поиска.

## 12. Безопасность и управление зависимостями
- Включить Dependabot/Renovate для автоматических PR обновлений зависимостей.
- Добавить статический анализ `bandit` и проверку уязвимостей `safety` в pre-commit и CI.
- Настроить secret-scanning (например, truffleHog) для всех pull-requests.
- Периодически запускать SCA-сканирование (Snyk/OWASP Dependency-Check).

## 13. Удаление legacy-кода
- Депрецировать и постепенно удалить модуль `core/bash_commands` и устаревший `services/dynamic_batch_processor.py`.
- Перенести логику batch-processing в отдельный сервис (Celery/RQ) или переиспользовать существующие очереди.
- Очистить фикстуры и тестовые данные, относящиеся к удаляемым модулям.

## 14. Автоматизация документации
- Подключить `mkdocs-material` и автогенерацию раздела API из OpenAPI-спецификации.
- Внедрить метрику покрытия docstrings (> 85 %) и проверку в CI.
- Публиковать документацию автоматически в GitHub Pages на каждый релиз.

## 15. Метрики качества и наблюдаемости
- Интегрировать SonarQube/CodeClimate для отслеживания code smells и technical debt.
- KPI: покрытие тестами ≥ 90 %, SQALE-рейтинг ≤ 2 %, критические баги = 0.
- Визуализировать ключевые метрики (coverage, баги, уязвимости) в Dashboard Grafana.

---

_Ответственный_: ⟨указать имя⟩  
_Запланированная версия_: ⟨v0.2.0⟩  
_Оценка трудозатрат_: 3–4 недели (с учётом ревью и CI). 