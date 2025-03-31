# Configuration Templates

This document provides ready-to-use configuration templates for common monitoring scenarios.

## Website Monitoring Templates

### Basic Website Availability

```python
{
    "url": "https://www.example.com",
    "timeout": 30,
    "expected_status": 200,
    "follow_redirects": True,
    "verify_ssl": True
}
```

### API Endpoint

```python
{
    "url": "https://api.example.com/health",
    "method": "GET",
    "headers": {
        "Accept": "application/json",
        "User-Agent": "MonitorPy/1.0"
    },
    "timeout": 15,
    "expected_status": 200,
    "expected_content": "\"status\":\"ok\""
}
```

### Secured Admin Portal

```python
{
    "url": "https://admin.example.com/dashboard",
    "method": "GET",
    "auth_username": "admin",
    "auth_password": "your_password",
    "timeout": 30,
    "expected_status": 200,
    "expected_content": "Admin Dashboard",
    "verify_ssl": True
}
```

### E-commerce Product Page

```python
{
    "url": "https://shop.example.com/products/123",
    "headers": {
        "User-Agent": "MonitorPy/1.0",
        "Accept-Language": "en-US,en;q=0.9"
    },
    "timeout": 45,  # E-commerce sites may be slower
    "expected_status": 200,
    "expected_content": "Add to Cart",
    "unexpected_content": ["Out of stock", "Error", "Not found"],
    "follow_redirects": True
}
```

### GraphQL API Query

```python
{
    "url": "https://api.example.com/graphql",
    "method": "POST",
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_TOKEN"
    },
    "body": """
        {
            "query": "{ status { code message serverTime } }"
        }
    """,
    "expected_status": 200,
    "expected_content": "\"code\":\"ok\""
}
```

## SSL Certificate Templates

### Standard SSL Check

```python
{
    "hostname": "www.example.com",
    "port": 443,
    "timeout": 30,
    "warning_days": 30,
    "critical_days": 14,
    "verify_hostname": True
}
```

### E-commerce SSL (Stricter Requirements)

```python
{
    "hostname": "shop.example.com",
    "port": 443,
    "timeout": 30,
    "warning_days": 60,  # Longer lead time for e-commerce
    "critical_days": 30,
    "check_chain": True,  # Verify the entire certificate chain
    "verify_hostname": True
}
```

### Custom Port Service

```python
{
    "hostname": "secure-api.example.com",
    "port": 8443,  # Non-standard port
    "timeout": 30,
    "warning_days": 30,
    "critical_days": 14
}
```

### Internal Certificate (Self-Signed)

```python
{
    "hostname": "internal.example.com",
    "port": 443,
    "timeout": 30,
    "warning_days": 30,
    "critical_days": 14,
    "verify_hostname": False,  # Don't strictly verify hostname for internal services
    "check_chain": False  # Don't check the certificate chain for self-signed certificates
}
```

## Mail Server Templates

### SMTP Basic Check

```python
{
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "port": 25,
    "timeout": 30
}
```

### Secure SMTP with Authentication

```python
{
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "port": 587,
    "use_tls": True,
    "username": "user@example.com",
    "password": "your_password",
    "timeout": 30
}
```

### IMAP Check

```python
{
    "hostname": "mail.example.com",
    "protocol": "imap",
    "port": 993,
    "use_ssl": True,
    "username": "user@example.com",
    "password": "your_password",
    "timeout": 30
}
```

### POP3 Check

```python
{
    "hostname": "mail.example.com",
    "protocol": "pop3",
    "port": 995,
    "use_ssl": True,
    "username": "user@example.com",
    "password": "your_password",
    "timeout": 30
}
```

### Complete Mail Check with Test Send

```python
{
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "port": 587,
    "use_tls": True,
    "username": "user@example.com",
    "password": "your_password",
    "timeout": 45,
    "test_send": True,
    "from_email": "user@example.com",
    "to_email": "recipient@example.com",
    "subject": "MonitorPy Test Email",
    "message": "This is a test email sent by MonitorPy to verify mail server functionality."
}
```

