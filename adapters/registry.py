"""
Adapter registry and dynamic ecosystem discovery engine.
Automatically scans target projects to detect and instantiate the appropriate test adapter.
"""
import os
from typing import Dict, Any, Type, Optional, List

from adapters.base import BaseAdapter


# Global registry mapping adapter_id -> AdapterClass
_ADAPTER_REGISTRY: Dict[str, Type[BaseAdapter]] = {}

# Priority list for dynamic detection (order matters)
_DETECTION_ORDER: List[Type[BaseAdapter]] = []


def register_adapter(adapter_cls: Type[BaseAdapter]) -> Type[BaseAdapter]:
    """Register an adapter class with the central registry."""
    aid = adapter_cls.adapter_id().lower()
    _ADAPTER_REGISTRY[aid] = adapter_cls
    if adapter_cls not in _DETECTION_ORDER:
        _DETECTION_ORDER.append(adapter_cls)
    return adapter_cls


def get_registered_adapters() -> Dict[str, Type[BaseAdapter]]:
    """Return dictionary of all registered adapters."""
    _ensure_defaults_registered()
    return dict(_ADAPTER_REGISTRY)


def detect_adapter(project_path: str) -> Optional[Type[BaseAdapter]]:
    """
    Dynamically scan a directory path to auto-detect its matching ecosystem adapter.
    Returns the first matching adapter class, or None if unrecognized.
    """
    if not project_path or not os.path.exists(project_path):
        return None

    _ensure_defaults_registered()

    # Normalize path
    norm_path = os.path.abspath(project_path)

    for adapter_cls in _DETECTION_ORDER:
        try:
            if adapter_cls.applies(norm_path):
                return adapter_cls
        except Exception:
            continue

    return None


def get_adapter(project_config: Dict[str, Any]) -> BaseAdapter:
    """
    Factory returning the instantiated adapter for a given project configuration.
    Resolves by explicit 'type' first, then falls back to filesystem auto-detection.
    """
    _ensure_defaults_registered()

    p_type = (project_config.get('type') or '').lower().strip()
    p_path = project_config.get('path', '')

    # 1. Direct type resolution from registry or known aliases
    type_aliases = {
        'django': 'django',
        'python': 'django',
        'fastapi': 'django',
        'flask': 'django',
        'node': 'node',
        'react': 'node',
        'vite': 'node',
        'next': 'node',
        'nextjs': 'node',
        'javascript': 'node',
        'typescript': 'node',
    }
    
    target_id = type_aliases.get(p_type, p_type)
    if target_id in _ADAPTER_REGISTRY:
        return _ADAPTER_REGISTRY[target_id](project_config)

    # 2. Dynamic auto-detection based on project files
    detected_cls = detect_adapter(p_path)
    if detected_cls:
        return detected_cls(project_config)

    # 3. Default fallback
    default_cls = _ADAPTER_REGISTRY.get('django') or list(_ADAPTER_REGISTRY.values())[0]
    return default_cls(project_config)


def _ensure_defaults_registered():
    """Ensure core built-in adapters (Django, Node) are registered."""
    if not _ADAPTER_REGISTRY:
        from adapters.django_adapter import DjangoAdapter
        from adapters.node_adapter import NodeAdapter
        register_adapter(DjangoAdapter)
        register_adapter(NodeAdapter)
