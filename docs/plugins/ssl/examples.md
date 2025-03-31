# SSL Certificate Monitoring Examples

This document provides examples for common SSL certificate monitoring scenarios using MonitorPy.

## Basic Usage Examples

### Basic SSL Certificate Check

Check if an SSL certificate is valid and not expiring soon:

```bash
monitorpy ssl example.com
```

```python
from monitorpy import run_check

config = {
    "hostname": "example.com"
}

result = run_check("ssl_certificate", config)
print(f"Status: {result.status}, Message: {result.message}")
```

### Check Certificate with Custom Warning Thresholds

Set custom warning and critical thresholds for certificate expiration:

```bash
monitorpy ssl example.com --warning 60 --critical 30
```

```python
config = {
    "hostname": "example.com",
    "warning_days": 60,  # Warn if expiring within 60 days
    "critical_days": 30  # Critical if expiring within 30 days
}

result = run_check("ssl_certificate", config)
```

### Check Certificate on Non-Standard Port

Check an SSL certificate on a non-standard port:

```bash
monitorpy ssl example.com --port 8443
```

```python
config = {
    "hostname": "example.com",
    "port": 8443
}

result = run_check("ssl_certificate", config)
```

### Check with Detailed Certificate Information

Get detailed information about a certificate:

```bash
monitorpy ssl example.com --check-chain --verbose
```

```python
config = {
    "hostname": "example.com",
    "check_chain": True
}

result = run_check("ssl_certificate", config)

# Print certificate details
print(f"Subject: {result.raw_data['subject']}")
print(f"Issuer: {result.raw_data['issuer']}")
print(f"Valid from: {result.raw_data['not_before']}")
print(f"Valid until: {result.raw_data['not_after']}")
print(f"Days until expiration: {result.raw_data['days_until_expiration']}")
print(f"Alternative names: {result.raw_data['alternative_names']}")
```

### Check Multiple Domains

Monitor SSL certificates for multiple domains:

```python
from monitorpy import run_check

domains = [
    "example.com",
    "example.org",
    "example.net"
]

results = {}
for domain in domains:
    config = {"hostname": domain}
    results[domain] = run_check("ssl_certificate", config)

# Print summary
for domain, result in results.items():
    status = "✅" if result.is_success() else "❌"
    expiry = result.raw_data.get("days_until_expiration", "N/A")
    print(f"{status} {domain}: {result.message} ({expiry} days remaining)")
```

## Advanced Usage Examples

### Extract and Verify Certificate Attributes

Check specific certificate attributes:

```python
from monitorpy import run_check
from datetime import datetime

def check_certificate_details(hostname):
    """Check specific attributes of an SSL certificate."""
    config = {
        "hostname": hostname,
        "check_chain": True
    }
    
    result = run_check("ssl_certificate", config)
    
    if not result.is_success():
        print(f"❌ Certificate check failed: {result.message}")
        return False
    
    # Extract certificate details
    subject = result.raw_data.get("subject", {})
    issuer = result.raw_data.get("issuer", {})
    alternative_names = result.raw_data.get("alternative_names", [])
    
    # Check for specific issuer
    if "Let's Encrypt" not in str(issuer):
        print(f"⚠️ Certificate not issued by Let's Encrypt: {issuer}")
    
    # Check for minimum validity period
    days_left = result.raw_data.get("days_until_expiration", 0)
    if days_left < 60:
        print(f"⚠️ Certificate will expire soon: {days_left} days left")
    
    # Check for wildcard
    is_wildcard = any("*." in name for name in alternative_names)
    print(f"Wildcard certificate: {'Yes' if is_wildcard else 'No'}")
    
    # Check if specific subdomains are covered
    required_domains = [hostname, f"www.{hostname}", f"api.{hostname}"]
    missing_domains = [domain for domain in required_domains if domain not in alternative_names]
    
    if missing_domains:
        print(f"⚠️ Certificate is missing coverage for: {', '.join(missing_domains)}")
    
    # Print TLS version and cipher if available
    if "protocol" in result.raw_data:
        print(f"TLS Version: {result.raw_data['protocol']}")
    
    if "cipher" in result.raw_data:
        print(f"Cipher: {result.raw_data['cipher'][0]}, Strength: {result.raw_data['cipher'][2]} bits")
    
    return True

# Example usage
check_certificate_details("example.com")
```

