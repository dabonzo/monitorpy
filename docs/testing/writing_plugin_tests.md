# Writing Plugin Tests

This guide explains how to write effective tests for new MonitorPy plugins. Following these practices will help ensure your plugins are reliable and maintainable.

## Basic Test Structure

When creating a test file for your plugin, follow this structure:

```python
import unittest
from unittest.mock import patch, Mock
from monitorpy.core import run_check, CheckResult
from monitorpy.plugins.your_plugin import YourPlugin

class TestYourPlugin(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Define standard configuration for tests
        self.base_config = {
            "required_param1": "value1",
            "required_param2": "value2"
        }
    
    # Test methods go here...
```

## Essential Tests for Every Plugin

At minimum, your plugin test suite should include:

### 1. Configuration Validation Tests

```python
def test_get_required_config(self):
    """Test required configuration parameters."""
    required = YourPlugin.get_required_config()
    self.assertIsInstance(required, list)
    self.assertIn("required_param1", required)
    self.assertIn("required_param2", required)

def test_get_optional_config(self):
    """Test optional configuration parameters."""
    optional = YourPlugin.get_optional_config()
    self.assertIsInstance(optional, list)
    self.assertIn("optional_param1", optional)

def test_validate_config_valid(self):
    """Test validation with valid configuration."""
    plugin = YourPlugin(self.base_config)
    self.assertTrue(plugin.validate_config())

def test_validate_config_missing_required(self):
    """Test validation with missing required parameters."""
    plugin = YourPlugin({"required_param1": "value1"})  # Missing required_param2
    self.assertFalse(plugin.validate_config())
```

### 2. Success Path Tests

```python
@patch('some_external_dependency')
def test_run_check_success(self, mock_dependency):
    """Test successful check operation."""
    # Configure mock
    mock_dependency.return_value = some_success_value
    
    # Create plugin and run check
    plugin = YourPlugin(self.base_config)
    result = plugin.run_check()
    
    # Verify result
    self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
    self.assertIn("expected message fragment", result.message)
    self.assertEqual(result.raw_data["some_key"], "expected_value")
```

### 3. Error Handling Tests

```python
@patch('some_external_dependency')
def test_run_check_error_condition(self, mock_dependency):
    """Test handling of a specific error condition."""
    # Configure mock to simulate an error
    mock_dependency.side_effect = SomeException("Error message")
    
    # Create plugin and run check
    plugin = YourPlugin(self.base_config)
    result = plugin.run_check()
    
    # Verify result
    self.assertEqual(result.status, CheckResult.STATUS_ERROR)
    self.assertIn("error message fragment", result.message.lower())
    self.assertEqual(result.raw_data["error_type"], "SomeException")
```

## Mocking External Dependencies

Most monitoring plugins interact with external systems (APIs, network services, databases). In tests, you should mock these dependencies rather than making actual external calls:

### Network Request Mocking

```python
@patch('requests.get')
def test_api_check(self, mock_get):
    """Test API interaction."""
    # Configure mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok", "data": [1, 2, 3]}
    mock_get.return_value = mock_response
    
    # Create plugin and run check
    plugin = YourPlugin(self.base_config)
    result = plugin.run_check()
    
    # Verify result
    self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
```

### Socket/Connection Mocking

```python
@patch('socket.create_connection')
def test_socket_connection(self, mock_socket):
    """Test socket connection."""
    # Configure mock socket
    mock_sock = Mock()
    mock_socket.return_value = mock_sock
    
    # Additional mock setup...
    
    # Create plugin and run check
    plugin = YourPlugin(self.base_config)
    result = plugin.run_check()
    
    # Verify result
    self.assertEqual(result.status, CheckResult.STATUS_SUCCESS)
```

## Testing Complex Plugins

For plugins with complex behavior, consider these approaches:

### 1. Mock at the Right Level

Sometimes it's better to mock higher-level methods within your plugin rather than low-level dependencies:

```python
@patch('your_plugin.YourPlugin._some_internal_method')
def test_complex_behavior(self, mock_method):
    """Test complex behavior by mocking an internal method."""
    mock_method.return_value = some_value
    
    # Test code...
```

### 2. Test State Changes

If your plugin maintains state, test that state changes correctly:

```python
def test_state_changes(self):
    """Test that plugin's internal state changes correctly."""
    plugin = YourPlugin(self.base_config)
    
    # Call method that should change state
    plugin.some_method()
    
    # Verify state changed correctly
    self.assertEqual(plugin.some_internal_state, expected_value)
```

### 3. Parametrized Tests

For testing multiple similar cases, use parametrized tests:

```python
@pytest.mark.parametrize("input_value,expected_status,expected_message", [
    ("valid_input", CheckResult.STATUS_SUCCESS, "success message"),
    ("warning_input", CheckResult.STATUS_WARNING, "warning message"),
    ("error_input", CheckResult.STATUS_ERROR, "error message"),
])
def test_multiple_scenarios(self, input_value, expected_status, expected_message):
    """Test multiple input scenarios."""
    config = self.base_config.copy()
    config["some_param"] = input_value
    
    plugin = YourPlugin(config)
    result = plugin.run_check()
    
    self.assertEqual(result.status, expected_status)
    self.assertIn(expected_message, result.message)
```

## Example Tests

For real-world examples, review the existing plugin test files:

- [Website Plugin Tests](website_plugin_tests.md)
- [SSL Certificate Plugin Tests](ssl_plugin_tests.md)
- [Mail Server Plugin Tests](mail_plugin_tests.md)

These demonstrate practical testing approaches for different types of monitoring plugins.

## Testing Best Practices

1. **Mock external dependencies**: Never make actual network calls in tests.
2. **Test both success and failure cases**: Ensure your plugin gracefully handles errors.
3. **Use descriptive test names**: Test names should clearly explain what they're testing.
4. **Keep tests isolated**: Each test should be independent of other tests.
5. **Verify all components**: Test configuration handling, execution, and result formatting.
6. **Test edge cases**: Include tests for boundary conditions and unusual inputs.
7. **Maintain test coverage**: Aim for high test coverage of your plugin code.

Following these practices will help you create robust, reliable plugins that integrate smoothly with the MonitorPy system.
