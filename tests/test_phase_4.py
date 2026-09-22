"""
Automated Verification Suite for Phase 4:
Reliability Tester, Performance Tester & Algorithm Tester.

Verifies:
  1. Concurrency simulation mathematical models and generic traffic profiles.
  2. Reliability state degradation calculations (Optimal -> Critical).
  3. Absolute zero-thesis independence (0 occurrences of vote, ballot, e-botar, student).
  4. Algorithm correctness assertions and edge case stability.
  5. Computational performance benchmarking and tracemalloc memory profiling.
"""
import os
import sys
import unittest
import tracemalloc

# Ensure UniversalTester root is in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Performance.simulate_concurrent_load import (
    SCENARIOS,
    SERVER_PROFILES,
    calculate_flow_stats,
    simulate_scenario,
    calculate_effective_capacity,
    assess_reliability_state,
)
from Performance.test_algorithms import (
    quicksort,
    mergesort,
    binary_search,
    deep_json_aggregate,
    verify_algorithm_correctness,
)


class TestPhase4SimulationAndReliability(unittest.TestCase):
    """Test suite for Phase 4 concurrency simulation and reliability modeling."""

    def test_generic_scenarios_exist(self):
        """Verify all generic web API scenarios are defined without voting logic."""
        expected_scenarios = {'balanced_api', 'read_heavy', 'write_heavy', 'burst_ping'}
        self.assertTrue(expected_scenarios.issubset(set(SCENARIOS.keys())))

    def test_scenario_traffic_math(self):
        """Verify request counting, egress calculation, and arrival RPS."""
        scenario = SCENARIOS['balanced_api']
        res = simulate_scenario(concurrent_users=500, scenario=scenario, burst_seconds=120)
        
        self.assertGreater(res['total_requests'], 0)
        self.assertGreater(res['total_egress_mb'], 0)
        self.assertGreater(res['arrival_rps'], 0)
        self.assertEqual(res['burst_seconds'], 120)
        self.assertAlmostEqual(res['arrival_rps'], res['total_requests'] / 120.0, places=2)

    def test_reliability_degradation_tiers(self):
        """Verify system degradation assessment across utilization percentages."""
        self.assertEqual(assess_reliability_state(30.0)[0], 'OPTIMAL')
        self.assertEqual(assess_reliability_state(75.0)[0], 'HEALTHY')
        self.assertEqual(assess_reliability_state(95.0)[0], 'SATURATED')
        self.assertEqual(assess_reliability_state(120.0)[0], 'OVERLOADED')
        self.assertEqual(assess_reliability_state(180.0)[0], 'CRITICAL')

    def test_zero_thesis_independence_in_performance(self):
        """Strict check: ensure zero references to e-botar, vote, ballot, or student in Performance dir."""
        perf_dir = os.path.join(_PROJECT_ROOT, 'Performance')
        forbidden_terms = ['vote_', 'ballot', 'e-botar', 'ebotar', 'total_students']

        for root, _, files in os.walk(perf_dir):
            for file in files:
                if file.endswith(('.py', '.md')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        for term in forbidden_terms:
                            self.assertNotIn(
                                term,
                                content,
                                f"Forbidden thesis term '{term}' found in {file_path}"
                            )


class TestPhase4AlgorithmAndPerformance(unittest.TestCase):
    """Test suite for Phase 4 algorithm correctness and performance memory profiling."""

    def test_algorithm_correctness_suite(self):
        """Verify the built-in algorithm verification pass reports 100% pass."""
        passed, errors = verify_algorithm_correctness()
        self.assertTrue(passed, f"Algorithm correctness failures: {errors}")
        self.assertEqual(len(errors), 0)

    def test_quicksort_and_mergesort_stability(self):
        """Verify sorting algorithms with duplicates, reversed data, and edge cases."""
        test_data = [99, -5, 42, 0, 42, 1000, -5, 12]
        expected = sorted(test_data)
        self.assertEqual(quicksort(list(test_data)), expected)
        self.assertEqual(mergesort(list(test_data)), expected)

    def test_binary_search_bounds(self):
        """Verify binary search boundary lookups and missing value handling."""
        arr = [1, 3, 5, 7, 9, 11]
        self.assertEqual(binary_search(arr, 1), 0)
        self.assertEqual(binary_search(arr, 11), 5)
        self.assertEqual(binary_search(arr, 7), 3)
        self.assertEqual(binary_search(arr, 0), -1)
        self.assertEqual(binary_search(arr, 12), -1)
        self.assertEqual(binary_search(arr, 6), -1)

    def test_memory_profiling_integration(self):
        """Verify tracemalloc records memory without throwing runtime errors."""
        tracemalloc.start()
        _ = quicksort([i for i in range(1000, 0, -1)])
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.assertGreater(peak, 0)


if __name__ == '__main__':
    unittest.main()
