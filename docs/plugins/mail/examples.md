# Mail Server Monitoring Examples

This document provides examples for common mail server monitoring scenarios using MonitorPy.

## Basic Usage Examples

### Basic SMTP Server Check

Check if an SMTP server is accessible:

```bash
monitorpy mail mail.example.com --protocol smtp
```

```python
from monitorpy import run_check

config = {
    "hostname": "mail.example.com",
    "protocol": "smtp"
}

result = run_check("mail_server", config)
print(f"Status: {result.status}, Message: {result.message}")
```

### Disable MX Record Resolution

MX record resolution is enabled by default. To disable it:

```bash
monitorpy mail example.com --protocol smtp --no-resolve-mx
```

```python
config = {
    "hostname": "example.com",
    "protocol": "smtp",
    "resolve_mx": False  # Disable the default behavior
}

result = run_check("mail_server", config)
if result.is_success():
    # Show which MX server was used
    print(f"Successfully connected to MX server: {result.raw_data.get('hostname_used', 'unknown')}")
```

### SMTP with Authentication

Check SMTP server with login credentials:

```bash
monitorpy mail mail.example.com --protocol smtp --username user@example.com --password yourpassword
```

```python
config = {
    "hostname": "mail.example.com", 
    "protocol": "smtp",
    "username": "user@example.com",
    "password": "yourpassword"
}

result = run_check("mail_server", config)
```

### SMTP with TLS

Test a secure SMTP connection with TLS:

```bash
monitorpy mail mail.example.com --protocol smtp --tls --port 587
```

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "port": 587,
    "use_tls": True
}

result = run_check("mail_server", config)
```

### SMTP with SSL

Test a secure SMTP connection with SSL:

```bash
monitorpy mail mail.example.com --protocol smtp --ssl --port 465
```

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "port": 465,
    "use_ssl": True
}

result = run_check("mail_server", config)
```

### Send Test Email

Verify full email delivery by sending a test message:

```bash
monitorpy mail mail.example.com --protocol smtp --username user@example.com --password yourpassword --send-test --from user@example.com --to recipient@example.com
```

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "username": "user@example.com",
    "password": "yourpassword",
    "test_send": True,
    "from_email": "user@example.com",
    "to_email": "recipient@example.com",
    "subject": "MonitorPy Test Email",
    "message": "This is a test email sent by MonitorPy to verify mail server functionality."
}

result = run_check("mail_server", config)
```

### Check IMAP Server

Test IMAP server connectivity and authentication:

```bash
monitorpy mail mail.example.com --protocol imap --username user@example.com --password yourpassword
```

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "imap",
    "username": "user@example.com",
    "password": "yourpassword"
}

result = run_check("mail_server", config)
if result.is_success():
    # Check mailbox stats if available
    if "mailbox_message_count" in result.raw_data:
        print(f"Mailbox contains {result.raw_data['mailbox_message_count']} messages")
```

### Check POP3 Server

Test POP3 server connectivity and authentication:

```bash
monitorpy mail mail.example.com --protocol pop3 --username user@example.com --password yourpassword
```

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "pop3",
    "username": "user@example.com",
    "password": "yourpassword"
}

result = run_check("mail_server", config)
if result.is_success():
    # Check mailbox stats if available
    if "message_count" in result.raw_data:
        print(f"Mailbox contains {result.raw_data['message_count']} messages")
```

## Advanced Usage Examples

### Checking Multiple Mail Servers

```python
from monitorpy import run_check
from concurrent.futures import ThreadPoolExecutor

def check_mail_server(config):
    """Check a single mail server with the given configuration."""
    result = run_check("mail_server", config)
    return {
        "hostname": config["hostname"],
        "protocol": config["protocol"],
        "status": result.status,
        "message": result.message
    }

# Define mail servers to check
mail_servers = [
    {"hostname": "mail1.example.com", "protocol": "smtp"},
    {"hostname": "mail1.example.com", "protocol": "imap", "use_ssl": True},
    {"hostname": "mail2.example.com", "protocol": "smtp"},
    {"hostname": "example.org", "protocol": "smtp", "resolve_mx": True}
]

# Check servers in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(check_mail_server, mail_servers))

# Print summary
for result in results:
    status_icon = "✅" if result["status"] == "success" else "❌"
    print(f"{status_icon} {result['hostname']} ({result['protocol']}): {result['message']}")
```

### Mail Server Capabilities Check

Check what features a mail server supports:

```python
from monitorpy import run_check
import json

