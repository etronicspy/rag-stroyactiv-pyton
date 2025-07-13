## Refactoring Plan

### core/config/base.py

**Observations:**
*   **Positive aspects:**
    *   Uses `pydantic_settings.BaseSettings` and `pydantic.Field` for type-safe and well-documented configuration.
    *   Avoids hardcoded values by importing defaults from `constants.py`.
    *   Includes `field_validator` for custom validation.
    *   Modular structure with imports for database and AI settings.
    *   Well-organized sections within the `Settings` class.

*   **Potential areas for review:**
    *   **File Size:** At 579 lines, it's quite large.
    *   **`get_*_config` Methods:** Methods like `get_vector_db_config`, `get_relational_db_config`, `get_ai_config`, and `get_ssh_tunnel_config` within the `Settings` class could potentially be moved to `core/config/factories.py` to further improve separation of concerns and reduce the size of `base.py`. This would align better with the "MODULAR REFACATORING CORE/CONFIG.PY COMPLETED!" memory which mentions `factories.py` as a place for "client factories with caching". These methods generate configuration dictionaries which are a step towards client creation. 

### core/config/factories.py

**Observations:**
*   **Positive aspects:**
    *   Correctly implements the factory pattern for creating database and AI clients, utilizing `@lru_cache(maxsize=1)` for caching, aligning with architectural rules.
    *   Imports `Settings` and `get_settings` from `core/config/base.py` and uses `settings.get_*_config()` methods to retrieve configuration dictionaries.
    *   Includes proper error handling for missing packages (`ImportError`).
    *   Well-defined docstrings following Google style.

*   **Potential areas for review:**
    *   **Dependency on `settings.get_*_config()` methods:** The `get_*_config()` methods reside in `base.py` but are used here. It might be beneficial to have `DatabaseConfig` and `AIConfig` (already imported in `base.py`) be directly responsible for generating these configuration dictionaries, allowing `factories.py` to focus solely on client creation from already structured configurations.
    *   **Hardcoded Parser-specific Timeouts:** `get_parser_ai_client` and `get_parser_embedding_client` contain hardcoded `timeout=45`. This violates the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule. These timeouts should be configurable via environment variables and defined in `core/config/ai.py` or `core/config/parsers.py` (if parser-specific) or `constants.py`. 

### core/config/database.py

**Observations:**
*   **Positive aspects:**
    *   Effectively acts as a factory for database configurations, aligning with the architectural pattern of "Фабрики клиентов с автоматическим переключением БД".
    *   Uses base classes (`BaseDatabaseConfig`, `VectorDatabaseConfig`, `RelationalDatabaseConfig`, `CacheDatabaseConfig`) for organizing and reusing common configuration logic.
    *   Imports constants from `constants.py` for default values, adhering to the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule.
    *   Docstrings are well-written and follow the specified format.
    *   The `DatabaseConfig` class acts as a unified facade.

*   **Potential areas for review:**
    *   **Redundancy with `base.py` methods:** The `get_*_config` methods in `DatabaseConfig` (e.g., `get_qdrant_config`, `get_postgresql_config`) essentially duplicate the configuration generation logic that is then called by `settings.get_*_config()` methods in `core/config/base.py`. 
        *   **Proposal:** Consolidate the configuration generation responsibility solely within `core/config/database.py` (and `core/config/ai.py`). The `Settings` class in `base.py` should directly pass its attributes to these configuration factories rather than having its own `get_*_config` methods that merely proxy the calls. This will make `base.py` purely a settings definition file and align better with the modular refactoring goals. 

### core/config/ai.py

**Observations:**
*   **Positive aspects:**
    *   Effectively acts as a factory for AI provider configurations.
    *   Uses `BaseAIConfig` for common settings like `timeout` and `max_retries`, promoting code reuse.
    *   Correctly imports `DefaultTimeouts` and `ModelNames` from `constants.py`, adhering to the rule against hardcoded values.
    *   Docstrings are well-defined and follow the specified format.
    *   The `AIConfig` class provides a unified facade for accessing different AI configurations.

*   **Potential areas for review:**
    *   **Redundancy with `base.py` methods:** Similar to `database.py`, the `get_*_config` methods in `AIConfig` duplicate the configuration generation logic that is then called by `settings.get_ai_config()` in `core/config/base.py`. 
        *   **Proposal:** Consolidate the AI configuration generation responsibility solely within `core/config/ai.py`. The `Settings` class in `base.py` should directly pass its attributes to these configuration factories instead of having its own `get_ai_config` method that merely proxies the call. This will make `base.py` purely a settings definition file.
    *   **Hardcoded `max_retries` in `BaseAIConfig`:** The `_get_base_config` method in `BaseAIConfig` has a hardcoded default `max_retries=3`. This could be made configurable via a constant in `constants.py` (e.g., `DefaultRetries.API_REQUESTS`) to align with the "ОБЯЗАТЕЛЬНОЕ использование констант вместо магических чисел" rule, and provide a single source of truth for such defaults.
    *   **Hardcoded `OllamaConfig` defaults:** `get_ollama_config` has `url="http://localhost:11434"` and `model="llama2"` hardcoded. These should ideally come from `constants.py` or be configurable via environment variables, adhering to the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule. 

### core/config/log_config.py

**Observations:**
*   **Positive aspects:**
    *   Centralizes all logging-related settings using Pydantic's `BaseSettings` and `Field` for maintainability and validation.
    *   Clearly defines various logging aspects: levels, structured logging, HTTP request logging, correlation ID, database logging, performance metrics, security, and formatting.
    *   Uses `Enum` for `LogLevel` and `LogTimestampFormat`, promoting type safety and readability.
    *   Includes `field_validator` for parsing list-like environment variables.
    *   Defines unified log format constants and functions, ensuring consistency.
    *   Docstrings are well-written and follow the specified format.

