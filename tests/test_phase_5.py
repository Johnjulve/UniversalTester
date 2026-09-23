"""
Automated Verification Suite for Phase 5:
Lean Security Tester & Static Vulnerability Scanner.

Verifies:
  1. Static AST detection of dangerous dynamic execution (eval, exec, os.system).
  2. SQL injection pattern detection in raw query execution.
  3. High-entropy hardcoded secret detection with exclusion rules.
  4. JavaScript/TypeScript pattern detection.
  5. Zero false-positives on clean UniversalTester codebase.
  6. BaseAdapter capability integration and graceful ecosystem audit fallbacks.
"""
import os
import sys
import tempfile
import unittest

# Ensure UniversalTester root is in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.security import (
    StaticSecurityScanner,
    SecurityFinding,
    run_ecosystem_audit,
    run_security_assessment
)
from core.models import TestResult, TestStatus
from adapters.base import Capability, BaseAdapter


class TestPhase5StaticSecurityScanner(unittest.TestCase):
    """Test suite for Phase 5 static security rules and AST inspection."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_file(self, filename: str, content: str) -> str:
        path = os.path.join(self.temp_dir.name, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def test_sec_001_hardcoded_secrets(self):
        """Verify SEC-001 flags real secret tokens while ignoring safe placeholders."""
        code = """
# Real high-risk credentials
api_key = "sk_live_99887766554433221100"
db_password = "superSecretPassword123!"

# Safe placeholder exclusions
sample_key = "your_key_here"
default_pass = "change_me"
"""
        self._write_file("test_secrets.py", code)
        scanner = StaticSecurityScanner(self.temp_dir.name)
        findings = scanner.scan()

        secret_findings = [f for f in findings if f.rule_id == "SEC-001"]
        self.assertGreaterEqual(len(secret_findings), 1)
        self.assertTrue(any("api_key" in f.snippet for f in secret_findings))
        # Placeholders should not trigger findings
        self.assertFalse(any("your_key_here" in f.snippet for f in secret_findings))

    def test_sec_002_sql_injection_patterns(self):
        """Verify SEC-002 flags unescaped dynamic string interpolation in SQL queries."""
        code = """
def fetch_user(db, user_id):
    # Vulnerable f-string query
    db.execute(f"SELECT * FROM users WHERE id = {user_id}")
    
    # Safe parameterized query (should not flag)
    db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
"""
        self._write_file("test_sql.py", code)
        scanner = StaticSecurityScanner(self.temp_dir.name)
        findings = scanner.scan()

        sql_findings = [f for f in findings if f.rule_id == "SEC-002"]
        self.assertEqual(len(sql_findings), 1)
        self.assertEqual(sql_findings[0].severity, "CRITICAL")
        self.assertIn("SELECT * FROM users", sql_findings[0].snippet)

    def test_sec_003_dangerous_dynamic_execution(self):
        """Verify SEC-003 flags eval(), exec(), os.system(), and shell=True."""
        code = """
import os
import subprocess

def run_user_code(user_payload):
    eval(user_payload)
    exec(user_payload)
    os.system("echo " + user_payload)
    subprocess.Popen("ls " + user_payload, shell=True)
"""
        self._write_file("test_exec.py", code)
        scanner = StaticSecurityScanner(self.temp_dir.name)
        findings = scanner.scan()

        exec_findings = [f for f in findings if f.rule_id == "SEC-003"]
        self.assertGreaterEqual(len(exec_findings), 3)
        rules = {f.title for f in exec_findings}
        self.assertTrue(any("eval" in r for r in rules))
        self.assertTrue(any("exec" in r for r in rules))
        self.assertTrue(any("os.system" in r for r in rules))

    def test_javascript_eval_and_secret_scanning(self):
        """Verify JavaScript/TypeScript files are scanned for eval and secret tokens."""
        js_code = """
// Client auth token
const authToken = "auth_tok_abcdef1234567890";

