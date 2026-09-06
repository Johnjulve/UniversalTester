# 🏗️ UniversalTester (`testx`) Architecture & Extension Guide

**UniversalTester** is architected around a **Two-Pillar Hybrid Design**:
1. **Pillar 1: Native Test Engine**: Self-contained, framework-agnostic algorithms, mathematical stress models, system health diagnostics, and concurrency simulations operating purely on the Python Standard Library.
2. **Pillar 2: Language & Framework Adapter System**: Modular delegates that discover, invoke, and normalize existing ecosystem test runners (`pytest`, `vitest`, `jest`, `junit`, `phpunit`) into a standardized result contract.

---

## 🏛️ Core Architecture Diagram

```text
               [ CLI Interface (tester.py / testx) ]
                                 │
                                 ▼
              [ Test Orchestrator & Menu Controller ]
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌───────────────────────────────┐     ┌───────────────────────────────────┐
│     Native Test Engine        │     │          Adapter System           │
├───────────────────────────────┤     ├───────────────────────────────────┤
│ • CS Stress Benchmarks        │     │ • adapters/base.py (Contract)     │
│   (Quicksort, Binary Search,  │     │ • adapters/django_adapter.py      │
│    SHA-256 throughput, JSON)  │     │ • adapters/node_adapter.py        │
│ • Concurrency Traffic Model   │     │ • Future: Python, Java, PHP, Go   │
│ • System & Host Health Check  │     │   (delegates to pytest, vitest)   │
└───────────────────────────────┘     └───────────────────────────────────┘
         │                                               │
         └───────────────────────┬───────────────────────┘
                                 ▼
                 [ Analytical Test Reporter ]
                     (core/reporter.py)
                                 │
                                 ▼
               [ Module Tree & Metrics Dashboard ]
```

---

## 📋 The 5 Execution Modes

UniversalTester organizes test workloads into five distinct suites:

| Key | Suite Name | Type | Description |
| :---: | :--- | :---: | :--- |
| **`[1]`** | **Ecosystem Unit & Component Tests** | *Adapter* | Delegates to the target project's native runner (`pytest`, `manage.py test`, `npm test`). |
| **`[2]`** | **Native Algorithm Benchmark** | *Native* | Pure CS CPU throughput stress test (Quicksort, Mergesort, Binary Search, SHA-256, JSON). |
| **`[3]`** | **Native Concurrency Simulation** | *Native* | Analytical traffic model simulating 50 to 1,000 concurrent user requests under burst conditions. |
| **`[4]`** | **Native System & Health Check** | *Native* | Inspects host OS, Python runtime, CPU cores, target directory access, and disk capacity. |
| **`[5]`** | **Full Comprehensive Suite** | *Orchestrated* | Executes the complete test battery end-to-end and renders a unified summary. |

---

## 🔌 Creating a New Framework Adapter

Any new language or framework adapter inherits from [`BaseAdapter`](adapters/base.py):

```python
import subprocess
from adapters.base import BaseAdapter
from core.ui import print_section_header

class GoAdapter(BaseAdapter):
    """Adapter for Go projects using 'go test'."""

    def run_components_test(self) -> bool:
        print_section_header(f"Running Go Unit Tests for {self.name}")
        res = subprocess.run(["go", "test", "./..."], cwd=self.project_path)
        return res.returncode == 0

    def run_simulation_test(self, concurrent_users: int) -> bool:
        # Delegates to native simulation or custom k6/locust scenario
        return True

    def run_algorithms_test(self) -> bool:
        # Executes native CS benchmarks
        from Performance.test_algorithms import run_benchmarks
        return run_benchmarks()

    def run_overall_test(self) -> bool:
        return self.run_components_test() and self.run_algorithms_test() and self.run_health_check()
```

### Steps to Register a New Adapter:
1. Create `adapters/<name>_adapter.py` inheriting from `BaseAdapter`.
2. Register the adapter in `adapters/__init__.py`.
3. Add a project definition in `tester_config.json` (or use `tester_config.example.json` as a guide).

---

## 📊 Analytical Output & Reporting Architecture

All test streams pass through [`core/reporter.py`](core/reporter.py):
- **ANSI-Aware Padding**: Visible character length calculations strip escape bytes so table borders (`┌─┬─┐`, `│`, `└─┴─┘`) remain laser-aligned.
- **Noise Suppression**: Suppresses internal database setup/teardown debug messages while surfacing real-time test passes (`✔`) and failures (`✘`).
- **Health Grading**: Computes overall pass rates and awards grades ($A+$ for 100% contracts verified, $B$ for minor failures, $F$ for critical regressions).