*   **Potential areas for review:**
    *   **Hardcoded `LOG_MAX_BODY_SIZE`:** The value is hardcoded to `65536`. It should ideally be derived from `FileSizeLimits` in `constants.py` or be a new constant there, to ensure all size limits are centrally managed and avoid magic numbers, adhering to the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule [[memory:581130]].
    *   **Hardcoded `LOG_FILE_MAX_SIZE_MB` and `LOG_FILE_BACKUP_COUNT`:** These values are also hardcoded. They should be defined in `constants.py` or in a new `LogFileSettings` class within `constants.py` (if specific to file logging) and then imported here. This maintains consistency with the rule of avoiding hardcoded values.
    *   **`logging` import inside `create_unified_formatter`:** The `logging` module is imported inside the `create_unified_formatter` function. While not critical, it's generally better practice to place imports at the top of the file for readability and to prevent potential (though unlikely here) circular import issues. 

### core/config/type_definitions.py

**Observations:**
*   **Positive aspects:**
    *   `type_definitions.py` is well-named, avoiding conflicts with the standard Python `types.py` module, aligning with filename conflict rules [[memory:581133]].
    *   Centralizes `Enum` definitions for `DatabaseType`, `AIProvider`, `LogLevel`, `Environment`, and `LogFormat`, promoting consistency and type safety.
    *   Docstrings are clear and follow the specified format.

*   **Potential areas for review:**
    *   **Duplicate `LogLevel`:** The `LogLevel` enum is also defined in `core/config/log_config.py`. This is a clear duplication.
        *   **Proposal:** `LogLevel` should be defined only once, and `core/config/log_config.py` should import it from `core/config/type_definitions.py`. This ensures a single source of truth for log levels.
    *   **`LogFormat` usage:** While `LogFormat` is defined here, its usage was not immediately apparent in `log_config.py`. It might be redundant or not fully utilized.
        *   **Proposal:** Verify where `LogFormat` is used and if it's necessary. If `ENABLE_STRUCTURED_LOGGING` or similar boolean flags fully cover the formatting needs, `LogFormat` might be redundant and can be removed.
    *   **`TEST` environment alias:** The comment `TEST = "test" # legacy alias for unit tests` suggests `TEST` is a legacy alias for `TESTING`. Consider consolidating to just `TESTING` if the legacy usage is minimal or easily updateable, to simplify environment checks. 

### core/config/__init__.py

**Observations:**
*   **Positive aspects:**
    *   `__init__.py` acts as a central entry point for the `core.config` module, simplifying imports for other parts of the application.
    *   It re-exports key classes and functions from submodules (`base`, `constants`, `database`, `ai`, `factories`, `type_definitions`, `log_config`), which is a good practice for module organization.
    *   Uses `@lru_cache` for `get_logging_config()`, ensuring single initialization of logging configuration and good performance optimization.
    *   The `__all__` variable explicitly defines exported symbols, which is good for controlling the module's public API.

*   **Potential areas for review:**
    *   **Global `settings` and `logging_config` instances:**
        *   `settings = get_settings()` and `logging_config = get_logging_config()` are created as global instances within the `__init__.py` file. While providing backward compatibility, this can lead to issues in testing or more complex scenarios where different configurations might be needed dynamically.
        *   **Proposal:** Relying solely on the cached `get_settings()` and `get_logging_config()` functions is a more flexible and testable approach. The global `settings` and `logging_config` variables could be removed, with consumers directly calling the `get_*` functions. This would be a breaking change, requiring careful consideration but aligning with modern dependency injection patterns.
    *   **Direct re-export of `get_environment_name`, `is_production`, `is_development` from `base.py`:** These utility functions from `base.py` are directly re-exported here. While convenient, the `Settings` class itself already provides `is_production()` and `is_development()` methods. If `get_environment_name` is only used for logging or specific non-`Settings` related checks, its presence might be justified, but generally, accessing environment status through the `settings` object is preferred.
        *   **Proposal:** Consider if these utility functions are truly necessary at the module level or if they should primarily be accessed via the `Settings` instance.
    *   **Mixing configuration classes and factory functions in `__all__`:** While `__all__` is clear, it includes both Pydantic configuration classes (`Settings`, `DatabaseConfig`, `AIConfig`, `LoggingConfig`) and client factory functions (`get_vector_db_client`, `get_ai_client`, etc.). This is more of an organizational style point.
        *   **Proposal:** This is generally acceptable, but in very large projects, some might prefer to separate the re-export of configuration *definitions* from *factory functions* or *instances*. For the current project size, it's likely fine. 

### core/database/interfaces.py

**Observations:**
*   **Positive aspects:**
    *   `interfaces.py` correctly defines abstract base classes (`ABC`) for various database types (`IVectorDatabase`, `IRelationalDatabase`, `ICacheDatabase`), perfectly aligning with the architectural rule "Абстрактные интерфейсы (ABC) для БД операций".
    *   The `IVectorDatabase` interface includes all required methods: `search`, `upsert`, `delete`, `batch_upsert`, `get_by_id`, plus `create_collection`, `collection_exists`, `update_vector`, and `health_check`, showing strong adherence to "Обязательные методы векторных репозиториев".
    *   All methods are `abstractmethod` and `async`, enforcing asynchronous operations.
    *   Docstrings are well-defined for each interface and method, including descriptions, arguments, and return values, in line with the "Docstrings обязательны для всех публичных классов, методов и функций" rule.
    *   The file clearly states its purpose in both Russian and English.

*   **Potential areas for review:**
    *   **No immediate refactoring needs based on current rules:** This file is exceptionally well-structured and adheres to the specified architectural patterns. There are no obvious redundancies or hardcoded values. 

### core/database/factories.py

**Observations:**
*   **Positive aspects:**
    *   Successfully implements the factory pattern for creating database and AI provider clients, utilizing `lru_cache` for caching, aligning with caching and dependency injection rules.
    *   Supports runtime switching between different database types and includes fallback logic to mock adapters in case of connection disablement or failures, consistent with "Фабрики клиентов с автоматическим переключением БД" and "Fallback стратегии".
    *   Correctly imports interfaces and exceptions, maintaining a modular structure.
    *   Includes `clear_cache` and `get_cache_info` methods for management, useful for monitoring and testing.
    *   Docstrings are well-defined and follow the specified format.

