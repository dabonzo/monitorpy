"""
Core module for the monitorpy package.

This module provides the foundational components of the monitoring system.
"""

from monitorpy.core.result import CheckResult
from monitorpy.core.plugin_base import MonitorPlugin
from monitorpy.core.registry import registry, register_plugin, run_check, PluginRegistry
from monitorpy.core.batch_runner import run_checks_in_parallel, run_check_batch

__all__ = [
    "CheckResult",
    "MonitorPlugin",
    "registry",
    "register_plugin",
    "run_check",
    "PluginRegistry",
    "run_checks_in_parallel",
    "run_check_batch",
]