### Certificate Expiration Dashboard

Create a simple certificate expiration dashboard:

```python
from monitorpy import run_check
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def create_expiration_dashboard(domains):
    """Create a visual dashboard of certificate expiration dates."""
    results = []
    
    for domain in domains:
        config = {"hostname": domain}
        result = run_check("ssl_certificate", config)
        
        # Store domain and expiration info
        days_left = result.raw_data.get("days_until_expiration", 0) if result.is_success() else 0
        expiry_date = result.raw_data.get("not_after", "Unknown") if result.is_success() else "Unknown"
        
        results.append({
            "domain": domain,
            "days_left": days_left,
            "expiry_date": expiry_date,
            "status": result.status
        })
    
    # Sort by days remaining
    results.sort(key=lambda x: x["days_left"])
    
    # Create visualization data
    domains = [r["domain"] for r in results]
    days_left = [r["days_left"] for r in results]
    colors = [
        "red" if r["status"] == "error" else 
        "orange" if r["status"] == "warning" else 
        "green" for r in results
    ]
    
    # Create bar chart
    plt.figure(figsize=(12, 6))
    bars = plt.barh(domains, days_left, color=colors)
    
    # Add labels
    for i, bar in enumerate(bars):
        plt.text(
            bar.get_width() + 5, 
            bar.get_y() + bar.get_height()/2, 
            f"{days_left[i]} days ({results[i]['expiry_date']})",
            va='center'
        )
    
    # Add lines for warning/critical thresholds
    plt.axvline(x=30, color='r', linestyle='--', label='Critical (30 days)')
    plt.axvline(x=60, color='orange', linestyle='--', label='Warning (60 days)')
    
    plt.xlabel('Days until expiration')
    plt.title('SSL Certificate Expiration Dashboard')
    plt.xlim(0, max(days_left) * 1.2)
    plt.legend()
    plt.tight_layout()
    
    # Save and display
    plt.savefig('ssl_expiration_dashboard.png')
    plt.show()
    
    return results

# Example usage
domains = [
    "example.com",
    "example.org",
    "example.net",
    "example.io",
    "example.co"
]

dashboard_data = create_expiration_dashboard(domains)
```

### Scheduled Certificate Monitoring

Using MonitorPy with Python's `schedule` library to run periodic certificate checks:

```python
import schedule
import time
from monitorpy import run_check
from datetime import datetime
import smtplib
from email.message import EmailMessage

def send_alert_email(domain, days_left, expiry_date):
    """Send an email alert for expiring certificates."""
    msg = EmailMessage()
    msg['Subject'] = f'SSL Certificate Alert: {domain}'
    msg['From'] = 'alerts@example.com'
    msg['To'] = 'admin@example.com'
    
    msg.set_content(f"""
    SSL CERTIFICATE ALERT

    Domain: {domain}
    Expiration: {expiry_date}
    Days Remaining: {days_left}

    Please renew your SSL certificate soon to avoid service disruption.
    """)
    
    # Send the message
    server = smtplib.SMTP('smtp.example.com')
    server.send_message(msg)
    server.quit()

def check_certificates():
    """Check SSL certificates and send alerts for expiring certs."""
    print(f"\n[{datetime.now().isoformat()}] Running SSL certificate checks...")
    
    domains = [
        {"domain": "example.com", "warning": 45, "critical": 15},
        {"domain": "api.example.com", "warning": 60, "critical": 30},
        {"domain": "secure.example.com", "warning": 90, "critical": 45}
    ]
    
    for domain_info in domains:
        domain = domain_info["domain"]
        warning_days = domain_info.get("warning", 30)
        critical_days = domain_info.get("critical", 14)
        
        print(f"\nChecking {domain}...")
        
        config = {
            "hostname": domain,
            "warning_days": warning_days,
            "critical_days": critical_days
        }
        
        result = run_check("ssl_certificate", config)
        
        # Extract expiration info
        days_left = result.raw_data.get("days_until_expiration", 0) if result.is_success() else 0
        expiry_date = result.raw_data.get("not_after", "Unknown") if result.is_success() else "Unknown"
        
        # Determine status and icon
        if result.status == "error":
            icon = "❌"
            # Send alert email for critical status
            send_alert_email(domain, days_left, expiry_date)
        elif result.status == "warning":
            icon = "⚠️"
            # Send warning email
            send_alert_email(domain, days_left, expiry_date)
        else:
            icon = "✅"
        
        print(f"{icon} {result.message}")
        print(f"   Expires: {expiry_date} ({days_left} days remaining)")

# Schedule checks
schedule.every(1).day.at("08:00").do(check_certificates)

print("Starting scheduled SSL certificate monitoring...")
check_certificates()  # Run once immediately

while True:
    schedule.run_pending()
    time.sleep(1)
```