*   **Potential areas for review:**
    *   **Significant Duplication with `core/config/factories.py`:** This is the most critical issue. There are two sets of factory functions for creating DB and AI clients: `core/database/factories.py` (with `DatabaseFactory` and `AIClientFactory` classes) and `core/config/factories.py` (with `get_vector_db_client`, `get_ai_client`, etc. functions).
        *   **Proposal:** Consolidate the client instance creation logic into a single location. `core/database/factories.py` appears to be the more appropriate place for factories that directly create and manage *database instances*, while `core/config/factories.py` should either be removed or refactored to solely retrieve *configuration dictionaries* (as discussed earlier for `base.py`), rather than creating actual *clients*.
    *   **Reliance on Global `settings` Variable:** The factories directly access the global `settings` variable from `core.config`. This complicates testing and contradicts dependency injection principles, which advocate passing dependencies rather than importing them from a global context.
        *   **Proposal:** Pass the `settings` instance to the factories as an argument rather than importing it globally.
    *   **Hardcoded Redis URL in `create_cache_database`:** The `create_cache_database` method contains a hardcoded Redis URL: `config = config_override or {"redis_url": redis_url or "redis://localhost:6379"}`. This violates the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule [[memory:581130]].
        *   **Proposal:** Utilize the `DefaultPorts.REDIS` constant from `constants.py` to construct the URL, or retrieve it from `settings` if it's meant to be configurable via environment variables. 

### core/database/pool_manager.py

**Observations:**
*   **Positive aspects:**
    *   The file implements a `DynamicPoolManager` with auto-scaling, monitoring, and metrics collection for connection pools, aligning well with the "Connection pooling for performance" rule.
    *   It uses `asyncio` for the monitoring loop and `threading.Lock` for thread-safety, indicating good practices for concurrency.
    *   The `PoolMetrics` and `PoolConfig` dataclasses provide structured and configurable parameters for pool management.
    *   The `PoolProtocol` defines a clear interface for pools that can be managed by the manager.
    *   Includes logic for scaling up and down based on utilization, and checks system resources before scaling up.
    *   Docstrings are well-defined for classes and methods, and the module clearly states its purpose in both English and Russian.

*   **Potential areas for review/refactoring:**
    *   **Hardcoded values within `PoolConfig` defaults:** While `PoolConfig` is designed to be configurable, several default values are hardcoded within its definition (e.g., `min_size=2`, `max_size=50`, `target_utilization=0.75`, `monitoring_interval=30.0`, `connection_timeout=30.0`, `idle_timeout=300.0`). These values should ideally be sourced from `core/config/constants.py` (e.g., `DefaultTimeouts.CONNECTION_POOL` for timeouts) or new constants defined there to avoid "magic numbers" and ensure a single source of truth, aligning with the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule [[memory:581130]]. This would also allow for easier adjustment via environment variables if these settings become more dynamic.
    *   **Direct access to `psutil` in `_check_system_resources`:** The `_check_system_resources` method directly uses `psutil` to check CPU and memory usage. While `psutil` is a useful library, directly embedding resource checks in the pool manager might make it less modular.
        *   **Proposal:** Consider creating a separate `SystemResourceMonitor` utility in `core/monitoring/` or `core/utils/` that the `DynamicPoolManager` can depend on. This would separate concerns and make the resource monitoring logic reusable and testable independently.
    *   **Global `logger` instance:** The `logger = get_logger(__name__)` is defined globally. While common, in a highly modular system, passing the logger explicitly or using a DI container for loggers can sometimes be preferred for better testability and control. However, for a logger, this is often an acceptable pattern. 

### core/database/seed_data.py

**Observations:**
*   **Positive aspects:**
    *   The file is clearly designed for seeding initial reference data (categories and units), which is a common and necessary practice for database initialization.
    *   It uses `AsyncSession` from SQLAlchemy, indicating adherence to asynchronous database operations.
    *   Includes checks (`SELECT COUNT(*)`) to prevent re-seeding data if it already exists, which is good for idempotent operations.
    *   Uses explicit SQL `text()` for inserts, providing fine-grained control over the seeding process.
    *   Handles hierarchical data for categories and conversion factors for units, demonstrating a thoughtful data model.
    *   Includes `try-except` blocks with rollback for transactions, ensuring data consistency in case of errors.
    *   Logging is used to track the seeding process, which is good for monitoring.
    *   Docstrings are well-defined and follow the specified format.

*   **Potential areas for review/refactoring:**
    *   **Hardcoded Seed Data:** The `SEED_CATEGORIES` and `SEED_UNITS` lists contain all the seed data directly within the file. While this is typical for small, static datasets, for larger or potentially evolving reference data, it could be beneficial to:
        *   **Proposal:** Externalize this data into a more manageable format, such as JSON or YAML files located in a `data/` subdirectory within `core/database/` or `resources/`. This would allow for easier updates, versioning, and potentially even dynamic loading of seed data without modifying code. This aligns with the "no hardcoded values" rule in a broader sense, by preventing hardcoded *data* from being intertwined with code logic.
    *   **Direct SQL Queries:** The `seed_categories` and `seed_units` methods use raw SQL queries via `text()` directly within the seeder logic. While effective, the "Repository pattern for each type of DB" rule suggests abstracting database operations through repositories.
        *   **Proposal:** Consider if these seeding operations could leverage the existing repository pattern (e.g., if there were `CategoryRepository` and `UnitRepository`) instead of raw SQL. This would make the seeding logic more consistent with the rest of the application's data access layer and potentially reduce coupling to specific SQL syntax. However, for simple seeding, direct SQL might be acceptable if the focus is on performance and direct insertion. This is more of an architectural consistency point.
    *   **Redundant `logger` initialization:** `logger = get_logger(__name__)` is at the top of the file. This is acceptable, but if the `get_logger` function were to be dependency injected (as discussed in `core/config/__init__.py`), it would align better with that pattern. For this specific file, it's a minor point. 

### core/database/exceptions.py

