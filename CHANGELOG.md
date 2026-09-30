# Changelog

All notable changes to the UniversalTester project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added
- **Hexagonal Architecture (Core + Adapters)**:
  - Built `TesterService` in `core/service.py` providing an in-process programmatic API ("call a function, get structured result") with zero HTTP dependencies.
  - Added serializable dataclasses `RunRequest` and `RunResult` in `core/models.py` for structured input/output contracts.
  - Added `ProgressEvent` and `EventHandler` callback protocol in `core/events.py` for real-time progress streaming.
- **Modular CLI Package (`cli/`)**:
  - Implemented `cli/parser.py` supporting `testx run [PROJECT] [--pillar P] [--users U] [--json]`, `testx bench`, `testx matrix`, and `testx doctor`.
  - Implemented `cli/interactive.py` rendering terminal menus dynamically generated from `TesterService.list_capabilities()`.
  - Implemented `cli/main.py` master dispatcher and refactored root `tester.py` to a thin 16-line launcher.
- **Cross-Platform Desktop GUI (`gui/`)**:
  - Created desktop application for Windows and Linux built purely on Standard Library `tkinter`/`ttk`.
  - Built `AsyncTestRunner` in `gui/worker.py` for non-blocking background test execution with live event queue streaming.
  - Built visual project selector, dynamic capability sidebar, real-time progress bar, live execution console, and results cards.
- **Packaging & Entrypoints**:
  - Registered `testx-gui = "gui.main:main"` in `pyproject.toml` and updated package discovery to include `cli*` and `gui*`.
- **Phase 8 Verification Suite**:
  - Added `tests/test_phase_8.py` with 12 unit tests validating data contracts, service facade, CLI parser, and GUI async worker.


## [1.2.0] - 2026-09-28


### Added
- **Cross-Language Benchmark Matrix**: Multi-runtime algorithm benchmark engine evaluating Python, Node.js (V8), and Dart SDK side-by-side in an ANSI-aligned terminal comparison table.
- **4 Expanded Algorithmic Workloads**:
  - *Heap Sort*: In-place min/max heapify tracking swap counts, comparisons, and peak memory.
  - *Hash Table Lookups*: $O(1)$ lookup latency benchmark matching $100\text{k}$ dataset size.
  - *Fibonacci*: Dual execution comparing naive recursive vs. $O(N)$ linear memoized speedup with runaway call stack protection ($N \le 32$).
  - *Monte Carlo $\pi$*: High-throughput point sampling measuring mathematical error ($|\pi_{\text{est}} - \pi|$) and samples/sec with sample-size adaptive statistical tolerance.
- **Standardized Benchmark Contract Schema**: Created `Performance/contracts/algo_result_schema.json` enforcing uniform JSON outputs across all language backends.
- **Multi-Runtime Runners**: Built pure standard-library runners in Python (`algo_bench.py`), Node.js (`algo_bench.js`), and Dart (`algo_bench.dart`).
- **Phase 7 Automated Verification Suite**: Added `tests/test_phase_7.py` validating schema compliance and mathematical assertions across all 3 language backends.


## [1.1.0] - 2026-09-28

### Added
- **Standalone Packaging & testx Entrypoint**: Added `pyproject.toml` with PEP 518/621 compliance, declaring package metadata, 0 external dependencies (Standard Library purity), and `[project.scripts] testx = "tester:main"`.
- **Lean Security Tester**: Built `core/security.py` featuring an AST-based static vulnerability scanner (detecting hardcoded secrets, SQL injection patterns, dangerous `eval`/`exec`/`os.system`, and insecure shell execution) and ecosystem dependency audit delegation (`npm audit`, `pip-audit`, `safety`).
- **Master 5-Pillar Test Orchestrator**: Built `core/orchestrator.py` coordinating the 5 official testing pillars (Adaptive, Algorithm, Performance, Reliability, Security) and rendering consolidated overall system health scorecards.
- **Scriptable CLI Subcommand Dispatch**: Updated `tester.py` to support direct, non-interactive CLI subcommand invocations (`testx [adaptive|algo|perf|reliability|security|all]`) with exit code signaling for CI/CD pipelines.
- **Phase 5 Automated Verification Suite**: Added `tests/test_phase_5.py` covering static vulnerability detection, placeholder exclusions, zero false-positives on clean code, capability integration, and orchestrator dispatch routing.
- **Phase 4 Reliability & Performance Engine**: Upgraded `Performance/reliability_tester.py` and `Performance/algorithm_tester.py` with generic web API traffic profiles, over-capacity boundary simulation, mathematical degradation tiers, algorithm correctness assertions, and `tracemalloc` memory profiling.
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

