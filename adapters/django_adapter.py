"""
Django framework adapter.
Executes Django manage.py tests, analytical load simulations, and algorithm benchmarks.
"""
import os
import sys
import time
import subprocess
from typing import Dict, Any, Set

from adapters.base import BaseAdapter, Capability
from core.models import TestResult, TestStatus
from core.ui import Colors, print_section_header, print_status, print_divider
from core.reporter import AnalyticalTestReporter


class DjangoAdapter(BaseAdapter):
    """Adapter executing tests for Django/DRF projects."""

    @classmethod
    def adapter_id(cls) -> str:
        return "django"

    @classmethod
    def display_name(cls) -> str:
        return "Python / Django Adapter"

    @classmethod
    def applies(cls, project_path: str) -> bool:
        """Check if project path contains Django/Python project indicators."""
        if not project_path or not os.path.exists(project_path):
            return False
        return (
            os.path.exists(os.path.join(project_path, 'manage.py')) or
            os.path.exists(os.path.join(project_path, 'backend', 'manage.py')) or
            os.path.exists(os.path.join(project_path, 'pytest.ini')) or
            os.path.exists(os.path.join(project_path, 'setup.py'))
        )

    @classmethod
    def is_available(cls) -> bool:
        return True  # sys.executable is always available

    def supported_capabilities(self) -> Set[str]:
        return {
            Capability.COMPONENTS,
            Capability.ALGORITHMS,
            Capability.SIMULATION,
            Capability.BENCHMARKS,
            Capability.HEALTH,
        }

    def __init__(self, project_config: Dict[str, Any]):
        super().__init__(project_config)
        self.backend_dir = project_config.get('backend_dir', os.path.join(self.project_path, 'backend'))
        
        # Dynamic python environment resolution: config -> project venv -> fallback to sys.executable
        configured_py = project_config.get('python_env')
        if configured_py and os.path.exists(configured_py):
            self.python_bin = configured_py
        else:
            candidates = [
                os.path.join(self.project_path, '.venv', 'Scripts', 'python.exe'),
                os.path.join(self.project_path, 'env', 'Scripts', 'python.exe'),
                os.path.join(self.project_path, '.venv', 'bin', 'python'),
                os.path.join(self.project_path, 'env', 'bin', 'python'),
                os.path.join(self.backend_dir, '.venv', 'Scripts', 'python.exe'),
                os.path.join(self.backend_dir, 'env', 'Scripts', 'python.exe'),
            ]
            self.python_bin = next((p for p in candidates if os.path.exists(p)), sys.executable)
        
        # Testing directory path relative to this file
        self.testing_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.performance_dir = os.path.join(self.testing_dir, 'Performance')

    def _run_process(self, cmd: list, cwd: str, label: str) -> TestResult:
        """Run a subprocess and stream output nicely."""
        print(f"\n{Colors.DIM}Executing: {' '.join(cmd)}{Colors.RESET}\n")
        start_time = time.time()
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                sys.stdout.write(line)
                sys.stdout.flush()
                
            process.wait()
            elapsed = time.time() - start_time
            
            if process.returncode == 0:
                print(f"\n{Colors.BRIGHT_GREEN}✔ {label} PASSED ({elapsed:.2f}s){Colors.RESET}")
                return TestResult.from_bool(label, True, duration=elapsed)
            else:
                print(f"\n{Colors.BRIGHT_RED}✘ {label} FAILED with exit code {process.returncode} ({elapsed:.2f}s){Colors.RESET}")
                return TestResult.from_bool(label, False, duration=elapsed)
                
        except Exception as e:
            print(f"\n{Colors.BRIGHT_RED}✘ Process execution error: {e}{Colors.RESET}")
            return TestResult(suite_name=label, status=TestStatus.ERROR, failed=1, errors=[str(e)])

    def _run_analytical_test(self, cmd: list, cwd: str, label: str) -> TestResult:
        """Run a test subprocess with real-time analytical parsing and structured dashboard."""
        print(f"\n{Colors.DIM}Executing: {' '.join(cmd)}{Colors.RESET}\n")
        reporter = AnalyticalTestReporter(suite_name=label)
        start_time = time.time()
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                reporter.feed_line(line)
                
            process.wait()
            passed = reporter.render_dashboard()
            elapsed = time.time() - start_time
            success = passed and (process.returncode == 0)
            
            return TestResult(
                suite_name=label,
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                passed=reporter.passed_tests,
                failed=reporter.failed_tests,
                skipped=reporter.skipped_tests,
                duration=reporter.duration_seconds or elapsed,
                errors=[f['title'] for f in reporter.failures]
            )
        except Exception as e:
            print(f"\n{Colors.BRIGHT_RED}✘ Test execution error: {e}{Colors.RESET}")
            return TestResult(suite_name=label, status=TestStatus.ERROR, failed=1, errors=[str(e)])

    def run_components_test(self) -> TestResult:
        """Run Tier 1 Django unit and component tests with analytical dashboard."""
        print_section_header(f"Running Component Unit Tests for {self.name}")
        cmd = [self.python_bin, 'manage.py', 'test', 'tests', '-v', '2']
        return self._run_analytical_test(cmd, cwd=self.backend_dir, label=f"{self.name} Components")

    def run_simulation_test(self, concurrent_users: int) -> TestResult:
        """Run analytical concurrent load simulation."""
        print_section_header(f"Running Concurrency Simulation ({concurrent_users} Users) for {self.name}")
        sim_script = os.path.join(self.performance_dir, 'simulate_concurrent_load.py')
        
        cmd = [
            self.python_bin,
            sim_script,
            '--scenario', 'vote_rush',
            '--concurrent', str(concurrent_users),
            '--burst-seconds', '120'
        ]
        return self._run_process(cmd, cwd=self.project_path, label=f"Concurrency Simulation ({concurrent_users} Users)")

    def run_algorithms_test(self) -> TestResult:
        """Run algorithm verification and execution speed tests."""
        print_section_header(f"Running Algorithm Benchmarks for {self.name}")
        algo_script = os.path.join(self.performance_dir, 'test_algorithms.py')
        cmd = [self.python_bin, algo_script]
        return self._run_process(cmd, cwd=self.project_path, label="Algorithm Benchmarks")

    def run_benchmarks(self) -> TestResult:
        """Run computational stress and throughput benchmarks."""
        print_section_header(f"Running Performance Benchmarks for {self.name}")
        algo_script = os.path.join(self.performance_dir, 'test_algorithms.py')
        cmd = [self.python_bin, algo_script]
        return self._run_process(cmd, cwd=self.project_path, label="Performance Benchmark")

    def run_overall_test(self) -> TestResult:
        """Run full test suite: components, algorithms, and 500-user simulation."""
        print_section_header(f"Running Full Overall Test Suite for {self.name}")
        
        results: Dict[str, TestResult] = {}
        
        # 1. Component Unit Tests
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 1/3] Executing Component Tests...{Colors.RESET}")
        results['components'] = self.run_components_test()
        
        # 2. Algorithm Benchmarks
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 2/3] Executing Algorithm Verification...{Colors.RESET}")
        results['algorithms'] = self.run_algorithms_test()
        
        # 3. Concurrency Simulation (500 users baseline)
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 3/3] Executing Concurrency Simulation (500 Users)...{Colors.RESET}")
        results['simulation'] = self.run_simulation_test(500)
        
        print_divider()
        print(f"\n{Colors.BOLD}OVERALL TEST SUITE SUMMARY FOR {self.name.upper()}:{Colors.RESET}\n")
        
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        all_passed = True
        errors = []
        
        for suite_key, result in results.items():
            if result.is_unavailable:
                print_status("UNAVAIL", f"{suite_key.capitalize()} Suite (Not Supported)", color=Colors.DIM)
                total_skipped += 1
            elif result.is_success:
                print_status("PASS", f"{suite_key.capitalize()} Suite", color=Colors.BRIGHT_GREEN)
                total_passed += result.passed or 1
            else:
                print_status("FAIL", f"{suite_key.capitalize()} Suite", color=Colors.BRIGHT_RED)
                total_failed += result.failed or 1
                all_passed = False
                errors.extend(result.errors)
                
        print()
        return TestResult(
            suite_name=f"{self.name} Overall Suite",
            status=TestStatus.PASSED if all_passed else TestStatus.FAILED,
            passed=total_passed,
            failed=total_failed,
            skipped=total_skipped,
            errors=errors
        )