**Observations:**
*   **Positive aspects:**
    *   The file defines a clear hierarchy of custom exceptions, inheriting from a `DatabaseError` base class. This is a good practice for structured error handling and allows for specific exception catching.
    *   Specific exceptions are provided for common database issues (`ConnectionError`, `QueryError`, `ConfigurationError`, `TransactionError`, `ValidationError`, `CacheError`), which enhances the clarity of error messages and facilitates targeted error handling.
    *   Each exception class has a well-defined `__init__` method that accepts a `message` and optional `details`, and also specific attributes relevant to the error (e.g., `database_type` for `ConnectionError`, `query` for `QueryError`).
    *   Default messages are provided for each exception, which makes them easy to use without requiring a custom message every time.
    *   Docstrings are present for all classes and `__init__` methods, adhering to the specified format and clearly explaining the purpose and arguments.

*   **Potential areas for review:**
    *   **No immediate refactoring needs based on current rules:** This file is very well-structured and adheres to the principles of good exception design. There are no obvious hardcoded values or redundancies that violate the stated architectural rules. It effectively supports the "Обработка ошибок для всех БД" rule mentioned in the API design rules. 

### core/database/adapters/postgresql_adapter.py

**Observations:**
*   **Positive aspects:**
    *   `postgresql_adapter.py` implements a PostgreSQL adapter, inheriting from `IRelationalDatabase`, aligning with the "Абстрактные интерфейсы (ABC) для БД операций" architectural pattern.
    *   Uses SQLAlchemy 2.0+ with async capabilities (`create_async_engine`, `AsyncSession`, `async_sessionmaker`), consistent with the "PostgreSQL: SQLAlchemy 2.0+ с async" rule.
    *   Defines SQLAlchemy models (`MaterialModel`, `RawProductModel`) with `Mapped`, `mapped_column`, and `UUID` for database interaction, including indexes for full-text search (GIN) and `pgvector` for embeddings, demonstrating a well-designed data schema.
    *   Integrates with the SSH tunnel service (`get_tunnel_service()`), ensuring secure remote DB connection.
    *   Handles connections, disconnections, and health checks (`connect`, `disconnect`, `health_check`), including error logging.
    *   Injecting `Settings` via the class constructor (`__init__`) is a good practice, even if the `Settings` instance itself might be global as previously discussed.
    *   Docstrings are present and well-formatted for classes and methods.

*   **Potential areas for review/refactoring:**
    *   **Hardcoded default values for connection pool:** In the `connect` method, `create_async_engine` uses `getattr(self.settings, 'POSTGRESQL_POOL_SIZE', 10)`, `max_overflow=getattr(self.settings, 'POSTGRESQL_MAX_OVERFLOW', 20)`, `pool_timeout=getattr(self.settings, 'POSTGRESQL_POOL_TIMEOUT', 30)`, `pool_recycle=getattr(self.settings, 'POSTGRESQL_POOL_RECYCLE', 3600)`. While `getattr` is used with defaults, these default values are *still hardcoded* within this file. This violates the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule [[memory:581130]].
        *   **Proposal:** These default values should be defined exclusively in `core/config/constants.py` (e.g., `ConnectionPools.POSTGRESQL_POOL_SIZE`) and imported from there to ensure a single source of truth.
    *   **Direct SQLAlchemy model operations and SQL queries:** The adapter contains methods like `create_material`, `search_materials_hybrid`, `get_materials` that perform direct SQLAlchemy model operations and SQL queries. While part of an adapter, the "Repository pattern for each type of DB" rule suggests that these higher-level CRUD operations and business logic should be encapsulated within separate repository classes (e.g., `MaterialRepository`) which *utilize* the adapter.
        *   **Proposal:** Move the logic for `create_material`, `search_materials_hybrid`, `get_materials` (and similar) to their respective repositories, and the adapter should only expose lower-level methods like `execute_query`, `execute_command`, and `get_session`. This would significantly improve separation of concerns.
    *   **`Settings` import:** The `PostgreSQLAdapter` class imports `Settings` from `core.config`. This is fine, but as we discussed previously, relying on a global `settings` instance can be problematic. Passing the config directly (or retrieving it via DI) is a more robust approach.
    *   **Passing `LOG_LEVEL` for `echo`:** `echo=self.settings.LOG_LEVEL == "DEBUG"` is a valid way to enable SQL logging, but it implies using `LOG_LEVEL` from settings for behavioral logic, not just logging. This might be acceptable but is worth noting. 

### core/database/adapters/mock_adapters.py

**Observations:**
*   **Positive aspects:**
    *   The file correctly implements mock adapters for `IRelationalDatabase` and `ICacheDatabase` interfaces, fulfilling the "Абстрактные интерфейсы (ABC) для БД операций" rule.
    *   It uses inner mock classes (`MockRedisClient`, `MockPostgreSQLAdapter` from `core/database/mocks.py`) to simulate database behavior, which is a good separation of concerns for mock implementations.
    *   The adapters contain basic mock implementations for the methods defined in their respective interfaces, providing a functional fallback for testing and "Fallback стратегии".
    *   Factory functions (`create_mock_relational_adapter`, `create_mock_cache_adapter`) are provided for easy instantiation.
    *   Docstrings are present for classes and methods.

*   **Potential areas for review/refactoring:**
    *   **Redundant methods in `MockRelationalAdapter`:** `MockRelationalAdapter` directly implements methods like `create_material`, `get_materials`, `search_materials_sql`, `update_material`, `delete_material`, `get_material_by_id`. However, these methods are not part of the `IRelationalDatabase` interface. The `IRelationalDatabase` only defines `execute_query`, `execute_command`, `begin_transaction`, and `health_check`.
        *   **Proposal:** These high-level CRUD methods should ideally not be part of the `IRelationalDatabase` interface or its direct adapter implementations. They belong in the repository layer (e.g., a `MaterialRepository` that *uses* the `IRelationalDatabase` adapter). Removing them from the mock adapter would align it more closely with the `IRelationalDatabase` interface it's supposed to implement, reducing the "surface area" of the adapter.
    *   **Hardcoded mock data/responses:** While it's a mock, some responses like in `get_material_by_id` return hardcoded dictionaries. For more comprehensive testing, these could be configurable or generated dynamically (though for a mock, it's often acceptable for simplicity). However, the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule, while primarily for production configuration, suggests a broader principle of avoiding magic values, which could extend to dynamic test data.
    *   **Import of `contextlib.asynccontextmanager` within `begin_transaction`:** Similar to the `logging` import in `log_config.py`, this import is placed inside the method. It's generally better practice to put imports at the top of the file for readability. 

