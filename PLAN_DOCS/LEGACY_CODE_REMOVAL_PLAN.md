# Legacy Code Removal Plan

> Status: **Draft** (generated automatically – _review & approve before execution_)

---

## 1. Purpose
This document outlines a systematic approach for identifying and eliminating **legacy code** from the repository `rag-stroyactiv-pyton`.  The project is still in a solution-seeking phase, therefore legacy artefacts add unnecessary maintenance overhead and technical debt.

## 2. Definition of "Legacy" for this project
1. **Backup copies or duplicated modules** that were superseded by refactored code but are still kept under directories such as `backup/`.
2. **Temporary compatibility shims** (e.g. `core/config.py`) introduced to ease migration.
3. **Fallback import paths** that reference backup packages (e.g. `importlib.import_module("backup.core.*")`).
4. **Deprecated tests** exclusively covering legacy code.
5. **Old API endpoints / services** that are no longer part of the current architecture (e.g. duplicated middleware, obsolete tunnels).

## 3. Inventory of Legacy Code
| Category | Path / Pattern | Notes |
|----------|----------------|-------|
| Directory | `backup/` | Full copy of old *core* subsystem (middleware, monitoring, etc.) |
| File | `core/config.py` | Compatibility wrapper – original config was modularised into `core/config/**` |
| Module duplicates | `core/middleware/request_logging.py` vs. `core/logging/.../request_logging_middleware.py` | Two implementations – one to be kept (new logging system) |
| Fallback imports | `core/monitoring/metrics.py` | Dynamically imports `backup.core.monitoring.metrics` if new implementation missing |
| Tests | Multiple tests in `tests/` referencing `backup.core` or the shim in `core/config.py` | Need to be updated/removed once legacy code is gone |

> A full grep report of files importing `backup.core` is provided at the bottom of this plan.

## 4. Risk Assessment
* **Medium**: Deleting legacy modules may break runtime if some paths still rely on them.
* **Low**: No production deployment yet, so breakage risk is limited to local development & CI.

## 5. Removal Strategy (High-Level)
1. **Freeze the current main branch** – create `legacy-removal` feature branch.
2. **Replace all remaining runtime dependencies** on legacy code with their modern equivalents.
   * Refactor any `importlib.import_module("backup.core…")` fallbacks.
   * Migrate code that still imports `core.config` (shim) to direct imports from the new modular config package.
3. **Run test suite** – ensure no regressions (green baseline before deletion).
4. **Delete backup directory** and remove shim `core/config.py`.
5. **Update tests** – remove mocks around `core.config`, adjust paths if necessary.
6. **Run static analysis & linters** – ensure no unresolved imports remain.
7. **Update documentation** – delete references to legacy modules.
8. **Open Pull Request** – include migration guide in `CHANGELOG.md`.

## 6. Detailed Task Breakdown
### 6.1  Identify & Migrate Legacy Imports
- [ ] Search for `"backup.core"` imports and refactor (see Appendix A).
- [ ] Search for `"from core.config import"` in non-config files; replace with explicit imports from `core.config.*` sub-modules (e.g. `from core.config.base import settings`).
- [ ] Remove dynamic fallback logic in:
  - `core/monitoring/metrics.py`
  - any similar helper utilities.

### 6.2  Drop Compatibility Shim `core/config.py`
- [ ] Ensure **all** modules use new config API.
- [ ] Delete file and run `pytest`.

### 6.3  Remove `backup/` Directory
- [ ] Delete directory.
- [ ] Check for missing assets (e.g. test fixtures) that might reside inside and migrate if needed.

### 6.4  Update Tests
- [ ] Adjust fixtures & mocks that patch `core.config`.
- [ ] Remove tests that exclusively validate legacy behaviour.

### 6.5  Documentation & Changelog
- [ ] Add section "Removed legacy code" to `CHANGELOG.md` (BREAKING change if public API altered).
- [ ] Update any guides referencing backup modules.

### 6.6  CI Pipeline
- [ ] Ensure pre-commit hooks & CI scripts do not reference deleted modules.
- [ ] Validate OpenAPI generation after removal.

## 7. Timeline & Milestones
| Milestone | Owner | ETA |
|-----------|-------|-----|
| Branch `feature/legacy-removal` created | — | Day 0 |
| Imports refactored & tests passing | — | Day 1 |
| Legacy directories deleted | — | Day 2 |
| Documentation updated | — | Day 2 |
| Pull Request merged | — | Day 3 |

## 8. Appendix A – Current Legacy Import References
<!-- Auto-generated grep snippet (abridged) -->
```text
core/monitoring/metrics.py:11:_backup_metrics: ModuleType = importlib.import_module("backup.core.monitoring.metrics")
core/monitoring/metrics.py:15:_backup_metrics: ModuleType = importlib.import_module("backup.core.monitoring.metrics")
```
_Rerun `grep -R "backup.core" *.py` to ensure list is up-to-date._

---

*Generated on $(date +'%Y-%m-%d %H:%M:%S') by AI assistant.* 