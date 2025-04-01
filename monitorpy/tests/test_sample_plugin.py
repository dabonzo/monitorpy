"""
Tests for the sample plugin templates.

These tests verify that the sample plugins function correctly and demonstrate
proper testing patterns for MonitorPy plugins.
"""

import unittest
from unittest.mock import patch

from monitorpy.core.registry import run_check
from monitorpy.core.result import CheckResult
from monitorpy.plugins.sample_template import (
    SampleMonitorPlugin,
    CustomAPIMonitorPlugin,
)


class TestSampleMonitorPlugin(unittest.TestCase):
    """Test suite for the SampleMonitorPlugin."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_config = {
            "target": "example.com",
            "check_interval": 60,
            "timeout": 30,
            "warning_threshold": 5.0,
        }

        self.invalid_config = {
            "target": "example.com",
            # Missing required check_interval
        }

    def test_get_required_config(self):
        """Test that the plugin correctly reports required parameters."""
        required = SampleMonitorPlugin.get_required_config()
        self.assertIsInstance(required, list)
        self.assertIn("target", required)
        self.assertIn("check_interval", required)

    def test_validate_config_valid(self):
        """Test validation with valid configuration."""
        plugin = SampleMonitorPlugin(self.valid_config)
        self.assertTrue(plugin.validate_config())

    def test_validate_config_missing_required(self):
        """Test validation with missing required parameters."""
        plugin = SampleMonitorPlugin(self.invalid_config)
        self.assertFalse(plugin.validate_config())

    def test_validate_config_invalid_values(self):
        """Test validation with invalid parameter values."""
        invalid_values = {
            "target": "example.com",
            "check_interval": -10,  # Negative interval is invalid
        }
        plugin = SampleMonitorPlugin(invalid_values)
        self.assertFalse(plugin.validate_config())

    def test_run_check_success(self):
        """Test successful check execution."""
        result = run_check("sample_monitor", self.valid_config)
        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertIn("Check completed successfully", result.message)
        self.assertIn("target", result.raw_data)

    def test_run_check_warning(self):
        """Test check execution resulting in warning status."""
        # Configure to trigger warning threshold
        config = self.valid_config.copy()
        config["warning_threshold"] = 0.1  # Very low threshold to ensure warning

        with patch("time.sleep", return_value=None):  # Prevent actual sleeping
            result = run_check("sample_monitor", config)

        self.assertEqual(result.status, CheckResult.STATUS_WARNING)
        self.assertIn("exceeds warning threshold", result.message)

    def test_get_id(self):
        """Test that get_id returns a unique identifier."""
        plugin = SampleMonitorPlugin(self.valid_config)
        plugin_id = plugin.get_id()
        self.assertIn("SampleMonitorPlugin", plugin_id)
        self.assertIn(self.valid_config["target"], plugin_id)


class TestCustomAPIMonitorPlugin(unittest.TestCase):
    """Test suite for the CustomAPIMonitorPlugin."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_config = {
            "target": "api.example.com",
            "check_interval": 60,
            "api_key": "test_key",
            "endpoint": "/status",
            "headers": {"Accept": "application/json"},
            "query_params": {"format": "json"},
        }

        self.invalid_config = {
            "target": "api.example.com",
            "check_interval": 60,
            # Missing required api_key and endpoint
        }

    def test_get_required_config(self):
        """Test that the plugin correctly reports required parameters."""
        required = CustomAPIMonitorPlugin.get_required_config()
        self.assertIsInstance(required, list)
        self.assertIn("target", required)  # Inherited requirement
        self.assertIn("check_interval", required)  # Inherited requirement
        self.assertIn("api_key", required)  # Added requirement
        self.assertIn("endpoint", required)  # Added requirement

    def test_validate_config_valid(self):
        """Test validation with valid configuration."""
        plugin = CustomAPIMonitorPlugin(self.valid_config)
        self.assertTrue(plugin.validate_config())

    def test_validate_config_missing_required(self):
        """Test validation with missing required parameters."""
        plugin = CustomAPIMonitorPlugin(self.invalid_config)
        self.assertFalse(plugin.validate_config())

    def test_run_check(self):
        """Test check execution."""
        result = run_check("custom_api_monitor", self.valid_config)
        # Since CustomAPIMonitorPlugin uses the parent implementation,
        # we expect similar results as the parent
        self.assertIn(result.status, CheckResult.VALID_STATUSES)
        self.assertTrue(len(result.message) > 0)


if __name__ == "__main__":
    unittest.main()