### core/database/adapters/qdrant_adapter.py

**Observations:**
*   **Positive aspects:**
    *   `qdrant_adapter.py` implements a Qdrant adapter, inheriting from `IVectorDatabase`, aligning with the "Абстрактные интерфейсы (ABC) для БД операций" architectural pattern and ensuring a unified interface for vector databases.
    *   Includes all required vector repository methods: `create_collection`, `collection_exists`, `upsert`, `search`, `get_by_id`, `update_vector`, `delete`, `batch_upsert` (presence and parameters indicate batching usage), and `health_check`.
    *   Uses `QdrantClient` and `asyncio.to_thread` for asynchronous operations, which is good practice for non-blocking interactions.
    *   Handles exceptions, converting them into custom `ConnectionError`, `QueryError`, and `DatabaseError`, consistent with error handling rules.
    *   Logging is used to track operations, adhering to logging rules.
    *   Docstrings are well-defined for the class and its methods.

*   **Potential areas for review/refactoring:**
    *   **Hardcoded default values in `__init__`:** In the `QdrantVectorDatabase` constructor, default values for `timeout` (`30`), `collection_name` (`"materials"`), `vector_size` (`1536`), and `distance` (`"COSINE"`) are hardcoded in `config.get()` calls. This violates the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule [[memory:581130]].
        *   **Proposal:** These default values should be sourced from `core/config/constants.py` (e.g., `DefaultTimeouts.DATABASE`, `DatabaseNames.QDRANT_COLLECTION`, `VectorSize.OPENAI_SMALL`, and potentially a new constant for the default distance) and imported from there to ensure a single source of truth.
    *   **Direct `create_collection` call in `upsert`:** The `upsert` method includes logic to create the collection if it doesn't exist. While convenient, this couples `upsert` with collection creation logic. In some architectural approaches, collection creation might be an explicit initialization or migration step, rather than implicit during an `upsert` operation. This is more of an architectural style point than a strict rule violation. 

### core/database/adapters/weaviate_adapter.py

**Observations:**
*   **Positive aspects:**
    *   `weaviate_adapter.py` implements an adapter for Weaviate, inheriting from `IVectorDatabase`, aligning with the "Абстрактные интерфейсы (ABC) для БД операций" architectural pattern and ensuring a unified interface for vector databases.
    *   Includes all required vector repository methods: `create_collection`, `collection_exists`, `upsert`, `search`, `get_by_id`, `update_vector`, `delete`, `batch_upsert`, and `health_check`.
    *   Handles errors (`ConnectionError`, `DatabaseError`, `ConfigurationError`), converting Weaviate exceptions to custom types.
    *   Uses logging to track operations.
    *   Docstrings are well-defined and formatted.

*   **Potential areas for review/refactoring:**
    *   **Hardcoded default values in `__init__`:** In the `WeaviateVectorDatabase` constructor, default values for `class_name` (`"Materials"`), `vector_size` (`1536`), and `timeout` (`30`) are hardcoded in `config.get()` calls. This violates the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule [[memory:581130]].
        *   **Proposal:** These default values should be sourced from `core/config/constants.py` (e.g., `DatabaseNames.WEAVIATE_CLASS`, `VectorSize.OPENAI_SMALL`, `DefaultTimeouts.DATABASE`) and imported from there to ensure a single source of truth.
    *   **Hardcoded `certainty` in `search` method:** The value `0.7` for `certainty` (minimum similarity threshold) is hardcoded in the `search` method. This should be a configurable value, possibly via a constant in `constants.py` or a setting in `Settings`.
    *   **Hardcoded schema definition in `_ensure_schema`:** The `materials_class` dictionary defining the Weaviate schema is hardcoded within the `_ensure_schema` method. This makes the schema less flexible for changes and does not align with the principle of avoiding hardcoded data.
        *   **Proposal:** Externalize the schema definition into an external file (e.g., JSON or YAML) or create a Pydantic model for the schema structure, which can then be loaded and used to create the Weaviate class. This would allow for schema management separate from the adapter's code.
    *   **Implicit `connect()` call in `search` and `upsert`:** Methods like `search` and `upsert` (and likely others) include an `if not self.client: await self.connect()` check. While providing resilience, this also means the adapter implicitly manages its own connection lifecycle.
        *   **Proposal:** Ensure the client is connected by the caller (e.g., `DatabaseFactory` or `PoolManager`) before the adapter instance is passed, or explicitly document this implicit connection behavior if it is a design choice for resilience. 

### core/database/adapters/pinecone_adapter.py

**Observations:**
*   **Positive aspects:**
    *   `pinecone_adapter.py` implements an adapter for Pinecone, inheriting from `IVectorDatabase`, aligning with the "Абстрактные интерфейсы (ABC) для БД операций" architectural pattern and ensuring a unified interface for vector databases.
    *   Includes all required vector repository methods: `create_collection`, `collection_exists`, `upsert`, `search`, `get_by_id`, `update_vector`, `delete`, `batch_upsert`, and `health_check`.
    *   Correctly uses `pinecone.init` for initialization and `pinecone.Index` for index interaction.
    *   Handles errors (`ConnectionError`, `DatabaseError`, `ConfigurationError`), converting Pinecone exceptions to custom types.
    *   Uses logging to track operations.
    *   Docstrings are well-defined and formatted.

