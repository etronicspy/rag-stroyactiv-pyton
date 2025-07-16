# Batch Processing Qdrant-Only Implementation Plan

## Цель
Обеспечить полноценную работу batch processing, прогресса, статусов и статистики только на Qdrant (vector DB), чтобы fallback-архитектура работала без PostgreSQL.

---

## Этапы

### 1. Анализ и проектирование
- [x] Определить, какие данные и статусы должны храниться для batch processing (request_id, material_id, status, progress, error, timestamps).
- [x] Решить, где хранить эти данные в Qdrant:
    - [x] В отдельной коллекции (например, `processing_records`)
    - [x] Использовать payload для хранения статусов и метаданных

### 2. Реализация методов batch processing в Qdrant-адаптере
- [x] Реализовать метод `create_processing_records` (добавление записей с payload).
- [x] Реализовать метод `update_processing_status` (обновление payload по material_id/request_id).
- [x] Реализовать метод `get_processing_progress` (расчёт прогресса по batch).
- [x] Реализовать метод `get_processing_results` (выдача результатов по request_id).
- [x] Реализовать метод `get_processing_statistics` (статистика по batch processing).
- [x] Реализовать метод `cleanup_old_records` (удаление устаревших записей).

### 3. Тестирование
- [x] Добавить unit/integration тесты для новых методов Qdrant-адаптера.
- [x] Проверить работу fallback-менеджера только с Qdrant.
- [x] Проверить сценарии: создание batch, обновление статуса, прогресс, результаты, статистика, очистка.

### 4. Документация
- [x] Описать архитектуру batch processing на Qdrant в DATABASE_ARCHITECTURE.md.
- [x] Добавить troubleshooting для Qdrant-only режима.

### 5. (Опционально) Временный mock-адаптер для тестов
- [x] Если реализация займёт время, временно вернуть mock-адаптер для SQL.

---

## Критерии готовности
- [x] Batch processing работает полностью на Qdrant (без PostgreSQL).
- [x] Все методы интерфейса реализованы и протестированы.
- [x] Fallback-менеджер корректно маршрутизирует batch операции только на Qdrant.
- [x] Нет NotImplementedError для batch processing в Qdrant-адаптере.
- [x] Документация и тесты обновлены. 

---

## План устранения ошибки update_processing_status (Qdrant)

### Проблема
- Ошибка при вызове update_processing_status: 
  - `2 validation errors for PointRequest\nids.0.int\n  Input should be a valid integer [type=int_type, input_value=None, input_type=NoneType]...`
- Причина: material_id передаётся как None или невалидный тип (ожидается str или int).

### Шаги диагностики и исправления
1. **Проверить, что material_id всегда строка**
   - Везде, где вызывается update_processing_status, убедиться, что material_id не None и это str.
2. **Проверить формирование material_id в create_processing_records**
   - При создании записей material_id должен быть str (UUID или id из материала).
3. **Проверить вызовы update_processing_status в batch_processing_service**
   - Передавать именно material_id, а не record_id или None.
4. **Добавить assert/logging для material_id**
   - Перед вызовом update_processing_status логировать тип и значение material_id.
5. **Проверить Qdrant-адаптер**
   - В методе update_processing_status добавить валидацию material_id и raise/log при ошибке.
6. **Проверить, что PointStruct(id=...) всегда получает str**
   - Исправить, если id=None или невалидный тип.
7. **Пере-тестировать batch processing**
   - Проверить, что статус обновляется, ошибок PointRequest нет, материал переходит из pending в completed/failed.

---

**Ответственный:** [указать исполнителя]
**Deadline:** [указать срок]
**Контроль:** Логи ошибок, интеграционные тесты, ручная проверка через API 