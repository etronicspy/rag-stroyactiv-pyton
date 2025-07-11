# ADR: Parser Module Integration

Date: 2024-10-01

## Context
The `parser_module` is currently a separate directory with hacky imports via `sys.path` in `services/enhanced_parser_integration.py`, which violates modularity and can cause import issues. Integrating it into the main structure will improve maintainability, allow better dependency injection, and align with project rules like no hardcoded values and documentation-first.

## Decision
Integrate `parser_module` into a new `core/parsers/` directory. Rename files to avoid conflicts (e.g., `parser_config.py` to `parser_config_service.py`). Adapt code to use `core/config/` for settings, add logging, Pydantic validation, and tests. Update dependent files and documentation.

## Consequences
- Positive: Cleaner imports, better integration with core services, improved testability.
- Negative: Minor refactoring effort; potential temporary breaking changes (mitigated by tests).
- Risks: Import errors during transition; mitigated by thorough testing and backward compatibility. 