*   **Potential areas for review/refactoring:**
    *   **Hardcoded default values in `__init__`:** In the `PineconeVectorDatabase` constructor, default values for `index_name` (`"materials"`), `vector_size` (`1536`), and `timeout` (`30`) are hardcoded in `config.get()` calls. This violates the "КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ" rule [[memory:581130]].
        *   **Proposal:** These default values should be sourced from `core/config/constants.py` (e.g., `DatabaseNames.PINECONE_INDEX`, `VectorSize.OPENAI_SMALL`, `DefaultTimeouts.DATABASE`) and imported from there to ensure a single source of truth.
    *   **Hardcoded metric in `pinecone.create_index`:** In the `connect` method, `metric="cosine"` is hardcoded during index creation. This value is hardcoded, whereas other adapters (e.g., Qdrant) allow for metric configuration.
        *   **Proposal:** The distance metric should be configurable via `config` and use a constant from `constants.py` if it's a default value.
    *   **Implicit `connect()` call:** Methods like `create_collection`, `collection_exists`, `search`, `upsert` (and likely others) include an `if not self.pinecone: await self.connect()` or `if not self.index: await self.connect()` check. As with Weaviate, this means the adapter implicitly manages its own connection lifecycle.
        *   **Proposal:** Ensure the client is connected by the caller (e.g., `DatabaseFactory` or `PoolManager`) before the adapter instance is passed, or explicitly document this implicit connection behavior.
    *   **`time` import within `connect` and `create_collection` methods:** The import of the `time` module is placed inside these methods. This is not a critical issue, but as mentioned previously, imports are generally placed at the top of the file for better readability and organization. 

### core/database/adapters/__init__.py

**Observations:**
*   **Positive aspects:**
    *   The `__init__.py` file serves its purpose well by re-exporting the various database adapter classes. This simplifies imports for other modules that need to access these adapters (e.g., `core/database/factories.py`).
    *   The `__all__` variable explicitly defines the public API of the `adapters` subpackage, which is good practice.
    *   The file is concise and clearly indicates its role.

*   **Potential areas for review/refactoring:**
    *   **No immediate issues based on current rules:** This file is well-structured and adheres to its intended purpose. It primarily acts as an export hub for adapters, which is a common and acceptable pattern. 

### `api/routes/` Directory Analysis

1.  **`api/routes/health_unified.py`**:
    *   **Positive:** Defines health check endpoints (`/health`, `/health/deep`), uses `Depends` for dependency injection, includes database availability checks (PostgreSQL, Qdrant, Redis), logs the status of each check, returns a detailed JSON response.
    *   **Potential for Refactoring:** Hardcoded error message strings (`"Failed to connect to PostgreSQL"`, `"Qdrant client not available"`) (extract to constants). Health check logic could be moved to a separate service for better separation of concerns.

2.  **`api/routes/materials.py`**:
    *   **Positive:** Defines endpoints for material management (`/materials`, `/materials/{material_id}`), uses `Depends` for the repository, Pydantic models for requests/responses, handles various HTTP methods (GET, POST, PUT, DELETE), includes field validation, handles exceptions, logs operations.
    *   **Potential for Refactoring:** Lack of pagination for `get_all_materials` endpoint (add pagination). Hardcoded HTTP status codes in `responses` (use `status` from `fastapi`). Business logic handling could be moved to a service layer. Duplication of CSV/Excel handling code (unify in one service).

3.  **`api/routes/prices.py`**:
    *   **Positive:** Defines endpoint for price list upload (`/prices/upload`), accepts CSV/Excel files, uses `FastAPI.UploadFile` and `BackgroundTasks`, injects dependencies for parser and processing service, logs the process, returns upload status.
    *   **Potential for Refactoring:** Lack of file size validation before starting upload. Lack of upload progress for the user. Hardcoded message strings (`"Price list processing started in background."`). File handling logic (reading, parsing) could be extracted to a separate service.

4.  **`api/routes/search_unified.py`**:
    *   **Positive:** Defines unified search endpoints (`/search`, `/search/vector`, `/search/sql`), uses `Depends` for the search service, Pydantic models for requests, handles various search types (vector, SQL LIKE, hybrid), includes error handling and empty results.
    *   **Potential for Refactoring:** Hardcoded values for `limit` and `offset` (use constants or query parameters). Query building logic could be more modular.

5.  **`api/routes/enhanced_processing.py`**:
    *   **Positive:** Defines endpoints for enhanced material processing (`/process/csv`), uses `BackgroundTasks` for asynchronous processing, injects dependencies for parser and repository, handles CSV files, logs the process.
    *   **Potential for Refactoring:** Similar to `prices.py`, lack of file size validation. Hardcoded message strings. Dependency on `material_parser_service.parse_materials_from_csv` (make more generic or move logic to service).

6.  **`api/routes/reference.py`**:
    *   **Positive:** Defines endpoints for retrieving reference data (`/units`, `/colors`, `/categories`), uses `Depends` for repositories, returns lists of data.
    *   **Potential for Refactoring:** Data retrieval logic could be moved to a separate service (e.g., `ReferenceService`) for better separation of concerns if data grows.

7.  **`api/routes/tunnel.py`**:
    *   **Positive:** Defines endpoint for SSH tunnel status check (`/tunnel/status`), uses `Depends` for SSH service, returns tunnel status and configuration, handles errors.
    *   **Potential for Refactoring:** Lack of endpoint protection (e.g., authentication) for sensitive information. Status retrieval logic could be expanded for more detailed diagnostics.

8.  **`api/routes/__init__.py`**:
    *   **Positive:** Central entry point for routes, imports all routes, explicitly defines `__all__`.
    *   **Potential for Refactoring:** No immediate refactoring needs.

**General Observations for `api/routes/`:**

*   **Security Rule Violations:** Some endpoints return or process data without explicit authentication/authorization, which may violate security rules. Endpoints related to configuration or status (e.g., `tunnel.py`) should be protected.
*   **Excessive Logic in Routes:** Some routes contain excessive business logic (e.g., file parsing, detailed data processing) that should ideally be moved to the service layer (`services/`).
*   **Hardcoded Values:** There are hardcoded message strings, limits, etc., that should be extracted into constants or configurable parameters.
*   **Error Handling:** While `try-except` blocks are present, it might be beneficial to implement a centralized FastAPI error handler for consistent responses.
*   **Code Duplication:** Minor code duplication exists for file handling (CSV/Excel) across different routes. 

### `services/` Directory Analysis

1.  **`services/advanced_search.py`**:
    *   **Positive:** Designed to implement advanced search functionalities (vector, SQL LIKE, hybrid), utilizes various repositories (vector, relational, cache), handles fallback strategies (`ENABLE_FALLBACK_DATABASES`), includes logic for search mode selection, has asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** Hardcoded values for `limit`, `offset`, `fallback_threshold` (extract to constants or configuration parameters). Search mode selection logic could be more flexible (e.g., via a factory method or strategy pattern). Duplication of search logic between different methods (`vector_search`, `sql_search`, `hybrid_search`).

