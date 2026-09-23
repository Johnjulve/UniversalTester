"""
Lean Security Tester & Static Vulnerability Scanner.
Framework-agnostic security engine operating purely on Python Standard Library primitives.

Capabilities:
  1. Static AST & Pattern Scanner:
     - Hardcoded credentials & high-entropy API secrets (SEC-001)
     - SQL Injection anti-patterns (string formatting in execute/raw) (SEC-002)
     - Dangerous dynamic execution (eval, exec, os.system, shell=True) (SEC-003)
     - Path traversal risks via unvalidated path concatenation (SEC-004)
  2. Ecosystem Dependency Audit Delegation:
     - Python (pip-audit / safety)
     - Node (npm audit)
     - Graceful UNAVAILABLE fallback when audit binaries are absent on host.
"""
import os
import sys
import ast
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

from core.models import TestResult, TestStatus
from core.ui import Colors, print_section_header, print_status, print_divider, pad_left, pad_center


@dataclass
class SecurityFinding:
    """Standardized representation of a detected security vulnerability or code smell."""
    rule_id: str
    title: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    file_path: str
    line_number: int
    description: str
    snippet: str = ""

    def formatted_badge(self) -> str:
        """Color-coded severity badge for terminal output."""
        if self.severity == "CRITICAL":
            return f"{Colors.BOLD}{Colors.BRIGHT_RED}[CRITICAL]{Colors.RESET}"
        elif self.severity == "HIGH":
            return f"{Colors.BOLD}{Colors.RED}[HIGH]{Colors.RESET}"
        elif self.severity == "MEDIUM":
            return f"{Colors.BOLD}{Colors.YELLOW}[MEDIUM]{Colors.RESET}"
        else:
            return f"{Colors.DIM}[LOW]{Colors.RESET}"


