# Changelog

All notable changes to the UniversalTester project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
### Added
- **Lean Security Tester**: Built `core/security.py` featuring an AST-based static vulnerability scanner (detecting hardcoded secrets, SQL injection patterns, dangerous `eval`/`exec`/`os.system`, and insecure shell execution) and ecosystem dependency audit delegation (`npm audit`, `pip-audit`, `safety`).
- **Master 5-Pillar Test Orchestrator**: Built `core/orchestrator.py` coordinating the 5 official testing pillars (Adaptive, Algorithm, Performance, Reliability, Security) and rendering consolidated overall system health scorecards.
- **Scriptable CLI Subcommand Dispatch**: Updated `tester.py` to support direct, non-interactive CLI subcommand invocations (`python tester.py [adaptive|algo|perf|reliability|security|all]`) with exit code signaling for CI/CD pipelines.
- **Phase 5 Automated Verification Suite**: Added `tests/test_phase_5.py` covering static vulnerability detection, placeholder exclusions, zero false-positives on clean code, capability integration, and orchestrator dispatch routing.
- **Universal Python Adapter**: Created `adapters/python_adapter.py` providing dynamic runner detection across Django `manage.py test`, `pytest`, and `unittest discover`, configurable simulation scenario dispatch, and structured reporting.
- **Smart Runner Detection in Node Adapter**: Upgraded `adapters/node_adapter.py` to inspect `package.json.scripts`, gracefully returning `TestResult.unavailable()` when tests are omitted, and auto-detecting Vitest (`--run`) vs Jest (`--watchAll=false`).
- **Consolidated Multi-Suite Reporter**: Added `render_overall_summary()` in `core/reporter.py` to render ANSI-aligned overall summary tables that handle unavailable capabilities without unfairly degrading overall system health grades.
- **Phase 3 Automated Verification Suite**: Added `tests/test_phase_3.py` validating dual adapter discovery, non-blocking flags, and reporter metrics.

### Changed
- **Subclassed Django Adapter**: Refactored `adapters/django_adapter.py` to inherit from `PythonAdapter`, preserving full backwards compatibility while inheriting multi-runner capabilities.
- **Registry Dynamic Resolution**: Updated `adapters/registry.py` and `adapters/__init__.py` to register and export `PythonAdapter` and its ecosystem aliases (`fastapi`, `flask`, `pytest`).
- **Framework-Agnostic CLI Path Detection**: Updated `tester.py` custom project path handler to leverage `detect_adapter()` instead of hardcoded framework file checks.

### Added
- **Dynamic Virtual Environment Resolution**: Added `_resolve_python_environment()` in `adapters/python_adapter.py` scanning backend, root, and parent directories for `.venv`, `venv`, `env`, etc., with framework-aware dependency verification.
- **Early Crash Diagnostics**: Added error output capture in `adapters/python_adapter.py` to display raw Python traces when a test runner exits with an error before emitting test results.
- **Multiline Docstring Test Parser**: Enhanced `AnalyticalTestReporter` in `core/reporter.py` to correctly parse standard Python unittest multiline docstring test outputs and synchronize test pass counts.

### Changed
- **CLI Custom Path Subfolder Inversion**: Enhanced `tester.py` to allow pasting directly to `/backend`, `/server`, or `/frontend` subdirectories, automatically resolving root directories and removing hardcoded system Python defaults.

### Fixed
- **Dataclass Field Shadowing**: Resolved method collision in `core/models.py` where `@classmethod def skipped` shadowed dataclass field `skipped: int = 0`, renaming method to `skipped_result()` and adding `passed_result()`.
- **Silent Test Failures**: Fixed issue where missing framework packages in global Python caused 0-test runs to silently report as `○ UNAVAIL` without diagnostic errors.


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

