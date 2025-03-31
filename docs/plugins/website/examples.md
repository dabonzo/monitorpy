# Website Monitoring Examples

This document provides examples for common website monitoring scenarios using MonitorPy.

## Basic Usage Examples

### Basic Website Availability Check

Check if a website is accessible:

```bash
monitorpy website https://www.example.com
```

```python
from monitorpy import run_check

config = {
    "url": "https://www.example.com"
}

result = run_check("website_status", config)
print(f"Status: {result.status}, Message: {result.message}")
```

### Check for Specific Content

Verify that a website contains specific text:

```bash
monitorpy website https://www.example.com --content "Welcome to Example"
```

```python
config = {
    "url": "https://www.example.com",
    "expected_content": "Welcome to Example"
}

result = run_check("website_status", config)
if result.is_success():
    print("Website contains the expected content")
else:
    print(f"Error: {result.message}")
```

### Check for Unwanted Content

Ensure a website doesn't contain specific text (e.g., error messages):

```bash
monitorpy website https://www.example.com --no-content "Error" --no-content "Not Found"
```

```python
config = {
    "url": "https://www.example.com",
    "unexpected_content": "Error"
}

result = run_check("website_status", config)
if result.status == "warning":
    print("Warning: Unwanted content found on the website")
```

### Check with Authentication

Monitor a protected website using basic authentication:

```bash
monitorpy website https://private.example.com --auth-username user --auth-password pass
```

```python
config = {
    "url": "https://private.example.com",
    "auth_username": "user",
    "auth_password": "pass"
}

result = run_check("website_status", config)
```

### Check with Custom Timeout

Set a custom timeout for slow websites:

```bash
monitorpy website https://slow.example.com --timeout 60
```

```python
config = {
    "url": "https://slow.example.com",
    "timeout": 60  # 60 seconds
}

result = run_check("website_status", config)
```

## Advanced Usage Examples

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

```python
config = {
    "url": "https://api.example.com/users",
    "method": "POST",
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    },
    "body": '{"name": "Test User", "email": "test@example.com"}',
    "expected_status": 201
}

result = run_check("website_status", config)
```

### Check Without Following Redirects

Check redirect behavior without following the redirect:

```bash
monitorpy website https://example.com/redirect --no-redirect --status 302
```

```python
config = {
    "url": "https://example.com/redirect",
    "follow_redirects": False,
    "expected_status": 302  # Expect a redirect status
}

result = run_check("website_status", config)
print(f"Redirect status: {result.raw_data['status_code']}")
if result.raw_data.get('redirect_history'):
    print(f"Would redirect to: {result.raw_data['redirect_history']}")
```

### Check Without SSL Verification

For testing websites with self-signed certificates:

```bash
monitorpy website https://self-signed.example.com --no-verify
```

```python
config = {
    "url": "https://self-signed.example.com",
    "verify_ssl": False
}

result = run_check("website_status", config)
```

### Check Response Headers

Examine response headers in the result data:

```python
from monitorpy import run_check
from pprint import pprint

config = {
    "url": "https://www.example.com"
}

result = run_check("website_status", config)

# Examine headers
if result.is_success():
    print("Response headers:")
    pprint(result.raw_data["response_headers"])
    
    # Check for specific headers
    if "Content-Type" in result.raw_data["response_headers"]:
        print(f"Content type: {result.raw_data['response_headers']['Content-Type']}")
```

## Monitoring Examples

### Scheduled Website Monitoring

```python
import schedule
import time
from monitorpy import run_check
from datetime import datetime

def check_website():
    print(f"\n[{datetime.now().isoformat()}] Running website check...")
    
    websites = [
        {"name": "Main Website", "url": "https://www.example.com"},
        {"name": "API", "url": "https://api.example.com", "expected_content": "API version"},
        {"name": "Admin Portal", "url": "https://admin.example.com", 
         "auth_username": "monitor", "auth_password": "password123"}
    ]
    
    for site in websites:
        print(f"\nChecking {site['name']} ({site['url']}):")
        config = {k: v for k, v in site.items() if k != "name"}  # Copy all except name
        
        result = run_check("website_status", config)
        
        status_icon = "✅" if result.is_success() else "⚠️" if result.status == "warning" else "❌"
        print(f"{status_icon} {result.message}")
        print(f"  Response time: {result.response_time:.4f} seconds")

# Schedule checks
schedule.every(5).minutes.do(check_website)

print("Starting scheduled website monitoring...")
check_website()  # Run once immediately

while True:
    schedule.run_pending()
    time.sleep(1)
```

