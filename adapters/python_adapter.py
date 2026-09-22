"""
Universal Python / Django / Pytest framework adapter.
Executes Python test runners (manage.py test, pytest, unittest), load simulations, and algorithm benchmarks.
"""
import os
import sys
import time
import subprocess
from typing import Dict, Any, Set, Optional, List

from adapters.base import BaseAdapter, Capability
from core.models import TestResult, TestStatus
from core.ui import Colors, print_section_header, print_status, print_divider
from core.reporter import AnalyticalTestReporter, render_overall_summary


class PythonAdapter(BaseAdapter):
    """Universal adapter executing tests and benchmarks for Python/Django/FastAPI projects."""

    @classmethod
    def adapter_id(cls) -> str:
        return "python"

    @classmethod
    def display_name(cls) -> str:
        return "Python / Django / Pytest Adapter"

    @classmethod
    def applies(cls, project_path: str) -> bool:
        """Check if project path contains Python project indicators."""
        if not project_path or not os.path.exists(project_path):
            return False
        return (
            os.path.exists(os.path.join(project_path, 'manage.py')) or
            os.path.exists(os.path.join(project_path, 'backend', 'manage.py')) or
            os.path.exists(os.path.join(project_path, 'pytest.ini')) or
            os.path.exists(os.path.join(project_path, 'pyproject.toml')) or
            os.path.exists(os.path.join(project_path, 'setup.py')) or
            os.path.exists(os.path.join(project_path, 'requirements.txt'))
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
        
        # Resolve backend directory: explicit config -> backend/ subfolder -> project root
        configured_backend = project_config.get('backend_dir')
        if configured_backend and os.path.exists(configured_backend):
            self.backend_dir = configured_backend
        else:
            backend_sub = os.path.join(self.project_path, 'backend')
            if os.path.exists(backend_sub):
                self.backend_dir = backend_sub
            else:
                self.backend_dir = self.project_path

        # Dynamic python environment resolution: config -> project venvs -> fallback to sys.executable
        self.python_bin = self._resolve_python_environment(project_config.get('python_env'))

        # Testing directory path relative to this file
        self.testing_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.performance_dir = os.path.join(self.testing_dir, 'Performance')

    def _resolve_python_environment(self, configured_py: Optional[str]) -> str:
        """
        Dynamically locate the appropriate Python virtual environment executable:
        1. Explicit configuration (if provided and valid executable).
        2. Candidate virtual environments in backend, project root, and parent directories.
        3. Active shell virtual environment ($VIRTUAL_ENV).
        4. Fallback to sys.executable.
        """
        if configured_py and os.path.isfile(configured_py):
            return os.path.abspath(configured_py)

        venv_folder_names = ['.venv', 'venv', 'env', '.env', 'virtualenv', '.virtualenv', 'pyenv']
        bin_subpaths = [
            os.path.join('Scripts', 'python.exe'),
            os.path.join('bin', 'python3'),
            os.path.join('bin', 'python'),
            'python.exe'
        ]

        # Scan backend_dir, project_path, and their parent folders
        search_roots: List[str] = []
        for d in [
            self.backend_dir,
            self.project_path,
            os.path.dirname(os.path.abspath(self.project_path)) if self.project_path else None,
            os.path.dirname(os.path.abspath(self.backend_dir)) if self.backend_dir else None,
        ]:
            if d and os.path.isdir(d):
                norm_d = os.path.abspath(d)
                if norm_d not in search_roots:
                    search_roots.append(norm_d)

        found_interpreters: List[str] = []

        for root in search_roots:
            for v_name in venv_folder_names:
                v_dir = os.path.join(root, v_name)
                if os.path.isdir(v_dir):
                    for b_sub in bin_subpaths:
                        candidate = os.path.join(v_dir, b_sub)
                        if os.path.isfile(candidate):
                            abs_cand = os.path.abspath(candidate)
                            if abs_cand not in found_interpreters:
                                found_interpreters.append(abs_cand)

        # Also inspect active shell virtualenv
        active_env = os.environ.get('VIRTUAL_ENV')
        if active_env and os.path.isdir(active_env):
            for b_sub in bin_subpaths:
                candidate = os.path.join(active_env, b_sub)
                if os.path.isfile(candidate):
                    abs_cand = os.path.abspath(candidate)
                    if abs_cand not in found_interpreters:
                        found_interpreters.insert(0, abs_cand)

        if not found_interpreters:
            return sys.executable

        # Framework-aware verification: prefer the interpreter that can import framework dependencies
        is_django = (
            os.path.exists(os.path.join(self.backend_dir, 'manage.py')) or
            os.path.exists(os.path.join(self.project_path, 'manage.py'))
        )
        if is_django:
            for py_cand in found_interpreters:
                try:
                    res = subprocess.run(
                        [py_cand, '-c', 'import django'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=2
                    )
                    if res.returncode == 0:
                        return py_cand
                except Exception:
                    continue

        return found_interpreters[0]

    def _run_process(self, cmd: List[str], cwd: str, label: str) -> TestResult:
        """Run a subprocess and stream output with status reporting."""
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

    def _run_analytical_test(self, cmd: List[str], cwd: str, label: str) -> TestResult:
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

            if process.returncode != 0 and reporter.total_tests == 0:
                print(f"\n{Colors.BOLD}{Colors.BRIGHT_RED}✘ Test runner exited with code {process.returncode} before running tests:{Colors.RESET}")
                for err_line in reporter.raw_unmatched_lines[-25:]:
                    print(f"  {Colors.BRIGHT_RED}{err_line}{Colors.RESET}")
                print()

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

    def _detect_test_runner(self) -> Optional[Dict[str, Any]]:
        """
        Dynamically detect the appropriate Python test runner:
        1. Django manage.py test
        2. pytest
        3. unittest discover
        Returns dict with 'cmd' and 'cwd', or None if no runner/tests found.
        """
        # 1. Django check: manage.py
        for candidate_dir in [self.backend_dir, self.project_path]:
            manage_py = os.path.join(candidate_dir, 'manage.py')
            if os.path.exists(manage_py):
                tests_dir = os.path.join(candidate_dir, 'tests')
                tests_file = os.path.join(candidate_dir, 'tests.py')
                if os.path.exists(tests_dir) or os.path.exists(tests_file):
                    return {
                        'cmd': [self.python_bin, 'manage.py', 'test', 'tests' if os.path.exists(tests_dir) else '', '-v', '2'],
                        'cwd': candidate_dir,
                        'type': 'django'
                    }
                else:
                    return {
                        'cmd': [self.python_bin, 'manage.py', 'test', '-v', '2'],
                        'cwd': candidate_dir,
                        'type': 'django'
                    }

        # 2. Pytest check: pytest.ini or pytest installed
        for candidate_dir in [self.backend_dir, self.project_path]:
            pytest_ini = os.path.join(candidate_dir, 'pytest.ini')
            tests_dir = os.path.join(candidate_dir, 'tests')
            if os.path.exists(pytest_ini) or os.path.exists(tests_dir):
                # Verify if pytest is available in the target python environment
                try:
                    res = subprocess.run(
                        [self.python_bin, '-m', 'pytest', '--version'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=candidate_dir
                    )
                    if res.returncode == 0:
                        return {
                            'cmd': [self.python_bin, '-m', 'pytest', '-v'],
                            'cwd': candidate_dir,
                            'type': 'pytest'
                        }
                except Exception:
                    pass

        # 3. Standard unittest discover
        for candidate_dir in [self.backend_dir, self.project_path]:
            tests_dir = os.path.join(candidate_dir, 'tests')
            if os.path.exists(tests_dir) or any(f.startswith('test_') and f.endswith('.py') for f in os.listdir(candidate_dir)):
                return {
                    'cmd': [self.python_bin, '-m', 'unittest', 'discover', '-v'],
                    'cwd': candidate_dir,
                    'type': 'unittest'
                }

        return None

    def run_components_test(self) -> TestResult:
        """Run unit and component tests with dynamic runner detection."""
        suite_name = f"{self.name} Unit & Component Tests"
        print_section_header(f"Running Component Unit Tests for {self.name}")

        runner_info = self._detect_test_runner()
        if not runner_info:
            reason = f"No test runner or test suite discovered in {self.backend_dir}"
            print_status("UNAVAIL", reason, color=Colors.DIM)
            return TestResult.unavailable(suite_name, reason)

        # Clean command (filter empty strings)
        cmd = [c for c in runner_info['cmd'] if c]
        return self._run_analytical_test(cmd, cwd=runner_info['cwd'], label=suite_name)

    def run_simulation_test(self, concurrent_users: int) -> TestResult:
        """Run analytical concurrent load simulation across configurable traffic profiles."""
        suite_name = f"Concurrency Simulation ({concurrent_users} Users)"
        print_section_header(f"Running Concurrency Simulation ({concurrent_users} Users) for {self.name}")
        sim_script = os.path.join(self.performance_dir, 'simulate_concurrent_load.py')

        if not os.path.exists(sim_script):
            reason = f"Simulation script not found: {sim_script}"
            print_status("UNAVAIL", reason, color=Colors.DIM)
            return TestResult.unavailable(suite_name, reason)

        # Configurable scenario with default to comprehensive 'all'
        scenario = self.config.get('simulation_scenario', 'all')
        cmd = [
            self.python_bin,
            sim_script,
            '--scenario', scenario,
            '--concurrent', str(concurrent_users),
            '--burst-seconds', '120'
        ]
        return self._run_process(cmd, cwd=self.project_path, label=suite_name)

    def run_algorithms_test(self) -> TestResult:
        """Run algorithm verification and execution speed tests."""
        print_section_header(f"Running Algorithm Benchmarks for {self.name}")
        algo_script = os.path.join(self.performance_dir, 'test_algorithms.py')
        cmd = [self.python_bin, algo_script]
        return self._run_process(cmd, cwd=self.project_path, label=f"{self.name} Algorithm Benchmarks")

    def run_benchmarks(self) -> TestResult:
        """Run computational stress and throughput benchmarks."""
        print_section_header(f"Running Performance Benchmarks for {self.name}")
        algo_script = os.path.join(self.performance_dir, 'test_algorithms.py')
        cmd = [self.python_bin, algo_script]
        return self._run_process(cmd, cwd=self.project_path, label=f"{self.name} Performance Benchmark")

    def run_overall_test(self) -> TestResult:
        """Run full test suite: components, algorithms, simulation, and health check with consolidated summary."""
        print_section_header(f"Running Full Overall Test Suite for {self.name}")
        results: Dict[str, TestResult] = {}

        # 1. Component Unit Tests
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 1/4] Executing Component Tests...{Colors.RESET}")
        results['components'] = self.run_components_test()

        # 2. Algorithm Benchmarks
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 2/4] Executing Algorithm Verification...{Colors.RESET}")
        results['algorithms'] = self.run_algorithms_test()

        # 3. Concurrency Simulation (500 users baseline)
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 3/4] Executing Concurrency Simulation (500 Users)...{Colors.RESET}")
        results['simulation'] = self.run_simulation_test(500)

        # 4. Native Health Check
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 4/4] Executing Health Check...{Colors.RESET}")
        results['health'] = self.run_health_check()

        return render_overall_summary(self.name, results)
