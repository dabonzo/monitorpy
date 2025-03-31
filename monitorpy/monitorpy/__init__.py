"""
MonitorPy - A plugin-based website and service monitoring system.

This package provides a flexible and extensible system for monitoring
websites, SSL certificates, mail servers, and other network services.

This module automatically imports all available plugins to register them
with the plugin registry.
"""

# Import plugins to register them
from monitorpy.plugins.website import WebsiteStatusPlugin
from monitorpy.plugins.ssl_certificate import SSLCertificatePlugin
from monitorpy.plugins.mail_server import MailServerPlugin
from monitorpy.plugins.dns_plugin import DNSRecordPlugin  # Add this line

# Add new plugin imports here as they're developed

__all__ = [
    'WebsiteStatusPlugin',
    'SSLCertificatePlugin',
    'MailServerPlugin',
    'DNSRecordPlugin',
]
