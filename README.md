# MonitorPy

A plugin-based website and service monitoring system.

## Overview

MonitorPy is a flexible and extensible monitoring system designed to check website availability, SSL certificate validity, mail server functionality, DNS records, and more. It features a plugin architecture that makes it easy to add new monitoring capabilities.

## Features

- **Website Monitoring**: Check website availability, response codes, and content
- **SSL Certificate Monitoring**: Verify certificate validity and expiration dates
- **Mail Server Monitoring**: Test SMTP, IMAP, and POP3 functionality and authentication
- **DNS Monitoring**: Validate DNS records, check propagation, and verify DNSSEC
- **Enhanced Plugin Framework**: Easily create custom monitoring plugins with helper methods
- **Comprehensive CLI**: Command-line interface for all monitoring functions
- **RESTful API**: Complete API for integration with other systems and services
- **Flexible Database Storage**: Optional database integration with support for SQLite, PostgreSQL, and MySQL
- **Detailed Reporting**: Get in-depth information about monitoring results
- **Plugin Template System**: Start new plugins quickly with pre-implemented functionality

## Installation

### From source

```bash
# Clone the repository
git clone https://github.com/yourusername/monitorpy.git
cd monitorpy

# Install in development mode
pip install -e .
```

### Using pip (future)

```bash
pip install monitorpy
```

## Quick Start

After installation, you can use the `monitorpy` command to access the monitoring functions:

```bash
# List available plugins
monitorpy list

# Check a website
monitorpy website https://www.example.com

# Check an SSL certificate
monitorpy ssl www.example.com

# Check a mail server
monitorpy mail example.com --protocol smtp --basic-check --resolve-mx

# Check DNS records
monitorpy dns example.com --type A --check-propagation
```

## Documentation

For more detailed documentation, see the [docs](docs/) directory:

### Getting Started
- [Getting Started Guide](docs/getting_started.md)
- [CLI Usage](docs/cli_usage.md)

### Monitoring Plugins
- Website Monitoring: [Overview](docs/plugins/website/index.md) | [Configuration](docs/plugins/website/configuration.md) | [Examples](docs/plugins/website/examples.md) | [Advanced](docs/plugins/website/advanced.md)
- SSL Certificate Monitoring: [Overview](docs/plugins/ssl/index.md) | [Configuration](docs/plugins/ssl/configuration.md) | [Examples](docs/plugins/ssl/examples.md) | [Advanced](docs/plugins/ssl/advanced.md)
- Mail Server Monitoring: [Overview](docs/plugins/mail/index.md) | [Configuration](docs/plugins/mail/configuration.md) | [Examples](docs/plugins/mail/examples.md) | [Advanced](docs/plugins/mail/advanced.md)
- DNS Monitoring: [Overview](docs/plugins/dns/index.md) | [Configuration](docs/plugins/dns/configuration.md) | [Examples](docs/plugins/dns/examples.md) | [Advanced](docs/plugins/dns/advanced.md)

### CLI Documentation
- [Website Commands](docs/plugins/cli/website.md)
- [SSL Commands](docs/plugins/cli/ssl.md)
- [Mail Server Commands](docs/plugins/cli/mail.md)
- [DNS Commands](docs/plugins/cli/dns.md)

### Development
- [Writing Plugins](docs/writing_plugins.md)
- [Sample Plugin](docs/plugins/sample/index.md)
- [API Documentation](monitorpy/monitorpy/api/README.md)
- [Testing](docs/testing/index.md)

## Monitoring Capabilities

### Website Monitoring

Monitor website availability, status codes, and content:

```bash
# Basic check
monitorpy website https://www.example.com

# Check for specific content
monitorpy website https://www.example.com --content "Welcome to Example"

# Check with authentication
monitorpy website https://secure.example.com --auth-username user --auth-password pass
```

```python
from monitorpy import run_check

config = {
    "url": "https://www.example.com",
    "timeout": 10,
    "expected_content": "Welcome to Example"
}

result = run_check("website_status", config)
```

### SSL Certificate Monitoring

Verify SSL certificate validity and expiration:

