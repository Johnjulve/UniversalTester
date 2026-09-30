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

    def test_gui_app_active_capability_highlight(self):
        from gui.main import UniversalTesterApp, HAS_CTK
        if not HAS_CTK:
            self.skipTest("customtkinter is not installed")

        app = UniversalTesterApp()
        app.withdraw()
        try:
            self.assertIn("components", app.cap_buttons)
            self.assertIn("full_suite", app.cap_buttons)
            app._set_active_capability("components")
            self.assertEqual(app.active_capability, "components")
            self.assertEqual(app.cap_buttons["components"].cget("fg_color"), ("#0284c7", "#0369a1"))
            self.assertEqual(app.cap_buttons["full_suite"].cget("fg_color"), ("gray75", "gray25"))
        finally:
            app.destroy()

    def test_gui_app_select_capability_flow(self):
        from gui.main import UniversalTesterApp, HAS_CTK
        if not HAS_CTK:
            self.skipTest("customtkinter is not installed")

        app = UniversalTesterApp()
        app.withdraw()
        try:
            app._select_capability("components")
            self.assertEqual(app.active_capability, "components")
            self.assertIn("Unit & Component Tests", app.active_test_var.get())
            self.assertEqual(app.status_var.get(), "● READY")
            self.assertEqual(app.action_btn.cget("text"), "Start Test")
            self.assertEqual(app.action_btn.cget("fg_color"), "#10b981")
            self.assertFalse(app.runner.is_running())
        finally:
            app.destroy()

    def test_gui_app_log_text_read_only_and_highlightable(self):
        from gui.main import UniversalTesterApp, HAS_CTK
        if not HAS_CTK:
            self.skipTest("customtkinter is not installed")

        app = UniversalTesterApp()
        app.withdraw()
        try:
            # 1. State must be disabled so user cannot delete or type text
            self.assertEqual(app.log_text.cget("state"), "disabled")

            # 2. Programmatic logging appends text properly
            app._append_log("Test Line 1\nTest Line 2\n")
            content = app.log_text.get("1.0", "end")
            self.assertIn("Test Line 1", content)
            self.assertEqual(app.log_text.cget("state"), "disabled")

            # 3. Text is highlightable and selectable
            app.log_text._textbox.tag_add("sel", "1.0", "1.11")
            sel_text = app.log_text._textbox.get("sel.first", "sel.last")
            self.assertEqual(sel_text, "Test Line 1")

            # 4. Clearing resets content while preserving disabled state
            app._clear_log()
            self.assertEqual(app.log_text.get("1.0", "end").strip(), "")
            self.assertEqual(app.log_text.cget("state"), "disabled")
        finally:
            app.destroy()

    def test_reporter_accurate_pass_rate_and_unavailable_capabilities(self):
        import tempfile
        import os
        import io
        import contextlib
        from core.reporter import AnalyticalTestReporter
        from core.service import TesterService

        # 1. When 0 tests run, pass rate must be N/A (not fake 100%)
        rep_empty = AnalyticalTestReporter("Empty Suite")
        cap_empty = io.StringIO()
        with contextlib.redirect_stdout(cap_empty):
            res = rep_empty.render_dashboard()
        self.assertFalse(res)
        self.assertIn("N/A (0 active tests)", cap_empty.getvalue())
        self.assertNotIn("100.0%", cap_empty.getvalue())

        # 2. When failures occur, pass rate must reflect actual fraction
        rep_partial = AnalyticalTestReporter("Partial Suite")
        rep_partial.feed_line("test_1 (mod.C) ... ok")
        rep_partial.feed_line("test_2 (mod.C) ... FAIL")
        cap_partial = io.StringIO()
        with contextlib.redirect_stdout(cap_partial):
            res_partial = rep_partial.render_dashboard()
        self.assertFalse(res_partial)
        self.assertIn("50.0%", cap_partial.getvalue())

        # 3. Dynamic availability: non-project directory flags capabilities as unavailable
        with tempfile.TemporaryDirectory() as td:
            service = TesterService()
            caps = service.list_capabilities(td)
            cap_dict = {c["id"]: c["available"] for c in caps}
            self.assertFalse(cap_dict["components"])
            self.assertFalse(cap_dict["algorithms"])
            self.assertFalse(cap_dict["full_suite"])
            self.assertTrue(cap_dict["health"])

    def test_reliability_simulation_high_concurrency_degradation_and_diagnostics(self):
        from Performance.reliability_tester import evaluate_reliability_sla, SCENARIOS, SERVER_PROFILES

        # 1. At 2000 users across all servers, capacity is exceeded and pass rate must lower (<100%)
        scenarios = [SCENARIOS["balanced_api"]]
        servers = list(SERVER_PROFILES.keys())
        concurrent_list = [10, 25, 50, 100, 200, 500, 1000, 2000]

        summary = evaluate_reliability_sla(scenarios, servers, concurrent_list, burst_seconds=120)
        self.assertGreater(summary["failed"], 0)
        self.assertLess(summary["pass_rate"], 100.0)
        self.assertGreater(len(summary["causes"]), 0)
        self.assertGreater(len(summary["remediations"]), 0)

        # 2. Check that root causes explain overload and mention specific remedy areas
        cause_text = " ".join(summary["causes"]).lower()
        self.assertIn("capacity exceeded", cause_text)
        rem_text = " ".join(summary["remediations"]).lower()
        self.assertIn("worker", rem_text)
        self.assertIn("database", rem_text)

        # 3. At low concurrency (50 users), pass rate must remain 100%
        summary_low = evaluate_reliability_sla(scenarios, servers, [10, 25, 50], burst_seconds=120)
        self.assertEqual(summary_low["failed"], 0)
        self.assertEqual(summary_low["pass_rate"], 100.0)
        self.assertEqual(len(summary_low["causes"]), 0)

    def test_session_memory_tracking(self):
        from core.ui import get_session_memory_mb
        mem = get_session_memory_mb()
        self.assertIsInstance(mem, dict)
        self.assertIn("current_mb", mem)
        self.assertIn("peak_mb", mem)
        self.assertGreaterEqual(mem["peak_mb"], 0.0)

    def test_benchmark_caution_sla_threshold(self):
        from core.models import TestResult, TestStatus
        from core.reporter import render_overall_summary
        import io, contextlib

        res_caution = TestResult(
            suite_name="Simulation (2000 Users)",
            status=TestStatus.PASSED,
            passed=20,
            failed=3, # 3 overloaded tiers out of 23 = 87% pass rate (within tolerable SLA)
            errors=["High load queue buildup"]
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            overall = render_overall_summary("TestTarget", {"simulation": res_caution})
        self.assertEqual(overall.status, TestStatus.PASSED)
        self.assertIn("CAUTION", out.getvalue())

    def test_gui_concurrency_selector(self):
        try:
            import customtkinter as ctk
            from gui.main import UniversalTesterGUI
        except ImportError:
            self.skipTest("customtkinter not available for GUI test")

        app = UniversalTesterGUI()
        try:
            self.assertTrue(hasattr(app, "concurrency_var"))
            self.assertTrue(hasattr(app, "concurrency_menu"))
            self.assertTrue(hasattr(app, "concurrency_box"))
            self.assertEqual(app.concurrency_var.get(), "200")

            # 1. Verify presets and ComboBox custom support
            options = app.concurrency_menu.cget("values")
            self.assertIn("2000", options)
            self.assertIn("50", options)

            # 2. Conditional visibility: hidden on components test
            app._select_capability("components")
            self.assertEqual(app.concurrency_box.winfo_manager(), "")

            # 3. Conditional visibility: visible on simulation and full_suite
            app._select_capability("simulation")
            self.assertEqual(app.concurrency_box.winfo_manager(), "pack")
            app._select_capability("full_suite")
            self.assertEqual(app.concurrency_box.winfo_manager(), "pack")

            # 4. Custom user count rather than just fixed 2000
            app.concurrency_var.set("3500")
            app._select_capability("simulation")
            self.assertIn("3500 Users", app.active_test_var.get())
        finally:
            app.destroy()


if __name__ == '__main__':
    unittest.main()