2.  **`services/batch_processing_service.py`**:
    *   **Positive:** Designed for processing large volumes of data in the background, uses `DynamicBatchProcessor` and repositories, includes logic for queue processing, error handling, and retries, has asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** Hardcoded values for `batch_size`, `max_retries`, `retry_delay_seconds` (extract to constants). Lack of mechanism to pause/resume processing.

3.  **`services/collection_initializer.py`**:
    *   **Positive:** Designed for initializing collections in vector databases (Qdrant, Weaviate, Pinecone), uses `IVectorDatabase` and `PostgresqlAdapter` (for data retrieval), includes logic for checking collection existence and creation, asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** Hardcoded `collection_name`, `vector_size`, `distance_metric` (retrieve from constants or configuration). Data retrieval logic from PostgreSQL for initialization could be more abstract.

4.  **`services/combined_embedding_service.py`**:
    *   **Positive:** Designed for generating embeddings using various AI providers, uses `AIClientFactory`, includes logic for provider selection (OpenAI, Ollama), error handling, and retries, asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** Hardcoded values for `max_retries`, `retry_delay_seconds` (extract to constants). Provider selection logic could be more flexible.

5.  **`services/dynamic_batch_processor.py`**:
    *   **Positive:** Implements dynamic batch processing with adaptive batch size adjustment, uses `asyncio.Queue` and `asyncio.Lock`, includes performance monitoring and error handling logic, good docstrings.
    *   **Potential for Refactoring:** Hardcoded values for `initial_batch_size`, `max_batch_size`, `min_batch_size`, `adjustment_factor`, `cooldown_period`, `error_threshold` (extract to constants or configuration). Dependency on global `logger` instance (minor style).

6.  **`services/embedding_comparison.py`**:
    *   **Positive:** Designed for comparing embeddings, uses `CombinedEmbeddingService`, includes methods for cosine similarity calculation, has asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** No immediate refactoring needs.

7.  **`services/enhanced_parser_integration.py`**:
    *   **Positive:** Designed for integration with the enhanced parsing module, uses `MaterialParserService`, includes methods for file processing and result saving, asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** Dependency on specific file path (`file_path: Path`) (make more general for streams/byte data). Hardcoded message strings.

8.  **`services/material_processing_pipeline.py`**:
    *   **Positive:** Designed for implementing a material processing pipeline, uses `DynamicBatchProcessor`, `CombinedEmbeddingService`, repositories, includes extract, transform, load (ETL) logic, asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** Hardcoded values for `batch_size`, `max_retries` (extract to constants). Too many responsibilities in one class (consider splitting into smaller, specialized services).

9.  **`services/materials.py`**:
    *   **Positive:** Designed for material management, uses repositories (cache, hybrid, Redis), includes CRUD operation logic, CSV/Excel handling, asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** Significant duplication of CSV/Excel reading and parsing logic, which is also present in `api/routes/prices.py` and `api/routes/enhanced_processing.py` (extract to a separate utility or service class). Hardcoded message strings.

10. **`services/optimized_search.py`**:
    *   **Positive:** Designed for optimized search, uses `IVectorDatabase` and `PostgresqlAdapter`, includes logic for selecting search method (vector, SQL), handles errors, asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** Duplication of search logic with `services/advanced_search.py` (consolidate into one place). Hardcoded values for `limit`, `offset` (extract to constants).

11. **`services/price_processor.py`**:
    *   **Positive:** Designed for price list processing, uses repositories and `MaterialProcessingPipeline`, includes file parsing and data loading logic, asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** Duplication of file reading and parsing logic with `services/materials.py` (extract to a dedicated `FileProcessingService` class). Hardcoded message strings. Dependency on specific CSV/Excel column names.

12. **`services/sku_search_service.py`**:
    *   **Positive:** Designed for SKU search, uses `PostgresqlAdapter`, includes logic for exact match search, asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** No immediate refactoring needs.

13. **`services/ssh_tunnel_service.py`**:
    *   **Positive:** Designed for SSH tunnel management, uses `SSHTunnelManager`, includes logic for starting/stopping/checking tunnel status, handles errors, has asynchronous methods, good docstrings.
    *   **Potential for Refactoring:** Dependency on specific `ssh_tunnel.py` file path (could be more abstract). Hardcoded message strings. Lack of retry handling for connection.

14. **`services/__init__.py`**:
    *   **Positive:** Central entry point for services, imports all services, explicitly defines `__all__`.
    *   **Potential for Refactoring:** No immediate refactoring needs.

**General Observations for `services/`:**

*   **Code Duplication:** Significant duplication of search logic (`advanced_search.py`, `optimized_search.py`) and file processing logic (`materials.py`, `price_processor.py`, `enhanced_parser_integration.py`). This is a critical area for refactoring.
*   **Security Rule Violations:** Some services use hardcoded values that should be configurable (e.g., connection parameters, limits, timeouts, retry attempts).
*   **Over-responsibility:** Some services (e.g., `material_processing_pipeline.py`) perform too many tasks, which can make them harder to maintain and test.
*   **Hardcoded Values:** A large number of hardcoded values (limits, timeouts, batch sizes, collection names) that should be extracted into constants or configuration.
*   **Configuration Logic:** Some services depend on global `settings` objects or hardcoded values for database/AI client configuration.
*   **Testing:** Code duplication can complicate testing and lead to errors. 

### `core/dependencies/` Directory Analysis

1.  **`core/dependencies/database.py`**:
    *   **Positive:** Defines FastAPI dependency functions for databases (`get_db_session`, `get_vector_db`, `get_cache_db`), uses `yield` for session context management, includes `try-finally` to ensure session closure, encapsulates logic for getting DB clients.
    *   **Potential for Refactoring:** Dependency on global `get_db_client`, `get_vector_database`, `get_cache_database` functions from `core.database.factories` (possibly pass them as arguments during application initialization for better testability and inversion of control).

