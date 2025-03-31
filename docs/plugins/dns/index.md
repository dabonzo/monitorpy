# DNS Monitoring

## Overview

The DNS monitoring plugin provides comprehensive capabilities for checking DNS records, verifying propagation, validating DNSSEC, and checking authoritative nameservers. It supports all standard DNS record types and can be used to monitor complete DNS health.

## Features

- **Record Verification**: Check the existence and content of any DNS record type
- **Propagation Checking**: Verify DNS records have properly propagated across multiple resolvers
- **DNSSEC Validation**: Confirm DNSSEC is properly configured and validates
- **Authoritative Checking**: Verify responses come from authoritative nameservers
- **Multi-resolver Support**: Test DNS resolution across multiple public or custom resolvers
- **Flexible Configuration**: Support for custom nameservers, resolvers, and timeouts

## Quick Start

### Command Line

```bash
# Basic DNS check
monitorpy dns example.com

# Check specific record type with expected value
monitorpy dns example.com --type MX --value "10 mail.example.com"

# Check DNS propagation
monitorpy dns example.com --check-propagation

# Comprehensive DNS health check
monitorpy dns example.com --check-propagation --check-dnssec --check-authoritative
```

### Programmatic Use

```python
from monitorpy import run_check

# Basic configuration
config = {
    "domain": "example.com",
    "record_type": "A"
}

# Run the check
result = run_check("dns_record", config)

# Process the result
if result.is_success():
    print(f"DNS check passed: {result.message}")
else:
    print(f"DNS check failed: {result.message}")
```

## Documentation

- [Configuration Options](configuration.md) - Detailed configuration parameter reference
- [Usage Examples](examples.md) - Common usage patterns and scenarios
- [Advanced Usage](advanced.md) - Advanced features and techniques

## Requirements

The DNS monitoring plugin requires the `dnspython` library:

```bash
pip install dnspython
```