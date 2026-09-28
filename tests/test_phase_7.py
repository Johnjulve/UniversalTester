"""
Automated Verification Suite for Phase 7:
Cross-Language Algorithm Benchmarks (Python • Node.js • Dart).

Verifies:
  1. Standardized JSON output contracts across all available runtime backends.
  2. Algorithmic correctness assertions for Heap Sort, Hash Table, Fibonacci, and Monte Carlo Pi.
  3. Graceful handling of missing host binaries without crashing the engine.
  4. Integration with run_cross_language_benchmarks in Performance/algorithm_tester.py.
"""
import os
import sys
import json
import shutil
import unittest
import subprocess

# Ensure UniversalTester root is in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Performance.runners.algo_bench import execute_all_benchmarks as py_execute
from Performance.algorithm_tester import run_cross_language_benchmarks


class TestPhase7CrossLanguageBenchmarks(unittest.TestCase):
    """Test suite for Phase 7 multi-runtime algorithm benchmarks and schema conformity."""

    @classmethod
    def setUpClass(cls):
        cls.runners_dir = os.path.join(_PROJECT_ROOT, 'Performance', 'runners')
        cls.schema_path = os.path.join(_PROJECT_ROOT, 'Performance', 'contracts', 'algo_result_schema.json')

    def test_01_schema_contract_file_exists_and_valid_json(self):
        """Verify algo_result_schema.json exists and is valid JSON."""
        self.assertTrue(os.path.exists(self.schema_path), "Schema contract file missing")
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        self.assertEqual(schema.get("title"), "CrossLanguageAlgorithmBenchmarkResult")
        self.assertIn("heap_sort", schema["properties"]["workloads"]["properties"])
        self.assertIn("hash_table", schema["properties"]["workloads"]["properties"])
        self.assertIn("fibonacci", schema["properties"]["workloads"]["properties"])
        self.assertIn("monte_carlo_pi", schema["properties"]["workloads"]["properties"])

    def test_02_python_runner_contract_and_correctness(self):
        """Verify Python runner generates valid contract and passes all assertions."""
        result = py_execute(dataset_size=5000, lookup_keys=500, fib_n=25, pi_samples=50000)
        self.assertEqual(result["runtime"], "python")
        self.assertIn("Python", result["version"])
        self.assertGreater(result["total_duration_ms"], 0)

        workloads = result["workloads"]
        self.assertTrue(workloads["heap_sort"]["correctness_verified"])
        self.assertGreater(workloads["heap_sort"]["comparisons"], 0)
        self.assertGreater(workloads["heap_sort"]["swaps"], 0)

        self.assertTrue(workloads["hash_table"]["correctness_verified"])
        self.assertEqual(workloads["hash_table"]["found_count"], 250)

        self.assertTrue(workloads["fibonacci"]["correctness_verified"])
        self.assertEqual(workloads["fibonacci"]["expected_result"], 75025)  # fib(25) = 75025

        self.assertTrue(workloads["monte_carlo_pi"]["correctness_verified"])
        self.assertLess(workloads["monte_carlo_pi"]["absolute_error"], 0.05)

    def test_03_node_runner_cli_json_contract(self):
        """Verify Node.js runner CLI execution and JSON conformity if node is installed."""
        node_bin = shutil.which('node')
        if not node_bin:
            self.skipTest("Node.js runtime not installed on host PATH")

        script = os.path.join(self.runners_dir, 'algo_bench.js')
        res = subprocess.run(
            [node_bin, script, '--json', '--dataset', '5000', '--lookups', '500', '--fib-n', '25', '--samples', '50000'],
            capture_output=True,
            text=True,
            timeout=15
        )
        self.assertEqual(res.returncode, 0, f"Node runner failed: {res.stderr}")
        data = json.loads(res.stdout)

        self.assertEqual(data["runtime"], "node")
        self.assertIn("Node.js", data["version"])
        self.assertTrue(data["workloads"]["heap_sort"]["correctness_verified"])
        self.assertTrue(data["workloads"]["hash_table"]["correctness_verified"])
        self.assertTrue(data["workloads"]["fibonacci"]["correctness_verified"])
        self.assertEqual(data["workloads"]["fibonacci"]["expected_result"], 75025)
        self.assertTrue(data["workloads"]["monte_carlo_pi"]["correctness_verified"])

    def test_04_dart_runner_cli_json_contract(self):
        """Verify Dart runner CLI execution and JSON conformity if dart is installed."""
        dart_bin = shutil.which('dart')
        if not dart_bin:
            self.skipTest("Dart SDK runtime not installed on host PATH")

        script = os.path.join(self.runners_dir, 'algo_bench.dart')
        res = subprocess.run(
            [dart_bin, script, '--json', '--dataset', '5000', '--lookups', '500', '--fib-n', '25', '--samples', '50000'],
            capture_output=True,
            text=True,
            timeout=15
        )
        self.assertEqual(res.returncode, 0, f"Dart runner failed: {res.stderr}")
        data = json.loads(res.stdout)

        self.assertEqual(data["runtime"], "dart")
        self.assertIn("Dart", data["version"])
        self.assertTrue(data["workloads"]["heap_sort"]["correctness_verified"])
        self.assertTrue(data["workloads"]["hash_table"]["correctness_verified"])
        self.assertTrue(data["workloads"]["fibonacci"]["correctness_verified"])
        self.assertEqual(data["workloads"]["fibonacci"]["expected_result"], 75025)
        self.assertTrue(data["workloads"]["monte_carlo_pi"]["correctness_verified"])

    def test_05_matrix_orchestrator_execution(self):
        """Verify run_cross_language_benchmarks executes and passes across active runtimes."""
        passed = run_cross_language_benchmarks(
            dataset_size=5000,
            lookup_keys=500,
            fib_n=25,
            pi_samples=50000
        )
        self.assertTrue(passed, "Cross-language benchmark matrix failed assertion pass")


if __name__ == '__main__':
    unittest.main()
