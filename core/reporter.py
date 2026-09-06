"""
Analytical Test Reporter & Metrics Formatter.
Parses raw test runner outputs (Django unittest, Pytest, Node/Jest) into
structured module trees, analytical metrics tables, and quality scores.
"""
import re
import sys
import time
from typing import Dict, List, Any, Optional

from core.ui import Colors, get_terminal_width, print_divider

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def _visible_len(s: str) -> int:
    """Return the visible string length excluding ANSI escape sequences."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))


def _pad_left(s: str, width: int) -> str:
    """Pad string on the right so it aligns to the left within visible width."""
    v = _visible_len(s)
    return s + (' ' * max(width - v, 0))


def _pad_center(s: str, width: int) -> str:
    """Center string based on its visible width."""
    v = _visible_len(s)
    pad = max(width - v, 0)
    left = pad // 2
    right = pad - left
    return (' ' * left) + s + (' ' * right)


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

    def feed_line(self, raw_line: str):
        """Process a single line of streamed test output."""
        line = raw_line.strip()
        if not line:
            return

        # Check for noise to filter or convert to status badges
        if "Creating test database" in line or "Found 42 test(s)" in line:
            print(f"  {Colors.DIM}{Colors.CYAN}⚙  [FIXTURES] Initializing ephemeral test database...{Colors.RESET}")
            return
        if "Destroying test database" in line:
            print(f"\n  {Colors.DIM}{Colors.GRAY}🧹 [TEARDOWN] Cleaning test database & memory caches...{Colors.RESET}")
            return
        if "System check identified no issues" in line or "Updated legacy vote receipts" in line:
            return

        # Check for timing line
        time_match = self.TIMING_PATTERN.search(line)
        if time_match:
            self.total_tests = int(time_match.group(1))
            self.duration_seconds = float(time_match.group(2))
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

        # Check for unittest result line
        match = self.UNITTEST_PATTERN.match(line)
        if match:
            method, path, status_raw = match.groups()
            status_upper = status_raw.upper()

            # Parse path into module and class
            parts = path.split('.')
            if parts and parts[-1] == method:
                parts = parts[:-1]
            class_name = parts[-1] if parts else "Test"
            module_name = '.'.join(parts[:-1]) if len(parts) > 1 else "tests"

            # Clean method name for high human readability
            clean_name = method
            if clean_name.startswith("test_"):
                clean_name = clean_name[5:]
            clean_desc = clean_name.replace("_", " ")

            # Init module stats if new
            if module_name not in self.modules:
                self.modules[module_name] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

            self.modules[module_name]["total"] += 1

            # Print module header when entering new module
            if module_name != self.current_module:
                self.current_module = module_name
                short_mod = module_name.split('.')[-1] if '.' in module_name else module_name
                print(f"\n  {Colors.BOLD}{Colors.BRIGHT_CYAN}📦 {short_mod}{Colors.RESET} {Colors.DIM}({module_name}){Colors.RESET}")

            # Status handling
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
            status_text = f"{Colors.BRIGHT_GREEN}✔ PASS{Colors.RESET}" if self.failed_tests == 0 else f"{Colors.BRIGHT_RED}✘ FAIL{Colors.RESET}"
            c_name = _pad_left(f" {self.suite_name[:col_mod - 3]}", col_mod)
            c_tot = _pad_center(str(self.total_tests), col_tot)
            c_pass = _pad_center(str(self.passed_tests), col_pass)
            c_fail = _pad_center(str(self.failed_tests), col_fail)
            c_stat = _pad_center(status_text, col_stat)
            print(f"{Colors.DIM}│{Colors.RESET}{c_name}{Colors.DIM}│{Colors.RESET}{c_tot}{Colors.DIM}│{Colors.RESET}{c_pass}{Colors.DIM}│{Colors.RESET}{c_fail}{Colors.DIM}│{Colors.RESET}{c_stat}{Colors.DIM}│{Colors.RESET}")
        else:
            for mod_name, stats in self.modules.items():
                mod_display = mod_name if len(mod_name) <= col_mod - 3 else "..." + mod_name[-(col_mod - 6):]
                mod_status = f"{Colors.BRIGHT_GREEN}✔ PASS{Colors.RESET}" if stats["failed"] == 0 else f"{Colors.BRIGHT_RED}✘ FAIL{Colors.RESET}"
                c_name = _pad_left(f" {Colors.CYAN}{mod_display}{Colors.RESET}", col_mod)
                c_tot = _pad_center(str(stats['total']), col_tot)
                c_pass = _pad_center(str(stats['passed']), col_pass)
                c_fail = _pad_center(str(stats['failed']), col_fail)
                c_stat = _pad_center(mod_status, col_stat)
                print(f"{Colors.DIM}│{Colors.RESET}{c_name}{Colors.DIM}│{Colors.RESET}{c_tot}{Colors.DIM}│{Colors.RESET}{c_pass}{Colors.DIM}│{Colors.RESET}{c_fail}{Colors.DIM}│{Colors.RESET}{c_stat}{Colors.DIM}│{Colors.RESET}")

        # Total Footer Row
        print(f"{Colors.DIM}├{'─' * col_mod}┼{'─' * col_tot}┼{'─' * col_pass}┼{'─' * col_fail}┼{'─' * col_stat}┤{Colors.RESET}")
        overall_status = f"{Colors.BOLD}{Colors.BRIGHT_GREEN}100% OK{Colors.RESET}" if self.failed_tests == 0 and self.total_tests > 0 else f"{Colors.BOLD}{Colors.BRIGHT_RED}FAILED{Colors.RESET}"
        f_name = _pad_left(f" {Colors.BOLD}TOTAL SUITES{Colors.RESET}", col_mod)
        f_tot = _pad_center(f"{Colors.BOLD}{self.total_tests}{Colors.RESET}", col_tot)
        f_pass = _pad_center(f"{Colors.BOLD}{self.passed_tests}{Colors.RESET}", col_pass)
        f_fail = _pad_center(f"{Colors.BOLD}{self.failed_tests}{Colors.RESET}", col_fail)
        f_stat = _pad_center(overall_status, col_stat)
        print(f"{Colors.DIM}│{Colors.RESET}{f_name}{Colors.DIM}│{Colors.RESET}{f_tot}{Colors.DIM}│{Colors.RESET}{f_pass}{Colors.DIM}│{Colors.RESET}{f_fail}{Colors.DIM}│{Colors.RESET}{f_stat}{Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}└{'─' * col_mod}┴{'─' * col_tot}┴{'─' * col_pass}┴{'─' * col_fail}┴{'─' * col_stat}┘{Colors.RESET}")

        # 3. Performance & Reliability Analytics
        pass_ratio = (self.passed_tests / self.total_tests) if self.total_tests > 0 else 1.0
        bar_len = 20
        filled = int(pass_ratio * bar_len)
        bar_color = Colors.BRIGHT_GREEN if self.failed_tests == 0 else Colors.BRIGHT_RED
        bar_visual = f"{bar_color}[{'█' * filled}{'░' * (bar_len - filled)}]{Colors.RESET}"
        
        avg_time = (self.duration_seconds / self.total_tests) if self.total_tests > 0 else 0.0

        if self.failed_tests == 0:
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
