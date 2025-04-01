# Examples

This document provides examples for common monitoring scenarios using MonitorPy.

## Website Monitoring Examples

### Basic Website Availability Check

Check if a website is accessible:

```bash
monitorpy website https://www.example.com
```

### Check for Specific Content

Verify that a website contains specific text:

```bash
monitorpy website https://www.example.com --content "Welcome to Example"
```

### Check with Authentication

Monitor a protected website using basic authentication:

```bash
monitorpy website https://private.example.com --auth-username user --auth-password pass
```

### API Endpoint Test

Test an API endpoint with custom headers and body:

```bash
monitorpy website https://api.example.com/users \
  --method POST \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer token123" \
  --body '{"name": "Test User", "email": "test@example.com"}' \
  --status 201
```

### Check for Unwanted Content

Ensure a website doesn't contain specific text (e.g., error messages):

```bash
monitorpy website https://www.example.com --no-content "Error" --no-content "Not Found"
```

## SSL Certificate Monitoring Examples

### Basic SSL Certificate Check

Check if an SSL certificate is valid and not expiring soon:

```bash
monitorpy ssl www.example.com
```

### Custom Expiration Thresholds

Set custom warning and critical thresholds for certificate expiration:

```bash
monitorpy ssl www.example.com --warning 60 --critical 30
```

### Check Certificate on Non-Standard Port

Monitor SSL on a non-standard port:

```bash
monitorpy ssl secure.example.com --port 8443
```

### Detailed Certificate Information

Get detailed information about a certificate:

```bash
monitorpy ssl www.example.com --check-chain --verbose
```

## Using MonitorPy Programmatically

### Basic Website Check from Python

```python
from monitorpy import run_check
from monitorpy.utils.formatting import format_result

# Configure the check
config = {
    "url": "https://www.example.com",
    "timeout": 10
}

# Run the check
result = run_check("website_status", config)

# Process the result
print(format_result(result, verbose=True))

if result.is_success():
    print("Website is up!")
elif result.is_warning():
    print("Website has warnings!")
else:
    print("Website is down!")
```

### Checking Multiple Websites in Series

```python
from monitorpy import run_check

websites = [
    "https://www.example.com",
    "https://api.example.com",
    "https://blog.example.com"
]

results = {}
for website in websites:
    config = {"url": website}
    results[website] = run_check("website_status", config)

# Print summary
for website, result in results.items():
    status = "✅" if result.is_success() else "❌"
    print(f"{status} {website}: {result.message}")
```

### Checking Multiple Websites in Parallel

```python
from monitorpy.core import run_checks_in_parallel

websites = [
    "https://www.example.com",
    "https://api.example.com",
    "https://blog.example.com",
    "https://github.com",
    "https://gitlab.com",
    "https://bitbucket.org"
]

# Create check configurations
check_configs = [
    {
        "id": f"site{i+1}",
        "plugin_type": "website_status",
        "config": {
            "url": url,
            "timeout": 30,
            "expected_status": 200
        }
    }
    for i, url in enumerate(websites)
]

# Run checks in parallel with up to 10 worker threads
results = run_checks_in_parallel(check_configs, max_workers=10)

# Process results
for check_config, result in results:
    url = check_config["config"]["url"]
    status = "✅" if result.is_success() else "❌"
    print(f"{status} {url}: {result.message} ({result.response_time:.2f}s)")

# Calculate statistics
total = len(results)
success = sum(1 for _, result in results if result.status == "success")
print(f"Summary: {success}/{total} successful")
```

### Scheduled Monitoring

Using MonitorPy with Python's `schedule` library to run periodic checks:

```python
import schedule
import time
from monitorpy import run_check
from datetime import datetime

def check_website():
    print(f"\n[{datetime.now().isoformat()}] Running website check...")
    config = {"url": "https://www.example.com"}
    result = run_check("website_status", config)
    print(f"Status: {result.status}, Message: {result.message}")

def check_ssl():
    print(f"\n[{datetime.now().isoformat()}] Running SSL check...")
    config = {"hostname": "www.example.com"}
    result = run_check("ssl_certificate", config)
    print(f"Status: {result.status}, Message: {result.message}")

# Schedule checks
schedule.every(5).minutes.do(check_website)
schedule.every(1).day.at("08:00").do(check_ssl)

print("Starting scheduled monitoring...")
while True:
    schedule.run_pending()
    time.sleep(1)
```

### Creating a Simple Monitoring Dashboard

Using MonitorPy with Flask to create a simple web dashboard:

```python
from flask import Flask, render_template_string
from monitorpy import run_check
import threading
import time

app = Flask(__name__)

# Store monitoring results
results = {}

# Define sites to monitor
sites = [
    {"name": "Example", "url": "https://www.example.com"},
    {"name": "Google", "url": "https://www.google.com"},
    {"name": "GitHub", "url": "https://github.com"}
]

def background_monitoring():
    """Background thread to run checks periodically"""
    while True:
        for site in sites:
            config = {"url": site["url"]}
            result = run_check("website_status", config)
            results[site["name"]] = {
                "status": result.status,
                "message": result.message,
                "time": result.response_time,
                "timestamp": result.timestamp.isoformat()
            }
        time.sleep(60)  # Check every minute

# Start background monitoring
threading.Thread(target=background_monitoring, daemon=True).start()

# Simple HTML template for the dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>MonitorPy Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr.success { background-color: #dff0d8; }
        tr.warning { background-color: #fcf8e3; }
        tr.error { background-color: #f2dede; }
        .refresh { margin-top: 20px; }
    </style>
</head>
<body>
    <h1>MonitorPy Dashboard</h1>
    <table>
        <tr>
            <th>Site</th>
            <th>Status</th>
            <th>Message</th>
            <th>Response Time</th>
            <th>Last Checked</th>
        </tr>
        {% for name, result in results.items() %}
        <tr class="{{ result.status }}">
            <td>{{ name }}</td>
            <td>{{ result.status|upper }}</td>
            <td>{{ result.message }}</td>
            <td>{{ "%.4f"|format(result.time) }} s</td>
            <td>{{ result.timestamp }}</td>
        </tr>
        {% endfor %}
    </table>
    <div class="refresh">
        <p>Auto-refreshes every 60 seconds</p>
        <button onclick="location.reload()">Refresh Now</button>
    </div>
    <script>
        setTimeout(function() {
            location.reload();
        }, 60000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_TEMPLATE, results=results)

if __name__ == '__main__':
    app.run(debug=True)
```

## Automation Examples

### Adding MonitorPy to a CI/CD Pipeline

Here's an example GitLab CI configuration that uses MonitorPy to check a website after deployment:

```yaml
stages:
  - deploy
  - monitor

deploy:
  stage: deploy
  script:
    - echo "Deploying the application..."
    - # Deployment commands here
  
monitor:
  stage: monitor
  script:
    - pip install monitorpy
    - echo "Checking website availability..."
    - monitorpy website https://www.example.com --content "Welcome"
    - echo "Checking API endpoints..."
    - monitorpy website https://api.example.com/health --status 200
    - echo "Checking SSL certificate..."
    - monitorpy ssl www.example.com
  after_script:
    - echo "Monitoring completed"
```

### Batch Processing for Large Numbers of Checks

When you need to monitor hundreds or thousands of endpoints, it's better to use the batch processing functionality:

```python
from monitorpy.core import run_check_batch
import csv
import time

# Load URLs from a CSV file
def load_urls_from_csv(file_path):
    urls = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].startswith('http'):
                urls.append(row[0])
    return urls

# Load a large number of URLs
urls = load_urls_from_csv('large_website_list.csv')
print(f"Loaded {len(urls)} URLs to check")

# Create check configurations
check_configs = [
    {
        "id": f"site{i+1}",
        "plugin_type": "website_status",
        "config": {
            "url": url,
            "timeout": 10,
            "expected_status": 200
        }
    }
    for i, url in enumerate(urls)
]

# Start timing
start_time = time.time()

# Process in batches of 50 with 20 workers each
results = run_check_batch(check_configs, batch_size=50, max_workers=20)

# Print stats
duration = time.time() - start_time
total_count = len(results)
success_count = sum(1 for _, result in results if result.status == "success")
error_count = sum(1 for _, result in results if result.status == "error")
warning_count = sum(1 for _, result in results if result.status == "warning")

print(f"Completed {total_count} checks in {duration:.2f} seconds")
print(f"Results: {success_count} successful, {warning_count} warnings, {error_count} errors")
print(f"Average time per check: {duration/total_count:.4f} seconds")
```

### Creating a System Service for Continuous Monitoring

This example shows how to create a systemd service on Linux to run MonitorPy continuously:

1. Create a monitoring script (`/usr/local/bin/monitorpy-service.py`):

```python
#!/usr/bin/env python3
import time
import logging
import json
from datetime import datetime
from monitorpy import run_check

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/var/log/monitorpy.log'
)
logger = logging.getLogger("monitorpy-service")

# Sites to monitor
SITES = [
    {
        "name": "Main Website",
        "type": "website_status",
        "config": {"url": "https://www.example.com"},
        "interval": 300  # 5 minutes
    },
    {
        "name": "API Service",
        "type": "website_status",
        "config": {
            "url": "https://api.example.com/health",
            "expected_content": "\"status\":\"ok\""
        },
        "interval": 60  # 1 minute
    },
    {
        "name": "SSL Certificate",
        "type": "ssl_certificate",
        "config": {"hostname": "www.example.com"},
        "interval": 86400  # 1 day
    }
]

# Track last check times
last_checks = {site["name"]: 0 for site in SITES}

# Main monitoring loop
logger.info("Starting monitoring service")
while True:
    now = time.time()
    
    for site in SITES:
        # Check if it's time to run this check
        time_since_last_check = now - last_checks[site["name"]]
        if time_since_last_check < site["interval"]:
            continue
            
        logger.info(f"Running check for {site['name']}")
        
        try:
            # Run the check
            result = run_check(site["type"], site["config"])
            
            # Log the result
            logger.info(f"{site['name']}: {result.status} - {result.message}")
            
            # Save results to a JSON file for each site
            with open(f"/var/lib/monitorpy/{site['name'].replace(' ', '_')}.json", 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
                
            # Update last check time
            last_checks[site["name"]] = now
                
        except Exception as e:
            logger.error(f"Error running check for {site['name']}: {str(e)}")
    
    # Sleep for a short time before next iteration
    time.sleep(10)
```

2. Create a systemd service file (`/etc/systemd/system/monitorpy.service`):

```
[Unit]
Description=MonitorPy Monitoring Service
After=network.target

[Service]
ExecStart=/usr/local/bin/monitorpy-service.py
Restart=always
User=monitorpy
Group=monitorpy
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo chmod +x /usr/local/bin/monitorpy-service.py
sudo systemctl enable monitorpy
sudo systemctl start monitorpy
```
