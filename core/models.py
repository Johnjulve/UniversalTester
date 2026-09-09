"""
Core data models and standardized test result structures.
"""
from dataclasses import dataclass, field
from typing import List, Optional

class TestStatus:
    """Standardized test execution status strings"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"

@dataclass
class TestResult:
    suite_name: str
    status: str = TestStatus.PASSED
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration: float = 0.0
    errors: List[str] = field(default_factory=list)
    raw_output: str = ""

    @property
    def total(self) -> int:
        """Total number of executed test cases."""
        return self.passed + self.failed + self.skipped
    @property
    def is_success(self) -> bool:
        """Helper to check if the test suite succeeded with zero failures or errors."""
        return self.status == TestStatus.PASSED and self.failed == 0 and len(self.errors) == 0
    @classmethod
    def from_bool(cls, suite_name: str, success: bool, duration: float = 0.0, raw_output: str = "") -> 'TestResult':
        """Convenience constructor to convert boolean test results during migration."""
        return cls(
            suite_name=suite_name,
            status=TestStatus.PASSED if success else TestStatus.FAILED,
            passed=1 if success else 0,
            failed=0 if success else 1,
            duration=duration,
            raw_output=raw_output
        )