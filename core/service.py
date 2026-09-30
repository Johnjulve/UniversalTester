"""
TesterService Facade: The unified programmatic in-process API for UniversalTester.
Acts as the single entrypoint for all thin front-ends (CLI, Desktop GUI, scripts).
"""
import os
import uuid
import time
from typing import Dict, Any, List, Optional, Set

from core.models import RunRequest, RunResult, TestStatus, TestResult
from core.events import ProgressEvent, EventHandler
from adapters.registry import detect_adapter, get_adapter
from adapters.base import BaseAdapter, Capability
from core.orchestrator import TestOrchestrator


class TesterService:
    """Hexagonal Facade providing an in-process programmatic API for UniversalTester."""

    STANDARD_CAPABILITIES: List[Dict[str, Any]] = [
        {
            "id": Capability.COMPONENTS,
            "name": "Unit & Component Tests",
            "pillar": 1,
            "description": "Ecosystem unit & integration tests (pytest, vitest, jest)"
        },
        {
            "id": Capability.ALGORITHMS,
            "name": "Algorithm Correctness",
            "pillar": 2,
            "description": "Quicksort, Mergesort, Binary Search, Heap Sort, Hash Table, Fibonacci, Pi"
        },
        {
            "id": Capability.BENCHMARKS,
            "name": "Computational Benchmarks",
            "pillar": 3,
            "description": "Execution latency & tracemalloc memory profiling"
        },
        {
            "id": Capability.SIMULATION,
            "name": "Reliability & Concurrency Load",
            "pillar": 4,
            "description": "Concurrent user traffic simulation & capacity thresholds"
        },
        {
            "id": Capability.SECURITY,
            "name": "Security & AST Vulnerability Scan",
            "pillar": 5,
            "description": "Static AST scanner for secrets, SQLi, unsafe eval & package audits"
        },
        {
            "id": "full_suite",
            "name": "Full Assessment (All 5 Pillars)",
            "pillar": "ALL",
            "description": "Complete sequential execution with consolidated health scorecard"
        },
        {
            "id": Capability.HEALTH,
            "name": "Host System Health Check",
            "pillar": "SYS",
            "description": "Host environment, Python version, RAM, and tool availability"
        },
    ]

    def __init__(self):
        self._canceled_runs: Set[str] = set()

    def list_capabilities(self, project_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all testing capabilities, optionally flagging availability for a project."""
        capabilities = [dict(c) for c in self.STANDARD_CAPABILITIES]
        if not project_path or not os.path.exists(project_path):
            for cap in capabilities:
                cap["available"] = True
            return capabilities

        adapter_cls = detect_adapter(project_path)
        supported = set()
        if adapter_cls:
            adapter_instance = adapter_cls({"name": os.path.basename(project_path), "path": project_path})
            supported = set(adapter_instance.supported_capabilities())

        for cap in capabilities:
            cap_id = cap["id"]
            if cap_id in ("full_suite", Capability.HEALTH):
                cap["available"] = True
            else:
                cap["available"] = cap_id in supported

        return capabilities

    def cancel(self, run_id: str) -> None:
        """Signal an active test run to cancel."""
        self._canceled_runs.add(run_id)

    def is_canceled(self, run_id: str) -> bool:
        """Check if a run_id was signaled for cancellation."""
        return run_id in self._canceled_runs

    def run(self, request: RunRequest, on_event: Optional[EventHandler] = None) -> RunResult:
        """Execute a test workload according to RunRequest, streaming events to on_event."""
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        start_time = time.perf_counter()

        def emit(step: str, percent: float, msg: str, level: str = "info"):
            if on_event:
                on_event(ProgressEvent(run_id=run_id, step=step, percent=percent, message=msg, level=level))

        emit(request.capability, 0.0, f"Initializing {request.capability} run...")

        if self.is_canceled(run_id):
            return RunResult(run_id=run_id, status="canceled", duration_s=0.0, raw_output="Run canceled.")

        project_path = request.project_path or os.getcwd()
        adapter_cls = detect_adapter(project_path)
        project_config = {
            "name": os.path.basename(os.path.abspath(project_path)) or "CurrentProject",
            "path": project_path,
            **request.options
        }

        if adapter_cls:
            adapter = adapter_cls(project_config)
        else:
            from adapters.python_adapter import PythonAdapter
            adapter = PythonAdapter(project_config)

        orchestrator = TestOrchestrator(adapter)
        cap = request.capability.lower().strip()
        concurrent_users = int(request.options.get("concurrent_users", 500))

        try:
            emit(cap, 25.0, f"Executing {cap}...")
            if cap in (Capability.COMPONENTS, "adaptive", "unit"):
                result = orchestrator.run_adaptive()
            elif cap in (Capability.ALGORITHMS, "algo"):
                result = orchestrator.run_algorithms()
            elif cap in (Capability.BENCHMARKS, "performance", "perf"):
                result = orchestrator.run_performance()
            elif cap in (Capability.SIMULATION, "reliability", "rel"):
                result = orchestrator.run_reliability(concurrent_users)
            elif cap in (Capability.SECURITY, "sec"):
                result = orchestrator.run_security()
            elif cap in ("full_suite", "all", "overall"):
                result = orchestrator.run_all_pillars(concurrent_users)
            elif cap in (Capability.HEALTH, "health"):
                result = adapter.run_health_check()
            else:
                result = TestResult.unavailable(cap, f"Unrecognized capability: '{cap}'")

            duration = time.perf_counter() - start_time
            emit(cap, 100.0, f"Completed {cap} with status {result.status}")

            return RunResult(
                run_id=run_id,
                status=result.status,
                metrics={
                    "passed": result.passed,
                    "failed": result.failed,
                    "skipped": result.skipped,
                    "total": result.total,
                },
                duration_s=round(duration, 4),
                details=[{"errors": result.errors}] if result.errors else [],
                raw_output=result.raw_output
            )

        except Exception as e:
            duration = time.perf_counter() - start_time
            emit(cap, 100.0, f"Error: {e}", level="error")
            return RunResult(
                run_id=run_id,
                status=TestStatus.ERROR,
                duration_s=round(duration, 4),
                details=[{"error": str(e)}],
                raw_output=str(e)
            )
        finally:
            self._canceled_runs.discard(run_id)
