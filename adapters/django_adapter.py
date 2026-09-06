"""
Django framework adapter.
Executes Django manage.py tests, analytical load simulations, and algorithm benchmarks.
"""
import os
import sys
import time
import subprocess
from typing import Dict, Any

from adapters.base import BaseAdapter
from core.ui import Colors, print_section_header, print_status, print_divider


class DjangoAdapter(BaseAdapter):
    """Adapter executing tests for Django/DRF projects."""

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

    def _run_process(self, cmd: list, cwd: str, label: str) -> bool:
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
                return True
            else:
                print(f"\n{Colors.BRIGHT_RED}✘ {label} FAILED with exit code {process.returncode} ({elapsed:.2f}s){Colors.RESET}")
                return False
                
        except Exception as e:
            print(f"\n{Colors.BRIGHT_RED}✘ Process execution error: {e}{Colors.RESET}")
            return False

    def run_components_test(self) -> bool:
        """Run Tier 1 Django unit and component tests."""
        print_section_header(f"Running Component Unit Tests for {self.name}")
        cmd = [self.python_bin, 'manage.py', 'test', 'tests']
        return self._run_process(cmd, cwd=self.backend_dir, label="Component Unit Tests")

    def run_simulation_test(self, concurrent_users: int) -> bool:
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

    def run_algorithms_test(self) -> bool:
        """Run algorithm verification and execution speed tests."""
        print_section_header(f"Running Algorithm Benchmarks for {self.name}")
        algo_script = os.path.join(self.performance_dir, 'test_algorithms.py')
        cmd = [self.python_bin, algo_script]
        return self._run_process(cmd, cwd=self.project_path, label="Algorithm Benchmarks")

    def run_benchmarks(self) -> bool:
        """Run live API latency and database query smoke tests."""
        print_section_header(f"Running API Latency & Query Benchmarks for {self.name}")
        perf_script = os.path.join(self.performance_dir, 'quick_performance_test.py')
        cmd = [self.python_bin, perf_script]
        return self._run_process(cmd, cwd=self.project_path, label="Performance Benchmark")

    def run_overall_test(self) -> bool:
        """Run full test suite: components, algorithms, and 500-user simulation."""
        print_section_header(f"Running Full Overall Test Suite for {self.name}")
        
        results = {}
        
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
        all_passed = True
        for suite, passed in results.items():
            status_tag = "PASS" if passed else "FAIL"
            color = Colors.BRIGHT_GREEN if passed else Colors.BRIGHT_RED
            print_status(status_tag, f"{suite.capitalize()} Suite", color=color)
            if not passed:
                all_passed = False
                
        print()
        return all_passed
