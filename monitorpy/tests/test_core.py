"""
Tests for the core components of MonitorPy.
"""
import unittest
from unittest.mock import MagicMock, patch

from monitorpy.core.result import CheckResult
from monitorpy.core.plugin_base import MonitorPlugin
from monitorpy.core.registry import registry, register_plugin, run_check


class TestCheckResult(unittest.TestCase):
    """Tests for the CheckResult class."""

    def test_init_valid_status(self):
        """Test initialization with valid status values."""
        for status in CheckResult.VALID_STATUSES:
            result = CheckResult(status, "Test message")
            self.assertEqual(result.status, status)
            self.assertEqual(result.message, "Test message")
            self.assertEqual(result.response_time, 0.0)
            self.assertEqual(result.raw_data, {})

    def test_init_invalid_status(self):
        """Test initialization with an invalid status value."""
        with self.assertRaises(ValueError):
            CheckResult("invalid_status", "Test message")

    def test_to_dict(self):
        """Test conversion to dictionary."""
        raw_data = {"key": "value"}
        result = CheckResult(
            CheckResult.STATUS_SUCCESS,
            "Test message",
            1.23,
            raw_data
        )
        result_dict = result.to_dict()

        self.assertEqual(result_dict["status"], CheckResult.STATUS_SUCCESS)
        self.assertEqual(result_dict["message"], "Test message")
        self.assertEqual(result_dict["response_time"], 1.23)
        self.assertEqual(result_dict["raw_data"], raw_data)
        self.assertIn("timestamp", result_dict)

    def test_status_check_methods(self):
        """Test is_success, is_warning, and is_error methods."""
        success_result = CheckResult(CheckResult.STATUS_SUCCESS, "Success")
        warning_result = CheckResult(CheckResult.STATUS_WARNING, "Warning")
        error_result = CheckResult(CheckResult.STATUS_ERROR, "Error")

        self.assertTrue(success_result.is_success())
        self.assertFalse(success_result.is_warning())
        self.assertFalse(success_result.is_error())

        self.assertFalse(warning_result.is_success())
        self.assertTrue(warning_result.is_warning())
        self.assertFalse(warning_result.is_error())

        self.assertFalse(error_result.is_success())
        self.assertFalse(error_result.is_warning())
        self.assertTrue(error_result.is_error())


class MockPlugin(MonitorPlugin):
    """Mock plugin for testing."""

    @classmethod
    def get_required_config(cls):
        return ["required_param"]

    @classmethod
    def get_optional_config(cls):
        return ["optional_param"]

    def validate_config(self):
        return "required_param" in self.config

    def run_check(self):
        if not self.validate_config():
            return CheckResult(
                CheckResult.STATUS_ERROR,
                "Invalid configuration"
            )
        if self.config.get("should_fail", False):
            return CheckResult(
                CheckResult.STATUS_ERROR,
                "Check failed"
            )
        return CheckResult(
            CheckResult.STATUS_SUCCESS,
            "Check succeeded"
        )


class TestPluginRegistry(unittest.TestCase):
    """Tests for the PluginRegistry class."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear registry before each test
        registry.plugins = {}

    def test_register_plugin(self):
        """Test registering a plugin."""
        registry.register("mock", MockPlugin)
        self.assertIn("mock", registry.plugins)
        self.assertEqual(registry.plugins["mock"], MockPlugin)

    def test_register_invalid_plugin(self):
        """Test registering an invalid plugin."""
        with self.assertRaises(TypeError):
            registry.register("invalid", object)

    def test_get_plugin(self):
        """Test getting a plugin instance."""
        registry.register("mock", MockPlugin)
        config = {"required_param": "value"}
        plugin = registry.get_plugin("mock", config)

        self.assertIsInstance(plugin, MockPlugin)
        self.assertEqual(plugin.config, config)

    def test_get_nonexistent_plugin(self):
        """Test getting a non-existent plugin."""
        with self.assertRaises(ValueError):
            registry.get_plugin("nonexistent", {})

    def test_get_all_plugins(self):
        """Test getting information about all plugins."""
        registry.register("mock", MockPlugin)
        plugins_info = registry.get_all_plugins()

        self.assertIn("mock", plugins_info)
        self.assertIn("description", plugins_info["mock"])
        self.assertIn("required_config", plugins_info["mock"])
        self.assertIn("optional_config", plugins_info["mock"])

        self.assertEqual(plugins_info["mock"]["required_config"], ["required_param"])
        self.assertEqual(plugins_info["mock"]["optional_config"], ["optional_param"])

    def test_register_plugin_decorator(self):
        """Test the register_plugin decorator."""
        @register_plugin("decorated_mock")
        class DecoratedMockPlugin(MockPlugin):
            pass

        self.assertIn("decorated_mock", registry.plugins)
        self.assertEqual(registry.plugins["decorated_mock"], DecoratedMockPlugin)

    def test_run_check_success(self):
        """Test running a check successfully."""
        registry.register("mock", MockPlugin)
        result = run_check("mock", {"required_param": "value"})

        self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
        self.assertEqual(result.message, "Check succeeded")

    def test_run_check_failure(self):
        """Test running a check that fails."""
        registry.register("mock", MockPlugin)
        result = run_check("mock", {"required_param": "value", "should_fail": True})

        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertEqual(result.message, "Check failed")

    def test_run_check_invalid_config(self):
        """Test running a check with invalid configuration."""
        registry.register("mock", MockPlugin)
        result = run_check("mock", {})

        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("Invalid configuration", result.message)

    def test_run_check_nonexistent_plugin(self):
        """Test running a check with a non-existent plugin."""
        result = run_check("nonexistent", {})

        self.assertEqual(result.status, CheckResult.STATUS_ERROR)
        self.assertIn("not found in registry", result.message)

    def test_run_check_exception(self):
        """Test running a check that raises an exception."""
        registry.register("mock", MockPlugin)

        # Create a mock plugin instance that raises an exception
        mock_plugin = MagicMock(spec=MockPlugin)
        mock_plugin.validate_config.return_value = True
        mock_plugin.run_check.side_effect = Exception("Test exception")

        with patch.object(registry, 'get_plugin', return_value=mock_plugin):
            result = run_check("mock", {"required_param": "value"})

            self.assertEqual(result.status, CheckResult.STATUS_ERROR)
            self.assertIn("Exception running check", result.message)
            self.assertIn("Test exception", result.message)


if __name__ == '__main__':
    unittest.main()
