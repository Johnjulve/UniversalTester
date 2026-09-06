"""
Base adapter interface for multi-framework test execution.
Enables expanding the Universal Tester to Node, React, Go, FastAPI, etc.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAdapter(ABC):
    """Abstract interface defining required test runner hooks for any project type."""

    def __init__(self, project_config: Dict[str, Any]):
        self.config = project_config
        self.name = project_config.get('name', 'Unknown Project')
        self.project_path = project_config.get('path', '')

    @abstractmethod
    def run_components_test(self) -> bool:
        """Run fast component/unit test suite."""
        pass

    @abstractmethod
    def run_simulation_test(self, concurrent_users: int) -> bool:
        """Run concurrent load simulation."""
        pass

    @abstractmethod
    def run_overall_test(self) -> bool:
        """Run comprehensive system & component suite."""
        pass

    @abstractmethod
    def run_benchmarks(self) -> bool:
        """Run performance/latency benchmarks."""
        pass

    @abstractmethod
    def run_algorithms_test(self) -> bool:
        """Run algorithm verification & performance checks."""
        pass
