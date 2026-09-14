"""
Node.js / React / Frontend framework adapter.
Executes JavaScript/TypeScript test suites (Vitest, Jest, npm test), builds, and benchmarks.
"""
import os
import subprocess
import sys
import time
from typing import Dict, Any, Set

from adapters.base import BaseAdapter, Capability
from core.models import TestResult, TestStatus
from core.ui import Colors, print_section_header, print_status, print_divider
from core.reporter import AnalyticalTestReporter


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
        import shutil
        return shutil.which('npm') is not None or shutil.which('node') is not None

    def supported_capabilities(self) -> Set[str]:
        return {
            Capability.COMPONENTS,
            Capability.ALGORITHMS,
            Capability.HEALTH,
        }

    def __init__(self, project_config: Dict[str, Any]):
        super().__init__(project_config)
        # Check if project has a frontend subdirectory or is the frontend project itself
        frontend_sub = os.path.join(self.project_path, 'frontend')
        if os.path.exists(frontend_sub):
            self.frontend_dir = project_config.get('frontend_dir', frontend_sub)
        else:
            self.frontend_dir = project_config.get('frontend_dir', self.project_path)

    def run_components_test(self) -> TestResult:
        suite_name = f"{self.name} Frontend Tests"
        print_section_header(f"Running Frontend Unit Tests (npm test) for {self.name}")
        
        if not os.path.exists(self.frontend_dir):
            reason = f"Directory not found: {self.frontend_dir}"
            print_status("UNAVAIL", reason, color=Colors.DIM)
            return TestResult.unavailable(suite_name, reason)

        pkg_json = os.path.join(self.frontend_dir, 'package.json')
        if not os.path.exists(pkg_json):
            reason = f"No package.json found in {self.frontend_dir}"
            print_status("UNAVAIL", reason, color=Colors.DIM)
            return TestResult.unavailable(suite_name, reason)

        cmd = ['npm', 'test', '--', '--watchAll=false']
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
        algo_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Performance', 'test_algorithms.py'))
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
        print_section_header(f"Running Full Overall Suite for {self.name}")
        results: Dict[str, TestResult] = {}
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 1/3] Executing Frontend Unit Tests...{Colors.RESET}")
        results['components'] = self.run_components_test()
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 2/3] Executing Algorithm Benchmarks...{Colors.RESET}")
        results['algorithms'] = self.run_algorithms_test()
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 3/3] Executing Health Check...{Colors.RESET}")
        results['health'] = self.run_health_check()
        
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
