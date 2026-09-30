"""
Verification test suite for Phase 8: Hexagonal Architecture, Data Contracts & Facade.
"""
import unittest
from core.models import RunRequest, RunResult, TestStatus
from core.events import ProgressEvent


class TestPhase8DataContracts(unittest.TestCase):
    """Test suite for serializable RunRequest, RunResult, and ProgressEvent contracts."""

    def test_run_request_serialization(self):
        req = RunRequest(
            capability="benchmark",
            project_path="/sample/path",
            options={"runtime": "python", "iterations": 5}
        )
        data = req.to_dict()
        self.assertEqual(data["capability"], "benchmark")
        self.assertEqual(data["project_path"], "/sample/path")
        self.assertEqual(data["options"]["runtime"], "python")

        reconstructed = RunRequest.from_dict(data)
        self.assertEqual(reconstructed.capability, req.capability)
        self.assertEqual(reconstructed.project_path, req.project_path)
        self.assertEqual(reconstructed.options, req.options)

    def test_run_result_serialization(self):
        res = RunResult(
            run_id="run-12345",
            status=TestStatus.PASSED,
            metrics={"duration_ms": 12.5, "passed": 10},
            duration_s=0.0125,
            details=[{"test": "Quicksort", "passed": True}],
            raw_output="All tests passed"
        )
        self.assertTrue(res.is_success)

        data = res.to_dict()
        self.assertEqual(data["run_id"], "run-12345")
        self.assertEqual(data["status"], "PASSED")
        self.assertEqual(data["metrics"]["passed"], 10)

        reconstructed = RunResult.from_dict(data)
        self.assertEqual(reconstructed.run_id, res.run_id)
        self.assertEqual(reconstructed.status, res.status)
        self.assertTrue(reconstructed.is_success)
        self.assertEqual(reconstructed.details, res.details)

    def test_progress_event_serialization(self):
        evt = ProgressEvent(
            run_id="run-99",
            step="sha256",
            percent=40.0,
            message="Hashing test vectors",
            level="info"
        )
        data = evt.to_dict()
        self.assertEqual(data["step"], "sha256")
        self.assertEqual(data["percent"], 40.0)

        reconstructed = ProgressEvent.from_dict(data)
        self.assertEqual(reconstructed.run_id, evt.run_id)
        self.assertEqual(reconstructed.step, evt.step)
        self.assertEqual(reconstructed.percent, evt.percent)
        self.assertEqual(reconstructed.message, evt.message)


if __name__ == '__main__':
    unittest.main()