### Domain MX Record Check

```python
{
    "hostname": "example.com",  # Just the domain, not the mail server
    "protocol": "smtp",
    "resolve_mx": True,  # Resolve MX records and check the highest priority server
    "timeout": 30
}
```

## DNS Monitoring Templates

### Basic A Record Check

```python
{
    "domain": "example.com",
    "record_type": "A",
    "timeout": 10
}
```

### A Record with Expected Value

```python
{
    "domain": "example.com",
    "record_type": "A",
    "expected_value": "192.0.2.1",
    "timeout": 10
}
```

### Multiple Expected Values

```python
{
    "domain": "example.com",
    "record_type": "A",
    "expected_value": ["192.0.2.1", "192.0.2.2", "192.0.2.3"],  # Any of these values is acceptable
    "timeout": 10
}
```

### MX Record Check

```python
{
    "domain": "example.com",
    "record_type": "MX",
    "timeout": 10
}
```

### TXT Record for SPF

```python
{
    "domain": "example.com",
    "record_type": "TXT",
    "expected_value": "v=spf1",  # Just checking for SPF presence
    "timeout": 10
}
```

### Comprehensive Domain Check

```python
{
    "domain": "example.com",
    "record_type": "A",
    "expected_value": "192.0.2.1",
    "check_propagation": True,
    "propagation_threshold": 90.0,
    "check_dnssec": True,
    "check_authoritative": True,
    "timeout": 30,
    "max_workers": 10
}
```

### Subdomain Check

```python
{
    "domain": "example.com",
    "subdomain": "www",  # Will check www.example.com
    "record_type": "A",
    "timeout": 10
}
```

## Template System

You can create a simple template system to make it easier to apply these configurations:

```python
def apply_template(template, **replacements):
    """
    Apply a template with custom replacements.
    
    Args:
        template: The template dictionary to use
        replacements: Key-value pairs to replace in the template
        
    Returns:
        Dict: The template with replacements applied
    """
    import copy
    import json
    
    # Deep copy to avoid modifying the original
    result = copy.deepcopy(template)
    
    # Convert to string to apply replacements
    config_str = json.dumps(result)
    
    # Apply replacements
    for key, value in replacements.items():
        placeholder = f"{{{key}}}"
        config_str = config_str.replace(placeholder, str(value))
    
    # Convert back to dictionary
    return json.loads(config_str)

# Example usage
website_template = {
    "url": "https://{domain}",
    "timeout": 30,
    "expected_status": 200,
    "expected_content": "{content}"
}

# Apply template for specific site
my_config = apply_template(
    website_template,
    domain="example.com",
    content="Welcome to Example"
)
```

## Composite Checks

For more comprehensive monitoring, you can combine multiple checks:

```python
def check_website_complete(domain):
    """
    Perform a complete website check including SSL and DNS.
    
    Args:
        domain: The domain to check
        
    Returns:
        Dict: Results of all checks
    """
    from monitorpy import run_check
    
    results = {}
    
    # Website availability
    website_config = {
        "url": f"https://{domain}",
        "timeout": 30,
        "expected_status": 200
    }
    results["website"] = run_check("website_status", website_config)
    
    # SSL certificate
    ssl_config = {
        "hostname": domain,
        "warning_days": 30,
        "critical_days": 14
    }
    results["ssl"] = run_check("ssl_certificate", ssl_config)
    
    # DNS A record
    dns_config = {
        "domain": domain,
        "record_type": "A"
    }
    results["dns"] = run_check("dns_record", dns_config)
    
    return results

# Example usage
results = check_website_complete("example.com")
```

These templates should help you get started with common monitoring scenarios. You can adapt them to your specific needs by adjusting the parameters as needed.