# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
### Removed
- Legacy compatibility shim `core/config.py`.
- Entire `backup/` directory containing outdated monitoring and middleware code.
- Dynamic fallback import from `core/monitoring/metrics.py` to legacy backup module.

### Added
- `PLAN_DOCS/LEGACY_CODE_REMOVAL_PLAN.md` – detailed plan for removing legacy code.

### Changed
- `core/monitoring/metrics.py` now directly re-exports canonical metrics without fallbacks.

--- 