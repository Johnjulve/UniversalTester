"""
Master Test Orchestrator & Unified 5-Pillar Coordinator.
Coordinates execution across the 5 official UniversalTester testing pillars:
  1. Adaptive Tester     : Project's ecosystem unit & component tests (pytest, vitest, jest)
  2. Algorithm Tester    : Algorithmic correctness assertions & test vectors
  3. Performance Tester  : Latency benchmarks & tracemalloc memory profiling
  4. Reliability Tester  : Concurrency traffic simulation & capacity thresholds
  5. Security Tester     : Static AST vulnerability scanning & ecosystem audits
  6. Full Assessment     : Executes all active pillars and renders a unified scorecard
"""
from typing import Dict, Any, Optional

from core.models import TestResult, TestStatus
from core.ui import Colors, print_section_header
from core.reporter import render_overall_summary
from adapters.base import BaseAdapter, Capability


class TestOrchestrator:
    """
    Central orchestration engine for UniversalTester.
    Dispatches single pillars or orchestrates the full 5-pillar assessment.
    """

    PILLAR_ALIASES: Dict[str, str] = {
        '1': 'adaptive',
        'adaptive': 'adaptive',
        'components': 'adaptive',
        'unit': 'adaptive',

        '2': 'algorithms',
        'algo': 'algorithms',
        'algorithms': 'algorithms',
        'algorithm': 'algorithms',

        '3': 'performance',
        'perf': 'performance',
        'performance': 'performance',
        'benchmarks': 'performance',

        '4': 'reliability',
        'rel': 'reliability',
        'reliability': 'reliability',
        'simulation': 'reliability',

        '5': 'security',
        'sec': 'security',
        'security': 'security',

        '6': 'all',
        'all': 'all',
        'overall': 'all',
        'full': 'all',
    }

    def __init__(self, adapter: BaseAdapter):
        self.adapter = adapter
        self.project_name = adapter.name

    def run_adaptive(self) -> TestResult:
        """Pillar 1: Adaptive Tester (Ecosystem Unit & Component Tests)."""
        print_section_header(f"[Pillar 1/5: Adaptive Tester] {self.project_name}")
        return self.adapter.run_components_test()

    def run_algorithms(self) -> TestResult:
        """Pillar 2: Algorithm Tester (Correctness Assertions & Test Vectors)."""
        print_section_header(f"[Pillar 2/5: Algorithm Tester] {self.project_name}")
        return self.adapter.run_algorithms_test()

    def run_performance(self) -> TestResult:
        """Pillar 3: Performance Tester (Speed Benchmarks & Memory Profiling)."""
        print_section_header(f"[Pillar 3/5: Performance Tester] {self.project_name}")
        return self.adapter.run_benchmarks()

    def run_reliability(self, concurrent_users: int = 500) -> TestResult:
        """Pillar 4: Reliability Tester (Concurrency Traffic & Capacity Envelope)."""
        print_section_header(f"[Pillar 4/5: Reliability Tester] {self.project_name} ({concurrent_users} Users)")
        return self.adapter.run_simulation_test(concurrent_users)

    def run_security(self) -> TestResult:
        """Pillar 5: Security Tester (Static AST Vulnerability Scan & Ecosystem Audit)."""
        print_section_header(f"[Pillar 5/5: Security Tester] {self.project_name}")
        return self.adapter.run_security_scan()

    def run_all_pillars(self, concurrent_users: int = 500) -> TestResult:
        """
        Execute the comprehensive 5-Pillar Assessment battery and render
        a consolidated analytical summary scorecard.
        """
        print_section_header(f"Universal 5-Pillar System Assessment: {self.project_name}")
        results: Dict[str, TestResult] = {}

        # 1. Adaptive Tester
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 1/5] Executing Adaptive Unit & Component Tests...{Colors.RESET}")
        results['adaptive'] = self.run_adaptive()

        # 2. Algorithm Tester
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 2/5] Executing Algorithm Verification...{Colors.RESET}")
        results['algorithms'] = self.run_algorithms()

        # 3. Performance Tester
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 3/5] Executing Computational Performance Profiling...{Colors.RESET}")
        results['performance'] = self.run_performance()

        # 4. Reliability Tester
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 4/5] Executing Concurrency Load Simulation ({concurrent_users} Users)...{Colors.RESET}")
        results['reliability'] = self.run_reliability(concurrent_users)

        # 5. Security Tester
        print(f"\n{Colors.BOLD}{Colors.CYAN}[Phase 5/5] Executing Security & Vulnerability Scan...{Colors.RESET}")
        results['security'] = self.run_security()

        # Render Unified Analytical Summary
        return render_overall_summary(self.project_name, results)

    def dispatch(self, pillar_key: str, concurrent_users: int = 500) -> TestResult:
        """Dispatch execution by pillar key or alias."""
        normalized = self.PILLAR_ALIASES.get(str(pillar_key).lower().strip())
        if not normalized:
            raise ValueError(f"Unknown testing pillar: '{pillar_key}'. Supported: adaptive, algo, perf, rel, sec, all")

        if normalized == 'adaptive':
            return self.run_adaptive()
        elif normalized == 'algorithms':
            return self.run_algorithms()
        elif normalized == 'performance':
            return self.run_performance()
        elif normalized == 'reliability':
            return self.run_reliability(concurrent_users)
        elif normalized == 'security':
            return self.run_security()
        elif normalized == 'all':
            return self.run_all_pillars(concurrent_users)
        else:
            raise ValueError(f"Unhandled pillar: {normalized}")
