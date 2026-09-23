"""
Node.js / React / Frontend framework adapter.
Executes JavaScript/TypeScript test suites (Vitest, Jest, npm test), builds, and benchmarks.
"""
import os
import json
import shutil
import subprocess
import sys
import time
from typing import Dict, Any, Set, Optional

from adapters.base import BaseAdapter, Capability
from core.models import TestResult, TestStatus
from core.ui import Colors, print_section_header, print_status, print_divider
from core.reporter import AnalyticalTestReporter, render_overall_summary


class NodeAdapter(BaseAdapter):
    """Adapter for Node.js / React / Vite projects."""

    @classmethod
    def adapter_id(cls) -> str:
        return "node"

    @classmethod
    def display_name(cls) -> str:
        return "Node.js / React / Vite Adapter"

    @classmethod
    def applies(cls, project_path: str) -> bool:
        """Check if project path contains Node/React project indicators."""
        if not project_path or not os.path.exists(project_path):
            return False
        return (
            os.path.exists(os.path.join(project_path, 'package.json')) or
            os.path.exists(os.path.join(project_path, 'frontend', 'package.json'))
        )

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which('npm') is not None or shutil.which('node') is not None

    def supported_capabilities(self) -> Set[str]:
        return {
            Capability.COMPONENTS,
            Capability.ALGORITHMS,
            Capability.HEALTH,
        }

    def __init__(self, project_config: Dict[str, Any]):
        super().__init__(project_config)
        # Check if project has an explicit or default frontend subdirectory
        configured_front = project_config.get('frontend_dir')
        if configured_front and os.path.exists(configured_front):
            self.frontend_dir = configured_front
        else:
            frontend_sub = os.path.join(self.project_path, 'frontend')
            if os.path.exists(frontend_sub):
                self.frontend_dir = frontend_sub
            else:
                self.frontend_dir = self.project_path

    def _resolve_npm_cmd(self, pkg_json_path: str) -> Optional[list]:
        """
        Inspect package.json to detect test runner and construct non-blocking test command.
        Returns command list if a test script is found, or None if no test script is configured.
        """
        try:
            with open(pkg_json_path, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
        except Exception as e:
            return None

        scripts = pkg.get('scripts', {})
        candidate_keys = ['test', 'test:unit', 'test:run', 'unit']
        selected_key = next((k for k in candidate_keys if k in scripts), None)

        if not selected_key:
            return None

        deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
        script_body = str(scripts.get(selected_key, ''))

        is_vitest = 'vitest' in deps or 'vitest' in script_body
        is_jest = 'jest' in deps or 'react-scripts' in deps or 'jest' in script_body

        if selected_key == 'test':
            cmd = ['npm', 'test']
        else:
            cmd = ['npm', 'run', selected_key]

        # Append non-blocking flags based on detected runner
        if is_vitest:
            if '--run' not in script_body and 'run' not in script_body.split():
                cmd.extend(['--', '--run'])
        elif is_jest:
            if '--watchAll=false' not in script_body and '--watch=false' not in script_body:
                cmd.extend(['--', '--watchAll=false'])

        return cmd

    def run_components_test(self) -> TestResult:
        """Run frontend unit/component tests with smart runner detection and graceful fallback."""
        suite_name = f"{self.name} Frontend Tests"
        print_section_header(f"Running Frontend Unit Tests for {self.name}")

        if not os.path.exists(self.frontend_dir):
            reason = f"Directory not found: {self.frontend_dir}"
            print_status("UNAVAIL", reason, color=Colors.DIM)
            return TestResult.unavailable(suite_name, reason)

        pkg_json = os.path.join(self.frontend_dir, 'package.json')
        if not os.path.exists(pkg_json):
            reason = f"No package.json found in {self.frontend_dir}"
            print_status("UNAVAIL", reason, color=Colors.DIM)
            return TestResult.unavailable(suite_name, reason)

        cmd = self._resolve_npm_cmd(pkg_json)
        if not cmd:
            reason = "No 'test' script defined in package.json"
            print_status("UNAVAIL", reason, color=Colors.DIM)
            return TestResult.unavailable(suite_name, reason)

        print(f"\n{Colors.DIM}Executing: {' '.join(cmd)} (cwd: {self.frontend_dir}){Colors.RESET}\n")
        reporter = AnalyticalTestReporter(suite_name=suite_name)
        start_time = time.time()
        try:
            process = subprocess.Popen(
                cmd,
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                shell=True
            )
            for line in iter(process.stdout.readline, ''):
                reporter.feed_line(line)
            process.wait()
            passed = reporter.render_dashboard()
            elapsed = time.time() - start_time
            success = passed and (process.returncode == 0)

            return TestResult(
                suite_name=suite_name,
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                passed=reporter.passed_tests,
                failed=reporter.failed_tests,
                skipped=reporter.skipped_tests,
                duration=reporter.duration_seconds or elapsed,
                errors=[f['title'] for f in reporter.failures]
            )
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}Error running Node test: {e}{Colors.RESET}")
            return TestResult(suite_name=suite_name, status=TestStatus.ERROR, failed=1, errors=[str(e)])

    def run_simulation_test(self, concurrent_users: int) -> TestResult:
        suite_name = f"{self.name} Concurrency Simulation"
        reason = "Node.js concurrent traffic simulation is not configured for this project."
        print(f"{Colors.DIM}○ {suite_name}: {reason}{Colors.RESET}")
        return TestResult.unavailable(suite_name, reason)

    def run_benchmarks(self) -> TestResult:
        suite_name = f"{self.name} Frontend Benchmarks"
        reason = "Frontend Lighthouse / bundle size benchmark is not configured."
        print(f"{Colors.DIM}○ {suite_name}: {reason}{Colors.RESET}")
        return TestResult.unavailable(suite_name, reason)

    def run_algorithms_test(self) -> TestResult:
        """Run the universal CS algorithm benchmarks."""
        print_section_header(f"Running Algorithm Benchmarks for {self.name}")
        algo_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Performance', 'algorithm_tester.py'))
        start_time = time.time()
        try:
            res = subprocess.run([sys.executable, algo_script])
            elapsed = time.time() - start_time
            success = (res.returncode == 0)
            return TestResult.from_bool(f"{self.name} Algorithms", success, duration=elapsed)
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}Error running algorithm benchmarks: {e}{Colors.RESET}")
            return TestResult(suite_name=f"{self.name} Algorithms", status=TestStatus.ERROR, failed=1, errors=[str(e)])

    def run_overall_test(self) -> TestResult:
        """Run full test suite: components, algorithms, and health check with consolidated summary."""
        print_section_header(f"Running Full Overall Suite for {self.name}")
        results: Dict[str, TestResult] = {}

        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 1/3] Executing Frontend Unit Tests...{Colors.RESET}")
        results['components'] = self.run_components_test()

        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 2/3] Executing Algorithm Benchmarks...{Colors.RESET}")
        results['algorithms'] = self.run_algorithms_test()

        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 3/3] Executing Health Check...{Colors.RESET}")
        results['health'] = self.run_health_check()

        return render_overall_summary(self.name, results)
