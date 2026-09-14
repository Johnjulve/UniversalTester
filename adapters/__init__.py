"""
Adapter registry and factory for multi-framework support.
"""
from adapters.base import BaseAdapter, Capability
from adapters.registry import (
    register_adapter,
    get_registered_adapters,
    detect_adapter,
    get_adapter
)

__all__ = [
    'BaseAdapter',
    'Capability',
    'register_adapter',
    'get_registered_adapters',
    'detect_adapter',
    'get_adapter',
]
