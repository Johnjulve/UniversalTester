"""
Analytical Test Reporter & Metrics Formatter.
Parses raw test runner outputs (Django unittest, Pytest, Node/Jest) into
structured module trees, analytical metrics tables, and quality scores.
"""
import re
import sys
import time
from typing import Dict, List, Any, Optional

from core.ui import Colors, get_terminal_width, print_divider, visible_len, pad_left, pad_center

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        # Reconfiguration may fail on non-text/redirected streams or test runners
        pass

# Aliases for module backward-compatibility
_visible_len = visible_len
_pad_left = pad_left
_pad_center = pad_center


class AnalyticalTestReporter:
    """Real-time parser and analytical dashboard formatter for test runs."""

    # Unittest line regex: test_name (module.Class[.method]) ... (ok|FAIL|ERROR|skipped)
    UNITTEST_PATTERN = re.compile(
        r"^(test_\w+)\s+\(([\w\.]+)\)\s+\.\.\.\s+(ok|FAIL|ERROR|skipped.*)$",
        re.IGNORECASE
    )
    
    # Timing line regex: Ran 42 tests in 39.705s
    TIMING_PATTERN = re.compile(r"Ran (\d+) tests? in ([\d\.]+)s", re.IGNORECASE)

    def __init__(self, suite_name: str = "Component Unit Tests"):
        self.suite_name = suite_name
        self.current_module: Optional[str] = None
        self.modules: Dict[str, Dict[str, int]] = {}  # {module_name: {"total": 0, "passed": 0, "failed": 0, "skipped": 0}}
        self.total_tests: int = 0
        self.passed_tests: int = 0
        self.failed_tests: int = 0
        self.skipped_tests: int = 0
        self.duration_seconds: float = 0.0
        self.failures: List[Dict[str, str]] = []
        self._capturing_failure = False
        self._current_failure_lines: List[str] = []
        self._current_failure_title: str = ""
        self.start_time = time.time()
        self.raw_unmatched_lines: List[str] = []
        self._pending_test: Optional[tuple] = None

    def _record_test_result(self, method: str, path: str, status_upper: str):
        """Record and display an individual test execution result."""
        parts = path.split('.')
        if parts and parts[-1] == method:
            parts = parts[:-1]
        class_name = parts[-1] if parts else "Test"
        module_name = '.'.join(parts[:-1]) if len(parts) > 1 else "tests"

        clean_name = method
        if clean_name.startswith("test_"):
            clean_name = clean_name[5:]
        clean_desc = clean_name.replace("_", " ")

        if module_name not in self.modules:
            self.modules[module_name] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

        self.modules[module_name]["total"] += 1

        if module_name != self.current_module:
            self.current_module = module_name
            short_mod = module_name.split('.')[-1] if '.' in module_name else module_name
            print(f"\n  {Colors.BOLD}{Colors.BRIGHT_CYAN}📦 {short_mod}{Colors.RESET} {Colors.DIM}({module_name}){Colors.RESET}")

        if "OK" in status_upper:
            self.passed_tests += 1
            self.modules[module_name]["passed"] += 1
            print(f"    {Colors.BRIGHT_GREEN}✔{Colors.RESET} {Colors.WHITE}{class_name}{Colors.RESET} {Colors.GRAY}›{Colors.RESET} {clean_desc}")
        elif "FAIL" in status_upper or "ERROR" in status_upper:
            self.failed_tests += 1
            self.modules[module_name]["failed"] += 1
            badge = "✘ FAIL" if "FAIL" in status_upper else "✘ ERR"
            print(f"    {Colors.BRIGHT_RED}{badge}{Colors.RESET} {Colors.WHITE}{class_name}{Colors.RESET} {Colors.GRAY}›{Colors.RESET} {Colors.BRIGHT_RED}{clean_desc}{Colors.RESET}")
        else:
            self.skipped_tests += 1
            self.modules[module_name]["skipped"] += 1
            print(f"    {Colors.YELLOW}○ SKIP{Colors.RESET} {Colors.WHITE}{class_name}{Colors.RESET} {Colors.GRAY}›{Colors.RESET} {clean_desc}")

    def feed_line(self, raw_line: str):
        """Process a single line of streamed test output."""
        line = raw_line.strip()
        if not line:
            return

        # Check for noise to filter or convert to status badges
        if "Creating test database" in line or re.search(r"Found \d+ test\(s\)", line):
            print(f"  {Colors.DIM}{Colors.CYAN}⚙  [FIXTURES] Initializing ephemeral test database...{Colors.RESET}")
            return
        if "Destroying test database" in line:
            print(f"\n  {Colors.DIM}{Colors.GRAY}🧹 [TEARDOWN] Cleaning test database & memory caches...{Colors.RESET}")
            return
        if "System check identified no issues" in line:
            return

        # Check for timing line
        time_match = self.TIMING_PATTERN.search(line)
        if time_match:
            self.total_tests = int(time_match.group(1))
            self.duration_seconds = float(time_match.group(2))
            return

        # Check for test runner suite success
        if line == "OK" or line.startswith("OK ("):
            if self.total_tests > 0 and self.failed_tests == 0 and self.passed_tests < self.total_tests:
                diff = (self.total_tests - self.failed_tests - self.skipped_tests) - self.passed_tests
                self.passed_tests += diff
                if self.modules:
                    first_mod = list(self.modules.keys())[0]
                    self.modules[first_mod]["passed"] += diff
            return

        # Check for failure block header (e.g. "FAIL: test_foo", "ERROR: test_bar")
        if line.startswith("FAIL: ") or line.startswith("ERROR: "):
            self._finish_current_failure()
            self._capturing_failure = True
            self._current_failure_title = line
            self._current_failure_lines = []
            return

        if self._capturing_failure:
            if line.startswith("----------------------------------------------------------------------") or line.startswith("==="):
                self._finish_current_failure()
            else:
                self._current_failure_lines.append(line)
            return

        # Check for standard single-line unittest: test_foo (path.Class) ... ok
        match = self.UNITTEST_PATTERN.search(line)
        if match:
            method, path, status_raw = match.groups()
            self._record_test_result(method, path, status_raw.upper())
            self._pending_test = None
            return

        # Check for unittest test declaration line without status (docstrings will follow): test_foo (path.Class)
        header_match = re.search(r"(test_\w+)\s+\(([\w\.]+)\)", line)
        if header_match:
            method, path = header_match.group(1), header_match.group(2)
            status_match = re.search(r"\.\.\.\s*(ok|FAIL|ERROR|skipped.*)$", line, re.IGNORECASE)
            if status_match:
                self._record_test_result(method, path, status_match.group(1).upper())
                self._pending_test = None
            else:
                self._pending_test = (method, path)
            return

        # Check if line completes a pending test (docstring finishing with ... ok)
        if self._pending_test:
            status_match = re.search(r"\.\.\.\s*(ok|FAIL|ERROR|skipped.*)$", line, re.IGNORECASE)
            if status_match:
                method, path = self._pending_test
                self._record_test_result(method, path, status_match.group(1).upper())
                self._pending_test = None
                return

        # Check for Jest / Vitest / Node test runner lines
        if line.startswith("PASS ") or line.startswith("FAIL "):
            status_word = line.split()[0]
            suite_file = line[len(status_word):].strip()
            mod_name = os.path.basename(suite_file)
            if mod_name not in self.modules:
                self.modules[mod_name] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
            self.current_module = mod_name
            print(f"\n  {Colors.BOLD}{Colors.BRIGHT_CYAN}📦 {mod_name}{Colors.RESET} {Colors.DIM}({suite_file}){Colors.RESET}")
            return

        if line.startswith("✓ ") or line.startswith("✔ ") or line.startswith("✕ ") or line.startswith("✘ "):
            is_pass = line.startswith("✓ ") or line.startswith("✔ ")
            test_desc = line[2:].strip()
            curr_mod = self.current_module or "frontend"
            if curr_mod not in self.modules:
                self.modules[curr_mod] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
            self.modules[curr_mod]["total"] += 1
            if is_pass:
                self.passed_tests += 1
                self.modules[curr_mod]["passed"] += 1
                print(f"    {Colors.BRIGHT_GREEN}✔{Colors.RESET} {test_desc}")
            else:
                self.failed_tests += 1
                self.modules[curr_mod]["failed"] += 1
                print(f"    {Colors.BRIGHT_RED}✘ FAIL{Colors.RESET} {test_desc}")
            return

        # If not recognized, store in case we need to inspect
        self.raw_unmatched_lines.append(line)

    def _finish_current_failure(self):
        if self._capturing_failure and self._current_failure_title:
            self.failures.append({
                "title": self._current_failure_title,
                "body": "\n".join(self._current_failure_lines)
            })
            self._capturing_failure = False
            self._current_failure_lines = []
            self._current_failure_title = ""

    def render_dashboard(self) -> bool:
        """Render the complete analytical summary report and metrics table."""
        self._finish_current_failure()
        
        if self.duration_seconds <= 0.0:
            self.duration_seconds = max(time.time() - self.start_time, 0.01)
            
        if self.total_tests == 0:
            self.total_tests = self.passed_tests + self.failed_tests + self.skipped_tests

        print("\n")
        print_divider()
        
        # 1. Failure Breakdown (if any failed)
        if self.failures:
            print(f"\n{Colors.BOLD}{Colors.BRIGHT_RED}✘ DIAGNOSTIC FAILURE TRACE(S):{Colors.RESET}\n")
            for f in self.failures:
                print(f"{Colors.BG_DARK}{Colors.BRIGHT_RED} ✖ {f['title']} {Colors.RESET}")
                for l in f['body'].splitlines():
                    print(f"    {Colors.GRAY}{l}{Colors.RESET}")
                print()

        # 2. Module Analytical Breakdown Table
        w = min(get_terminal_width(), 80)
        col_mod = max(w - 38, 22)
        col_tot = 7
        col_pass = 8
        col_fail = 8
        col_stat = 10

        # Header
        h_mod = _pad_left(f" {Colors.BOLD}Test Module{Colors.RESET}", col_mod)
        h_tot = _pad_center(f"{Colors.BOLD}Tests{Colors.RESET}", col_tot)
        h_pass = _pad_center(f"{Colors.BOLD}Passed{Colors.RESET}", col_pass)
        h_fail = _pad_center(f"{Colors.BOLD}Failed{Colors.RESET}", col_fail)
        h_stat = _pad_center(f"{Colors.BOLD}Status{Colors.RESET}", col_stat)

        print(f"{Colors.DIM}┌{'─' * col_mod}┬{'─' * col_tot}┬{'─' * col_pass}┬{'─' * col_fail}┬{'─' * col_stat}┐{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET}{h_mod}{Colors.DIM}│{Colors.RESET}{h_tot}{Colors.DIM}│{Colors.RESET}{h_pass}{Colors.DIM}│{Colors.RESET}{h_fail}{Colors.DIM}│{Colors.RESET}{h_stat}{Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}├{'─' * col_mod}┼{'─' * col_tot}┼{'─' * col_pass}┼{'─' * col_fail}┼{'─' * col_stat}┤{Colors.RESET}")

        if not self.modules:
            if self.total_tests == 0 or (self.passed_tests == 0 and self.failed_tests == 0):
                status_text = f"{Colors.DIM}○ UNAVAIL{Colors.RESET}"
            elif self.failed_tests == 0:
                status_text = f"{Colors.BRIGHT_GREEN}✔ PASS{Colors.RESET}"
            else:
                status_text = f"{Colors.BRIGHT_RED}✘ FAIL{Colors.RESET}"
            c_name = _pad_left(f" {self.suite_name[:col_mod - 3]}", col_mod)
            c_tot = _pad_center(str(self.total_tests), col_tot)
            c_pass = _pad_center(str(self.passed_tests), col_pass)
            c_fail = _pad_center(str(self.failed_tests), col_fail)
            c_stat = _pad_center(status_text, col_stat)
            print(f"{Colors.DIM}│{Colors.RESET}{c_name}{Colors.DIM}│{Colors.RESET}{c_tot}{Colors.DIM}│{Colors.RESET}{c_pass}{Colors.DIM}│{Colors.RESET}{c_fail}{Colors.DIM}│{Colors.RESET}{c_stat}{Colors.DIM}│{Colors.RESET}")
        else:
            for mod_name, stats in self.modules.items():
                mod_display = mod_name if len(mod_name) <= col_mod - 3 else "..." + mod_name[-(col_mod - 6):]
                if stats["failed"] > 0:
                    mod_status = f"{Colors.BRIGHT_RED}✘ FAIL{Colors.RESET}"
                elif stats["passed"] > 0:
                    mod_status = f"{Colors.BRIGHT_GREEN}✔ PASS{Colors.RESET}"
                else:
                    mod_status = f"{Colors.DIM}○ SKIP{Colors.RESET}"
                c_name = _pad_left(f" {Colors.CYAN}{mod_display}{Colors.RESET}", col_mod)
                c_tot = _pad_center(str(stats['total']), col_tot)
                c_pass = _pad_center(str(stats['passed']), col_pass)
                c_fail = _pad_center(str(stats['failed']), col_fail)
                c_stat = _pad_center(mod_status, col_stat)
                print(f"{Colors.DIM}│{Colors.RESET}{c_name}{Colors.DIM}│{Colors.RESET}{c_tot}{Colors.DIM}│{Colors.RESET}{c_pass}{Colors.DIM}│{Colors.RESET}{c_fail}{Colors.DIM}│{Colors.RESET}{c_stat}{Colors.DIM}│{Colors.RESET}")

        # Total Footer Row
        print(f"{Colors.DIM}├{'─' * col_mod}┼{'─' * col_tot}┼{'─' * col_pass}┼{'─' * col_fail}┼{'─' * col_stat}┤{Colors.RESET}")
        active_tests = self.passed_tests + self.failed_tests
        if self.failed_tests == 0 and self.passed_tests > 0:
            overall_status = f"{Colors.BOLD}{Colors.BRIGHT_GREEN}100% OK{Colors.RESET}"
        elif active_tests == 0:
            overall_status = f"{Colors.DIM}UNAVAILABLE{Colors.RESET}"
        else:
            overall_status = f"{Colors.BOLD}{Colors.BRIGHT_RED}FAILED{Colors.RESET}"
        f_name = _pad_left(f" {Colors.BOLD}TOTAL SUITES{Colors.RESET}", col_mod)
        f_tot = _pad_center(f"{Colors.BOLD}{self.total_tests}{Colors.RESET}", col_tot)
        f_pass = _pad_center(f"{Colors.BOLD}{self.passed_tests}{Colors.RESET}", col_pass)
        f_fail = _pad_center(f"{Colors.BOLD}{self.failed_tests}{Colors.RESET}", col_fail)
        f_stat = _pad_center(overall_status, col_stat)
        print(f"{Colors.DIM}│{Colors.RESET}{f_name}{Colors.DIM}│{Colors.RESET}{f_tot}{Colors.DIM}│{Colors.RESET}{f_pass}{Colors.DIM}│{Colors.RESET}{f_fail}{Colors.DIM}│{Colors.RESET}{f_stat}{Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}└{'─' * col_mod}┴{'─' * col_tot}┴{'─' * col_pass}┴{'─' * col_fail}┴{'─' * col_stat}┘{Colors.RESET}")

        # 3. Performance & Reliability Analytics
        pass_ratio = (self.passed_tests / active_tests) if active_tests > 0 else 1.0
        bar_len = 20
        filled = int(pass_ratio * bar_len)
        bar_color = Colors.BRIGHT_GREEN if self.failed_tests == 0 else Colors.BRIGHT_RED
        bar_visual = f"{bar_color}[{'█' * filled}{'░' * (bar_len - filled)}]{Colors.RESET}"
        
        avg_time = (self.duration_seconds / self.total_tests) if self.total_tests > 0 else 0.0

        if active_tests == 0:
            grade = f"{Colors.DIM}Grade N/A (No active tests executed){Colors.RESET}"
        elif self.failed_tests == 0:
            grade = f"{Colors.BOLD}{Colors.BRIGHT_GREEN}Grade A+{Colors.RESET} (No regressions, 100% contracts verified)"
        elif pass_ratio >= 0.90:
            grade = f"{Colors.BOLD}{Colors.YELLOW}Grade B{Colors.RESET} (Minor failures detected, check diagnostics)"
        else:
            grade = f"{Colors.BOLD}{Colors.BRIGHT_RED}Grade F{Colors.RESET} (Critical failure count, immediate fix required)"

        print(f"\n{Colors.BOLD}{Colors.WHITE}📊 Performance & Quality Analysis:{Colors.RESET}")
        print(f"  • {Colors.GRAY}Execution Time   :{Colors.RESET} {self.duration_seconds:.2f}s")
        print(f"  • {Colors.GRAY}Average Per Test :{Colors.RESET} {avg_time:.2f}s / test")
        print(f"  • {Colors.GRAY}Pass Rate        :{Colors.RESET} {pass_ratio * 100:.1f}% {bar_visual}")
        print(f"  • {Colors.GRAY}System Health    :{Colors.RESET} {grade}\n")

        return self.failed_tests == 0


