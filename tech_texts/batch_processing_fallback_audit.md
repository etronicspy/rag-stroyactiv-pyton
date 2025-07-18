# Batch Processing Fallback Audit: Взаимозаменяемость Vector DB и SQL DB

## 1. Текущее состояние

- Вся логика batch processing (BatchProcessingService, ProcessingRepository) жёстко завязана на SQL (PostgreSQL):
  - Создание записей, статусы, прогресс — через SQL таблицу processing_results.
  - Используется SQLAlchemy session, raw SQL, транзакции.
- Векторная БД (Qdrant) используется только для векторного поиска, upsert, поиска материалов, но не для batch-статусов или прогресса.
- Нет fallback-реализации batch processing через Qdrant.
- Если SQL недоступен, batch processing не работает, потому что нет методов для хранения batch-статусов, прогресса, очередей в Qdrant.
- Аналогично, если Qdrant недоступен, векторный поиск не fallback-ится на SQL (например, через LIKE).

## 2. Вывод

**Взаимозаменяемость БД для batch processing и статусов НЕ реализована.**
- Сейчас:
  - Batch processing = только SQL
  - Векторный поиск = только Qdrant
- Нет универсального слоя, который бы позволял хранить batch-статусы и прогресс в любой из БД.

## 3. Что нужно сделать для полной взаимозаменяемости

### 1. Реализовать batch processing и статусы для Qdrant
- Добавить методы в Qdrant-адаптер:
  - create_processing_records
  - update_processing_status
  - get_processing_progress
  - и т.д.
- Хранить batch-статусы и прогресс как payload в Qdrant коллекции (например, processing_results).

### 2. Реализовать векторный поиск через SQL
- Добавить fallback-методы поиска через SQL (например, через LIKE/ILIKE по материалам).

### 3. Обновить DatabaseFallbackManager
- Все методы (batch, статусы, поиск) должны сначала пробовать одну БД, если не работает — вторую.
- Сервис/репозиторий не должен знать, какая БД используется.

### 4. Обновить сервисы и репозитории
- Все обращения к БД — только через fallback-менеджер.
- Удалить прямые вызовы к vector_db или sql_db.

## 4. Следующий шаг

- Реализовать хранение batch-статусов и прогресса в Qdrant (или другой vector DB), чтобы обеспечить взаимозаменяемость.
- Обновить DatabaseFallbackManager для маршрутизации всех функций.
- Обновить сервисы/репозитории — только через fallback-менеджер.

---

**Документ создан автоматически на основе аудита кода и архитектурных требований.** 