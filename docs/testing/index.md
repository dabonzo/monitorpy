# MonitorPy Testing

This documentation covers the testing approach and structure for the MonitorPy project. Tests are essential to ensure that the monitoring plugins work reliably across different environments and scenarios.

## Testing Philosophy

MonitorPy follows these testing principles:

1. **Comprehensive Coverage**: Each plugin and core component should have thorough test coverage, including success paths and error conditions.

2. **Isolation**: Tests should be isolated and not depend on external resources or network connectivity whenever possible.

3. **Mocking**: External dependencies (like network connections) should be mocked to ensure tests are fast, reliable, and don't depend on external resources.

4. **Readability**: Tests should be clear and serve as documentation for how components should behave.

## Test Organization

Tests are organized in the `monitorpy/tests/` directory, with separate files for each major component:

- `test_core.py`: Tests for the core components (CheckResult, MonitorPlugin, registry)
- `test_website.py`: Tests for the website status monitoring plugin
- `test_ssl_cert_check.py`: Tests for the SSL certificate monitoring plugin
- `test_mail_server.py`: Tests for the mail server monitoring plugin

As new plugins are added, corresponding test files should be created following the same patterns.

## Running Tests

You can run the MonitorPy tests using pytest:

```bash
# Run all tests
pytest monitorpy/tests/

# Run tests for a specific component
pytest monitorpy/tests/test_website.py

# Run tests with verbose output
pytest -v monitorpy/tests/

# Run tests and generate coverage report
pytest --cov=monitorpy monitorpy/tests/
```

## Detailed Test Documentation

For more detailed information about specific test suites:

- [Core Module Tests](core_tests.md)
- [Website Plugin Tests](website_plugin_tests.md)
- [SSL Certificate Plugin Tests](ssl_plugin_tests.md)
- [Mail Server Plugin Tests](mail_plugin_tests.md)

## Writing Tests for New Plugins

When creating a new monitoring plugin, you should also create corresponding tests. Follow these guidelines:

1. Create a new test file in the `monitorpy/tests/` directory
2. Test configuration validation
3. Test success and error scenarios
4. Mock external dependencies
5. Follow the patterns established in existing test files

See the [Writing Plugin Tests](writing_plugin_tests.md) guide for detailed instructions.
