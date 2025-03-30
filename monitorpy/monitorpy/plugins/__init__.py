"""
Monitoring plugins for the monitorpy package.

This module automatically imports all available plugins to register them
with the plugin registry.
"""
# Import plugins to register them
from monitorpy.plugins.website import WebsiteStatusPlugin
from monitorpy.plugins.ssl_certificate import SSLCertificatePlugin

# Add new plugin imports here as they're developed

__all__ = [
    'WebsiteStatusPlugin',
    'SSLCertificatePlugin',
]
