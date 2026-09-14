"""
Verification test script for Phase 3: Dual Smart Adapters & Reporter UNAVAILABLE handling.
"""
import tempfile
import json
import os
import sys

# Ensure repository root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from adapters import NodeAdapter, PythonAdapter, DjangoAdapter, get_adapter, detect_adapter
from core.models import TestResult, TestStatus
from core.reporter import render_overall_summary


def test_node_adapter():
    print("--- 1. Testing NodeAdapter ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Case A: Missing package.json
        adapter = NodeAdapter({'id': 'test_node', 'name': 'Test Node', 'path': tmpdir})
        res1 = adapter.run_components_test()
        assert res1.is_unavailable, f"Expected unavailable, got {res1.status}"
        print("  ✔ Case A: Missing package.json -> UNAVAILABLE confirmed")

        # Case B: package.json without test script
        pkg_path = os.path.join(tmpdir, 'package.json')
        with open(pkg_path, 'w', encoding='utf-8') as f:
            json.dump({'name': 'sample', 'scripts': {'build': 'vite build'}}, f)
        res2 = adapter.run_components_test()
        assert res2.is_unavailable, f"Expected unavailable, got {res2.status}"
        assert any("No 'test' script" in err for err in res2.errors)
        print("  ✔ Case B: Missing test script -> UNAVAILABLE confirmed")

        # Case C: Vitest detection
        with open(pkg_path, 'w', encoding='utf-8') as f:
            json.dump({'name': 'sample', 'scripts': {'test': 'vitest'}, 'devDependencies': {'vitest': '^1.0.0'}}, f)
        cmd_vitest = adapter._resolve_npm_cmd(pkg_path)
        assert '--run' in cmd_vitest, f"Expected --run in cmd, got {cmd_vitest}"
        print(f"  ✔ Case C: Vitest detected correctly: {' '.join(cmd_vitest)}")

        # Case D: Jest detection
        with open(pkg_path, 'w', encoding='utf-8') as f:
            json.dump({'name': 'sample', 'scripts': {'test': 'react-scripts test'}, 'dependencies': {'react-scripts': '5.0.0'}}, f)
        cmd_jest = adapter._resolve_npm_cmd(pkg_path)
        assert '--watchAll=false' in cmd_jest, f"Expected --watchAll=false in cmd, got {cmd_jest}"
        print(f"  ✔ Case D: Jest detected correctly: {' '.join(cmd_jest)}")


def test_python_adapter():
    print("\n--- 2. Testing PythonAdapter & Dynamic Runner Detection ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Case A: Empty directory without tests
        py_adapter = PythonAdapter({'id': 'test_py', 'name': 'Test Python', 'path': tmpdir})
        res_py = py_adapter.run_components_test()
        assert res_py.is_unavailable, f"Expected unavailable, got {res_py.status}"
        print("  ✔ Case A: No test files -> UNAVAILABLE confirmed")

        # Case B: Django manage.py runner detection
        with open(os.path.join(tmpdir, 'manage.py'), 'w', encoding='utf-8') as f:
            f.write("# fake manage.py\n")
        os.makedirs(os.path.join(tmpdir, 'tests'))
        runner = py_adapter._detect_test_runner()
        assert runner is not None, "Expected runner to be detected"
        assert runner['type'] == 'django', f"Expected django, got {runner['type']}"
        assert 'manage.py' in runner['cmd']
        print(f"  ✔ Case B: Django manage.py detected: {' '.join(runner['cmd'])}")

        # Case C: DjangoAdapter subclass compatibility
        django_adapter = DjangoAdapter({'id': 'test_django', 'name': 'Test Django', 'path': tmpdir})
        assert django_adapter.adapter_id() == 'django'
        assert isinstance(django_adapter, PythonAdapter)
        print("  ✔ Case C: DjangoAdapter backwards-compatible subclass confirmed")


def test_reporter_summary():
    print("\n--- 3. Testing Reporter render_overall_summary Table ---")
    mock_results = {
        'components': TestResult.unavailable('Frontend Tests', 'No test runner configured in package.json'),
        'algorithms': TestResult(suite_name='Algorithms Benchmark', status=TestStatus.PASSED, passed=4, failed=0, duration=0.15),
        'health': TestResult(suite_name='Health Check', status=TestStatus.PASSED, passed=1, failed=0, duration=0.05),
    }

    summary_res = render_overall_summary('Mock Frontend App', mock_results)
    assert summary_res.is_success, "Summary should be successful when non-unavailable tests pass"
    assert summary_res.skipped == 1, f"Expected 1 skipped, got {summary_res.skipped}"
    assert summary_res.passed == 5, f"Expected 5 passed active tests, got {summary_res.passed}"
    print("  ✔ Reporter render_overall_summary handled UNAVAILABLE capability without health penalty!")


if __name__ == '__main__':
    test_node_adapter()
    test_python_adapter()
    test_reporter_summary()
    print("\n🎉 ALL PHASE 3 VERIFICATION GATES PASSED SUCCESSFULLY!")
