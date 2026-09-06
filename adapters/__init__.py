"""
Adapter registry and factory for multi-framework support.
"""
from typing import Dict, Any
from adapters.base import BaseAdapter
from adapters.django_adapter import DjangoAdapter
from adapters.node_adapter import NodeAdapter


def get_adapter(project_config: Dict[str, Any]) -> BaseAdapter:
    """Factory returning the appropriate framework adapter."""
    p_type = project_config.get('type', 'django').lower()
    
    if p_type in ('django', 'python'):
        return DjangoAdapter(project_config)
    elif p_type in ('node', 'react', 'vite'):
        return NodeAdapter(project_config)
    else:
        # Default to Django for E-Botar projects
        return DjangoAdapter(project_config)
