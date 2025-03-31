# DNS Monitoring Examples

This document provides examples for common DNS monitoring scenarios using MonitorPy.

## Basic Usage Examples

### Check Domain A Record

Check if a domain has A records:

```bash
monitorpy dns example.com
```

```python
from monitorpy import run_check

config = {
    "domain": "example.com",
    "record_type": "A"
}

result = run_check("dns_record", config)
print(f"Status: {result.status}, Message: {result.message}")
```

### Check for Specific IP Address

Verify that a domain resolves to a specific IP address:

```bash
monitorpy dns example.com --type A --value 192.0.2.1
```

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "expected_value": "192.0.2.1"
}

result = run_check("dns_record", config)
if result.is_success():
    print("Domain resolves to expected IP address")
else:
    print(f"Error: {result.message}")
```

### Check MX Records

Check mail exchange records for a domain:

```bash
monitorpy dns example.com --type MX
```

```python
config = {
    "domain": "example.com",
    "record_type": "MX"
}

result = run_check("dns_record", config)
print(f"MX Records: {result.raw_data['records']}")
```

### Check MX Records with Expected Value

Verify specific mail server configuration:

```bash
monitorpy dns example.com --type MX --value "10 mail.example.com"
```

```python
config = {
    "domain": "example.com",
    "record_type": "MX",
    "expected_value": "10 mail.example.com"
}

result = run_check("dns_record", config)
if result.is_success():
    print("MX record is correctly configured")
```

### Check Multiple Expected MX Records

```bash
# Using CLI with multiple values isn't directly supported,
# but you can check for the presence of each one separately

# Using Python API
config = {
    "domain": "example.com",
    "record_type": "MX",
    "expected_value": [
        "10 mail.example.com",
        "20 backup-mail.example.com"
    ]
}

result = run_check("dns_record", config)
if result.is_success():
    print("All expected MX records are present")
```

### Check TXT Records

Check TXT records, useful for SPF, DKIM, or domain verification:

```bash
monitorpy dns example.com --type TXT
```

```python
config = {
    "domain": "example.com",
    "record_type": "TXT"
}

result = run_check("dns_record", config)
print(f"TXT Records: {result.raw_data['records']}")
```

### Check SPF Record

Verify SPF record configuration:

```bash
monitorpy dns example.com --type TXT --value "v=spf1 include:_spf.example.com ~all"
```

```python
config = {
    "domain": "example.com",
    "record_type": "TXT",
    "expected_value": "v=spf1 include:_spf.example.com ~all"
}

result = run_check("dns_record", config)
if result.is_success():
    print("SPF record is correctly configured")
```

### Check DKIM Record

Verify DKIM record for a selector:

```bash
monitorpy dns default._domainkey.example.com --type TXT
```

```python
config = {
    "domain": "example.com",
    "subdomain": "default._domainkey",
    "record_type": "TXT"
}

result = run_check("dns_record", config)
print(f"DKIM Record: {result.raw_data['records']}")
```

### Check Subdomain

Verify a subdomain's configuration:

```bash
monitorpy dns example.com --type A --subdomain www
```

```python
config = {
    "domain": "example.com",
    "subdomain": "www",
    "record_type": "A"
}

result = run_check("dns_record", config)
print(f"www subdomain records: {result.raw_data['records']}")
```

## Advanced Usage Examples

### Check DNS Propagation

Verify DNS propagation across multiple public resolvers:

```bash
monitorpy dns example.com --type A --check-propagation --verbose
```

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "check_propagation": True
}

result = run_check("dns_record", config)

# Print propagation details
prop_data = result.raw_data.get("propagation", {})
print(f"Propagation: {prop_data.get('percentage', 0)}% consistent")
print(f"({prop_data.get('consistent_count', 0)}/{prop_data.get('total_count', 0)} resolvers)")

# Show details for each resolver
for resolver in prop_data.get("resolvers", []):
    status = "✓" if resolver.get("match", False) else "✗"
    name = resolver.get("name", resolver.get("resolver", "Unknown"))
    records = ", ".join(resolver.get("records", []))
    print(f"  {status} {name}: {records}")
```

### Use Custom Resolvers

Test using specific DNS resolvers:

```bash
monitorpy dns example.com --type A --check-propagation --resolvers 8.8.8.8 1.1.1.1 9.9.9.9
```

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "check_propagation": True,
    "resolvers": [
        "8.8.8.8",     # Google
        "1.1.1.1",     # Cloudflare
        "9.9.9.9",     # Quad9
        "208.67.222.222"  # OpenDNS
    ]
}

