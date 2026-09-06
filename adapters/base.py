"""
Base adapter interface for multi-framework test execution.
Enables expanding the Universal Tester to Node, React, Go, FastAPI, etc.
"""
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAdapter(ABC):
    """Abstract interface defining required test runner hooks for any project type."""

    def __init__(self, project_config: Dict[str, Any]):
        self.config = project_config
        self.name = project_config.get('name', 'Unknown Project')
        self.project_path = project_config.get('path', '')

    @abstractmethod
    def run_components_test(self) -> bool:
        """Run fast component/unit test suite."""
        pass

    @abstractmethod
    def run_simulation_test(self, concurrent_users: int) -> bool:
        """Run concurrent load simulation."""
        pass

    @abstractmethod
    def run_overall_test(self) -> bool:
        """Run comprehensive system & component suite."""
        pass

    @abstractmethod
    def run_benchmarks(self) -> bool:
        """Run performance/latency benchmarks."""
        pass

    @abstractmethod
    def run_algorithms_test(self) -> bool:
        """Run algorithm verification & performance checks."""
        pass

    def run_health_check(self) -> bool:
        """Run universal system, host resource, and environment health check."""
        import platform
        import shutil
        import os
        from core.ui import Colors, print_section_header, print_status, print_divider

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
        all_passed = True
        for title, detail, ok in checks:
            tag = "PASS" if ok else "FAIL"
            color = Colors.BRIGHT_GREEN if ok else Colors.BRIGHT_RED
            print_status(tag, f"{title}: {Colors.WHITE}{detail}{Colors.RESET}", color=color)
            if not ok:
                all_passed = False
                
        print()
        return all_passed

