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


class TestPhase8TesterService(unittest.TestCase):
    """Integration tests for TesterService hexagonal facade."""

    def setUp(self):
        from core.service import TesterService
        self.service = TesterService()

    def test_list_capabilities_returns_all_pillars(self):
        caps = self.service.list_capabilities()
        cap_ids = [c["id"] for c in caps]
        self.assertIn("components", cap_ids)
        self.assertIn("algorithms", cap_ids)
        self.assertIn("benchmarks", cap_ids)
        self.assertIn("simulation", cap_ids)
        self.assertIn("security", cap_ids)
        self.assertIn("full_suite", cap_ids)
        self.assertIn("health", cap_ids)

    def test_service_run_with_event_streaming(self):
        events = []
        def on_event(evt):
            events.append(evt)

        req = RunRequest(capability="health", options={"silent": True})
        result = self.service.run(req, on_event=on_event)

        self.assertIsInstance(result, RunResult)
        self.assertTrue(result.run_id.startswith("run-"))
        self.assertGreater(len(events), 0)
        self.assertEqual(events[0].percent, 0.0)
        self.assertEqual(events[-1].percent, 100.0)

    def test_service_run_algorithms_success(self):
        req = RunRequest(capability="algorithms")
        result = self.service.run(req)

        self.assertIsInstance(result, RunResult)
        self.assertEqual(result.status, "PASSED")
        self.assertTrue(result.is_success)
        self.assertGreater(result.metrics.get("passed", 0), 0)

    def test_service_run_unrecognized_capability(self):
        req = RunRequest(capability="unknown_custom_cap")
        result = self.service.run(req)

        self.assertIsInstance(result, RunResult)
        self.assertEqual(result.status, "UNAVAILABLE")

    def test_service_run_gui_mode_silences_terminal_and_captures_stream(self):
        import io
        import contextlib

        log_events = []
        def on_event(evt):
            if evt.level == "log":
                log_events.append(evt.message)

        terminal_capture = io.StringIO()
        with contextlib.redirect_stdout(terminal_capture):
            req = RunRequest(
                capability="algorithms",
                options={"gui_mode": True, "capture_stdout": True}
            )
            result = self.service.run(req, on_event=on_event)

        # Terminal output must be completely silent in GUI mode
        self.assertEqual(terminal_capture.getvalue().strip(), "")
        # But logs are captured into events
        self.assertGreater(len(log_events), 0)
        self.assertTrue(result.is_success)


class TestPhase8ModularCLI(unittest.TestCase):
    """Test suite for modular CLI parser and dispatchers."""

    def test_cli_parser_run_subcommand(self):
        from cli.parser import build_parser
        parser = build_parser()
        args = parser.parse_args(["run", "sample_proj", "-p", "algo", "-u", "250", "--json"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.project, "sample_proj")
        self.assertEqual(args.pillar, "algo")
        self.assertEqual(args.users, 250)
        self.assertTrue(args.json)

    def test_cli_parser_gui_flag(self):
        from cli.parser import build_parser
        parser = build_parser()
        args = parser.parse_args(["--gui"])
        self.assertTrue(args.gui)

    def test_cli_main_doctor_exit_zero(self):
        from cli.main import main
        code = main(["doctor"])
        self.assertEqual(code, 0)


class TestPhase8DesktopGUI(unittest.TestCase):
    """Test suite for desktop GUI components and async runner."""

    def test_async_runner_execution(self):
        import time
        from core.service import TesterService
        from gui.worker import AsyncTestRunner

        service = TesterService()
        runner = AsyncTestRunner(service)
        completed_results = []

        runner.start_run(
            request=RunRequest(capability="health"),
            on_event=lambda e: None,
            on_complete=lambda r: completed_results.append(r)
        )

        # Wait for worker thread to finish
        for _ in range(50):
            if completed_results:
                break
            time.sleep(0.05)

        self.assertEqual(len(completed_results), 1)
        self.assertTrue(completed_results[0].run_id.startswith("run-"))

    def test_gui_app_initialization(self):
        from gui.main import UniversalTesterApp, HAS_CTK
        if not HAS_CTK:
            self.skipTest("customtkinter is not installed")

        app = UniversalTesterApp()
        app.withdraw()
        try:
            self.assertEqual(len(app.caps_scroll.winfo_children()), 7)
            self.assertEqual(app.status_var.get(), "● READY")
        finally:
            app.destroy()



if __name__ == '__main__':
    unittest.main()



