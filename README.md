# ⚡ UniversalTester (`testx`): Universal 5-Pillar Test & Simulation Engine

> **Version 2.0.0** • 100% Python Standard Library Core • Desktop GUI & CLI

**UniversalTester** is an independent, framework-agnostic testing, simulation, and security analysis engine. It provides a standardized **5-pillar testing methodology** to assess any software project across adaptivity, algorithmic correctness, performance latency, concurrency reliability, and security vulnerabilities.

---

## 🏛️ The 5 Foundational Testing Pillars

| Pillar | Focus | Target Coverage | Engine |
| :--- | :--- | :--- | :--- |
| **1. 🔄 Adaptive Tester** | Ecosystem Unit & Component Tests | Django (`manage.py test`), `pytest`, `unittest`, React/Node (`vitest`, `jest`, `npm test`) | Dynamic Adapters |
| **2. 🧮 Algorithm Tester** | Algorithmic Correctness & Cross-Language Benchmarks | Quicksort, Mergesort, Heap Sort, Hash Table, Fibonacci speedup, Monte Carlo $\pi$ | Native Engine + Node.js & Dart Runners |
| **3. ⚡ Performance Tester** | Latency & Peak Memory Profiling | Execution duration (`perf_counter`), peak RAM usage & delta (`tracemalloc`), cryptographic throughput (MB/s) | Native Engine |
| **4. 🛡️ Reliability Tester** | Concurrency Capacity & Stress | 50 to 2,000+ simulated users, traffic profiles (`read_heavy`, `write_heavy`, `balanced_api`, `burst_ping`), hardware saturation tiers | Analytical Model |
| **5. 🔒 Security Tester** | Vulnerability Scan & Dependency Audit | Static AST detection of credentials, SQL injection, dangerous calls (`eval`/`exec`/`os.system`) + ecosystem audit delegation (`npm audit`, `pip-audit`, `safety`) | Static AST Engine |

---

## 🚀 Quick Start

### 1. Standalone Global Installation (`testx`)
Install UniversalTester as an editable CLI tool on your local machine:
```bash
git clone https://github.com/Johnjulve/UniversalTester.git
cd UniversalTester

# Install globally in your active environment
pip install -e .
```
Now `testx` is available directly from any terminal or project directory!

```bash
# Launch the Modern Desktop GUI
testx --gui
# or directly:
python tester.py --gui

# Run the unified 5-pillar assessment on the current project
testx all

# Run specific testing pillars directly
testx adaptive
testx algo
testx perf
testx reliability --concurrent 500
testx security

# Run cross-language benchmark matrix (Python • Node.js • Dart)
python Performance/algorithm_tester.py --cross-lang
```

---

### 2. Portable Launchers (Zero Installation)
If you prefer not to install into your global environment, run directly using the included zero-dependency launchers:

```bash
# Windows PowerShell (automatically finds local .venv or system Python)
.\run.ps1

# Windows CMD
run.cmd

# Direct Python invocation
python tester.py
```

---

### 3. Interactive Terminal Experience
Launching without arguments opens the full-featured interactive dashboard:

```text
╔══════════════════════════════════════════════════════════════════════════════╗
║                 ⚡ UNIVERSAL TEST & SIMULATION ENGINE                         ║
║       Multi-Framework Test Runner • Concurrency Simulator • Benchmarks       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Choose project for testing:
  [1] Django Backend API
  [2] React Frontend UI
  [3] Custom Project Path...
  [0] Exit

What type of Test/Simulation:
  [1] Adaptive Tester      - Target project native tests (pytest / vitest)
  [2] Algorithm Tester     - Algorithmic correctness assertions & edge cases
  [3] Performance Tester   - Latency benchmarks & tracemalloc memory profiling
  [4] Reliability Tester   - Concurrency capacity & over-limit stress simulation
  [5] Security Tester      - Static AST vulnerability scan & ecosystem audit
  [6] Full 5-Pillar Audit  - Complete sequential assessment with Grade A+ scorecard
  [0] Back to Project Selection
```

