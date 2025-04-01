"""
Plugin registry module for managing monitoring plugins.
"""
import logging
from typing import Dict, Any, Type, Callable

from monitorpy.core.plugin_base import MonitorPlugin
from monitorpy.core.result import CheckResult

# Configure logging
logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Registry for all available monitoring plugins.

    This class maintains a registry of plugin types and provides
    methods for registering, retrieving, and instantiating plugins.
    """

    def __init__(self):
        """Initialize an empty plugin registry."""
        self.plugins: Dict[str, Type[MonitorPlugin]] = {}

    def register(self, name: str, plugin_class: Type[MonitorPlugin]) -> None:
        """
        Register a new plugin with the registry.

        Args:
            name: The unique name of the plugin
            plugin_class: The plugin class to register

        Raises:
            TypeError: If the plugin class does not inherit from MonitorPlugin
            ValueError: If a plugin with the same name is already registered
        """
        if not issubclass(plugin_class, MonitorPlugin):
            raise TypeError("Plugin class must inherit from MonitorPlugin")

        if name in self.plugins:
            raise ValueError(f"A plugin named '{name}' is already registered")

        self.plugins[name] = plugin_class
        logger.info(f"Registered plugin: {name}")

    def get_plugin(self, name: str, config: Dict[str, Any]) -> MonitorPlugin:
        """
        Get an instance of a plugin with the given configuration.

        Args:
            name: The name of the plugin to instantiate
            config: Configuration to pass to the plugin

        Returns:
            MonitorPlugin: An instance of the requested plugin

        Raises:
            ValueError: If the plugin name is not registered
        """
        if name not in self.plugins:
            raise ValueError(f"Plugin '{name}' not found in registry")

        plugin_instance = self.plugins[name](config)
        return plugin_instance

    def get_all_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered plugins.

        Returns:
            Dict: Dictionary of plugin information, keyed by plugin name
        """
        result = {}
        for name, plugin_class in self.plugins.items():
            result[name] = {
                "description": plugin_class.get_description(),
                "required_config": plugin_class.get_required_config(),
                "optional_config": plugin_class.get_optional_config()
            }
        return result

    def get_plugin_names(self) -> list:
        """
        Get a list of all registered plugin names.

        Returns:
            List: List of plugin names
        """
        return list(self.plugins.keys())


# Create a global registry instance
registry = PluginRegistry()


def register_plugin(name: str) -> Callable:
    """
    Decorator for registering a plugin class with the global registry.

    Example usage:
        @register_plugin("website_status")
        class WebsiteStatusPlugin(MonitorPlugin):
            ...

    Args:
        name: The name to register the plugin under

    Returns:
        The decorated class
    """
    def decorator(cls):
        registry.register(name, cls)
        return cls
    return decorator


def run_check(plugin_name: str, config: Dict[str, Any]) -> CheckResult:
    """
    Run a single check with the given plugin and configuration.

    Args:
        plugin_name: Name of the plugin to use
        config: Configuration for the plugin

    Returns:
        CheckResult: The result of the check
    """
    try:
        plugin = registry.get_plugin(plugin_name, config)

        if not plugin.validate_config():
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Invalid configuration for plugin {plugin_name}",
                0.0,
                {"config": config}
            )

        return plugin.run_check()
    except Exception as e:
        logger.exception(f"Error running check with plugin {plugin_name}")
        return CheckResult(
            CheckResult.STATUS_ERROR,
            f"Exception running check: {str(e)}",
            0.0,
            {"error": str(e), "error_type": type(e).__name__}
        )
