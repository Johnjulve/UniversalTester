"""
TesterService Facade: The unified programmatic in-process API for UniversalTester.
Acts as the single entrypoint for all thin front-ends (CLI, Desktop GUI, scripts).
"""
import os
import sys
import io
import re
import uuid
import time
import contextlib
from typing import Dict, Any, List, Optional, Set, Callable

from core.models import RunRequest, RunResult, TestStatus, TestResult
from core.events import ProgressEvent, EventHandler
from adapters.registry import detect_adapter, get_adapter
from adapters.base import BaseAdapter, Capability
from core.orchestrator import TestOrchestrator

# Ensure fallback stream if packaged as a windowless executable (e.g., PyInstaller --noconsole)
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

ANSI_REGEX = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class StreamEmitter(io.StringIO):
    """Captures printed stdout/stderr and streams clean lines to an on_line callback."""
    def __init__(self, on_line: Callable[[str], None], mirror_stream=None):
        super().__init__()
        self.on_line = on_line
        self.mirror_stream = mirror_stream
        self._buffer = ""

    def reconfigure(self, **kwargs):
        pass

    def write(self, s: str):
        if self.mirror_stream:
            try:
                self.mirror_stream.write(s)
            except Exception:
                pass
        self._buffer += s
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            clean = ANSI_REGEX.sub("", line).rstrip("\r")
            self.on_line(clean)

    def flush(self):
        if self.mirror_stream:
            try:
                self.mirror_stream.flush()
            except Exception:
                pass
        if self._buffer:
            clean = ANSI_REGEX.sub("", self._buffer).rstrip("\r\n")
            if clean:
                self.on_line(clean)
            self._buffer = ""



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
            if cap_id == Capability.HEALTH:
                cap["available"] = True
            elif cap_id == "full_suite":
                cap["available"] = bool(supported)
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

        gui_mode = bool(
            request.options.get("gui_mode") or
            request.options.get("capture_stdout") or
            (on_event is not None and request.options.get("gui_mode") is not False)
        )
        captured_logs: List[str] = []

        def on_stdout_line(line: str):
            captured_logs.append(line)
            emit(cap, -1.0, line, level="log")

        if gui_mode:
            emitter = StreamEmitter(on_stdout_line, mirror_stream=None)
            redirect_ctx = contextlib.ExitStack()
            redirect_ctx.enter_context(contextlib.redirect_stdout(emitter))
            redirect_ctx.enter_context(contextlib.redirect_stderr(emitter))
        else:
            emitter = None
            redirect_ctx = contextlib.nullcontext()

        try:
            with redirect_ctx:
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

            if emitter:
                emitter.flush()

            duration = time.perf_counter() - start_time
            emit(cap, 100.0, f"Completed {cap} with status {result.status}")

            final_raw = result.raw_output if result.raw_output else ("\n".join(captured_logs) if captured_logs else "")

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
                raw_output=final_raw
            )

        except Exception as e:
            if emitter:
                emitter.flush()
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

