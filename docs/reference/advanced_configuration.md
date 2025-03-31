# MonitorPy Advanced Configuration Guide

This comprehensive guide details all configuration options across MonitorPy's monitoring plugins, with advanced usage patterns, optimization strategies, and troubleshooting tips.

## Table of Contents

- [Global Configuration](#global-configuration)
- [Website Monitoring Configuration](#website-monitoring-configuration)
- [SSL Certificate Monitoring Configuration](#ssl-certificate-monitoring-configuration)
- [Mail Server Monitoring Configuration](#mail-server-monitoring-configuration)
- [DNS Monitoring Configuration](#dns-monitoring-configuration)
- [Configuration Relationships](#configuration-relationships)
- [Environmental Configuration](#environmental-configuration)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)
- [Configuration Templates](#configuration-templates)

## Global Configuration

These settings apply across all plugins and affect the general behavior of MonitorPy.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_level` | string | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `log_file` | string | None | Path to log file (logs to stdout if not specified) |
| `max_workers` | integer | 10 | Maximum number of concurrent workers for parallel checks |
| `timeout` | integer | 30 | Default timeout in seconds (can be overridden by plugin-specific settings) |

### Usage Example

```python
from monitorpy import setup_logging

# Setup global logging
setup_logging(level="DEBUG", log_file="monitorpy.log")
```

Command-line usage:
```bash
monitorpy website https://example.com --log-level DEBUG --log-file monitorpy.log
```

## Website Monitoring Configuration

The website monitoring plugin (`website_status`) checks website availability, status codes, and content.

### Required Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | URL to check (must start with http:// or https://) |

### Optional Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | integer | 30 | Request timeout in seconds |
| `expected_status` | integer | 200 | Expected HTTP status code |
| `method` | string | "GET" | HTTP method (GET, POST, PUT, DELETE, etc.) |
| `headers` | dictionary | {} | Dictionary of HTTP headers to send |
| `body` | string | None | Request body for POST/PUT requests |
| `auth_username` | string | None | Username for basic authentication |
| `auth_password` | string | None | Password for basic authentication |
| `verify_ssl` | boolean | True | Whether to verify SSL certificates |
| `follow_redirects` | boolean | True | Whether to follow HTTP redirects |
| `expected_content` | string | None | Content that should be present in the response |
| `unexpected_content` | string | None | Content that should NOT be present in the response |

### Advanced Configuration Patterns

#### Content Validation with Regular Expressions

When you need more flexible content matching:

```python
import re
from monitorpy import run_check
from monitorpy.utils.formatting import format_result

# Define regex pattern
pattern = r"Welcome, [A-Za-z]+"

# Run check
result = run_check("website_status", {"url": "https://example.com"})

# Custom content validation with regex
if result.is_success():
    if re.search(pattern, result.raw_data.get("response_content", "")):
        print("Content validation passed!")
    else:
        print("Content validation failed!")
```

#### API Authentication Patterns

Different authentication methods for APIs:

```python
# Basic Auth
config_basic = {
    "url": "https://api.example.com/endpoint",
    "auth_username": "apiuser",
    "auth_password": "apipass"
}

# API Key in Header
config_api_key = {
    "url": "https://api.example.com/endpoint",
    "headers": {
        "X-API-Key": "your-api-key"
    }
}

# Bearer Token
config_bearer = {
    "url": "https://api.example.com/endpoint",
    "headers": {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}

# OAuth2 Token
config_oauth = {
    "url": "https://api.example.com/endpoint",
    "headers": {
        "Authorization": "OAuth2 access_token"
    }
}
```

#### Multi-stage Request Pattern

For APIs that require multiple sequential requests:

```python
from monitorpy import run_check

# First request to get authentication token
auth_config = {
    "url": "https://api.example.com/auth",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": '{"username": "user", "password": "pass"}',
    "expected_status": 200
}

auth_result = run_check("website_status", auth_config)

if auth_result.is_success():
    # Extract token from auth response
    import json
    response_data = json.loads(auth_result.raw_data.get("response_content", "{}"))
    token = response_data.get("token")
    
    # Second request using the token
    api_config = {
        "url": "https://api.example.com/data",
        "headers": {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        "expected_status": 200
    }
    
    api_result = run_check("website_status", api_config)
    print(f"API check result: {api_result.status}")
```

## SSL Certificate Monitoring Configuration

The SSL certificate plugin (`ssl_certificate`) checks SSL certificate validity and expiration.

### Required Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `hostname` | string | Hostname or URL to check |

### Optional Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | integer | 443 | Port number for the SSL connection |
| `timeout` | integer | 30 | Connection timeout in seconds |
| `warning_days` | integer | 30 | Days before expiration to trigger a warning |
| `critical_days` | integer | 14 | Days before expiration to trigger a critical alert |
| `check_chain` | boolean | False | Whether to check certificate chain details |
| `verify_hostname` | boolean | True | Whether to verify the hostname in the certificate |

### Advanced Configuration Patterns

#### Multiple Certificate Checks

For checking multiple certificates with different thresholds:

```python
from monitorpy import run_check
from concurrent.futures import ThreadPoolExecutor

certificates = [
    {
        "name": "Production Website",
        "hostname": "www.example.com",
        "warning_days": 45,  # More lead time for critical infrastructure
        "critical_days": 30
    },
    {
        "name": "Development API",
        "hostname": "dev-api.example.com",
        "warning_days": 14,  # Less critical environment
        "critical_days": 7
    },
    {
        "name": "Custom Port Service",
        "hostname": "secure.example.com",
        "port": 8443
    }
]

# Check all certificates in parallel
results = {}
with ThreadPoolExecutor(max_workers=len(certificates)) as executor:
    futures = {}
    for cert in certificates:
        # Extract name and create config
        name = cert.pop("name")
        futures[executor.submit(run_check, "ssl_certificate", cert)] = name
    
    # Process results
    for future in futures:
        name = futures[future]
        try:
            results[name] = future.result()
        except Exception as e:
            results[name] = f"Error: {str(e)}"

# Report results
for name, result in results.items():
    if hasattr(result, 'status'):
        print(f"{name}: {result.status} - {result.message}")
    else:
        print(f"{name}: {result}")
```

#### Certificate Chain Validation

For detailed certificate chain validation:

```python
config = {
    "hostname": "www.example.com",
    "check_chain": True,
    "warning_days": 60,
    "critical_days": 30
}

result = run_check("ssl_certificate", config)

if result.is_success():
    # Examine chain information
    chain_info = result.raw_data.get("chain", {})
    
    # Example: Check cipher strength
    cipher = chain_info.get("cipher")
    if cipher and isinstance(cipher, tuple) and len(cipher) > 2:
        cipher_name, protocol, strength = cipher
        if strength < 256:
            print(f"Warning: Weak cipher strength ({strength} bits)")
        else:
            print(f"Good cipher strength: {strength} bits")
```

## Mail Server Monitoring Configuration

The mail server plugin (`mail_server`) checks mail server connectivity and functionality.

### Required Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `hostname` | string | Mail server hostname or domain |
| `protocol` | string | Mail protocol to check (smtp, imap, pop3) |

### Optional Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | integer | Protocol-specific | Server port (default depends on protocol and SSL/TLS settings) |
| `username` | string | None | Username for authentication |
| `password` | string | None | Password for authentication |
| `use_ssl` | boolean | False | Use SSL connection |
| `use_tls` | boolean | False | Use TLS connection (SMTP only) |
| `timeout` | integer | 30 | Connection timeout in seconds |
| `test_send` | boolean | False | Send test email (SMTP only) |
| `from_email` | string | None | From email address (for test email) |
| `to_email` | string | None | To email address (for test email) |
| `subject` | string | "MonitorPy Mail Test" | Subject for test email |
| `message` | string | "Test email from MonitorPy" | Body for test email |
| `resolve_mx` | boolean | False | Resolve MX records for domain and check highest priority server |

### Advanced Configuration Patterns

#### Complete Mail Server Health Check

Checking different aspects of a mail server:

```python
from monitorpy import run_check
from datetime import datetime

def check_mail_server(domain, smtp_user=None, smtp_pass=None, imap_user=None, imap_pass=None):
    """Comprehensive mail server check including SMTP, IMAP, and MX records."""
    results = {}
    
    # Check MX records
    mx_config = {
        "hostname": domain,
        "protocol": "smtp",
        "resolve_mx": True,
        "timeout": 10
    }
    results["mx"] = run_check("mail_server", mx_config)
    
    # Basic SMTP check
    smtp_config = {
        "hostname": f"mail.{domain}",
        "protocol": "smtp",
        "timeout": 15
    }
    results["smtp_basic"] = run_check("mail_server", smtp_config)
    
    # SMTP with TLS
    smtp_tls_config = {
        "hostname": f"mail.{domain}",
        "protocol": "smtp",
        "port": 587,
        "use_tls": True,
        "timeout": 15
    }
    results["smtp_tls"] = run_check("mail_server", smtp_tls_config)
    
    # SMTP authentication if credentials provided
    if smtp_user and smtp_pass:
        smtp_auth_config = {
            "hostname": f"mail.{domain}",
            "protocol": "smtp",
            "port": 587,
            "use_tls": True,
            "username": smtp_user,
            "password": smtp_pass,
            "timeout": 20
        }
        results["smtp_auth"] = run_check("mail_server", smtp_auth_config)
    
    # IMAP check if credentials provided
    if imap_user and imap_pass:
        imap_config = {
            "hostname": f"mail.{domain}",
            "protocol": "imap",
            "use_ssl": True,
            "username": imap_user,
            "password": imap_pass,
            "timeout": 20
        }
        results["imap"] = run_check("mail_server", imap_config)
    
    # Print summary
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Mail server check for {domain} at {timestamp}:")
    for check_name, result in results.items():
        status_icon = "✅" if result.is_success() else "⚠️" if result.status == "warning" else "❌"
        print(f"{status_icon} {check_name}: {result.message}")
    
    return results

# Example usage
check_mail_server("example.com", 
                 smtp_user="user@example.com", 
                 smtp_pass="password",
                 imap_user="user@example.com", 
                 imap_pass="password")
```

#### Mail Delivery Testing

For testing complete mail delivery paths:

```python
mail_delivery_config = {
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "port": 587,
    "use_tls": True,
    "username": "sender@example.com",
    "password": "senderpass",
    "test_send": True,
    "from_email": "sender@example.com",
    "to_email": "recipient@example.com",
    "subject": "Delivery Test",
    "message": "This is a test of mail delivery at " + datetime.now().isoformat()
}

result = run_check("mail_server", mail_delivery_config)

if result.is_success() and result.raw_data.get("test_send_success"):
    print("Mail delivery test successful!")
    
    # Optional: Check recipient inbox to verify receipt
    if result.raw_data.get("test_send_message_id"):
        print(f"Message ID: {result.raw_data.get('test_send_message_id')}")
        # Could implement IMAP check here to verify the message was received
```

## DNS Monitoring Configuration

The DNS plugin (`dns_record`) checks DNS records, propagation, and DNSSEC validation.

### Required Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `domain` | string | Domain name to check |
| `record_type` | string | DNS record type (A, AAAA, MX, CNAME, TXT, NS, etc.) |

### Optional Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `expected_value` | string/list | None | Expected record value(s) |
| `nameserver` | string/list | System default | Specific nameserver(s) to query |
| `timeout` | integer | 10 | Query timeout in seconds |
| `check_propagation` | boolean | False | Check DNS propagation across multiple resolvers |
| `resolvers` | list | Default public resolvers | Custom DNS resolvers to check |
| `propagation_threshold` | float | 80.0 | Propagation threshold percentage (0-100) |
| `check_authoritative` | boolean | False | Check if response is from an authoritative server |
| `check_dnssec` | boolean | False | Check DNSSEC validation |
| `subdomain` | string | None | Subdomain to check (e.g., 'www') |
| `max_workers` | integer | 10 | Maximum workers for propagation checks |

### Advanced Configuration Patterns

#### Complete Domain Health Check

Checking multiple DNS aspects of a domain:

```python
from monitorpy import run_check
from pprint import pprint

def check_domain_dns_health(domain):
    """Complete DNS health check for a domain."""
    checks = [
        # Basic A record check
        {
            "name": "A Record",
            "config": {
                "domain": domain,
                "record_type": "A"
            }
        },
        # Check with expected value
        {
            "name": "www A Record",
            "config": {
                "domain": domain,
                "subdomain": "www",
                "record_type": "A"
            }
        },
        # MX record check
        {
            "name": "MX Record",
            "config": {
                "domain": domain,
                "record_type": "MX"
            }
        },
        # DNSSEC check
        {
            "name": "DNSSEC",
            "config": {
                "domain": domain,
                "record_type": "A",
                "check_dnssec": True
            }
        },
        # NS records check
        {
            "name": "NS Records",
            "config": {
                "domain": domain,
                "record_type": "NS"
            }
        },
        # TXT record check
        {
            "name": "TXT Records",
            "config": {
                "domain": domain,
                "record_type": "TXT"
            }
        },
        # Propagation check for A record
        {
            "name": "A Record Propagation",
            "config": {
                "domain": domain,
                "record_type": "A",
                "check_propagation": True,
                "propagation_threshold": 90.0
            }
        }
    ]
    
    results = {}
    for check in checks:
        name = check["name"]
        print(f"Running {name} check...")
        try:
            results[name] = run_check("dns_record", check["config"])
        except Exception as e:
            results[name] = f"Error: {str(e)}"
    
    # Print summary
    print("\nDNS Health Check Summary:")
    for name, result in results.items():
        if hasattr(result, 'status'):
            status_icon = "✅" if result.status == "success" else "⚠️" if result.status == "warning" else "❌"
            print(f"{status_icon} {name}: {result.message}")
        else:
            print(f"❌ {name}: {result}")
    
    return results

# Example usage
results = check_domain_dns_health("example.com")
```

#### DNS Propagation Monitoring

For detailed propagation monitoring:

```python
from monitorpy import run_check
import time

def monitor_dns_propagation(domain, record_type="A", expected_value=None, 
                          check_interval=300, max_checks=24):
    """
    Monitor DNS propagation over time.
    
    Args:
        domain: Domain to check
        record_type: Record type (A, AAAA, etc.)
        expected_value: Expected value for the record
        check_interval: Seconds between checks
        max_checks: Maximum number of checks to perform
    """
    config = {
        "domain": domain,
        "record_type": record_type,
        "check_propagation": True,
        "propagation_threshold": 95.0,
        "timeout": 30
    }
    
    if expected_value:
        config["expected_value"] = expected_value
    
    print(f"Monitoring DNS propagation for {record_type} record of {domain}")
    print(f"Will check every {check_interval} seconds, up to {max_checks} times")
    
    history = []
    for i in range(max_checks):
        check_time = time.time()
        try:
            result = run_check("dns_record", config)
            
            propagation_data = result.raw_data.get("propagation", {})
            percentage = propagation_data.get("percentage", 0)
            consistent = propagation_data.get("consistent_count", 0)
            total = propagation_data.get("total_count", 0)
            
            status_icon = "✅" if percentage >= 95 else "⚠️" if percentage >= 75 else "❌"
            print(f"Check {i+1}/{max_checks}: {status_icon} {percentage:.1f}% propagation ({consistent}/{total} resolvers)")
            
            history.append({
                "timestamp": check_time,
                "percentage": percentage,
                "consistent": consistent,
                "total": total,
                "status": result.status
            })
            
            # Stop if we reach 100% propagation
            if percentage == 100:
                print("Reached 100% propagation, monitoring complete!")
                break
                
        except Exception as e:
            print(f"Error during check {i+1}: {str(e)}")
            history.append({
                "timestamp": check_time,
                "error": str(e)
            })
        
        # Don't sleep after the last check
        if i < max_checks - 1:
            print(f"Next check in {check_interval} seconds...")
            time.sleep(check_interval)
    
    # Print summary
    successful_checks = len([h for h in history if h.get("percentage", 0) >= 95])
    print(f"\nPropagation Summary: {successful_checks}/{len(history)} checks showed good propagation")
    
    return history

# Example usage
monitor_dns_propagation("example.com", expected_value="192.0.2.1", check_interval=60, max_checks=10)
```

## Configuration Relationships

Understanding how different configuration parameters interact with each other is crucial for advanced usage.

### Website Plugin Parameter Relationships

- **`expected_status` and `expected_content`**: Both must match for a check to succeed; content checks run only if the status code check passes
- **`verify_ssl` and `follow_redirects`**: For HTTPS sites, SSL verification happens before redirect following
- **`expected_content` and `unexpected_content`**: You can use both simultaneously to check for required content while ensuring unwanted content is absent
- **`method` and `body`**: The body parameter is ignored for GET requests
- **`timeout` hierarchy**: Request connection → request read → overall timeout

### SSL Certificate Parameter Relationships

- **`warning_days` and `critical_days`**: Critical should always be less than warning; using the same value means no warning state
- **`check_chain` and `verify_hostname`**: Chain checking includes hostname verification unless explicitly disabled
- **`port` dependency**: Different SSL protocols might require different ports (443 for HTTPS, 465 for SMTPS, etc.)

### Mail Server Parameter Relationships

- **`protocol` and `port`/`use_ssl`/`use_tls`**: Default ports change based on SSL/TLS settings
- **`test_send` dependencies**: Requires username, password, from_email, and to_email to be set
- **`resolve_mx` and `hostname`**: When resolve_mx is true, hostname is treated as a domain rather than a server name

### DNS Plugin Parameter Relationships

- **`check_propagation` and `resolvers`/`propagation_threshold`**: Propagation checks use custom resolvers if provided, with threshold determining pass/fail
- **`subdomain` and `domain`**: Combined to form the full domain to check
- **`check_authoritative` and `check_dnssec`**: Can be used together but operate independently
- **`expected_value` format**: String for single values, array for multiple acceptable values

## Environmental Configuration

For sensitive information and deployment-specific settings, using environment variables is recommended.

### Environment Variable Pattern

```python
import os
from monitorpy import run_check

# Example function using environment variables for credentials
def check_secure_endpoint():
    api_key = os.environ.get("MONITOR_API_KEY")
    if not api_key:
        raise ValueError("MONITOR_API_KEY environment variable is required")
    
    config = {
        "url": os.environ.get("MONITOR_API_URL", "https://api.example.com"),
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        "timeout": int(os.environ.get("MONITOR_TIMEOUT", "30"))
    }
    
    return run_check("website_status", config)
```

### Configuration File Pattern

```python
import json
import os
from monitorpy import run_check

def load_config(config_path=None):
    """Load configuration from file with environment variable overrides."""
    # Default config path or from environment
    if not config_path:
        config_path = os.environ.get("MONITORPY_CONFIG", "monitorpy_config.json")
    
    # Load base configuration
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config file: {str(e)}")
        config = {}
    
    # Override with environment variables
    if "MONITORPY_TIMEOUT" in os.environ:
        config["timeout"] = int(os.environ["MONITORPY_TIMEOUT"])
    
    if "MONITORPY_LOG_LEVEL" in os.environ:
        config["log_level"] = os.environ["MONITORPY_LOG_LEVEL"]
    
    return config

# Example usage
base_config = load_config()
print(f"Using configuration with timeout: {base_config.get('timeout', 'default')}")
```

### Credential Management

For secure credential management:

```python
import keyring
from monitorpy import run_check

def check_with_secure_credentials(service_name, username):
    """Use keyring for secure credential retrieval."""
    # Retrieve password from system keyring
    password = keyring.get_password(service_name, username)
    
    if not password:
        raise ValueError(f"No password found for {username} in {service_name}")
    
    # Use the credentials for checking
    config = {
        "hostname": "mail.example.com",
        "protocol": "smtp",
        "username": username,
        "password": password,
        "use_tls": True
    }
    
    return run_check("mail_server", config)

# Example usage
result = check_with_secure_credentials("example_mail", "user@example.com")
```

## Performance Tuning

Optimize MonitorPy's performance for different scenarios.

### Timeout Optimization

```python
# For high-traffic production servers that should respond quickly
production_config = {
    "url": "https://production.example.com",
    "timeout": 5,  # Short timeout for production
    "expected_status": 200
}

# For development servers that might be slower
development_config = {
    "url": "https://dev.example.com",
    "timeout": 30,  # Longer timeout for development
    "expected_status": 200
}

# For API endpoints with varying response times
api_config = {
    "url": "https://api.example.com/data",
    "timeout": 45,  # Long timeout for data processing endpoints
    "expected_status": 200
}
```

### Parallel Processing Optimization

```python
from monitorpy import run_check
from concurrent.futures import ThreadPoolExecutor
import time

def check_multiple_endpoints(endpoints, max_workers=None):
    """Check multiple endpoints in parallel with optimal worker count."""
    # Calculate optimal worker count if not specified
    if max_workers is None:
        # A good rule of thumb is 2x the number of CPU cores,
        # but capped at the number of endpoints to avoid excess thread creation
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        max_workers = min(len(endpoints), cpu_count * 2)
    
    print(f"Using {max_workers} workers for {len(endpoints)} checks")
    
    start_time = time.time()
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for name, config in endpoints.items():
            futures[executor.submit(run_check, "website_status", config)] = name
        
        for future in futures:
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                results[name] = f"Error: {str(e)}"
    
    total_time = time.time() - start_time
    print(f"Completed {len(endpoints)} checks in {total_time:.2f} seconds")
    
    return results

# Example usage
endpoints = {
    "Main Website": {"url": "https://www.example.com"},
    "API Endpoint": {"url": "https://api.example.com/status"},
    "Admin Portal": {"url": "https://admin.example.com"}
    # Add more endpoints as needed
}

results = check_multiple_endpoints(endpoints)
```

### Memory Optimization

For handling large responses:

```python
# Configure for potentially large responses
large_content_config = {
    "url": "https://api.example.com/large-dataset",
    "timeout": 60,
    # Additional parameters to optimize memory usage
    "stream": True,  # Stream the response instead of loading it all at once
    "max_content_length": 10 * 1024 * 1024  # 10 MB max content size
}

# Note: Implementation would require extending the website plugin
```

## Troubleshooting

Common configuration issues and how to resolve them.

### Common Website Plugin Issues

| Issue | Possible Causes | Solution |
|-------|----------------|----------|
| Connection timeout | Server unreachable, network issues | Increase timeout, check network connectivity |
| SSL verification errors | Self-signed certificate, expired certificate | Use verify_ssl=False for testing, fix certificates |
| Content not found | Case sensitivity, HTML changes | Check exact content string, use more specific content checks |
| Redirect loop | Misconfigured website, cookies required | Use follow_redirects=False, add required cookies |

### Common SSL Certificate Issues

| Issue | Possible Causes | Solution |
|-------|----------------|----------|
| Certificate not trusted | Self-signed certificate, missing CA | Use check_chain=True to examine chain details |
| Hostname mismatch | Certificate for different domain | Use verify_hostname=False for testing |
| Cannot connect to port | Firewall blocking, wrong port | Check firewall rules, try standard port 443 |
| Handshake failure | Protocol mismatch, cipher mismatch | Check server SSL configuration |

### Common Mail Server Issues

| Issue | Possible Causes | Solution |
|-------|----------------|----------|
| Authentication failure | Wrong credentials, authentication not enabled | Verify credentials, check server requirements |
| Connection refused | Wrong port, firewall | Verify port numbers, check firewall rules |
| TLS negotiation failure | Old TLS version, cipher mismatch | Try different TLS/SSL options |
| Timeout during test send | Slow mail processing, anti-spam measures | Increase timeout, check spam configurations |

### Common DNS Issues

| Issue | Possible Causes | Solution |
|-------|----------------|----------|
| NXDOMAIN error | Domain doesn't exist, typo | Verify domain name spelling |
| No records of type found | Record doesn't exist, wrong record type | Verify record type, check DNS configuration |
| Poor propagation | Recent DNS changes | Wait for propagation, check with authoritative nameservers |
| DNSSEC validation failure | Misconfigured DNSSEC, expired signatures | Check DNSSEC configuration with registrar |

### Debugging Tips

1. **Enable verbose logging**:
   ```python
   from monitorpy.utils import setup_logging
   setup_logging(level="DEBUG", log_file="debug.log")
   ```

2. **Inspect raw data**:
   ```python
   import json
   result = run_check("website_status", config)
   print(json.dumps(result.raw_data, indent=2))
   ```

3. **Test incrementally**:
   ```python
   # Start with basic check
   basic_config = {"url": "https://example.com"}
   basic_result = run_check("website_status", basic_config)
   
   # If that succeeds, add more requirements
   if basic_result.is_success():
       content_config = {
           "url": "https://example.com",
           "expected_content": "Welcome"
       }
       content_result = run_check("website_status", content_config)
       
       # If that succeeds, try authentication
       if content_result.is_success():
           auth_config = {
               "url": "https://example.com/admin",
               "auth_username": "user",
               "auth_password": "pass"
           }
           run_check("website_status", auth_config)
   ```