result = run_check("dns_record", config)
```

### Check DNSSEC Validation

Verify DNSSEC is properly configured and validates:

```bash
monitorpy dns example.com --check-dnssec --verbose
```

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "check_dnssec": True
}

result = run_check("dns_record", config)

# Print DNSSEC details
dnssec_data = result.raw_data.get("dnssec", {})
if dnssec_data.get("is_valid", False):
    print("DNSSEC validation passed")
    if dnssec_data.get("is_signed", False):
        print("Domain is properly signed with DNSSEC")
    else:
        print("Domain is not DNSSEC-signed, but no validation errors")
else:
    print(f"DNSSEC validation failed: {dnssec_data.get('error', 'Unknown error')}")
```

### Check Authoritative Responses

Ensure responses are coming from authoritative nameservers:

```bash
monitorpy dns example.com --check-authoritative --verbose
```

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "check_authoritative": True
}

result = run_check("dns_record", config)

# Print authoritative details
auth_data = result.raw_data.get("authoritative", {})
if auth_data.get("is_authoritative", False):
    print(f"Response is authoritative from {auth_data.get('nameserver', 'Unknown')}")
    print(f"Flags: {auth_data.get('flags', '')}")
else:
    print(f"Non-authoritative response: {auth_data.get('error', 'Unknown error')}")
```

### Use Specific Nameserver

Query a specific nameserver:

```bash
monitorpy dns example.com --nameserver 8.8.8.8
```

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "nameserver": "8.8.8.8"  # Google's public DNS
}

result = run_check("dns_record", config)
```

### Comprehensive DNS Health Check

Perform a complete DNS health check:

```bash
monitorpy dns example.com --type A --value 192.0.2.1 --check-propagation --check-dnssec --check-authoritative --verbose
```

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "expected_value": "192.0.2.1",
    "check_propagation": True,
    "check_authoritative": True,
    "check_dnssec": True,
    "timeout": 15
}

result = run_check("dns_record", config)

# Check overall status
if result.is_success():
    print("DNS health check passed successfully")
elif result.is_warning():
    print(f"DNS health check passed with warnings: {result.message}")
else:
    print(f"DNS health check failed: {result.message}")
```

## Monitoring Examples

### Scheduled DNS Monitoring

```python
import schedule
import time
from monitorpy import run_check
from datetime import datetime

def check_dns():
    print(f"\n[{datetime.now().isoformat()}] Running DNS check...")
    
    domains = [
        {"name": "Main Website", "domain": "example.com", "type": "A", "value": "192.0.2.1"},
        {"name": "API", "domain": "api.example.com", "type": "A", "value": "192.0.2.2"},
        {"name": "Mail", "domain": "example.com", "type": "MX", "value": "10 mail.example.com"}
    ]
    
    for domain in domains:
        config = {
            "domain": domain["domain"],
            "record_type": domain["type"]
        }
        
        if "value" in domain:
            config["expected_value"] = domain["value"]
            
        print(f"\nChecking {domain['name']} ({domain['domain']}, {domain['type']}):")
        result = run_check("dns_record", config)
        
        status_icon = "✅" if result.is_success() else "⚠️" if result.is_warning() else "❌"
        print(f"{status_icon} {result.message}")

# Schedule checks
schedule.every(1).hour.do(check_dns)

print("Starting scheduled DNS monitoring...")
check_dns()  # Run once immediately

while True:
    schedule.run_pending()
    time.sleep(1)
```

### DNS Change Detection

```python
import time
from monitorpy import run_check
import json
import os
from datetime import datetime

def store_results(domain, record_type, results):
    """Store DNS check results for comparison."""
    filename = f"{domain.replace('.', '_')}_{record_type}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

def load_previous_results(domain, record_type):
    """Load previous DNS check results."""
    filename = f"{domain.replace('.', '_')}_{record_type}.json"
    
    if not os.path.exists(filename):
        return None
        
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return None