### Multi-Site Parallel Checking

Check multiple websites concurrently:

```python
from concurrent.futures import ThreadPoolExecutor
from monitorpy import run_check
import time

def check_website(url, name=None, **kwargs):
    """Check a single website with specified configuration."""
    start_time = time.time()
    
    config = {"url": url}
    config.update(kwargs)
    
    result = run_check("website_status", config)
    duration = time.time() - start_time
    
    return {
        "name": name or url,
        "url": url,
        "status": result.status,
        "message": result.message,
        "response_time": result.response_time,
        "duration": duration
    }

def check_websites_in_parallel(websites, max_workers=10):
    """Check multiple websites in parallel."""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all checks
        futures = []
        for site in websites:
            # Extract URL and name
            url = site.pop("url")
            name = site.pop("name", url)
            
            # Submit the task
            future = executor.submit(check_website, url, name, **site)
            futures.append(future)
        
        # Process results as they complete
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "name": "Unknown",
                    "url": "Unknown",
                    "status": "error",
                    "message": f"Exception: {str(e)}",
                    "response_time": 0,
                    "duration": 0
                })
    
    return results

# Example usage
websites_to_check = [
    {"name": "Example", "url": "https://www.example.com"},
    {"name": "Google", "url": "https://www.google.com"},
    {"name": "GitHub", "url": "https://github.com"},
    {"name": "Secured API", "url": "https://api.example.com", 
     "headers": {"Authorization": "Bearer token123"}}
]

results = check_websites_in_parallel(websites_to_check)

# Print summary
print(f"Checked {len(results)} websites:")
for result in sorted(results, key=lambda r: r["duration"]):
    status = "✅" if result["status"] == "success" else "⚠️" if result["status"] == "warning" else "❌"
    print(f"{status} {result['name']}: {result['message']} [{result['response_time']:.3f}s]")
```

## Integration Examples

### Alert on Website Issues

```python
import requests
from monitorpy import run_check
import time

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

def monitor_website(url, name, expected_content=None, webhook_url=None):
    """Monitor a website and send alerts for issues."""
    config = {
        "url": url,
        "timeout": 30
    }
    
    if expected_content:
        config["expected_content"] = expected_content
    
    result = run_check("website_status", config)
    
    # Determine if we need to alert
    should_alert = False
    
    if result.status == "error":
        alert_level = "🔴 CRITICAL"
        should_alert = True
    elif result.status == "warning":
        alert_level = "🟠 WARNING"
        should_alert = True
    else:
        alert_level = "✅ OK"
    
    # Generate alert message
    if should_alert and webhook_url:
        alert_message = f"{alert_level}: {name} ({url})\n"
        alert_message += f"Status: {result.status.upper()}\n"
        alert_message += f"Message: {result.message}\n"
        alert_message += f"Response time: {result.response_time:.3f}s"
        
        send_alert(alert_message, webhook_url)
    
    return {
        "name": name,
        "status": result.status,
        "message": result.message,
        "should_alert": should_alert,
        "alert_level": alert_level
    }

# Example usage
webhook_url = "https://hooks.slack.com/services/your_webhook_path"
websites = [
    {"name": "Main Website", "url": "https://www.example.com", 
     "expected_content": "Welcome"},
    {"name": "API Service", "url": "https://api.example.com", 
     "expected_content": "API version"}
]

while True:
    for site in websites:
        print(f"Checking {site['name']}...")
        result = monitor_website(
            site["url"], 
            site["name"], 
            site.get("expected_content"), 
            webhook_url
        )
        
        print(f"{result['alert_level']} {result['message']}")
    
    # Check every 5 minutes
    print("\nSleeping for 5 minutes...")
    time.sleep(300)
```

### Website Monitoring in CI/CD Pipeline

Example GitHub Actions workflow to verify websites after deployment:

```yaml
name: Website Verification

on:
  deployment:
    types: [completed]

jobs:
  verify-websites:
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
          
      - name: Wait for deployment to stabilize
        run: sleep 60  # Wait 1 minute
      
      - name: Verify websites
        run: |
          # Check main website with content verification
          monitorpy website ${{ vars.MAIN_URL }} --content "Welcome to our service" --timeout 60
          
          # Check API endpoint
          monitorpy website ${{ vars.API_URL }}/health --header "Authorization: Bearer ${{ secrets.API_TOKEN }}" --status 200
```