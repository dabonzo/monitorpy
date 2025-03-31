# Advanced Website Monitoring

This document covers advanced usage and techniques for the website monitoring plugin in MonitorPy.

## Working with Raw Results

The `CheckResult` object returned by the website plugin contains detailed information in its `raw_data` attribute. Understanding this structure allows for advanced analysis and custom processing.

### Raw Data Structure

```python
result = run_check("website_status", config)
raw_data = result.raw_data

# Structure of raw_data for website checks:
{
    "url": "https://www.example.com",    # URL checked
    "status_code": 200,                  # HTTP status code
    "expected_status": 200,              # Expected status code
    "status_match": True,                # Whether status codes matched
    "content_match": True,               # Whether content matched expectations
    "content_issues": [],                # List of content issues (if any)
    "response_headers": {                # HTTP response headers
        "Content-Type": "text/html",
        "Server": "nginx",
        ...
    },
    "response_size": 12345,              # Size of response in bytes
    "redirect_history": []               # List of redirects (if any)
}
```

### Processing Response Headers

```python
from monitorpy import run_check

config = {
    "url": "https://www.example.com"
}

result = run_check("website_status", config)

# Analyze headers
headers = result.raw_data.get("response_headers", {})

# Security headers check
security_headers = {
    "Strict-Transport-Security": False,
    "Content-Security-Policy": False,
    "X-Content-Type-Options": False,
    "X-Frame-Options": False,
    "X-XSS-Protection": False
}

for header in security_headers:
    if header in headers:
        security_headers[header] = True
        print(f"✅ {header}: {headers[header]}")
    else:
        print(f"❌ {header}: Missing")

# Calculate security score
security_score = sum(1 for h in security_headers.values() if h) / len(security_headers) * 100
print(f"Security header score: {security_score:.0f}%")

# Check for server information disclosure
if "Server" in headers:
    print(f"⚠️ Server information disclosed: {headers['Server']}")

# Check for caching headers
if "Cache-Control" in headers:
    print(f"Caching policy: {headers['Cache-Control']}")
```

### Analyzing Redirect Chains

```python
from monitorpy import run_check
from pprint import pprint

config = {
    "url": "https://example.com",
    "follow_redirects": True
}

result = run_check("website_status", config)

# Analyze redirect chain
redirects = result.raw_data.get("redirect_history", [])

if redirects:
    print(f"URL was redirected {len(redirects)} times:")
    for i, redirect_url in enumerate(redirects, 1):
        print(f"  {i}. {redirect_url}")
    print(f"Final URL: {result.raw_data.get('url')}")
    
    # Check for redirect loops or excessive redirects
    if len(redirects) > 5:
        print("⚠️ Warning: Excessive number of redirects")
    
    # Check for non-secure redirects (http -> https)
    for url in redirects:
        if url.startswith("http://"):
            print(f"⚠️ Warning: Non-secure redirect in chain: {url}")
else:
    print("No redirects occurred")
```

## Custom Website Checker Classes

You can extend the website plugin's functionality by creating custom checker classes:

