"""
MonitorPy - A plugin-based website and service monitoring system.

This package provides a flexible and extensible system for monitoring
websites, SSL certificates, mail servers, and other network services.
"""
from monitorpy.core import (
    CheckResult,
    MonitorPlugin,
    registry,
    register_plugin,
    run_check
)

__version__ = '0.1.0'
__author__ = 'MonitorPy Team'

__all__ = [
    'CheckResult',
    'MonitorPlugin',
    'registry',
    'register_plugin',
    'run_check'
]
