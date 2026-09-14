"""
Adapter registry and factory for multi-framework support.
"""
from adapters.base import BaseAdapter, Capability
from adapters.python_adapter import PythonAdapter
from adapters.django_adapter import DjangoAdapter
from adapters.node_adapter import NodeAdapter
from adapters.registry import (
    register_adapter,
    get_registered_adapters,
    detect_adapter,
    get_adapter
)

__all__ = [
    'BaseAdapter',
    'Capability',
    'PythonAdapter',
    'DjangoAdapter',
    'NodeAdapter',
    'register_adapter',
    'get_registered_adapters',
    'detect_adapter',
    'get_adapter',
]
