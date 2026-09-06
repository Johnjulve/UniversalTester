"""
Node.js / React / Frontend framework adapter.
Executes JavaScript/TypeScript test suites (Jest, Vitest, npm test), builds, and benchmarks.
"""
import os
import subprocess
from typing import Dict, Any

from adapters.base import BaseAdapter
from core.ui import Colors, print_section_header, print_status
from core.reporter import AnalyticalTestReporter


class NodeAdapter(BaseAdapter):
    """Adapter for Node.js / React / Vite projects."""

    def __init__(self, project_config: Dict[str, Any]):
        super().__init__(project_config)
        # Check if project has a frontend subdirectory or is the frontend project itself
        frontend_sub = os.path.join(self.project_path, 'frontend')
        if os.path.exists(frontend_sub):
            self.frontend_dir = project_config.get('frontend_dir', frontend_sub)
        else:
            self.frontend_dir = project_config.get('frontend_dir', self.project_path)

    def run_components_test(self) -> bool:
        print_section_header(f"Running Frontend Unit Tests (npm test) for {self.name}")
        cmd = ['npm', 'test', '--', '--watchAll=false']
        reporter = AnalyticalTestReporter(suite_name=f"{self.name} Frontend Tests")
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
            return passed and (process.returncode == 0)
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}Error running Node test: {e}{Colors.RESET}")
            return False

    def run_simulation_test(self, concurrent_users: int) -> bool:
        print(f"{Colors.YELLOW}Node.js concurrent simulation: delegate to Locust or k6.{Colors.RESET}")
        return True

    def run_overall_test(self) -> bool:
        print_section_header(f"Running Full Overall Suite for {self.name}")
        results = {}
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 1/3] Executing Frontend Unit Tests...{Colors.RESET}")
        results['components'] = self.run_components_test()
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 2/3] Executing Algorithm Benchmarks...{Colors.RESET}")
        results['algorithms'] = self.run_algorithms_test()
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 3/3] Executing Health Check...{Colors.RESET}")
        results['health'] = self.run_health_check()
        return all(results.values())

    def run_benchmarks(self) -> bool:
        print(f"{Colors.YELLOW}Frontend benchmark: Lighthouse / bundle analyzer.{Colors.RESET}")
        return True

    def run_algorithms_test(self) -> bool:
        """Run the universal CS algorithm benchmarks."""
        algo_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Performance', 'test_algorithms.py'))
        try:
            res = subprocess.run([sys.executable, algo_script])
            return res.returncode == 0
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}Error running algorithm benchmarks: {e}{Colors.RESET}")
            return False