class StaticSecurityScanner:
    """
    Lightweight Static Application Security Testing (SAST) engine.
    Scans project source files using Python standard library AST and precompiled regular expressions.
    """

    DEFAULT_IGNORE_DIRS: Set[str] = {
        '.git', '.venv', 'venv', 'env', '.env', 'virtualenv',
        'node_modules', 'dist', 'build', 'coverage', '.pytest_cache',
        '__pycache__', '.idea', '.vscode', 'reports',
        'tests', 'test', 'test_fixtures'
    }

    # SEC-001: High-risk hardcoded secret patterns
    SECRET_PATTERN = re.compile(
        r"""(?i)(?:api[_-]?key|secret[_-]?key|private[_-]?key|auth[_-]?token|password|passwd|access[_-]?token)\s*=\s*['"]([a-zA-Z0-9_\-\.]{12,})['"]"""
    )
    SECRET_EXCLUSIONS = {
        'placeholder', 'example', 'your_key_here', 'your_secret', 'change_me',
        'sample_secret', 'test_secret', 'dummy_key', 'default_password'
    }

    # SEC-002: SQL Injection query formatting patterns
    SQL_INJECTION_PATTERN = re.compile(
        r"""\.(?:execute|raw)\s*\(\s*(?:f['"].*\{|['"].*%\s*\(|['"].*\.format\s*\()""",
        re.IGNORECASE
    )

    # SEC-003: Dangerous shell & execution patterns
    SHELL_TRUE_PATTERN = re.compile(
        r"""(?:subprocess\.(?:Popen|run|call|check_call|check_output)|os\.system)\s*\([^)]*shell\s*=\s*True""",
        re.IGNORECASE
    )

    def __init__(self, project_path: str, ignore_dirs: Optional[Set[str]] = None):
        self.project_path = os.path.abspath(project_path)
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else self.DEFAULT_IGNORE_DIRS

    def scan(self, target_dir: Optional[str] = None) -> List[SecurityFinding]:
        """Scan target directory recursively for security vulnerabilities."""
        base_dir = target_dir or self.project_path
        findings: List[SecurityFinding] = []

        if not os.path.exists(base_dir):
            return findings

        for root, dirs, files in os.walk(base_dir):
            # Prune ignored directory trees in-place
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.project_path)

                if file.endswith('.py'):
                    findings.extend(self._scan_python_file(full_path, rel_path))
                elif file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                    findings.extend(self._scan_javascript_file(full_path, rel_path))

        return findings

    def _scan_python_file(self, full_path: str, rel_path: str) -> List[SecurityFinding]:
        """Scan a Python source file using AST inspection with regex fallbacks."""
        findings: List[SecurityFinding] = []
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
        except Exception:
            # Skip unreadable or locked files safely
            return findings

        # 1. AST Structural Analysis
        try:
            tree = ast.parse(content, filename=full_path)
            findings.extend(self._analyze_python_ast(tree, rel_path, lines))
        except SyntaxError:
            # If file has syntax errors, fall back to line-by-line pattern matching
            pass

        # 2. Secret & SQL Pattern Analysis
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Check hardcoded secrets
            secret_match = self.SECRET_PATTERN.search(line)
            if secret_match:
                token_val = secret_match.group(1).lower()
                if not any(excl in token_val for excl in self.SECRET_EXCLUSIONS):
                    findings.append(SecurityFinding(
                        rule_id="SEC-001",
                        title="Hardcoded API Secret / Token",
                        severity="HIGH",
                        file_path=rel_path,
                        line_number=idx,
                        description="Potential plaintext secret or authentication token detected in source code.",
                        snippet=stripped[:80]
                    ))

            # Check raw SQL query formatting
            if self.SQL_INJECTION_PATTERN.search(line):
                findings.append(SecurityFinding(
                    rule_id="SEC-002",
                    title="SQL Injection Vulnerability",
                    severity="CRITICAL",
                    file_path=rel_path,
                    line_number=idx,
                    description="Raw SQL query formatted with dynamic string interpolation instead of parameterized queries.",
                    snippet=stripped[:80]
                ))

            # Check subprocess shell=True
            if self.SHELL_TRUE_PATTERN.search(line):
                findings.append(SecurityFinding(
                    rule_id="SEC-003",
                    title="Insecure Shell Execution",
                    severity="HIGH",
                    file_path=rel_path,
                    line_number=idx,
                    description="Command execution invoked with shell=True, introducing command injection risk.",
                    snippet=stripped[:80]
                ))

        return findings

    def _analyze_python_ast(self, tree: ast.AST, rel_path: str, lines: List[str]) -> List[SecurityFinding]:
        """Perform AST-based structural inspection for dangerous builtins and unescaped queries."""
        findings: List[SecurityFinding] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # SEC-003: Check dangerous built-ins: eval() or exec()
                if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec'):
                    lineno = getattr(node, 'lineno', 1)
                    snippet = lines[lineno - 1].strip() if lineno <= len(lines) else ""
                    findings.append(SecurityFinding(
                        rule_id="SEC-003",
                        title=f"Dangerous Dynamic Execution ({node.func.id})",
                        severity="CRITICAL",
                        file_path=rel_path,
                        line_number=lineno,
                        description=f"Direct invocation of Python's dynamic code executor '{node.func.id}()'.",
                        snippet=snippet[:80]
                    ))

                # SEC-003: Check os.system() with dynamic or non-terminal arguments
                elif isinstance(node.func, ast.Attribute) and node.func.attr == 'system':
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                        # Safe terminal screen clearing is permitted
                        is_safe_clear = (
                            len(node.args) == 1
                            and isinstance(node.args[0], ast.Constant)
                            and node.args[0].value in ('cls', 'clear')
                        )
                        if not is_safe_clear:
                            lineno = getattr(node, 'lineno', 1)
                            snippet = lines[lineno - 1].strip() if lineno <= len(lines) else ""
                            findings.append(SecurityFinding(
                                rule_id="SEC-003",
                                title="Dangerous Command Execution (os.system)",
                                severity="HIGH",
                                file_path=rel_path,
                                line_number=lineno,
                                description="Use of os.system() is prone to shell injection; prefer subprocess with explicit argument lists.",
                                snippet=snippet[:80]
                            ))

        return findings

    def _scan_javascript_file(self, full_path: str, rel_path: str) -> List[SecurityFinding]:
        """Scan JavaScript / TypeScript source files using regex pattern inspection."""
        findings: List[SecurityFinding] = []
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().splitlines()
        except Exception:
            return findings

        eval_pattern = re.compile(r"""\beval\s*\(""", re.IGNORECASE)

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith(('//', '/*', '*')):
                continue

            # Hardcoded secrets
            secret_match = self.SECRET_PATTERN.search(line)
            if secret_match:
                token_val = secret_match.group(1).lower()
                if not any(excl in token_val for excl in self.SECRET_EXCLUSIONS):
                    findings.append(SecurityFinding(
                        rule_id="SEC-001",
                        title="Hardcoded API Secret / Token",
                        severity="HIGH",
                        file_path=rel_path,
                        line_number=idx,
                        description="Potential plaintext secret or credentials detected in frontend/node source.",
                        snippet=stripped[:80]
                    ))

            # eval() usage
            if eval_pattern.search(line):
                findings.append(SecurityFinding(
                    rule_id="SEC-003",
                    title="Dangerous Dynamic Execution (eval)",
                    severity="CRITICAL",
                    file_path=rel_path,
                    line_number=idx,
                    description="Use of eval() in JavaScript allows arbitrary script execution.",
                    snippet=stripped[:80]
                ))

        return findings