## Integration Examples

### Certificate Monitoring with Prometheus

```python
from prometheus_client import start_http_server, Gauge
from monitorpy import run_check
import time
import threading

# Create Prometheus metrics
CERT_DAYS_REMAINING = Gauge('ssl_certificate_days_remaining', 
                          'Days until certificate expiration', 
                          ['domain'])
CERT_STATUS = Gauge('ssl_certificate_status',
                  'Certificate status (0=error, 1=warning, 2=ok)',
                  ['domain'])

def monitor_certificates(domains, interval=3600):
    """Monitor certificates and update Prometheus metrics."""
    while True:
        for domain in domains:
            try:
                config = {"hostname": domain}
                result = run_check("ssl_certificate", config)
                
                # Update days remaining metric
                days_left = result.raw_data.get("days_until_expiration", 0) if result.is_success() else 0
                CERT_DAYS_REMAINING.labels(domain=domain).set(days_left)
                
                # Update status metric
                status_value = 2 if result.status == "success" else 1 if result.status == "warning" else 0
                CERT_STATUS.labels(domain=domain).set(status_value)
                
                print(f"[{time.ctime()}] Updated metrics for {domain}: {days_left} days remaining, status {result.status}")
                
            except Exception as e:
                print(f"Error updating metrics for {domain}: {str(e)}")
                # Set error status
                CERT_DAYS_REMAINING.labels(domain=domain).set(0)
                CERT_STATUS.labels(domain=domain).set(0)
        
        time.sleep(interval)

# Set up Prometheus HTTP server
start_http_server(8000)
print("Prometheus metrics available at http://localhost:8000/metrics")

# Monitor these domains
domains_to_monitor = [
    "example.com",
    "example.org",
    "example.net"
]

# Start monitoring in a background thread
monitoring_thread = threading.Thread(
    target=monitor_certificates,
    args=(domains_to_monitor,),
    daemon=True
)
monitoring_thread.start()

# Keep the main thread running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping monitoring...")
```

### SSL Certificate Monitoring in CI/CD Pipeline

Example GitHub Actions workflow to verify SSL certificates:

```yaml
name: SSL Certificate Verification

on:
  schedule:
    - cron: '0 8 * * *'  # Run daily at 8 AM

jobs:
  verify-certificates:
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
          pip install monitorpy
          
      - name: Verify SSL certificates
        run: |
          # Check all domains
          domains=("example.com" "api.example.com" "secure.example.com")
          
          for domain in "${domains[@]}"; do
            echo "Checking $domain..."
            monitorpy ssl $domain --warning 45 --critical 15
            
            if [ $? -eq 2 ]; then
              echo "::error::SSL certificate for $domain is critical!"
              exit_code=1
            elif [ $? -eq 1 ]; then
              echo "::warning::SSL certificate for $domain has warnings!"
            fi
          done
          
          exit ${exit_code:-0}
```