---

## 📁 Project Structure

```text
UniversalTester/
├── pyproject.toml                <-- PEP 518/621 packaging & testx CLI script definition
├── tester.py                     <-- Main CLI entrypoint & interactive menu controller
├── tester_config.example.json    <-- Example configuration template
├── tester_config.json            <-- Active multi-project local configuration (gitignored)
├── requirements.txt              <-- Optional test & benchmark dependencies
├── run.cmd / run.ps1             <-- Portable Windows execution launchers
├── README.md                     <-- User-facing overview & usage guide
├── ARCHITECTURE.md               <-- System architecture & adapter development guide
├── CHANGELOG.md                  <-- Release version log
├── LICENSE                       <-- MIT License
│
├── core/                         <-- Core Engine (100% Python Standard Library)
│   ├── models.py                 <-- Standardized TestResult and TestStatus models
│   ├── orchestrator.py           <-- Master 5-pillar test coordinator & dispatch engine
│   ├── reporter.py               <-- Stream parser, ANSI-aligned table formatter & health grading
│   ├── security.py               <-- Static AST vulnerability scanner & ecosystem audit delegation
│   └── ui.py                     <-- Terminal formatting, ANSI colors & screen clearing
│
├── adapters/                     <-- Dynamic Language & Framework Adapters
│   ├── base.py                   <-- BaseAdapter protocol & host system health check
│   ├── registry.py               <-- Ecosystem scanner & adapter discovery registry
│   ├── python_adapter.py         <-- Universal Python runner (Django, pytest, unittest)
│   ├── django_adapter.py         <-- Backwards-compatible Django adapter subclass
│   └── node_adapter.py           <-- JS/TS runner (vitest, jest, npm test)
│
├── Performance/                  <-- Native Benchmarks & Reliability Models
│   ├── algorithm_tester.py       <-- Correctness assertions, peak RAM & cross-language matrix
│   ├── reliability_tester.py     <-- Analytical peak traffic & reliability saturation model
│   ├── contracts/
│   │   └── algo_result_schema.json <-- Standardized JSON contract for benchmark results
│   ├── runners/                  <-- Multi-language benchmark runners
│   │   ├── algo_bench.py         <-- Python standard library runner
│   │   ├── algo_bench.js         <-- Node.js V8 runner
│   │   └── algo_bench.dart       <-- Dart SDK runner
│   └── README.md                 <-- Performance & reliability documentation
│
└── tests/                        <-- Automated Verification Suites
    ├── test_phase_3.py           <-- Dual adapter and runner discovery verification
    ├── test_phase_4.py           <-- Reliability and performance algorithm verification
    ├── test_phase_5.py           <-- Security AST scanner and orchestrator dispatch verification
    └── test_phase_7.py           <-- Cross-language runner and schema contract verification
```

---

## ⚙️ Adding & Configuring Projects

Copy `tester_config.example.json` to `tester_config.json`:

```json
{
  "version": "2.0.0",
  "app_name": "Universal Tester",
  "projects": {
    "1": {
      "id": "my_django_service",
      "name": "Django Backend API",
      "type": "django",
      "path": "d:/Projects/MyBackend",
      "backend_dir": "d:/Projects/MyBackend/backend",
      "python_env": ""
    },
    "2": {
      "id": "my_react_app",
      "name": "React Web Client",
      "type": "react",
      "path": "d:/Projects/MyFrontend",
      "frontend_dir": "d:/Projects/MyFrontend"
    }
  },
  "default_concurrency_options": [50, 100, 500, 1000, 2000]
}
```

> **Dynamic Virtual Environments**: If `"python_env"` is omitted or left empty, UniversalTester automatically searches `.venv`, `venv`, and `env` inside the project root, backend folder, and parent paths.
