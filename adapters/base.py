"""
Base adapter interface for multi-framework test execution.
Enables expanding UniversalTester to Python, Node/React, and future ecosystems.
"""
import os
import sys
import shutil
import platform
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set

from core.models import TestResult, TestStatus
from core.ui import Colors, print_section_header, print_status, print_divider


class Capability:
    """Standardized test runner capability identifiers."""
    COMPONENTS = "components"
    SIMULATION = "simulation"
    ALGORITHMS = "algorithms"
    BENCHMARKS = "benchmarks"
    HEALTH = "health"
    SECURITY = "security"


class BaseAdapter(ABC):
    """Abstract interface defining required test runner hooks and capabilities for any project type."""

    def __init__(self, project_config: Dict[str, Any]):
        self.config = project_config
        self.name = project_config.get('name', 'Unknown Project')
        self.project_path = project_config.get('path', '')

    @classmethod
    @abstractmethod
    def adapter_id(cls) -> str:
        """Unique identifier for this adapter (e.g., 'python', 'node')."""
        pass

    @classmethod
    @abstractmethod
    def display_name(cls) -> str:
        """Human-readable name for this adapter."""
        pass

    @classmethod
    @abstractmethod
    def applies(cls, project_path: str) -> bool:
        """Check if target project matches this ecosystem."""
        pass

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if required runtime/test binary is installed on host system."""
        pass

    def supported_capabilities(self) -> Set[str]:
        """Return the set of capabilities supported by this adapter for the current project."""
        return {Capability.COMPONENTS, Capability.HEALTH, Capability.SECURITY}

    def has_capability(self, capability: str) -> bool:
        """Helper to test whether a capability is supported."""
        return capability in self.supported_capabilities()

    @abstractmethod
    def run_components_test(self) -> TestResult:
        """Run fast component/unit test suite."""
        pass

    @abstractmethod
    def run_simulation_test(self, concurrent_users: int) -> TestResult:
        """Run concurrent load simulation."""
        pass

    @abstractmethod
    def run_overall_test(self) -> TestResult:
        """Run comprehensive system & component suite across supported capabilities."""
        pass

    @abstractmethod
    def run_benchmarks(self) -> TestResult:
        """Run performance/latency benchmarks."""
        pass

    @abstractmethod
    def run_algorithms_test(self) -> TestResult:
        """Run algorithm verification & performance checks."""
        pass

    def run_security_scan(self) -> TestResult:
        """Run static code security scanner and ecosystem vulnerability checks."""
        from core.security import run_security_assessment
        return run_security_assessment(self.project_path, self.name)

    def run_health_check(self) -> TestResult:
        """Run universal system, host resource, and environment health check."""
        print_section_header(f"System & Environment Health Check: {self.name}")
        
        checks = []
        
        # 1. Host OS & Platform
        os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        checks.append(("Host Platform", os_info, True))
        
        # 2. Python Runtime
        py_ver = f"Python {platform.python_version()} [{sys.executable}]"
        checks.append(("Python Runtime", py_ver, True))
        
        # 3. CPU Core Capacity
        cpu_count = os.cpu_count() or 1
        checks.append(("CPU Resources", f"{cpu_count} Logical Cores available", True))
        
        # 4. Project Path & Disk Storage
        if os.path.exists(self.project_path):
            try:
                usage = shutil.disk_usage(self.project_path)
                free_gb = usage.free / (1024 ** 3)
                total_gb = usage.total / (1024 ** 3)
                disk_status = f"{free_gb:.1f} GB free of {total_gb:.1f} GB"
                checks.append(("Disk Space", disk_status, free_gb > 1.0))
            except Exception:
                checks.append(("Disk Space", "Path accessible", True))
        else:
            checks.append(("Target Directory", f"Path not found: {self.project_path}", False))

        # Render Health Checklist
        passed_count = 0
        failed_count = 0
        errors = []
        for title, detail, ok in checks:
            tag = "PASS" if ok else "FAIL"
            color = Colors.BRIGHT_GREEN if ok else Colors.BRIGHT_RED
            print_status(tag, f"{title}: {Colors.WHITE}{detail}{Colors.RESET}", color=color)
            if ok:
                passed_count += 1
            else:
                failed_count += 1
                errors.append(f"{title}: {detail}")
                
        print()
        status = TestStatus.PASSED if failed_count == 0 else TestStatus.FAILED
        return TestResult(
            suite_name=f"{self.name} System Health",
            status=status,
            passed=passed_count,
            failed=failed_count,
            errors=errors
        )
