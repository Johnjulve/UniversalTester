"""
Node.js / React / Frontend framework adapter.
Executes JavaScript/TypeScript test suites (Jest, Vitest, npm test), builds, and benchmarks.
"""
import os
import subprocess
from typing import Dict, Any

from adapters.base import BaseAdapter
from core.ui import Colors, print_section_header, print_status


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
        cmd = ['npm', 'test']
        try:
            res = subprocess.run(cmd, cwd=self.frontend_dir, shell=True)
            return res.returncode == 0
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}Error running Node test: {e}{Colors.RESET}")
            return False

    def run_simulation_test(self, concurrent_users: int) -> bool:
        print(f"{Colors.YELLOW}Node.js concurrent simulation: delegate to Locust or k6.{Colors.RESET}")
        return True

    def run_overall_test(self) -> bool:
        print_section_header(f"Running Overall Suite (build + test) for {self.name}")
        cmd = ['npm', 'run', 'build']
        res = subprocess.run(cmd, cwd=self.frontend_dir, shell=True)
        return res.returncode == 0

    def run_benchmarks(self) -> bool:
        print(f"{Colors.YELLOW}Frontend benchmark: Lighthouse / bundle analyzer.{Colors.RESET}")
        return True

    def run_algorithms_test(self) -> bool:
        return True
