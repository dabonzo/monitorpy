# Website Monitoring

## Overview

The website monitoring plugin provides comprehensive capabilities for checking website availability, response status codes, and content verification. It allows you to verify that websites are accessible and contain expected content.

## Features

- **Availability Checking**: Verify that websites respond with expected status codes
- **Content Verification**: Check for the presence or absence of specific text
- **HTTP Authentication**: Support for basic authentication
- **Custom Headers**: Ability to set custom HTTP headers for requests
- **Redirect Handling**: Options for following or disabling HTTP redirects
- **SSL Verification**: Options for verifying or ignoring SSL certificates
- **Timeout Control**: Configurable request timeouts
- **Response Analysis**: Detailed information about response times and headers

## Quick Start

### Command Line

```bash
# Basic website check
monitorpy website https://www.example.com

# Check for specific content
monitorpy website https://www.example.com --content "Welcome to Example"

# Check with authentication
monitorpy website https://secure.example.com --auth-username user --auth-password pass
```

### Programmatic Use

```python
from monitorpy import run_check

# Basic configuration
config = {
    "url": "https://www.example.com",
    "timeout": 10,
    "expected_status": 200
}

# Run the check
result = run_check("website_status", config)

# Process the result
if result.is_success():
    print(f"Website check passed: {result.message}")
else:
    print(f"Website check failed: {result.message}")
```

## Documentation

- [Configuration Options](configuration.md) - Detailed configuration parameter reference
- [Usage Examples](examples.md) - Common usage patterns and scenarios
- [Advanced Usage](advanced.md) - Advanced features and techniques

## Requirements

The website monitoring plugin requires the `requests` library, which is a core dependency of MonitorPy.