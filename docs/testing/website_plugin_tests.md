# Website Status Plugin Test Documentation

## Overview

The website status plugin tests (`test_website.py`) validate the functionality of the `WebsiteStatusPlugin`, which is responsible for checking website availability, response status codes, and content verification.

## Test Classes and Functionality

### TestWebsiteStatusPlugin

This test class verifies that the website status plugin correctly performs HTTP requests, handles responses, and properly processes different website monitoring scenarios.

**Tests include:**

- **Configuration Requirements**: Tests for required and optional configuration parameters.
  - `test_get_required_config`: Verifies the plugin correctly reports URL as a required parameter.
  - `test_get_optional_config`: Ensures all optional parameters (timeout, status codes, etc.) are properly defined.

- **Configuration Validation**: Checks the plugin's validation logic.
  - `test_validate_config_valid`: Validates that proper configurations are accepted.
  - `test_validate_config_missing_required`: Ensures configurations missing required parameters are rejected.
  - `test_validate_config_invalid_url`: Verifies that URLs without proper schemes are rejected.

- **Core Functionality**: Validates the core website checking functionality.
  - `test_run_check_success`: Tests a basic successful website check.
  - `test_run_check_wrong_status`: Verifies correct handling of unexpected HTTP status codes.
  - `test_run_check_content_match`: Tests content verification when expected content is found.
  - `test_run_check_content_mismatch`: Tests content verification when expected content is not found.
  - `test_run_check_unexpected_content`: Tests detection of unexpected/unwanted content.

- **Authentication**: Tests authentication capabilities.
  - `test_run_check_with_auth`: Verifies HTTP basic authentication functionality.

- **Error Handling**: Tests the plugin's error handling capabilities.
  - `test_run_check_connection_error`: Validates handling of connection failures.
  - `test_run_check_timeout`: Tests timeout handling.

- **Redirects**: Tests redirect handling.
  - `test_run_check_redirects`: Verifies that HTTP redirects are properly followed and recorded.

## Mocking Strategy

The tests extensively use `unittest.mock` to mock the `requests` library, allowing controlled testing of different HTTP responses and error conditions without making actual network requests. This approach ensures tests are:

1. Fast and consistent
2. Independent of external network conditions
3. Able to test error cases that would be difficult to reproduce with real websites

Each test configures a mock response with appropriate status codes, content, and headers, then verifies that the plugin interprets these responses correctly.

## Testing Coverage

The test suite covers:

- Normal operation (successful responses)
- Error conditions (connection errors, timeouts, wrong status codes)
- Content verification (both positive and negative tests)
- Authentication
- Redirect handling
- Configuration validation

This comprehensive coverage ensures that the website status plugin behaves correctly under various conditions and properly reports website status.
