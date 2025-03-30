# Core Module Test Documentation

## Overview

The core module tests (`test_core.py`) verify the functionality of the fundamental components of the MonitorPy system, focusing on:

1. The `CheckResult` class for storing and processing monitoring results
2. The base `MonitorPlugin` abstract class
3. The plugin registry system for managing monitoring plugins

## Test Classes and Functionality

### TestCheckResult

This test class validates the proper functioning of the CheckResult class, which is the standardized result object returned by all monitoring plugins.

**Tests include:**

- **Initialization with Valid Status Values**: Verifies that the CheckResult can be properly created with all valid status values (success, warning, error).
- **Initialization with Invalid Status**: Ensures that creating a CheckResult with an invalid status value raises a ValueError.
- **Dictionary Conversion**: Tests that the `to_dict()` method correctly converts a CheckResult to a dictionary containing all essential information.
- **Status Check Methods**: Validates the functionality of the `is_success()`, `is_warning()`, and `is_error()` helper methods.

### TestPluginRegistry

This test class verifies the plugin registration and management system, which is a key part of MonitorPy's extensibility.

**Tests include:**

- **Plugin Registration**: Tests adding plugins to the registry.
- **Invalid Plugin Registration**: Verifies that trying to register a non-plugin class raises appropriate errors.
- **Plugin Retrieval**: Tests retrieving a plugin instance by name.
- **Non-existent Plugin Retrieval**: Ensures appropriate error handling when requesting a non-existent plugin.
- **Plugin Information Retrieval**: Tests retrieving information about all registered plugins.
- **Plugin Decorator Registration**: Validates the `@register_plugin` decorator functionality.
- **Running Checks**: Tests the `run_check` function with various scenarios:
  - Successful check execution
  - Failed check execution
  - Invalid configuration
  - Non-existent plugin
  - Exception handling during check execution

## Mock Objects

The tests use the `MockPlugin` class, which provides a controlled implementation of `MonitorPlugin` for testing purposes. This allows testing of the plugin system without relying on actual plugin implementations.

## Testing Strategy

These tests follow a unit testing approach, focusing on isolated testing of individual components with mocked dependencies where necessary. They validate both happy paths and error conditions to ensure robust behavior of the core system.

The core tests are fundamental to the stability of the entire system, as all other components rely on these core classes and functions.
