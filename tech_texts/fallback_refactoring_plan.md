# Fallback Refactoring Plan: Centralized Database Fallback Logic

## Goal
Implement a unified fallback mechanism in `core.database.factories` so that:
- If at least one database (vector or relational) is available, all API logic works as usual.
- If any database is unavailable, only log the error (do not break API logic).
- If **all** databases are unavailable, return a controlled error (e.g., 503 Service Unavailable).
- **No mock responses should be returned** — only real data or a clear error if all DBs are down.
- Remove duplicated fallback logic from services and repositories.

---

## Key Architectural Principle (as proposed by the user)
- **All fallback logic must be centralized in the database factories and/or a dedicated fallback manager (e.g., `core/database/factories.py` or `core/database/fallback_manager.py`).**
- All services and repositories must use this layer for all DB operations, with no local fallback or mock logic.
- If at least one DB is available, the API must work as normal, and errors for unavailable DBs must only be logged.
- If all DBs are unavailable, a controlled error (e.g., 503) must be returned. **No mock data should be returned in any case.**

---

## Motivation
- Avoid code duplication: fallback logic is currently scattered across services (e.g., batch_processing_service, statistics, etc.).
- Centralize error handling and fallback switching for all DB operations.
- Make it easy to extend fallback to new DB types (e.g., add new vector DBs or SQL backends).
- Ensure consistent API behavior: if at least one DB is up, API works; if all are down, return a clear error.

---

## Refactoring Steps

### 1. **Audit Current Fallbacks**
- Identify all places where fallback logic is implemented (services, repositories, adapters).
- List all DB operations that can fail and currently require fallback (search, upsert, get_by_id, etc.).

### 2. **Design Central Fallback Manager**
- Create a `DatabaseFallbackManager` class in `core.database.factories` (or a dedicated `fallback_manager.py` if logic grows).
- This manager will:
  - Track the health/status of each DB client (vector, SQL, etc.).
  - Provide unified methods for DB operations with built-in fallback.
  - Log errors for unavailable DBs, but transparently use available ones.
  - Expose health status for diagnostics/monitoring.

### 3. **Refactor DB Client Factories**
- Update all DB client factories to register their health with the fallback manager.
- On initialization, each client should perform a health check and report status.
- On operation failure, update status and trigger fallback logic.

### 4. **Update Repository/Service Layer**
- Refactor repositories/services to use the fallback manager for all DB operations instead of direct client calls.
- Remove local try/except fallback logic from services (e.g., batch_processing_service, statistics, etc.).
- Ensure all DB operations go through the fallback manager.

### 5. **Logging and Monitoring**
- Ensure all DB failures are logged with context (which DB, operation, error).
- Add metrics for DB availability and fallback events.
- Optionally, expose a health endpoint for DB status.

### 6. **Error Handling for Total Outage**
- If all DBs are unavailable, fallback manager should raise a controlled exception (e.g., `AllDatabasesUnavailableError`).
- API layer should catch this and return a 503 (Service Unavailable) or similar error.
- **No mock or fake responses should be returned.**

### 7. **Testing**
- Add unit/integration tests for fallback manager (simulate partial and total DB outages).
- Test that API works as expected with one or both DBs down.

### 8. **Documentation**
- Document the new fallback mechanism in `docs/DATABASE_ARCHITECTURE.md` and `docs/TROUBLESHOOTING.md`.
- Add inline docstrings and usage examples for the fallback manager.

---

## Example: Centralized Fallback Manager (Sketch)

```python
# core/database/factories.py
class DatabaseFallbackManager:
    def __init__(self, sql_client, vector_client):
        self.sql_client = sql_client
        self.vector_client = vector_client
        self.status = {'sql': True, 'vector': True}

    def _try(self, op, *args, **kwargs):
        errors = {}
        for db, client in [('sql', self.sql_client), ('vector', self.vector_client)]:
            if self.status[db]:
                try:
                    return getattr(client, op)(*args, **kwargs)
                except Exception as e:
                    self.status[db] = False
                    errors[db] = str(e)
                    # Log error
        if errors:
            # Log all DBs down
            raise AllDatabasesUnavailableError(errors)

    def search(self, *args, **kwargs):
        return self._try('search', *args, **kwargs)
    # ... other methods ...
```

---

## Deliverables
- [ ] `DatabaseFallbackManager` in `core/database/factories.py`
- [ ] Refactored repositories/services to use the manager
- [ ] Logging and metrics for DB health/fallback
- [ ] Tests for fallback scenarios
- [ ] Documentation updates

---

**Author:** AI Assistant  
**Date:** {{date}} 

---

## Выполнение плана (Execution Status)

- [x] 1. Audit Current Fallbacks — **Completed**
- [x] 2. Design Central Fallback Manager — **Completed**
- [x] 3. Refactor DB Client Factories — **Completed**
- [x] 4. Update Repository/Service Layer — **Completed**
- [x] 5. Logging and Monitoring — **Completed**
- [x] 6. Error Handling for Total Outage — **Completed**
- [x] 7. Testing — **Completed**
- [x] 8. Documentation — **Completed**

**Status:** All steps of the centralized fallback refactoring plan have been fully implemented and verified in the codebase. The system now uses only real data or a clear error if all DBs are down, with no mock responses in production logic. All fallback logic is centralized, and the API returns 503 on total DB outage as required.

--- 