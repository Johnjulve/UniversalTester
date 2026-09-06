# 🏗️ UniversalTester Architecture & Extension Guide

UniversalTester is built on the **Adapter Pattern**, ensuring that the CLI menu, terminal screen clearing, and result reporting logic remain completely separated from the framework-specific execution commands.

---

## 🏛️ Core Design

```
[CLI Terminal Interface (tester.py)]
         │
         ▼
  [Adapter Factory (adapters/__init__.py)]
         │
 ┌───────┴────────┬────────────────┬────────────────┐
 ▼                ▼                ▼                ▼
[DjangoAdapter]  [NodeAdapter]  [FastAPIAdapter] [GoAdapter]
 (manage.py test) (npm test)     (pytest)         (go test)
```

---

## 📝 Creating a New Framework Adapter

To support a new technology stack (e.g. Go, Rust, Ruby on Rails, or Spring Boot):

1. **Create a new file in `adapters/`** (e.g. `adapters/go_adapter.py`):
```python
import subprocess
from adapters.base import BaseAdapter
from core.ui import print_section_header

class GoAdapter(BaseAdapter):
    def run_components_test(self) -> bool:
        print_section_header(f"Running Go Unit Tests for {self.name}")
        res = subprocess.run(["go", "test", "./..."], cwd=self.project_path)
        return res.returncode == 0

    def run_simulation_test(self, concurrent_users: int) -> bool:
        # Load test logic or Locust runner
        return True

    def run_overall_test(self) -> bool:
        return self.run_components_test()

    def run_benchmarks(self) -> bool:
        res = subprocess.run(["go", "test", "-bench=.", "./..."], cwd=self.project_path)
        return res.returncode == 0

    def run_algorithms_test(self) -> bool:
        return True
```

2. **Register the adapter in `adapters/__init__.py`**:
```python
from adapters.go_adapter import GoAdapter

def get_adapter(project_config):
    p_type = project_config.get('type', '').lower()
    if p_type == 'go':
        return GoAdapter(project_config)
    # ... existing adapters ...
```

3. **Configure your project in `tester_config.json`**:
```json
{
  "projects": {
    "4": {
      "id": "my_go_service",
      "name": "Auth Microservice (Go)",
      "type": "go",
      "path": "d:/Projects/AuthService"
    }
  }
}
```

---

## ⚡ Concurrency Simulator Math

The analytical simulator (`Performance/simulate_concurrent_load.py`) uses an empirical queuing model:
1. Calculates aggregate HTTP requests per user journey (e.g. login, ballot fetching, submission).
2. Divides total requests by the burst time window (default: $120\text{s}$) to derive required arrival rate ($\text{req/s}$).
3. Calculates network egress based on JSON payload measurements.
4. Compares the arrival rate against server capacity profiles (e.g., single-process dev, 4-worker Gunicorn VPS, 8-worker clustered stack) to report server utilization percentage and user queuing delays.
