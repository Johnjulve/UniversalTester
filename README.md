# ⚡ UniversalTester: Multi-Framework Test & Simulation Engine

**UniversalTester** is an independent, framework-agnostic terminal CLI application designed to orchestrate tests, simulate concurrent user loads, and run performance benchmarks across multiple software projects and technology stacks.

---

## 🎯 Key Capabilities

- 🖥️ **Interactive Terminal UI**: Intuitive numbered menus with automatic screen clearing, color-coded status badges, and clean progress indicators.
- 🌐 **Multi-Project Management**: Effortlessly switch between multiple applications (`E_Botar`, `E_Botar lite`, or custom projects) from a single hub.
- 🔌 **Pluggable Adapter Architecture**: Ready-to-use adapters for **Django**, **Node.js/React**, **FastAPI**, and **Go**, with an open interface to add any language or framework.
- 📊 **Analytical Concurrency Simulation**: Mathematical load modeling for high-traffic peak events (e.g. 50 to 2,000 concurrent voters/users) calculating egress, req/s, and server hardware utilization.
- ⚡ **Automated Benchmarking**: Latency, database query count profiling, and algorithm speed verification.

---

## 🚀 Quick Start

### 1. Installation & Environment Setup
Clone and install optional dependencies (the core CLI requires only standard library Python 3.8+):
```bash
# Clone the repository
git clone https://github.com/Johnjulve/UniversalTester.git
cd UniversalTester

# (Optional) Create a virtual environment and install load-testing tools
python -m venv .venv
.\.venv\Scripts\activate   # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch Interactive CLI
Run with one click or command:
```bash
# Windows PowerShell (automatically detects local .venv or system Python)
.\run.ps1

# Windows CMD
run.cmd

# Direct Python execution
python tester.py
```

### 3. The Interactive Flow
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
  [1] Ecosystem Unit & Component Tests  - Delegates to project runner (pytest / vitest)
  [2] Native Algorithm Benchmark        - Pure CS stress test (Quicksort, SHA-256)
  [3] Native Concurrency Simulation     - Analytical peak traffic & capacity model
  [4] Native System & Health Check      - Host CPU, memory, runtime environment
  [5] Full Comprehensive Suite          - Complete run: Unit Tests + Algorithms + Simulation
  [0] Back to Project Selection
```

---

## 📁 Project Structure

```text
UniversalTester/
├── tester.py                     <-- Main terminal interactive CLI entrypoint
├── tester_config.example.json    <-- Example configuration template
├── tester_config.json            <-- Local active project configuration (ignored)
├── requirements.txt              <-- Optional test & benchmark dependencies
├── run.cmd / run.ps1             <-- Portable Windows execution launchers
├── README.md                     <-- Documentation and usage guide
├── ARCHITECTURE.md               <-- Two-pillar hybrid architecture guide
├── CHANGELOG.md                  <-- Release version log
├── LICENSE                       <-- MIT License
├── core/
│   ├── reporter.py               <-- Stream parser & analytical metrics dashboard
│   └── ui.py                     <-- Terminal formatting, ANSI colors & screen clearing
├── adapters/
│   ├── base.py                   <-- BaseAdapter interface & universal health checks
│   ├── django_adapter.py         <-- Django & DRF test execution & concurrency simulations
│   └── node_adapter.py           <-- Node.js / React / Vite / Next.js adapter
└── Performance/
    ├── test_algorithms.py        <-- Pure Universal CS stress benchmarks (Option A)
    └── simulate_concurrent_load.py <-- Analytical peak traffic & saturation model
```

---

## ⚙️ Adding & Configuring Projects

Copy `tester_config.example.json` to `tester_config.json` (or edit `tester_config.json` directly):

```json
{
  "version": "1.0.0",
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
  }
}
```

> **Note**: For Django projects, if `"python_env"` is left empty or omitted, `UniversalTester` will automatically locate your virtual environment (`.venv` or `env`) inside the project!