function parseFormula(rawFormula) {
    return eval(rawFormula);
}
"""
        self._write_file("frontend_test.js", js_code)
        scanner = StaticSecurityScanner(self.temp_dir.name)
        findings = scanner.scan()

        self.assertTrue(any(f.rule_id == "SEC-001" for f in findings))
        self.assertTrue(any(f.rule_id == "SEC-003" and "eval" in f.title for f in findings))


class TestPhase5IntegrationAndCapabilities(unittest.TestCase):
    """Test suite for adapter capabilities, clean codebase scan, and ecosystem audit."""

    def test_clean_self_scan_zero_critical_vulnerabilities(self):
        """Verify UniversalTester's own core codebase produces 0 critical or high findings."""
        core_dir = os.path.join(_PROJECT_ROOT, 'core')
        scanner = StaticSecurityScanner(core_dir)
        findings = scanner.scan()

        critical_or_high = [f for f in findings if f.severity in ("CRITICAL", "HIGH")]
        self.assertEqual(
            len(critical_or_high),
            0,
            f"Unexpected vulnerabilities detected in core/: {[f.title for f in critical_or_high]}"
        )

    def test_base_adapter_security_capability(self):
        """Verify Capability.SECURITY is registered and BaseAdapter supports it by default."""
        self.assertEqual(Capability.SECURITY, "security")

        class DummyAdapter(BaseAdapter):
            @classmethod
            def adapter_id(cls): return "dummy"
            @classmethod
            def display_name(cls): return "Dummy"
            @classmethod
            def applies(cls, path): return True
            @classmethod
            def is_available(cls): return True
            def run_components_test(self): return TestResult.passed_result("Dummy")
            def run_simulation_test(self, users): return TestResult.passed_result("Dummy")
            def run_overall_test(self): return TestResult.passed_result("Dummy")
            def run_benchmarks(self): return TestResult.passed_result("Dummy")
            def run_algorithms_test(self): return TestResult.passed_result("Dummy")

        adapter = DummyAdapter({"name": "TestProject", "path": _PROJECT_ROOT})
        self.assertTrue(adapter.has_capability(Capability.SECURITY))
        self.assertIn(Capability.SECURITY, adapter.supported_capabilities())

    def test_ecosystem_audit_graceful_handling(self):
        """Verify run_ecosystem_audit returns TestResult and handles missing tools gracefully."""
        res = run_ecosystem_audit(_PROJECT_ROOT)
        self.assertIsInstance(res, TestResult)
        self.assertIn(res.status, [TestStatus.PASSED, TestStatus.FAILED, TestStatus.UNAVAILABLE])


from core.orchestrator import TestOrchestrator


class TestPhase5Orchestrator(unittest.TestCase):
    """Test suite for master 5-pillar orchestrator and dispatch routing."""

    def setUp(self):
        class MockAdapter(BaseAdapter):
            @classmethod
            def adapter_id(cls): return "mock"
            @classmethod
            def display_name(cls): return "Mock"
            @classmethod
            def applies(cls, path): return True
            @classmethod
            def is_available(cls): return True
            def run_components_test(self): return TestResult.passed_result("Mock Components")
            def run_simulation_test(self, users): return TestResult.passed_result("Mock Simulation")
            def run_overall_test(self): return TestResult.passed_result("Mock Overall")
            def run_benchmarks(self): return TestResult.passed_result("Mock Benchmarks")
            def run_algorithms_test(self): return TestResult.passed_result("Mock Algorithms")
            def run_security_scan(self): return TestResult.passed_result("Mock Security")

        self.mock_adapter = MockAdapter({"name": "MockProject", "path": _PROJECT_ROOT})
        self.orchestrator = TestOrchestrator(self.mock_adapter)

    def test_orchestrator_individual_pillars(self):
        """Verify each of the 5 official pillars executes and returns TestResult."""
        res_adap = self.orchestrator.run_adaptive()
        self.assertTrue(res_adap.is_success)

        res_algo = self.orchestrator.run_algorithms()
        self.assertTrue(res_algo.is_success)

        res_perf = self.orchestrator.run_performance()
        self.assertTrue(res_perf.is_success)

        res_rel = self.orchestrator.run_reliability(100)
        self.assertTrue(res_rel.is_success)

        res_sec = self.orchestrator.run_security()
        self.assertTrue(res_sec.is_success)

    def test_orchestrator_dispatch_aliases(self):
        """Verify dispatch recognizes all standard pillar keys and aliases."""
        aliases = [
            ('1', 'Mock Components'),
            ('adaptive', 'Mock Components'),
            ('algo', 'Mock Algorithms'),
            ('perf', 'Mock Benchmarks'),
            ('rel', 'Mock Simulation'),
            ('sec', 'Mock Security'),
        ]
        for key, expected_suite in aliases:
            res = self.orchestrator.dispatch(key)
            self.assertEqual(res.suite_name, expected_suite)

    def test_orchestrator_invalid_pillar_raises(self):
        """Verify invalid pillar name raises ValueError."""
        with self.assertRaises(ValueError):
            self.orchestrator.dispatch('invalid_pillar_name')

    def test_orchestrator_full_assessment(self):
        """Verify run_all_pillars returns consolidated overall result."""
        res = self.orchestrator.run_all_pillars(concurrent_users=200)
        self.assertIsInstance(res, TestResult)
        self.assertTrue(res.is_success)


if __name__ == '__main__':
    unittest.main()

