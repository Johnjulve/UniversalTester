# Changelog

All notable changes to the UniversalTester project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
### Added
- **Universal Python Adapter**: Created `adapters/python_adapter.py` providing dynamic runner detection across Django `manage.py test`, `pytest`, and `unittest discover`, configurable simulation scenario dispatch, and structured reporting.
- **Smart Runner Detection in Node Adapter**: Upgraded `adapters/node_adapter.py` to inspect `package.json.scripts`, gracefully returning `TestResult.unavailable()` when tests are omitted, and auto-detecting Vitest (`--run`) vs Jest (`--watchAll=false`).
- **Consolidated Multi-Suite Reporter**: Added `render_overall_summary()` in `core/reporter.py` to render ANSI-aligned overall summary tables that handle unavailable capabilities without unfairly degrading overall system health grades.
- **Phase 3 Automated Verification Suite**: Added `tests/test_phase_3.py` validating dual adapter discovery, non-blocking flags, and reporter metrics.

### Changed
- **Subclassed Django Adapter**: Refactored `adapters/django_adapter.py` to inherit from `PythonAdapter`, preserving full backwards compatibility while inheriting multi-runner capabilities.
- **Registry Dynamic Resolution**: Updated `adapters/registry.py` and `adapters/__init__.py` to register and export `PythonAdapter` and its ecosystem aliases (`fastapi`, `flask`, `pytest`).
- **Framework-Agnostic CLI Path Detection**: Updated `tester.py` custom project path handler to leverage `detect_adapter()` instead of hardcoded framework file checks.

### Fixed
- **Dataclass Field Shadowing**: Resolved method collision in `core/models.py` where `@classmethod def skipped` shadowed dataclass field `skipped: int = 0`, renaming method to `skipped_result()` and adding `passed_result()`.


## [1.0.0] - 2026-09-07

### Added
- **Analytical Test Reporter**: Built `core/reporter.py` providing hierarchical module tree rendering, ANSI-aligned summary tables, and system health grades.
- **Universal CS Algorithm Benchmark**: Built framework-agnostic stress benchmark in `Performance/test_algorithms.py` (Quicksort, Mergesort, Binary Search, SHA-256 throughput, JSON aggregation).
- **Portable Launchers**: Added auto-detection of local `.venv`/`env` and system Python in `run.ps1` and `run.cmd`.
- **Configuration Templates**: Created `tester_config.example.json` and project manifest `requirements.txt`.
- **Native System Health Check**: Added universal platform, CPU, Python runtime, and disk space health check in `adapters/base.py`.
- **Agent SDLC Rules**: Installed custom `.agents/rules` and `.agents/skills` for continuous architecture and documentation synchronization.

### Changed
- Overhauled test selection menu in `tester.py` to reflect the two-pillar hybrid architecture (Ecosystem Unit Tests vs. Native Benchmarks & Simulations).
- Sanitized concurrency traffic prompts to generic concurrent user volume (50 to 1,000 users/reqs), completely removing legacy election terminology.
- Decoupled terminal branding to generic `⚡ UNIVERSAL TEST & SIMULATION ENGINE`.
- Removed legacy thesis imports and hardcoded path assumptions across all adapters.

### Removed
- Removed project-specific thesis directories (`UAT/`, `Security/`, `System/`) and obsolete performance scripts (`quick_performance_test.py`, `performance_tests.py`, `locustfile.py`) to eliminate thesis bias and keep UniversalTester generic and production-ready.