```python
from monitorpy.plugins.website import WebsiteStatusPlugin
from monitorpy.core import register_plugin, CheckResult
import re
import json

@register_plugin("website_health")
class WebsiteHealthPlugin(WebsiteStatusPlugin):
    """
    Extended website health checking plugin that performs comprehensive checks.
    """
    
    @classmethod
    def get_required_config(cls):
        return ["url"]
    
    @classmethod
    def get_optional_config(cls):
        # Add our own optional configs
        standard_optional = super().get_optional_config()
        return standard_optional + [
            "check_links",
            "check_images",
            "check_security_headers",
            "allowed_external_domains"
        ]
    
    def run_check(self):
        """Run comprehensive website health check."""
        # First run the standard website check
        basic_result = super().run_check()
        
        # If the basic check failed, return immediately
        if basic_result.status == CheckResult.STATUS_ERROR:
            return basic_result
            
        # If advanced.md checks are requested, proceed with them
        advanced_data = {}
        issues = []
        
        # Add the basic check data
        advanced_data["basic_check"] = basic_result.raw_data
        
        # Check for security headers if requested
        if self.config.get("check_security_headers", False):
            security_result = self._check_security_headers(basic_result)
            advanced_data["security_headers"] = security_result
            
            if security_result["score"] < 70:
                issues.append(f"Security headers score low: {security_result['score']}%")
        
        # Check for broken images if requested
        if self.config.get("check_images", False):
            # Implementation would go here
            pass
            
        # Check for broken links if requested
        if self.config.get("check_links", False):
            # Implementation would go here
            pass
        
        # Determine final status based on issues found
        status = basic_result.status
        if issues and status != CheckResult.STATUS_ERROR:
            status = CheckResult.STATUS_WARNING
            
        # Build message
        if not issues:
            message = f"Website health check passed for {self.config['url']}"
        else:
            message = f"Website health check found issues: {', '.join(issues)}"
        
        # Return comprehensive result
        return CheckResult(
            status=status,
            message=message,
            response_time=basic_result.response_time,
            raw_data=advanced_data
        )
    
    def _check_security_headers(self, basic_result):
        """Check for security headers in the response."""
        headers = basic_result.raw_data.get("response_headers", {})
        
        # Define security headers to check
        security_headers = {
            "Strict-Transport-Security": {
                "present": "Strict-Transport-Security" in headers,
                "value": headers.get("Strict-Transport-Security", "")
            },
            "Content-Security-Policy": {
                "present": "Content-Security-Policy" in headers,
                "value": headers.get("Content-Security-Policy", "")
            },
            "X-Content-Type-Options": {
                "present": "X-Content-Type-Options" in headers,
                "value": headers.get("X-Content-Type-Options", "")
            },
            "X-Frame-Options": {
                "present": "X-Frame-Options" in headers,
                "value": headers.get("X-Frame-Options", "")
            },
            "X-XSS-Protection": {
                "present": "X-XSS-Protection" in headers,
                "value": headers.get("X-XSS-Protection", "")
            }
        }
        
        # Calculate score
        total_headers = len(security_headers)
        present_headers = sum(1 for h in security_headers.values() if h["present"])
        score = (present_headers / total_headers) * 100
        
        return {
            "headers": security_headers,
            "score": score,
            "present": present_headers,
            "total": total_headers
        }
```

## Performance Testing

You can use the website plugin for basic performance testing:

```python
from monitorpy import run_check
import statistics
import time
from datetime import datetime

def run_performance_test(url, iterations=10, delay=1):
    """Run a simple performance test against a URL."""
    response_times = []
    status_codes = []
    
    print(f"Running performance test against {url}")
    print(f"Iterations: {iterations}, Delay between requests: {delay}s")
    print("-" * 60)
    
    for i in range(iterations):
        start_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        config = {
            "url": url,
            "timeout": 30
        }
        
        result = run_check("website_status", config)
        
        status = "✅" if result.is_success() else "❌"
        status_code = result.raw_data.get("status_code", 0)
        
        print(f"[{timestamp}] Request {i+1}/{iterations}: {status} {status_code} - {result.response_time:.4f}s")
        
        response_times.append(result.response_time)
        status_codes.append(status_code)
        
        # Wait before next request
        if i < iterations - 1:
            time.sleep(delay)
    
    # Calculate statistics
    if response_times:
        stats = {
            "min": min(response_times),
            "max": max(response_times),
            "avg": statistics.mean(response_times),
            "median": statistics.median(response_times),
            "p95": sorted(response_times)[int(iterations * 0.95) - 1] if iterations >= 20 else None,
            "success_rate": status_codes.count(200) / len(status_codes) * 100
        }
        
        # Print summary
        print("\nPerformance Summary:")
        print(f"Min Response Time: {stats['min']:.4f}s")
        print(f"Max Response Time: {stats['max']:.4f}s")
        print(f"Avg Response Time: {stats['avg']:.4f}s")
        print(f"Median Response Time: {stats['median']:.4f}s")
        if stats['p95']:
            print(f"95th Percentile: {stats['p95']:.4f}s")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        
        return stats
    
    return None

# Example usage
stats = run_performance_test("https://www.example.com", iterations=20, delay=0.5)
```

