"""
Base plugin system for monitoring plugins.

This module defines the abstract base class that all monitoring plugins must inherit from.
"""
import abc
from typing import Dict, Any, List

from monitorpy.core.result import CheckResult


class MonitorPlugin(abc.ABC):
    """
    Abstract base class for all monitoring plugins.

    All monitoring plugins must inherit from this class and implement
    its abstract methods. This ensures a consistent interface across
    all plugins.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize a new monitoring plugin.

        Args:
            config: Configuration dictionary for the plugin
        """
        self.config = config

    @abc.abstractmethod
    def validate_config(self) -> bool:
        """
        Validate that the plugin configuration is complete and valid.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate_config()")

    @abc.abstractmethod
    def run_check(self) -> CheckResult:
        """
        Execute the monitoring check and return a standardized result.

        Returns:
            CheckResult: The result of the check
        """
        raise NotImplementedError("Subclasses must implement run_check()")

    @classmethod
    @abc.abstractmethod
    def get_required_config(cls) -> List[str]:
        """
        Get a list of required configuration keys for this plugin.

        Returns:
            List[str]: List of required configuration keys
        """
        raise NotImplementedError("Subclasses must implement get_required_config()")

    @classmethod
    def get_optional_config(cls) -> List[str]:
        """
        Get a list of optional configuration keys for this plugin.

        Returns:
            List[str]: List of optional configuration keys
        """
        return []

    @classmethod
    def get_description(cls) -> str:
        """
        Get a human-readable description of what this plugin does.

        Returns:
            str: Plugin description
        """
        return cls.__doc__ or "No description available"

    def get_id(self) -> str:
        """
        Get a unique identifier for this plugin instance.

        The default implementation returns the plugin class name,
        but subclasses can override this to provide more specific IDs.

        Returns:
            str: Unique identifier
        """
        return self.__class__.__name__
