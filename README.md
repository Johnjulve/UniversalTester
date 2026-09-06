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

### 1. Launch Interactive CLI
Run from this directory:
```bash
# Windows CMD
run.cmd

# Windows PowerShell
.\run.ps1

# Direct Python execution
python tester.py
```

### 2. The Interactive Flow
```text
╔══════════════════════════════════════════════════════════════════════════════╗
║                 ⚡ UNIVERSAL TEST & SIMULATION ENGINE                         ║
║       Multi-Framework Test Runner • Concurrency Simulator • Benchmarks       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Choose project for testing:
  [1] E_Botar
  [2] E_Botar lite
  [3] Custom Project Path...
  [0] Exit
```

---

## 📁 Project Structure

```text
UniversalTester/
├── tester.py                     <-- Main terminal interactive CLI entrypoint
├── tester_config.json            <-- Multi-project configuration & paths
├── run.cmd / run.ps1             <-- One-click Windows execution launchers
├── README.md                     <-- Documentation and usage guide
├── ARCHITECTURE.md               <-- Guide to creating new adapters & adding frameworks
├── core/
│   └── ui.py                     <-- Terminal formatting, ANSI colors & screen clearing
├── adapters/
│   ├── base.py                   <-- BaseAdapter interface (all frameworks inherit this)
│   ├── django_adapter.py         <-- Django & DRF test execution & concurrency simulations
│   ├── node_adapter.py           <-- Node.js / React / Vite adapter
│   ├── fastapi_adapter.py        <-- FastAPI / Pytest adapter
│   └── go_adapter.py             <-- Go (go test) adapter
└── Performance/
    ├── simulate_concurrent_load.py
    ├── simulate_output.txt
    ├── performance_tests.py
    ├── quick_performance_test.py
    └── test_algorithms.py
```

---

## ⚙️ Adding a New Project

To add a new project to the menu, open [`tester_config.json`](tester_config.json) and add an entry under `"projects"`:

```json
{
  "projects": {
    "1": {
      "id": "e_botar",
      "name": "E_Botar",
      "type": "django",
      "path": "d:/Downloads_D/Project Thesis/E_Botar",
      "backend_dir": "d:/Downloads_D/Project Thesis/E_Botar/backend",
      "python_env": "d:/Downloads_D/Project Thesis/E_Botar/env/Scripts/python.exe"
    },
    "3": {
      "id": "my_web_app",
      "name": "My Next.js App",
      "type": "node",
      "path": "d:/Projects/MyWebApp",
      "frontend_dir": "d:/Projects/MyWebApp/frontend"
    }
  }
}
```

The next time you run `tester.py`, your new project will appear in the main menu automatically!