## Advanced Monitoring System

Here's a more complete example of a website health monitoring system:

```python
import logging
import json
import time
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from monitorpy import run_check

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("website_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("website_monitor")

class WebsiteMonitor:
    """Advanced website monitoring system."""
    
    def __init__(self, config_file):
        """Initialize with a configuration file."""
        self.config_file = config_file
        self.websites = []
        self.notifications = {}
        self.state_dir = "website_states"
        self.report_dir = "website_reports"
        
        # Create directories if they don't exist
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            self.websites = config.get("websites", [])
            self.notifications = config.get("notifications", {})
            self.check_interval = config.get("check_interval", 300)  # Default: 5 minutes
            self.max_workers = config.get("max_workers", 10)
            
            logger.info(f"Loaded configuration with {len(self.websites)} websites")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def check_website(self, website_info):
        """Check a single website."""
        url = website_info["url"]
        name = website_info.get("name", url)
        
        logger.info(f"Checking {name} ({url})...")
        
        # Build configuration
        config = {
            "url": url,
            "timeout": website_info.get("timeout", 30)
        }
        
        # Add optional parameters
        for key in ["expected_status", "method", "headers", "body", "auth_username", 
                  "auth_password", "verify_ssl", "follow_redirects", 
                  "expected_content", "unexpected_content"]:
            if key in website_info:
                config[key] = website_info[key]
        
        try:
            # Run the check
            result = run_check("website_status", config)
            
            # Check for changes from previous state
            changed = self.check_for_changes(name, url, result)
            
            # Save current state
            self.save_state(name, url, result)
            
            # Send notification if needed
            if changed or result.status != "success":
                self.send_notification(name, url, result, changed)
            
            return {
                "name": name,
                "url": url,
                "status": result.status,
                "message": result.message,
                "response_time": result.response_time,
                "changed": changed
            }
            
        except Exception as e:
            logger.error(f"Error checking {name}: {str(e)}")
            return {
                "name": name,
                "url": url,
                "status": "error",
                "message": f"Exception: {str(e)}",
                "response_time": 0.0,
                "changed": False
            }
    
    def check_for_changes(self, name, url, result):
        """Check if website status has changed from previous state."""
        state_file = os.path.join(self.state_dir, f"{name.replace(' ', '_')}.json")
        
        if not os.path.exists(state_file):
            return False  # No previous state
        
        try:
            with open(state_file, 'r') as f:
                previous_state = json.load(f)
            
            # Compare status and status code
            status_changed = previous_state.get("status") != result.status
            status_code_changed = (
                previous_state.get("status_code") != 
                result.raw_data.get("status_code")
            )
            
            if status_changed or status_code_changed:
                logger.info(f"Status change detected for {name}")
                if status_changed:
                    logger.info(f"  Status changed: {previous_state.get('status')} -> {result.status}")
                if status_code_changed:
                    logger.info(f"  Status code changed: {previous_state.get('status_code')} -> {result.raw_data.get('status_code')}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking changes for {name}: {str(e)}")
            return False
    
    def save_state(self, name, url, result):
        """Save the current state for future comparison."""
        state_file = os.path.join(self.state_dir, f"{name.replace(' ', '_')}.json")
        
        try:
            state = {
                "name": name,
                "url": url,
                "status": result.status,
                "message": result.message,
                "status_code": result.raw_data.get("status_code"),
                "response_time": result.response_time,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving state for {name}: {str(e)}")
    
    def send_notification(self, name, url, result, changed):
        """Send notification for important changes or issues."""
        if not self.notifications:
            return
            
        # Determine notification level
        if result.status == "error":
            level = "CRITICAL"
        elif result.status == "warning" or changed:
            level = "WARNING"
        else:
            return  # Don't notify for ok status without changes
        
        # Build notification message
        message = f"{level}: Website {name} ({url})\n"
        message += f"Status: {result.status.upper()}\n"
        message += f"Message: {result.message}\n"
        message += f"Response time: {result.response_time:.3f}s\n"
        message += f"Timestamp: {datetime.now().isoformat()}"
        
        # Send email notification if configured
        if self.notifications.get("email", {}).get("enabled", False):
            self.send_email_notification(level, name, message)
        
        # Send webhook notification if configured
        if self.notifications.get("webhook", {}).get("enabled", False):
            self.send_webhook_notification(level, name, message)
            
        logger.info(f"Sent {level} notification for {name}")
    
    def send_email_notification(self, level, name, message):
        """Send email notification."""
        # Implementation depends on your email sending library
        # Example using smtplib would go here
        pass
    
    def send_webhook_notification(self, level, name, message):
        """Send webhook notification."""
        try:
            import requests
            
            webhook_url = self.notifications.get("webhook", {}).get("url")
            if not webhook_url:
                return
                
            payload = {
                "level": level,
                "name": name,
                "message": message
            }
            
            response = requests.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Webhook notification failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")
    
    def run_checks(self):
        """Run all configured website checks in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.check_website, website): website 
                       for website in self.websites}
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    website = futures[future]
                    logger.error(f"Error in future for {website.get('url')}: {str(e)}")
        
        # Generate report
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results):
        """Generate a report of all website checks."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "total": len(results),
                "success": sum(1 for r in results if r["status"] == "success"),
                "warning": sum(1 for r in results if r["status"] == "warning"),
                "error": sum(1 for r in results if r["status"] == "error"),
                "changed": sum(1 for r in results if r.get("changed", False))
            }
        }
        
        # Save report
        report_file = os.path.join(
            self.report_dir, 
            f"website_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Generated report: {report_file}")
        
        # Log summary
        summary = report["summary"]
        logger.info(f"Website check summary: {summary['total']} websites checked")
        logger.info(f"  Success: {summary['success']}, Warning: {summary['warning']}, Error: {summary['error']}")
        logger.info(f"  Changed: {summary['changed']}")
    
    def run_monitoring_loop(self):
        """Run continuous monitoring."""
        logger.info("Starting website monitoring loop")
        
        while True:
            try:
                self.run_checks()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
            
            next_check = datetime.now() + timedelta(seconds=self.check_interval)
            logger.info(f"Next check scheduled at: {next_check.isoformat()}")
            time.sleep(self.check_interval)

# Example configuration file (website_monitor_config.json):
"""
{
    "websites": [
        {
            "name": "Main Website",
            "url": "https://www.example.com",
            "expected_content": "Welcome"
        },
        {
            "name": "API Health",
            "url": "https://api.example.com/health",
            "expected_status": 200,
            "headers": {
                "Authorization": "Bearer token123"
            }
        },
        {
            "name": "Admin Portal",
            "url": "https://admin.example.com",
            "auth_username": "monitor",
            "auth_password": "password123"
        }
    ],
    "check_interval": 300,
    "max_workers": 5,
    "notifications": {
        "email": {
            "enabled": true,
            "smtp_server": "smtp.example.com",
            "from_address": "monitor@example.com",
            "to_addresses": ["admin@example.com"]
        },
        "webhook": {
            "enabled": true,
            "url": "https://hooks.example.com/alerts"
        }
    }
}
"""

# Example usage
if __name__ == "__main__":
    monitor = WebsiteMonitor("website_monitor_config.json")
    monitor.run_monitoring_loop()
```