def monitor_dns_changes(domain, record_type):
    """Monitor DNS records for changes."""
    config = {
        "domain": domain,
        "record_type": record_type
    }
    
    result = run_check("dns_record", config)
    current_records = result.raw_data.get("records", [])
    timestamp = datetime.now().isoformat()
    
    results = {
        "timestamp": timestamp,
        "records": current_records,
        "status": result.status
    }
    
    previous = load_previous_results(domain, record_type)
    
    if previous:
        prev_records = set(previous.get("records", []))
        curr_records = set(current_records)
        
        # Check for changes
        if prev_records != curr_records:
            added = curr_records - prev_records
            removed = prev_records - curr_records
            
            print(f"[{timestamp}] DNS CHANGE DETECTED for {domain} ({record_type}):")
            if added:
                print(f"  Added records: {', '.join(added)}")
            if removed:
                print(f"  Removed records: {', '.join(removed)}")
                
            # Store the new results
            store_results(domain, record_type, results)
            return True
        else:
            print(f"[{timestamp}] No changes detected for {domain} ({record_type})")
            return False
    else:
        print(f"[{timestamp}] Initial DNS check for {domain} ({record_type}): {', '.join(current_records)}")
        store_results(domain, record_type, results)
        return False

# Example usage
domains_to_monitor = [
    {"domain": "example.com", "type": "A"},
    {"domain": "example.com", "type": "MX"},
    {"domain": "example.com", "type": "NS"}
]

while True:
    for domain_info in domains_to_monitor:
        monitor_dns_changes(domain_info["domain"], domain_info["type"])
    
    # Wait for 1 hour before next check
    print("\nSleeping for 1 hour...\n")
    time.sleep(3600)
```

## Integration Examples

### Alert on DNS Changes

```python
import requests
from monitorpy import run_check
import time
import json

def send_alert(message, webhook_url):
    """Send alert to webhook."""
    payload = {
        "text": message
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending alert: {str(e)}")
        return False

def monitor_critical_dns(domain, record_type, expected_value, webhook_url):
    """Monitor critical DNS records and alert on changes."""
    config = {
        "domain": domain,
        "record_type": record_type,
        "expected_value": expected_value,
        "check_propagation": True
    }
    
    result = run_check("dns_record", config)
    
    if not result.is_success():
        alert_message = f"❌ CRITICAL DNS ALERT: {domain} {record_type} record check failed!\n"
        alert_message += f"Expected: {expected_value}\n"
        alert_message += f"Message: {result.message}"
        
        send_alert(alert_message, webhook_url)
        return False
        
    # Also check propagation if available
    propagation = result.raw_data.get("propagation", {})
    percentage = propagation.get("percentage", 100)
    
    if percentage < 90:
        alert_message = f"⚠️ DNS PROPAGATION ALERT: {domain} {record_type} record propagation at {percentage}%\n"
        alert_message += f"Expected: {expected_value}\n"
        alert_message += f"Consistent on {propagation.get('consistent_count', 0)}/{propagation.get('total_count', 0)} resolvers"
        
        send_alert(alert_message, webhook_url)
        return False
        
    return True

# Example usage
webhook_url = "https://hooks.slack.com/services/your_webhook_path"
critical_records = [
    {"domain": "example.com", "type": "A", "value": "192.0.2.1"},
    {"domain": "api.example.com", "type": "A", "value": "192.0.2.2"},
    {"domain": "example.com", "type": "MX", "value": "10 mail.example.com"}
]

# Continuously monitor all critical records
while True:
    for record in critical_records:
        print(f"Checking {record['domain']} ({record['type']})...")
        monitor_critical_dns(record['domain'], record['type'], record['value'], webhook_url)
    
    # Check every 15 minutes
    print("Sleeping for 15 minutes...")
    time.sleep(900)
```

### DNS Monitoring in CI/CD Pipeline

Example GitHub Actions workflow to verify DNS changes after deployment:

```yaml
name: DNS Verification

on:
  deployment:
    types: [completed]

jobs:
  verify-dns:
    runs-on: ubuntu-latest
    steps:
      - name: Check out code
        uses: actions/checkout@v2
        
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install monitorpy dnspython
          
      - name: Wait for DNS propagation
        run: sleep 300  # Wait 5 minutes
      
      - name: Verify DNS records
        run: |
          # Verify main domain
          monitorpy dns ${{ vars.DOMAIN }} --type A --value ${{ vars.EXPECTED_IP }} --check-propagation --threshold 70
          
          # Verify www subdomain
          monitorpy dns ${{ vars.DOMAIN }} --type A --subdomain www --value ${{ vars.EXPECTED_IP }} --check-propagation
          
          # Verify API subdomain
          monitorpy dns ${{ vars.DOMAIN }} --type A --subdomain api --value ${{ vars.API_IP }} --check-propagation
```