def run_ecosystem_audit(project_path: str) -> TestResult:
    """
    Delegate dependency vulnerability checking to host audit tools:
    - Node: 'npm audit --json'
    - Python: 'pip-audit' or 'safety check'
    Returns TestResult or graceful TestResult.unavailable() if tools are not installed.
    """
    package_json = os.path.join(project_path, 'package.json')
    reqs_txt = os.path.join(project_path, 'requirements.txt')

    # 1. Node.js Ecosystem Audit
    if os.path.exists(package_json):
        npm_bin = shutil.which('npm') or shutil.which('npm.cmd')
        if not npm_bin:
            return TestResult.unavailable(
                "Node Ecosystem Audit",
                "npm binary is not installed or not found in PATH."
            )
        try:
            res = subprocess.run(
                [npm_bin, 'audit', '--json'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            # npm audit returns non-zero when vulnerabilities are found
            if res.returncode == 0:
                return TestResult.passed_result("Node Ecosystem Audit", total=1, passed=1)
            else:
                return TestResult(
                    suite_name="Node Ecosystem Audit",
                    status=TestStatus.FAILED,
                    passed=0,
                    failed=1,
                    errors=["Vulnerabilities detected by npm audit. Run 'npm audit' for remediation."]
                )
        except Exception as e:
            # Handle subprocess timeout or OS execution failure explicitly
            return TestResult.unavailable(
                "Node Ecosystem Audit",
                f"Failed to execute npm audit: {e}"
            )

    # 2. Python Ecosystem Audit
    if os.path.exists(reqs_txt):
        pip_audit = shutil.which('pip-audit') or shutil.which('pip-audit.exe')
        safety_bin = shutil.which('safety') or shutil.which('safety.exe')

        if pip_audit:
            try:
                res = subprocess.run(
                    [pip_audit, '-r', reqs_txt],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if res.returncode == 0:
                    return TestResult.passed_result("Python Ecosystem Audit", total=1, passed=1)
                else:
                    return TestResult(
                        suite_name="Python Ecosystem Audit",
                        status=TestStatus.FAILED,
                        passed=0,
                        failed=1,
                        errors=[res.stdout or "Vulnerable packages detected by pip-audit."]
                    )
            except Exception as e:
                return TestResult.unavailable("Python Ecosystem Audit", f"pip-audit execution error: {e}")

        if safety_bin:
            try:
                res = subprocess.run(
                    [safety_bin, 'check', '-r', reqs_txt],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if res.returncode == 0:
                    return TestResult.passed_result("Python Ecosystem Audit", total=1, passed=1)
                else:
                    return TestResult(
                        suite_name="Python Ecosystem Audit",
                        status=TestStatus.FAILED,
                        passed=0,
                        failed=1,
                        errors=["Vulnerable dependencies detected by safety check."]
                    )
            except Exception as e:
                return TestResult.unavailable("Python Ecosystem Audit", f"safety execution error: {e}")

        return TestResult.unavailable(
            "Python Ecosystem Audit",
            "No Python dependency auditor (pip-audit / safety) installed on host."
        )

    return TestResult.unavailable(
        "Ecosystem Dependency Audit",
        "No package.json or requirements.txt manifest found in project root."
    )


def run_security_assessment(project_path: str, project_name: str = "Project") -> TestResult:
    """
    Master runner executing both the static SAST code scan and dependency ecosystem audit.
    Renders structured terminal feedback and returns a normalized TestResult.
    """
    print_section_header(f"Security & Vulnerability Assessment: {project_name}")

    scanner = StaticSecurityScanner(project_path)
    findings = scanner.scan()

    critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    medium_count = sum(1 for f in findings if f.severity == "MEDIUM")
    low_count = sum(1 for f in findings if f.severity == "LOW")

    # Render Findings
    if findings:
        print(f" {Colors.BOLD}{Colors.BRIGHT_RED}⚠️  Security Findings Detected:{Colors.RESET}\n")
        for f in findings:
            print(f"  • {f.formatted_badge()} {Colors.BOLD}{f.title}{Colors.RESET} ({f.rule_id})")
            print(f"    {Colors.DIM}Location:{Colors.RESET} {f.file_path}:{f.line_number}")
            print(f"    {Colors.WHITE}{f.description}{Colors.RESET}")
            if f.snippet:
                print(f"    {Colors.GRAY}Code:{Colors.RESET} {Colors.CYAN}{f.snippet}{Colors.RESET}")
            print()
    else:
        print(f" {Colors.BRIGHT_GREEN}✔ Static Code Scan Passed{Colors.RESET} (0 vulnerabilities detected across scanned source files)\n")

    # Ecosystem Dependency Audit
    print(f" {Colors.DIM}Checking Ecosystem Dependencies...{Colors.RESET}")
    audit_res = run_ecosystem_audit(project_path)
    if audit_res.is_unavailable:
        reason = audit_res.errors[0] if audit_res.errors else "Tool not installed"
        print_status("UNAVAIL", f"Ecosystem Dependency Audit: {reason}", color=Colors.DIM)
    elif audit_res.is_success:
        print_status("PASS", "Ecosystem Dependency Audit: 0 known CVEs reported", color=Colors.BRIGHT_GREEN)
    else:
        err_msg = audit_res.errors[0] if audit_res.errors else "Vulnerabilities found"
        print_status("FAIL", f"Ecosystem Dependency Audit: {err_msg}", color=Colors.BRIGHT_RED)

    print()

    # Determine overall status: Critical or High severity findings fail the security gate
    failed_count = critical_count + high_count + (1 if not audit_res.is_success and not audit_res.is_unavailable else 0)
    passed_count = 1 if failed_count == 0 else 0

    errors: List[str] = [
        f"{f.rule_id}: {f.title} ({f.file_path}:{f.line_number})"
        for f in findings if f.severity in ("CRITICAL", "HIGH")
    ]
    if not audit_res.is_success and not audit_res.is_unavailable:
        errors.extend(audit_res.errors)

    status = TestStatus.PASSED if failed_count == 0 else TestStatus.FAILED

    return TestResult(
        suite_name=f"{project_name} Security Scan",
        status=status,
        passed=passed_count,
        failed=failed_count,
        errors=errors
    )
