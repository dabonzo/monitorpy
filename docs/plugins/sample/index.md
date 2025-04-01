# Sample Plugin Documentation

The sample plugins are designed to demonstrate the MonitorPy plugin development framework and serve as a reference for developers creating their own plugins.

## Overview

These plugins showcase best practices for plugin development including:

- Proper configuration validation
- Error handling
- Helper method usage
- Plugin inheritance and extension
- Documentation standards

## Available Sample Plugins

### SampleMonitorPlugin

A basic monitoring plugin that simulates checking a target with configurable thresholds.

```yaml
checks:
  - type: sample_monitor
    name: example_check
    target: example.com
    check_interval: 60
```

### CustomAPIMonitorPlugin

A specialized plugin that extends the sample monitor to demonstrate plugin inheritance.

```yaml
checks:
  - type: custom_api_monitor
    name: api_monitor
    target: api.example.com
    check_interval: 60
    api_key: YOUR_API_KEY_HERE
    endpoint: /status
```

## Key Features

The sample plugins demonstrate several key features of the MonitorPy plugin framework:

1. **Helper Methods**: Using the built-in helper methods for configuration validation, result creation, and timing
2. **Inheritance**: How to extend existing plugins to create specialized monitoring capabilities
3. **Configuration Validation**: Using validators to ensure configuration parameters meet requirements
4. **Error Handling**: Properly capturing and reporting errors during checks
5. **Consistent Results**: Generating standardized check results with appropriate status codes and messages

## Usage

These plugins are primarily intended as development examples, but they can also be used for basic monitoring or testing.

For detailed configuration options, see the [Configuration Guide](configuration.md).

For usage examples, see the [Examples](examples.md) page.

## Development Reference

The sample plugins provide a reference implementation for developers creating their own plugins. The source code includes detailed comments explaining the purpose and usage of each method.

To view the source code:

```bash
# View the sample template source
cat monitorpy/monitorpy/plugins/sample_template.py
```

For more information on developing plugins, see the [Writing Plugins](../../writing_plugins.md) guide.