2.  **`core/dependencies/tunnel.py`**:
    *   **Positive:** Defines FastAPI dependency function for SSH tunnel (`get_ssh_tunnel_service`), uses `Depends` to inject `SSHTunnelService`, includes `try-except` for handling errors when getting the service.
    *   **Potential for Refactoring:** If the SSH tunnel is a critical dependency, consider a more robust mechanism for checking its health on each request or treat it as a background task.

3.  **`core/dependencies/__init__.py`**:
    *   **Positive:** Central entry point for dependencies, re-exports key dependency functions, explicitly defines `__all__`.
    *   **Potential for Refactoring:** No immediate refactoring needs.

**General Observations for `core/dependencies/`:**

*   **Positive:** Good use of FastAPI's dependency mechanism, promoting modularity and testability. Ensure proper resource management (session closure).
*   **Potential for Refactoring:** The main area to consider is how global database factories or clients are passed into these dependency functions. While `Depends` is a good way to manage, direct global calls could make mocking for unit tests harder. 

### `core/repositories/` Directory Analysis

1.  **`core/repositories/base.py`**:
    *   **Positive:** Defines a `BaseRepository` abstract base class with generic CRUD operations (`add`, `get`, `update`, `delete`, `all`), uses `AsyncSession` for asynchronous database interactions, includes basic error handling, and provides good docstrings.
    *   **Potential for Refactoring:** No immediate refactoring needs. This is a solid base class.

2.  **`core/repositories/cached_materials.py`**:
    *   **Positive:** Implements a repository that combines a cache (`ICacheDatabase`) and a relational database (`IRelationalDatabase`) for materials, includes methods for adding/retrieving/updating/deleting materials with caching logic, uses `Pydantic` models for data, and has good docstrings.
    *   **Potential for Refactoring:** Cache invalidation strategy could be more explicit or configurable (e.g., time-based expiration). The `_get_from_cache` and `_set_to_cache` methods could be made more generic or encapsulated within a cache utility. Hardcoded cache expiration time (if any) should be moved to constants.

3.  **`core/repositories/hybrid_materials.py`**:
    *   **Positive:** Implements a hybrid repository that combines a vector database (`IVectorDatabase`) and a relational database (`IRelationalDatabase`) for materials, includes methods for adding/retrieving/updating materials with embedding generation and vector storage, uses `Pydantic` models for data, and has good docstrings.
    *   **Potential for Refactoring:** The coupling between the relational and vector database operations within a single method (`add`, `update`) could be slightly reduced (e.g., by using a domain service that orchestrates these calls). Error handling for vector database operations might need to be more robust, especially if the vector database is optional.

4.  **`core/repositories/interfaces.py`**:
    *   **Positive:** Correctly defines an abstract base class (`IMaterialRepository`) for material-related operations, includes abstract methods for common CRUD and search operations, and provides good docstrings.
    *   **Potential for Refactoring:** No immediate refactoring needs. This interface is well-defined.

5.  **`core/repositories/redis_materials.py`**:
    *   **Positive:** Implements a Redis-specific repository for materials, inherits from `IMaterialRepository`, uses `ICacheDatabase` for Redis interactions, includes methods for CRUD operations directly on Redis, and has good docstrings.
    *   **Potential for Refactoring:** Hardcoded cache expiration time (if any) should be moved to constants. The serialization/deserialization logic might be duplicated with the Redis adapter. 

### `core/schemas/` Directory Analysis

1.  **`core/schemas/materials.py`**:
    *   **Positive:** Defines Pydantic models for materials (`MaterialBase`, `MaterialCreate`, `MaterialResponse`, `MaterialUpdate`), uses `Field` for field descriptions and examples, clearly separates schemas for creation, update, and responses, includes data validation.
    *   **Potential for Refactoring:** Hardcoded `max_length`, `example` strings (extract to constants or `constants.py` if needed).

2.  **`core/schemas/colors.py`**:
    *   **Positive:** Defines Pydantic model for colors (`ColorSchema`), uses `Field` for field descriptions and examples.
    *   **Potential for Refactoring:** No immediate refactoring needs.

3.  **`core/schemas/enhanced_parsing.py`**:
    *   **Positive:** Defines Pydantic models for enhanced processing and parsing (`ParseMaterialRequest`, `ParsedMaterialResponse`, `ProcessingResultResponse`), uses `Field` for field descriptions and examples, includes data validation.
    *   **Potential for Refactoring:** Hardcoded `example` strings (extract to constants).

4.  **`core/schemas/pipeline_models.py`**:
    *   **Positive:** Defines Pydantic models for the processing pipeline (`ProcessingPipelineStage`, `ProcessingPipelineStatus`, `MaterialPipelineStage`, `PipelineMaterial`, `PipelineError`, `PipelineResult`), uses `Enum` for statuses, includes data validation, and has good docstrings.
    *   **Potential for Refactoring:** Hardcoded `example` strings (extract to constants).

5.  **`core/schemas/processing_models.py`**:
    *   **Positive:** Defines Pydantic models for processing results (`ProcessingResultBase`, `ProcessingResultCreate`, `ProcessingResultResponse`), uses `Field` for field descriptions and examples, clearly separates schemas for creation and responses, includes data validation.
    *   **Potential for Refactoring:** Hardcoded `example` strings (extract to constants).

6.  **`core/schemas/response_models.py`**:
    *   **Positive:** Defines common Pydantic models for API responses (`HealthCheckResponse`, `UploadStatusResponse`, `MessageResponse`, `ErrorResponse`), includes useful fields like `status`, `message`, `details`, and has good docstrings.
    *   **Potential for Refactoring:** Hardcoded `example` strings (extract to constants).

7.  **`core/schemas/__init__.py`**:
    *   **Positive:** Central entry point for schemas, re-exports key Pydantic models, explicitly defines `__all__`.
    *   **Potential for Refactoring:** No immediate refactoring needs.

**General Observations for `core/schemas/`:**

*   **Positive:** Consistent use of Pydantic for data model definition and validation, adhering to "Data Formats" and "Pydantic models: mandatory examples" rules. Good separation of schemas by domain area.
*   **Potential for Refactoring:** The main area for improvement is extracting all hardcoded string examples and some numerical constraints (e.g., `max_length`) into centralized constants to avoid duplication and facilitate modification. 