"""
Django framework adapter (backwards compatibility alias for PythonAdapter).
Executes Django manage.py tests, analytical load simulations, and algorithm benchmarks.
"""
from typing import Set
from adapters.python_adapter import PythonAdapter
from adapters.base import Capability


class DjangoAdapter(PythonAdapter):
    """Adapter executing tests for Django/DRF projects (subclass of PythonAdapter)."""

    @classmethod
    def adapter_id(cls) -> str:
        return "django"

    @classmethod
    def display_name(cls) -> str:
        return "Python / Django Adapter"
