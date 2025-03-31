# SSL Certificate Monitoring

## Overview

The SSL certificate monitoring plugin provides capabilities for checking SSL certificate validity, expiration dates, and overall certificate health. It helps ensure your websites maintain valid and up-to-date SSL certificates.

## Features

- **Certificate Validity**: Verify SSL certificates are valid and properly configured
- **Expiration Monitoring**: Check certificate expiration dates with custom thresholds
- **Chain Verification**: Option to validate the entire certificate chain
- **Hostname Verification**: Ensure certificates are valid for the specified hostname
- **Security Assessment**: Check certificate details like protocol and cipher strength
- **Detailed Reporting**: Comprehensive information about certificates

## Quick Start

### Command Line

```bash
# Basic SSL certificate check
monitorpy ssl example.com

# Check with custom warning thresholds
monitorpy ssl example.com --warning 60 --critical 30

# Check certificate on non-standard port
monitorpy ssl example.com --port 8443

# Get detailed certificate information
monitorpy ssl example.com --check-chain --verbose
```

### Programmatic Use

```python
from monitorpy import run_check

# Basic configuration
config = {
    "hostname": "example.com",
    "timeout": 10
}

# Run the check
result = run_check("ssl_certificate", config)

# Process the result
if result.is_success():
    print(f"Certificate is valid until {result.raw_data['not_after']}")
    print(f"Days remaining: {result.raw_data['days_until_expiration']}")
else:
    print(f"Certificate check failed: {result.message}")
```

## Documentation

- [Configuration Options](configuration.md) - Detailed configuration parameter reference
- [Usage Examples](examples.md) - Common usage patterns and scenarios
- [Advanced Usage](advanced.md) - Advanced features and techniques
- For advanced configuration options and techniques, see the [Advanced Configuration Guide](../../reference/advanced_configuration.md).


## Requirements

The SSL certificate monitoring plugin uses Python's built-in SSL library and does not require additional dependencies.