```bash
# Basic certificate check
monitorpy ssl example.com

# Check with custom warning thresholds
monitorpy ssl example.com --warning 60 --critical 30

# Check certificate on non-standard port
monitorpy ssl example.com --port 8443
```

```python
from monitorpy import run_check

config = {
    "hostname": "example.com",
    "warning_days": 30,
    "critical_days": 14
}

result = run_check("ssl_certificate", config)
```

### Mail Server Monitoring

Check mail server connectivity, authentication, and functionality:

```bash
# Basic SMTP server check
monitorpy mail mail.example.com --protocol smtp

# Check with MX record resolution
monitorpy mail example.com --protocol smtp --resolve-mx

# Check SMTP with authentication
monitorpy mail mail.example.com --protocol smtp --username user@example.com --password yourpassword

# Send test email
monitorpy mail mail.example.com --protocol smtp --username user@example.com --password yourpassword --send-test --from user@example.com --to recipient@example.com

# Check IMAP server
monitorpy mail mail.example.com --protocol imap --ssl --username user@example.com --password yourpassword

# Check POP3 server
monitorpy mail mail.example.com --protocol pop3 --ssl --username user@example.com --password yourpassword
```

```python
from monitorpy import run_check

# SMTP check
smtp_config = {
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "port": 587,
    "use_tls": True,
    "username": "user@example.com",
    "password": "yourpassword"
}

smtp_result = run_check("mail_server", smtp_config)

# IMAP check
imap_config = {
    "hostname": "mail.example.com",
    "protocol": "imap",
    "use_ssl": True,
    "username": "user@example.com",
    "password": "yourpassword"
}

imap_result = run_check("mail_server", imap_config)
```

### DNS Monitoring

Check DNS records, propagation, and DNSSEC validation:

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

```python
from monitorpy import run_check

config = {
    "domain": "example.com",
    "record_type": "A",
    "expected_value": "192.0.2.1",
    "check_propagation": True
}

result = run_check("dns_record", config)
```

## Advanced Usage

### Monitoring Multiple Services

You can monitor multiple services in a single script:

```python
from monitorpy import run_check
from concurrent.futures import ThreadPoolExecutor

# Define checks to run
checks = [
    {"name": "Website", "type": "website_status", "config": {"url": "https://www.example.com"}},
    {"name": "SSL", "type": "ssl_certificate", "config": {"hostname": "www.example.com"}},
    {"name": "SMTP", "type": "mail_server", "config": {"hostname": "mail.example.com", "protocol": "smtp"}},
    {"name": "DNS", "type": "dns_record", "config": {"domain": "example.com", "record_type": "A"}}
]

# Run checks in parallel
results = []
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(run_check, check["type"], check["config"]): check for check in checks}
    for future in futures:
        check = futures[future]
        try:
            result = future.result()
            print(f"{check['name']}: {result.status} - {result.message}")
            results.append({
                "name": check["name"],
                "status": result.status,
                "message": result.message
            })
        except Exception as e:
            print(f"{check['name']}: Error - {str(e)}")
```

### Scheduled Monitoring

Using MonitorPy with the `schedule` library for periodic monitoring:

```python
import schedule
import time
from monitorpy import run_check
from datetime import datetime

def check_website():
    config = {"url": "https://www.example.com"}
    result = run_check("website_status", config)
    print(f"[{datetime.now().isoformat()}] Website: {result.status} - {result.message}")

def check_mail():
    config = {"hostname": "mail.example.com", "protocol": "smtp"}
    result = run_check("mail_server", config)
    print(f"[{datetime.now().isoformat()}] Mail: {result.status} - {result.message}")

# Schedule checks
schedule.every(5).minutes.do(check_website)
schedule.every(15).minutes.do(check_mail)

# Run continuously
while True:
    schedule.run_pending()
    time.sleep(1)
```

## Testing

MonitorPy includes a comprehensive test suite to ensure reliable operation across different environments and scenarios. The tests use pytest and cover all core components and plugins.

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest monitorpy/tests/

# Generate coverage report
pytest --cov=monitorpy monitorpy/tests/
```

## Dependencies

- Python 3.8 or higher
- requests: For website monitoring
- Optional: dnspython for DNS monitoring and MX record resolution

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.