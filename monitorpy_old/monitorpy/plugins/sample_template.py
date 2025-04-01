"""
Sample plugin template demonstrating the enhanced plugin framework.

This module provides a complete example of how to implement a custom monitoring
plugin using the MonitorPy framework.
"""

import time
from typing import Dict, Any, List, Optional

from monitorpy.core.plugin_base import PluginTemplate
from monitorpy.core.result import CheckResult
from monitorpy.core.registry import register_plugin
from monitorpy.utils.logging import get_logger

# Configure module logger
logger = get_logger(__name__)


@register_plugin("sample_monitor")
class SampleMonitorPlugin(PluginTemplate):
    """
    A sample plugin demonstrating the enhanced plugin framework.

    This plugin provides a complete example of how to implement a
    monitoring plugin using the provided helper methods.
    """

    @classmethod
    def get_required_config(cls) -> List[str]:
        """Get required configuration parameters."""
        return ["target", "check_interval"]

    @classmethod
    def get_optional_config(cls) -> List[str]:
        """Get optional configuration parameters."""
        return ["timeout", "retry_count", "warning_threshold"]

    def validate_config(self) -> bool:
        """Validate that configuration parameters are valid."""
        # First check all required keys are present
        if not self.basic_config_validation():
            return False

        # Validate specific parameter types and values
        try:
            # Check that check_interval is a positive number
            interval = self.get_config_value(
                "check_interval",
                validator=lambda x: isinstance(x, (int, float)) and x > 0,
            )

            # Check that timeout is a positive number if provided
            if "timeout" in self.config:
                timeout = self.get_config_value(
                    "timeout", validator=lambda x: isinstance(x, (int, float)) and x > 0
                )

            # Check that retry_count is a non-negative integer if provided
            if "retry_count" in self.config:
                retries = self.get_config_value(
                    "retry_count", validator=lambda x: isinstance(x, int) and x >= 0
                )

            return True
        except ValueError as e:
            logger.error(f"Configuration validation error: {e}")
            return False

    def _execute_check(self) -> CheckResult:
        """
        Execute the actual monitoring check.

        This method demonstrates how to implement a check using the
        helper methods provided by the plugin framework.
        """
        target = self.config["target"]
        timeout = self.get_config_value("timeout", 30.0)
        warning_threshold = self.get_config_value("warning_threshold", 5.0)

        logger.info(f"Running check for target: {target}")

        # Simulate a check operation
        # In a real plugin, this would be an actual monitoring operation
        time.sleep(0.5)  # Simulate work

        # Example of checking a warning condition
        response_time = 3.0  # Simulated response time

        # Determine status based on response time
        if response_time > warning_threshold:
            return self.warning_result(
                f"Response time ({response_time:.2f}s) exceeds warning threshold ({warning_threshold:.2f}s)",
                response_time,
                {
                    "target": target,
                    "threshold": warning_threshold,
                    "measured_value": response_time,
                },
            )

        # Return success if everything is good
        return self.success_result(
            f"Check completed successfully for {target}",
            response_time,
            {"target": target, "measured_value": response_time},
        )

    def get_id(self) -> str:
        """Generate a unique identifier for this plugin instance."""
        # Override the default implementation to provide a more specific ID
        return f"{self.__class__.__name__}_{self.config['target']}"


# Example of a more specific plugin that inherits from our template
@register_plugin("custom_api_monitor")
class CustomAPIMonitorPlugin(SampleMonitorPlugin):
    """
    A specialized plugin for monitoring custom APIs.

    This plugin extends the sample plugin to demonstrate inheritance
    and specialization.
    """

    @classmethod
    def get_required_config(cls) -> List[str]:
        """Get required configuration parameters."""
        # Extend parent's required config
        return super().get_required_config() + ["api_key", "endpoint"]

    @classmethod
    def get_optional_config(cls) -> List[str]:
        """Get optional configuration parameters."""
        # Extend parent's optional config
        return super().get_optional_config() + ["headers", "query_params"]

    def _execute_check(self) -> CheckResult:
        """Execute API-specific checks."""
        # This would contain API-specific implementation
        # For this example, we'll just call the parent implementation
        return super()._execute_check()
