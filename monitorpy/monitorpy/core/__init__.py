"""
Core module for the monitorpy package.

This module provides the foundational components of the monitoring system.
"""

from monitorpy.core.result import CheckResult
from monitorpy.core.plugin_base import MonitorPlugin
from monitorpy.core.registry import registry, register_plugin, run_check, PluginRegistry

__all__ = [
    "CheckResult",
    "MonitorPlugin",
    "registry",
    "register_plugin",
    "run_check",
    "PluginRegistry",
]
