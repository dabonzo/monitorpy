"""
Base plugin system for monitoring plugins.

This module defines the abstract base class for monitoring plugins.
"""

import abc
import time
from typing import Dict, Any, List, Optional, Callable

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

    def get_config_value(
        self,
        key: str,
        default: Any = None,
        validator: Optional[Callable[[Any], bool]] = None,
    ) -> Any:
        """
        Get a configuration value with optional validation.

        Args:
            key: Configuration key to retrieve
            default: Default value if the key is not present
            validator: Optional function to validate the value

        Returns:
            The configuration value or default

        Raises:
            ValueError: If the validator returns False
        """
        value = self.config.get(key, default)
        if validator and value is not None and not validator(value):
            raise ValueError(f"Invalid value for config key {key}: {value}")
        return value

    def timed_execution(self, func: Callable, *args, **kwargs) -> tuple:
        """
        Execute a function and measure its execution time.

        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            tuple: (function result, execution time in seconds)
        """
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result, time.time() - start_time
        except Exception as e:
            return e, time.time() - start_time

    def success_result(
        self,
        message: str,
        response_time: float,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> CheckResult:
        """
        Create a success result with the given parameters.

        Args:
            message: Result message
            response_time: Time taken for the check
            raw_data: Additional result data

        Returns:
            CheckResult: A success result
        """
        return CheckResult(CheckResult.STATUS_SUCCESS, message, response_time, raw_data)

    def warning_result(
        self,
        message: str,
        response_time: float,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> CheckResult:
        """
        Create a warning result with the given parameters.

        Args:
            message: Result message
            response_time: Time taken for the check
            raw_data: Additional result data

        Returns:
            CheckResult: A warning result
        """
        return CheckResult(CheckResult.STATUS_WARNING, message, response_time, raw_data)

    def error_result(
        self,
        message: str,
        response_time: float,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> CheckResult:
        """
        Create an error result with the given parameters.

        Args:
            message: Result message
            response_time: Time taken for the check
            raw_data: Additional result data

        Returns:
            CheckResult: An error result
        """
        return CheckResult(CheckResult.STATUS_ERROR, message, response_time, raw_data)

    def basic_config_validation(self) -> bool:
        """
        Perform basic validation of required configuration keys.

        Returns:
            bool: True if all required keys are present, False otherwise
        """
        required_keys = self.get_required_config()
        return all(key in self.config for key in required_keys)


class PluginTemplate(MonitorPlugin):
    """
    A template class that implements common plugin patterns.

    This class can be used as a starting point for new plugins.
    It provides default implementations for common methods.
    """

    @classmethod
    def get_required_config(cls) -> List[str]:
        """Example implementation - override in your plugin."""
        return []

    def validate_config(self) -> bool:
        """Default implementation that checks required keys."""
        return self.basic_config_validation()

    def run_check(self) -> CheckResult:
        """
        Template implementation for run_check that handles exceptions.

        Override the _execute_check method in your plugin.
        """
        try:
            result, duration = self.timed_execution(self._execute_check)

            if isinstance(result, Exception):
                return self.error_result(
                    f"Error during check: {str(result)}",
                    duration,
                    {"error": str(result), "error_type": type(result).__name__},
                )

            return result
        except Exception as e:
            return self.error_result(
                f"Unexpected error: {str(e)}",
                0.0,
                {"error": str(e), "error_type": type(e).__name__},
            )

    def _execute_check(self) -> CheckResult:
        """
        Implement the actual check logic here.

        This method should be overridden by subclasses.

        Returns:
            CheckResult: The result of the check
        """
        raise NotImplementedError("Subclasses must implement _execute_check()")