def render_overall_summary(project_name: str, results: Dict[str, Any]) -> Any:
    """
    Render a consolidated multi-suite analytical summary table across all executed phases.
    Handles UNAVAILABLE capabilities gracefully without penalizing system health grade.
    """
    from core.models import TestResult, TestStatus
    print_divider()
    print(f"\n{Colors.BOLD}OVERALL TEST SUITE SUMMARY FOR {project_name.upper()}:{Colors.RESET}\n")

    w = min(get_terminal_width(), 80)
    col_mod = max(w - 38, 22)
    col_tot = 7
    col_pass = 8
    col_fail = 8
    col_stat = 10

    h_mod = _pad_left(f" {Colors.BOLD}Phase / Suite{Colors.RESET}", col_mod)
    h_tot = _pad_center(f"{Colors.BOLD}Tests{Colors.RESET}", col_tot)
    h_pass = _pad_center(f"{Colors.BOLD}Passed{Colors.RESET}", col_pass)
    h_fail = _pad_center(f"{Colors.BOLD}Failed{Colors.RESET}", col_fail)
    h_stat = _pad_center(f"{Colors.BOLD}Status{Colors.RESET}", col_stat)

    print(f"{Colors.DIM}┌{'─' * col_mod}┬{'─' * col_tot}┬{'─' * col_pass}┬{'─' * col_fail}┬{'─' * col_stat}┐{Colors.RESET}")
    print(f"{Colors.DIM}│{Colors.RESET}{h_mod}{Colors.DIM}│{Colors.RESET}{h_tot}{Colors.DIM}│{Colors.RESET}{h_pass}{Colors.DIM}│{Colors.RESET}{h_fail}{Colors.DIM}│{Colors.RESET}{h_stat}{Colors.DIM}│{Colors.RESET}")
    print(f"{Colors.DIM}├{'─' * col_mod}┼{'─' * col_tot}┼{'─' * col_pass}┼{'─' * col_fail}┼{'─' * col_stat}┤{Colors.RESET}")

    total_exec = 0
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    all_passed = True
    errors = []

    for suite_key, result in results.items():
        title = suite_key.capitalize()
        if hasattr(result, 'is_unavailable') and result.is_unavailable:
            c_name = _pad_left(f" {Colors.GRAY}{title} (Unsupported){Colors.RESET}", col_mod)
            c_tot = _pad_center("-", col_tot)
            c_pass = _pad_center("-", col_pass)
            c_fail = _pad_center("-", col_fail)
            c_stat = _pad_center(f"{Colors.DIM}○ UNAVAIL{Colors.RESET}", col_stat)
            total_skipped += 1
        elif hasattr(result, 'is_success') and result.is_success:
            c_name = _pad_left(f" {Colors.CYAN}{title}{Colors.RESET}", col_mod)
            c_tot = _pad_center(str(result.total or 1), col_tot)
            c_pass = _pad_center(str(result.passed or 1), col_pass)
            c_fail = _pad_center("0", col_fail)
            c_stat = _pad_center(f"{Colors.BRIGHT_GREEN}✔ PASS{Colors.RESET}", col_stat)
            total_exec += result.total or 1
            total_passed += result.passed or 1
        else:
            c_name = _pad_left(f" {Colors.CYAN}{title}{Colors.RESET}", col_mod)
            r_tot = getattr(result, 'total', 1) or 1
            r_pass = getattr(result, 'passed', 0)
            r_fail = getattr(result, 'failed', 1) or 1
            c_tot = _pad_center(str(r_tot), col_tot)
            c_pass = _pad_center(str(r_pass), col_pass)
            c_fail = _pad_center(str(r_fail), col_fail)
            c_stat = _pad_center(f"{Colors.BRIGHT_RED}✘ FAIL{Colors.RESET}", col_stat)
            total_exec += r_tot
            total_passed += r_pass
            total_failed += r_fail
            all_passed = False
            if hasattr(result, 'errors'):
                errors.extend(result.errors)

        print(f"{Colors.DIM}│{Colors.RESET}{c_name}{Colors.DIM}│{Colors.RESET}{c_tot}{Colors.DIM}│{Colors.RESET}{c_pass}{Colors.DIM}│{Colors.RESET}{c_fail}{Colors.DIM}│{Colors.RESET}{c_stat}{Colors.DIM}│{Colors.RESET}")

    # Total Footer
    print(f"{Colors.DIM}├{'─' * col_mod}┼{'─' * col_tot}┼{'─' * col_pass}┼{'─' * col_fail}┼{'─' * col_stat}┤{Colors.RESET}")
    overall_status = f"{Colors.BOLD}{Colors.BRIGHT_GREEN}100% OK{Colors.RESET}" if all_passed and total_passed > 0 else f"{Colors.BOLD}{Colors.BRIGHT_RED}FAILED{Colors.RESET}"
    if total_exec == 0 and total_skipped > 0:
        overall_status = f"{Colors.DIM}UNAVAILABLE{Colors.RESET}"

    f_name = _pad_left(f" {Colors.BOLD}TOTAL ACTIVE{Colors.RESET}", col_mod)
    f_tot = _pad_center(f"{Colors.BOLD}{total_exec}{Colors.RESET}", col_tot)
    f_pass = _pad_center(f"{Colors.BOLD}{total_passed}{Colors.RESET}", col_pass)
    f_fail = _pad_center(f"{Colors.BOLD}{total_failed}{Colors.RESET}", col_fail)
    f_stat = _pad_center(overall_status, col_stat)
    print(f"{Colors.DIM}│{Colors.RESET}{f_name}{Colors.DIM}│{Colors.RESET}{f_tot}{Colors.DIM}│{Colors.RESET}{f_pass}{Colors.DIM}│{Colors.RESET}{f_fail}{Colors.DIM}│{Colors.RESET}{f_stat}{Colors.DIM}│{Colors.RESET}")
    print(f"{Colors.DIM}└{'─' * col_mod}┴{'─' * col_tot}┴{'─' * col_pass}┴{'─' * col_fail}┴{'─' * col_stat}┘{Colors.RESET}")

    # Grade calculation
    pass_ratio = (total_passed / total_exec) if total_exec > 0 else 1.0
    if total_exec == 0:
        grade = f"{Colors.DIM}Grade N/A (Only unavailable capabilities requested){Colors.RESET}"
    elif all_passed:
        grade = f"{Colors.BOLD}{Colors.BRIGHT_GREEN}Grade A+{Colors.RESET} (100% contracts verified)"
    elif pass_ratio >= 0.90:
        grade = f"{Colors.BOLD}{Colors.YELLOW}Grade B{Colors.RESET} (Minor failures detected)"
    else:
        grade = f"{Colors.BOLD}{Colors.BRIGHT_RED}Grade F{Colors.RESET} (Critical failure count)"

    print(f"\n{Colors.BOLD}{Colors.WHITE}📊 Overall Health Grade:{Colors.RESET} {grade}\n")

    return TestResult(
        suite_name=f"{project_name} Overall Suite",
        status=TestStatus.PASSED if all_passed else TestStatus.FAILED,
        passed=total_passed,
        failed=total_failed,
        skipped=total_skipped,
        errors=errors
    )
