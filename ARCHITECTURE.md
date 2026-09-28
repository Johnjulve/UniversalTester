# 🏗️ UniversalTester (`testx`) Architecture & Extension Guide

> **Version 1.1.0** • Master 5-Pillar Architecture

**UniversalTester** coordinates software quality across five complementary disciplines through a **Hybrid Two-Pillar Engine**:
1. **Pillar 1: Native Test & Benchmark Engine**: Self-contained, framework-agnostic algorithms, mathematical stress models, system health diagnostics, concurrency traffic simulations, and static AST security auditing operating purely on the Python Standard Library.
2. **Pillar 2: Language & Framework Adapter System**: Modular delegates that discover, invoke, and normalize existing ecosystem test runners (`pytest`, `vitest`, `jest`, `manage.py`) into standardized [TestResult](file:///d:/System%20Projects/UniversalTester/core/models.py) objects.

---

## 🏛️ Master 5-Pillar Architecture Diagram

```text
                           [ CLI Interface: testx / tester.py ]
                                           │
                                           ▼
                     [ Master Test Orchestrator (core/orchestrator.py) ]
                                           │
          ┌────────────────────────────────┴────────────────────────────────┐
          ▼                                                                 ▼
┌───────────────────────────────────────┐       ┌───────────────────────────────────────┐
│        Native Testing Engines         │       │       Language & Adapter System       │
├───────────────────────────────────────┤       ├───────────────────────────────────────┤
│ • Pillar 2: Algorithm Tester          │       │ • Pillar 1: Adaptive Tester           │
│   (Performance/algorithm_tester.py)   │       │   (adapters/python_adapter.py)        │
│ • Pillar 3: Performance Profiler      │       │   (adapters/node_adapter.py)          │
│   (Latency + tracemalloc RAM)         │       │ • Capability Matrix                   │
│ • Pillar 4: Reliability Tester        │       │   (Capability.ADAPTIVE, SECURITY,...) │
│   (Performance/reliability_tester.py) │       │ • Ecosystem Registry                  │
│ • Pillar 5: Security Scanner          │       │   (adapters/registry.py)              │
│   (core/security.py - AST + Audit)    │       │                                       │
└───────────────────────────────────────┘       └───────────────────────────────────────┘
          │                                                                 │
          └────────────────────────────────┬────────────────────────────────┘
                                           ▼
                            [ Standardized TestResult Model ]
                                    (core/models.py)
                                           │
                                           ▼
                              [ Analytical Test Reporter ]
                                    (core/reporter.py)
                                           │
                                           ▼
                         [ ANSI Aligned Summary & Grade A+ ]
```

---

## 📋 The 5 Official Testing Pillars

UniversalTester organizes all testing operations into five standardized pillars:

| Pillar | Scope | Implementation | Output Contract |
| :---: | :--- | :--- | :--- |
| **`[1] Adaptive`** | Target project's native unit, component & integration tests | `PythonAdapter`, `NodeAdapter` delegating to `pytest`, `manage.py test`, `vitest`, `jest` | Normalized `TestResult` with pass/fail/skip counts |
| **`[2] Algorithm`** | Algorithmic correctness assertions comparing actual vs expected outputs | Quicksort, Mergesort, Binary Search, SHA-256 NIST vectors, JSON math | `TestResult` asserting mathematical precision |
| **`[3] Performance`** | Computational latency benchmarks and peak memory consumption | `time.perf_counter()` duration (ms) + `tracemalloc` peak RAM (KB/MB) | Memory delta and cryptographic MB/s metrics |
| **`[4] Reliability`** | Concurrency capacity, saturation limits, and degradation tiers | 50 to 2,000+ users, traffic profiles (`read_heavy`, `write_heavy`, `balanced_api`, `burst_ping`) | Hardware degradation status (`OPTIMAL` to `CRITICAL`) |
| **`[5] Security`** | Static vulnerability pattern scanning & ecosystem audit delegation | Static AST scanner for secrets, SQLi, unsafe `eval`/`exec`/`os.system` + `npm audit`/`pip-audit`/`safety` | Severity findings (`HIGH`, `MEDIUM`, `LOW`) |
| **`[6] Full Audit`** | Sequential execution of Pillars 1 through 5 | `TestOrchestrator.run_all_pillars()` | Consolidated ANSI scorecards with overall health grade |

---

## 🔌 Creating a New Framework Adapter

Any new language or framework adapter inherits from [`BaseAdapter`](adapters/base.py) and overrides the capability methods:

```python
import subprocess
from adapters.base import BaseAdapter, Capability
from core.models import TestResult

class GoAdapter(BaseAdapter):
    """Adapter for Go projects using 'go test'."""

    @classmethod
    def applies(cls, project_path: str) -> bool:
        import os
        return os.path.exists(os.path.join(project_path, "go.mod"))

    @classmethod
    def adapter_id(cls) -> str:
        return "go"

    def supported_capabilities(self) -> list:
        return [
            Capability.ADAPTIVE,
            Capability.ALGORITHMS,
            Capability.PERFORMANCE,
            Capability.RELIABILITY,
            Capability.SECURITY
        ]

    def run_components_test(self) -> TestResult:
        res = subprocess.run(["go", "test", "./..."], cwd=self.project_path, capture_output=True, text=True)
        return TestResult(
            suite_name="Go Unit Tests",
            status="PASS" if res.returncode == 0 else "FAIL",
            raw_output=res.stdout + res.stderr
        )
```

### Steps to Register a New Adapter:
1. Create `adapters/<name>_adapter.py` inheriting from `BaseAdapter`.
2. Register the adapter class in `adapters/registry.py` and `adapters/__init__.py`.
3. Add a project definition in `tester_config.json` (or use `tester_config.example.json` as a guide).

---

## 📊 Analytical Output & Reporting Architecture

All test streams pass through [`core/reporter.py`](core/reporter.py):
- **ANSI-Aware Padding**: Column widths account for terminal control codes, keeping table borders (`┌─┬─┐`, `│`, `└─┴─┘`) laser-aligned across Windows Terminal, PowerShell, and Unix bash.
- **Graceful Unavailability Handling**: When a project lacks a specific test runner or configuration (e.g. static HTML lacking API concurrency), the suite renders `[○ UNAVAILABLE]` without penalizing the overall system health grade.
- **Grading Matrix**: Health grades are awarded dynamically:
  - **Grade A+**: 100% active tests passing.
  - **Grade A / B**: 90%–99% passing with minor failures.
  - **Grade C / D**: 70%–89% passing.
  - **Grade F**: Critical failures (<70% passing or critical vulnerability finding).
