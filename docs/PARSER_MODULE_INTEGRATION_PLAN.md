# Parser Module Integration Plan

## Overview
This plan outlines the steps to integrate the `parser_module` into the main project structure, eliminating import hacks and ensuring compliance with project architecture (e.g., modularity in `core/parsers/`, dependency injection, Pydantic validation, and documentation-first approach).

**Goals:**
- Integrate into `core/parsers/` or `services/` for better modularity.
- Remove sys.path hacks and ensure clean imports.
- Maintain backward compatibility, update docs and tests.
- Adhere to rules: no hardcoded values, Pydantic validation, logging, health checks.
- Estimated time: 4-6 hours.

**Proposed Structure After Integration:**
- New directory: `core/parsers/` (for parsing logic).
- Update `enhanced_parser_integration.py` for direct imports.
- Remove original `parser_module/` post-integration.

## Step 1: Preparation (30-60 minutes)
**Status: Completed on 2024-10-01**
- Created branch `feature/parser-module-integration` from `main` (since `develop` doesn't exist).
- Analyzed files: No critical filename conflicts found (script not available, manual check); recommended renames for `parser_config.py` etc.
- Dependencies: No hardcoded keys; configs use env vars and are ready for core/config integration.
- Created ADR: `docs/adr/20241001-parser-module-integration.md`.
- Updated `docs/ARCHITECTURE.md` (created new) and created `core/parsers/README.md`.

## Step 2: Refactoring and File Transfer (1-2 hours)
- Create target directory: `core/parsers/`.
- Transfer and rename files:
  - `parser_module/ai_parser.py` → `core/parsers/ai_parser.py` (add ABC interface if needed).
  - `parser_module/material_parser.py` → `core/parsers/material_parser_service.py`.
  - `parser_module/parser_config.py` → `core/parsers/parser_config_service.py`.
  - `parser_module/system_prompts.py` → `core/parsers/system_prompts.py`.
  - `parser_module/units_config.py` → `core/parsers/units_config.py`.
  - Integrate `__init__.py` for exports.
- Adapt code:
  - Use dependency injection with `@lru_cache` in `core/config/factories.py`.
  - Add Pydantic validation for inputs.
  - Integrate logging with `core/logging/`.
  - Replace hardcoded values with constants from `core/config/constants.py`.
- Update imports: In `services/enhanced_parser_integration.py`, remove sys.path and use direct imports.

## Step 3: Integration and Optimization (1 hour)
- Update dependent files: Adjust imports in `services/material_processing_pipeline.py` and `services/__init__.py`.
- Add health check in `core/monitoring/` for AI API.
- Security: Add rate limiting via `core/middleware/rate_limiting.py`; validate inputs.
- Performance: Add batching if applicable.

## Step 4: Documentation and CHANGELOG (30-60 minutes)
- Update docs: Add to `docs/API_DESIGN.md`, `docs/ARCHITECTURE.md`; ensure docstrings (Google style).
- CHANGELOG.md: Add under "Changed" (minor version).
- OpenAPI: Update schemas in `core/schemas/` if affected.

## Step 5: Testing (1-2 hours)
- Unit tests: Create `tests/unit/test_parsers.py` with pytest and mocks.
- Integration tests: Update/create `tests/integration/test_parser_integration.py`.
- Functional tests: Check end-to-end in `tests/functional/`.
- Run `pytest`; ensure >80% coverage.
- Check conflicts: Run `make check-conflicts`.

## Step 6: Review, Merge, and Cleanup (30 minutes)
- Create PR to `develop`: Include description, tests, ADR link.
- Review: Ensure PEP 8, type hints, no hardcoded.
- Merge with squash.
- Cleanup: Remove `parser_module/` (commit: `chore(cleanup): remove legacy parser_module`).
- Post-merge: Update `requirements.txt` if needed.

## Risks and Mitigation
- Breaking changes: Test backward compatibility.
- Filename conflicts: Use prefixes like `parser_`.
- Import issues: Add exports to `core/__init__.py` if needed.

This plan aligns with project rules and architecture. Date: [Insert Date] 