def check_mail_server_capabilities(hostname):
    """Check the capabilities of a mail server across protocols."""
    capabilities = {}
    
    # Check SMTP
    smtp_config = {
        "hostname": hostname,
        "protocol": "smtp"
    }
    smtp_result = run_check("mail_server", smtp_config)
    capabilities["smtp"] = {
        "available": smtp_result.is_success(),
        "supports_tls": smtp_result.raw_data.get("supports_tls", False) if smtp_result.is_success() else False,
        "extensions": smtp_result.raw_data.get("extensions", {}) if smtp_result.is_success() else {},
        "message": smtp_result.message
    }
    
    # Check SMTP with SSL
    smtp_ssl_config = {
        "hostname": hostname,
        "protocol": "smtp",
        "port": 465,
        "use_ssl": True
    }
    smtp_ssl_result = run_check("mail_server", smtp_ssl_config)
    capabilities["smtp_ssl"] = {
        "available": smtp_ssl_result.is_success(),
        "message": smtp_ssl_result.message
    }
    
    # Check IMAP
    imap_config = {
        "hostname": hostname,
        "protocol": "imap"
    }
    imap_result = run_check("mail_server", imap_config)
    capabilities["imap"] = {
        "available": imap_result.is_success(),
        "capabilities": imap_result.raw_data.get("capabilities", "") if imap_result.is_success() else "",
        "message": imap_result.message
    }
    
    # Check POP3
    pop3_config = {
        "hostname": hostname,
        "protocol": "pop3"
    }
    pop3_result = run_check("mail_server", pop3_config)
    capabilities["pop3"] = {
        "available": pop3_result.is_success(),
        "capabilities": pop3_result.raw_data.get("capabilities", []) if pop3_result.is_success() else [],
        "message": pop3_result.message
    }
    
    return capabilities

# Example usage
capabilities = check_mail_server_capabilities("mail.example.com")
print(json.dumps(capabilities, indent=2))
```

### Scheduled Email Server Monitoring

Using MonitorPy with Python's `schedule` library for ongoing monitoring:

```python
import schedule
import time
from monitorpy import run_check
from datetime import datetime

def check_mail_servers():
    """Perform scheduled checks of mail servers."""
    print(f"\n[{datetime.now().isoformat()}] Running mail server checks...")
    
    mail_servers = [
        {
            "name": "Primary SMTP",
            "hostname": "mail.example.com",
            "protocol": "smtp",
            "username": "monitor@example.com",
            "password": "monitorpassword"
        },
        {
            "name": "Secondary SMTP",
            "hostname": "backup-mail.example.com",
            "protocol": "smtp"
        },
        {
            "name": "Primary IMAP",
            "hostname": "mail.example.com",
            "protocol": "imap",
            "use_ssl": True,
            "username": "monitor@example.com",
            "password": "monitorpassword"
        }
    ]
    
    for server in mail_servers:
        name = server.pop("name")
        print(f"\nChecking {name} ({server['hostname']}, {server['protocol']}):")
        
        result = run_check("mail_server", server)
        
        status_icon = "✅" if result.is_success() else "❌"
        print(f"{status_icon} {result.message}")

# Schedule daily checks
schedule.every().day.at("08:00").do(check_mail_servers)

print("Starting scheduled mail server monitoring...")
check_mail_servers()  # Run once immediately

while True:
    schedule.run_pending()
    time.sleep(1)
```

### Integration with Alert System

```python
from monitorpy import run_check
import requests
import time

def send_alert(title, message, level="error"):
    """Send an alert to a webhook or notification service."""
    webhook_url = "https://alerts.example.com/webhook"
    
    payload = {
        "title": title,
        "message": message,
        "level": level,
        "timestamp": time.time()
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send alert: {e}")
        return False

def monitor_mail_server(hostname, protocol, alert_on_failure=True):
    """Monitor a mail server and send alerts on failure."""
    config = {
        "hostname": hostname,
        "protocol": protocol
    }
    
    result = run_check("mail_server", config)
    
    if not result.is_success() and alert_on_failure:
        title = f"Mail Server Alert: {hostname} ({protocol})"
        message = f"Mail server check failed: {result.message}"
        send_alert(title, message)
        return False
    
    return result.is_success()

# Example usage
monitor_mail_server("mail.example.com", "smtp")
```

## CI/CD Integration Examples

### GitHub Actions: Mail Server Verification After Deployment

```yaml
name: Mail Server Verification

on:
  deployment:
    types: [completed]

jobs:
  verify-mail-servers:
    runs-on: ubuntu-latest
    steps:
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install monitorpy
          
      - name: Verify SMTP server
        run: |
          monitorpy mail ${{ secrets.MAIL_SERVER }} --protocol smtp --port 587 --tls \
            --username ${{ secrets.MAIL_USER }} --password ${{ secrets.MAIL_PASSWORD }}
          
      - name: Verify IMAP server
        run: |
          monitorpy mail ${{ secrets.MAIL_SERVER }} --protocol imap --ssl \
            --username ${{ secrets.MAIL_USER }} --password ${{ secrets.MAIL_PASSWORD }}
          
      - name: Test send email
        if: ${{ github.ref == 'refs/heads/main' }}
        run: |
          monitorpy mail ${{ secrets.MAIL_SERVER }} --protocol smtp --port 587 --tls \
            --username ${{ secrets.MAIL_USER }} --password ${{ secrets.MAIL_PASSWORD }} \
            --send-test --from ${{ secrets.MAIL_USER }} --to ${{ secrets.ADMIN_EMAIL }}
```