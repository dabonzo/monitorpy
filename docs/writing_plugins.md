# Writing Plugins

One of the key features of MonitorPy is its extensible plugin architecture. This guide explains how to write your own monitoring plugins to extend the system's capabilities.

## Plugin Architecture

MonitorPy plugins are Python classes that inherit from the `MonitorPlugin` base class and implement specific methods. Each plugin is registered with a unique name that users can reference when running checks.

## Enhanced Plugin Framework

The MonitorPy v2 framework includes enhanced base classes and helper methods to make plugin development easier:

- `MonitorPlugin`: The abstract base class that all plugins must inherit from
- `PluginTemplate`: A template class with pre-implemented common functionality
- Helper methods for creating check results, timing operations, and config validation

## Creating a Plugin Using the Template

The easiest way to create a new plugin is to inherit from the `PluginTemplate` class:

```python
from monitorpy.core.plugin_base import PluginTemplate
from monitorpy.core.registry import register_plugin
from monitorpy.utils.logging import get_logger

logger = get_logger(__name__)

@register_plugin("my_custom_check")
class MyCustomPlugin(PluginTemplate):
    """My custom monitoring plugin that checks XYZ."""
    
    @classmethod
    def get_required_config(cls):
        return ["target", "threshold"]
    
    def _execute_check(self):
        # Get config values with validation
        target = self.get_config_value("target")
        threshold = self.get_config_value(
            "threshold", 
            validator=lambda x: isinstance(x, (int, float)) and x > 0
        )
        
        # Implement your check logic here
        # ...
        
        # Return an appropriate result
        return self.success_result(
            f"Check successful for {target}",
            response_time,
            {"details": "your data here"}
        )
```

## Key Helper Methods

The framework provides several helper methods to simplify plugin development:

### Configuration Management

```python
# Get config with validation and default value
value = self.get_config_value(
    "key", 
    default="default_value",
    validator=lambda x: isinstance(x, str) and len(x) > 0
)

# Basic validation of all required config keys
is_valid = self.basic_config_validation()
```

### Result Creation

```python
# Create success result
result = self.success_result("All systems normal", 0.5, {"data": "value"})

# Create warning result
result = self.warning_result("Performance degraded", 3.2, {"data": "value"})

# Create error result
result = self.error_result("Service unavailable", 2.1, {"error": "details"})
```

### Execution Timing

```python
# Automatically time the execution of a function
result, duration = self.timed_execution(my_function, arg1, arg2, kwarg1=value)
```

## Complete Plugin Example

A complete example plugin is available at:
`monitorpy/plugins/sample_template.py`

This example demonstrates proper configuration validation, error handling, result creation, and other best practices.

## Plugin Registration

All plugins must be registered with the system to be discoverable. Use the `@register_plugin` decorator:

```python
from monitorpy.core.registry import register_plugin

@register_plugin("unique_plugin_name")
class MyPlugin(MonitorPlugin):
    # ...
```

Then import your plugin in the `monitorpy/plugins/__init__.py` file:

```python
from monitorpy.plugins.my_plugin import MyPlugin

__all__ = [
    # other plugins
    'MyPlugin',
]
```

## Required Implementation

At minimum, your plugin must implement:

1. `get_required_config()`: Returns a list of required configuration keys
2. `validate_config()`: Validates the configuration (or use `basic_config_validation()`)
3. `run_check()`: Executes the check and returns a result (or override `_execute_check()` if using `PluginTemplate`)

## Plugin Testing

Create a test file in the `tests` directory to verify your plugin works correctly. See the [Testing Documentation](testing/index.md) for details.

## Best Practices

When developing plugins, follow these best practices:

1. **Proper Error Handling**: Catch all exceptions and return appropriate error messages
2. **Detailed Logging**: Use the logger to record important events and errors
3. **Accurate Timing**: Measure and report the response time for checks
4. **Descriptive Messages**: Provide clear, informative messages in the CheckResult
5. **Thorough Validation**: Validate the configuration thoroughly to prevent runtime errors
6. **Comprehensive Documentation**: Document the plugin's purpose, requirements, and behavior
7. **Stateless Design**: Plugins should be stateless and not rely on external state between runs
8. **Thread Safety**: Ensure your plugin is thread-safe for parallel execution
9. **Resource Management**: Properly manage resources (like connections) to avoid leaks in parallel contexts

## Adding CLI Support

To make your plugin available through the command-line interface, update the `cli.py` file to add a subparser for your plugin. This will allow users to run your plugin from the command line.

## Documentation

Don't forget to document your plugin by adding information to the appropriate documentation files, including:

- Create a configuration guide in `docs/plugins/your_plugin/configuration.md`
- Add examples in `docs/plugins/your_plugin/examples.md`
- Document CLI usage in `docs/plugins/cli/your_plugin.md`

## Supporting Parallel Execution

MonitorPy provides a parallel execution system that allows running multiple checks concurrently. To ensure your plugin works well with this system:

1. **Thread Safety**: Make sure your plugin is thread-safe. Avoid using global or class variables that could be modified by multiple threads.

2. **Resource Management**: Properly close any opened resources (files, network connections, etc.) even if an exception occurs.

3. **Timeout Support**: Implement proper timeout handling in your plugin to prevent hanging in parallel contexts.

4. **Testing**: Test your plugin with the parallel execution framework to ensure it works correctly under concurrent load.

Example of implementing a thread-safe connection pool:

```python
import queue
from contextlib import contextmanager

class MyPlugin(PluginTemplate):
    """Plugin with connection pooling for parallel execution."""
    
    # Class-level connection pool
    _connection_pool = queue.Queue(maxsize=10)
    
    @classmethod
    @contextmanager
    def _get_connection(cls, config):
        """Get a connection from the pool or create a new one."""
        try:
            # Try to get a connection from the pool
            connection = cls._connection_pool.get(block=False)
            created = False
        except queue.Empty:
            # Create a new connection if the pool is empty
            connection = create_new_connection(config)
            created = True
            
        try:
            # Yield the connection for use
            yield connection
        finally:
            # Return to pool or close based on creation status
            if not created and cls._connection_pool.qsize() < 10:
                # Return borrowed connection to the pool
                cls._connection_pool.put(connection)
            else:
                # Close newly created connection
                connection.close()
    
    def _execute_check(self):
        with self._get_connection(self.config) as conn:
            # Use the connection to perform the check
            # ...
            return self.success_result("Check completed successfully", response_time)
```

For more information on parallel execution, see the [Parallel Execution](parallel/overview.md) documentation.

## Need Help?

For more detailed examples and guidance:

1. Look at the example plugins in the `monitorpy/plugins` directory
2. Check out the `sample_template.py` file for a comprehensive example
3. See the plugin tests in the `tests` directory for testing approaches
4. Review the `batch_runner.py` file to understand parallel execution