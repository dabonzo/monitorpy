# Mail Server Monitoring

## Overview

The mail server monitoring plugin provides capabilities for checking mail server connectivity, authentication, and functionality for SMTP, IMAP, and POP3 protocols. It helps ensure your mail servers are operational and correctly configured.

## Features

- **Multi-Protocol Support**: Check SMTP, IMAP, and POP3 mail servers
- **Basic Connectivity**: Verify mail servers are accessible and responding
- **Authentication**: Test login credentials for all protocols
- **SMTP Testing**: Send test emails to verify mail delivery
- **TLS/SSL Support**: Verify encrypted connections
- **MX Resolution**: Automatically resolve MX records for domains
- **Comprehensive Checking**: Test all aspects of mail server health

## Quick Start

### Command Line

```bash
# Basic SMTP server check
monitorpy mail example.com --protocol smtp --basic-check

# Basic check with domain (MX resolution happens automatically)
monitorpy mail example.com --protocol smtp --basic-check

# Disable automatic MX record resolution
monitorpy mail example.com --protocol smtp --basic-check --no-resolve-mx

# Check SMTP with authentication
monitorpy mail mail.example.com --protocol smtp --username user@example.com --password yourpassword

# Send test email via SMTP
monitorpy mail mail.example.com --protocol smtp --username user@example.com --password yourpassword --send-test --from user@example.com --to recipient@example.com

# Check IMAP server
monitorpy mail mail.example.com --protocol imap --username user@example.com --password yourpassword

# Check POP3 server with SSL
monitorpy mail mail.example.com --protocol pop3 --ssl --username user@example.com --password yourpassword
```

### Programmatic Use

```python
from monitorpy import run_check

# Basic SMTP server configuration
config = {
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "timeout": 10
}

# Run the check
result = run_check("mail_server", config)

# Process the result
if result.is_success():
    print(f"Mail server check passed: {result.message}")
else:
    print(f"Mail server check failed: {result.message}")
```

## Documentation

- [Configuration Options](configuration.md) - Detailed configuration parameter reference
- [Usage Examples](examples.md) - Common usage patterns and scenarios
- [Advanced Usage](advanced.md) - Advanced features and techniques
- For advanced configuration options and techniques, see the [Advanced Configuration Guide](../../reference/advanced_configuration.md).

## Requirements

The mail server monitoring plugin requires no additional dependencies for basic functionality. For MX record resolution, the `dnspython` package is recommended:

```bash
pip install dnspython
```
