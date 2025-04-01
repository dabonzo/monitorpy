# Parallel Execution Examples

This document provides practical examples of using MonitorPy's parallel execution capabilities in different scenarios.

## Batch File Format

When using the `batch` command or the batch API, you need to provide check configurations. Here's a complete example of a batch file:

```json
[
  {
    "id": "website1",
    "plugin_type": "website_status",
    "config": {
      "url": "https://example.com",
      "timeout": 30,
      "expected_status": 200,
      "follow_redirects": true
    }
  },
  {
    "id": "website2",
    "plugin_type": "website_status",
    "config": {
      "url": "https://example.org",
      "timeout": 30,
      "expected_status": 200,
      "expected_content": "Example Domain"
    }
  },
  {
    "id": "ssl1",
    "plugin_type": "ssl_certificate",
    "config": {
      "hostname": "example.com",
      "port": 443,
      "warning_days": 30,
      "critical_days": 7
    }
  },
  {
    "id": "mail1",
    "plugin_type": "mail_server",
    "config": {
      "hostname": "example.com",
      "protocol": "smtp",
      "resolve_mx": true,
      "timeout": 30
    }
  }
]
```

## Command Line Examples

### Basic Batch Command

```bash
# Run multiple checks from a JSON file
monitorpy batch checks.json --verbose

# Run with limited concurrency
monitorpy batch checks.json --max-workers 5

# Process in smaller batches for very large check files
monitorpy batch large-checks.json --batch-size 20 --max-workers 10

# Output results to a file
monitorpy batch checks.json --output results.txt

# Output JSON results for further processing
monitorpy batch checks.json --json --output results.json

# Set a timeout for each batch
monitorpy batch checks.json --timeout 60
```

### Parallel Website Checks

```bash
# Create a file with URLs (one per line)
cat > websites.txt << EOF
https://example.com
https://example.org
https://github.com
https://gitlab.com
https://stackoverflow.com
EOF

# Check all websites in parallel
monitorpy website --sites websites.txt --parallel --verbose

# Limit the number of concurrent workers
monitorpy website --sites websites.txt --parallel --max-workers 5

# Check with custom options
monitorpy website --sites websites.txt --parallel --timeout 10 --no-verify
```

### Parallel SSL Certificate Checks

```bash
# Create a file with hostnames
cat > ssl-hosts.txt << EOF
example.com
github.com
gitlab.com
stackoverflow.com
EOF

# Check all certificates in parallel
monitorpy ssl --hosts ssl-hosts.txt --parallel --verbose

# Set custom thresholds
monitorpy ssl --hosts ssl-hosts.txt --parallel --warning 60 --critical 30

# Check certificates with additional options
monitorpy ssl --hosts ssl-hosts.txt --parallel --check-chain --port 443
```

### Parallel Mail Server Checks

```bash
# Create a file with mail domains
cat > mail-domains.txt << EOF
gmail.com
yahoo.com
outlook.com
EOF

# Check all mail servers in parallel
monitorpy mail --servers mail-domains.txt --parallel --protocol smtp --basic-check

# Disable MX resolution for specific server names (not domains)
monitorpy mail --servers mail-servers.txt --parallel --no-resolve-mx
```

### Parallel DNS Checks

```bash
# Create a file with domains
cat > domains.txt << EOF
example.com
github.com
gitlab.com
stackoverflow.com
EOF

# Check all domains' A records in parallel
monitorpy dns --domains domains.txt --parallel --type A

# Check with DNS propagation
monitorpy dns --domains domains.txt --parallel --check-propagation --threshold 90
```

## Python Code Examples

### Website Monitoring Script

This example script checks multiple websites and sends an email if any of them fail:

```python
#!/usr/bin/env python3
"""
Script to monitor multiple websites and send alerts for any failures.
"""

import sys
import smtplib
from email.message import EmailMessage
from monitorpy.core import run_checks_in_parallel

# List of websites to monitor
WEBSITES = [
    "https://example.com",
    "https://example.org",
    "https://api.myservice.com/health",
    "https://admin.myservice.com/status"
]

# Email configuration
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "alerts@example.com",
    "password": "your_app_password",
    "from_email": "alerts@example.com",
    "to_email": "admin@example.com"
}

def check_websites():
    """Run parallel checks on all websites."""
    check_configs = [
        {
            "id": f"website{i+1}",
            "plugin_type": "website_status",
            "config": {
                "url": url,
                "timeout": 30,
                "expected_status": 200,
                "follow_redirects": True
            }
        }
        for i, url in enumerate(WEBSITES)
    ]
    
    results = run_checks_in_parallel(check_configs)
    return results

def send_alert_email(failed_checks):
    """Send an email alert for failed checks."""
    if not failed_checks:
        return
    
    msg = EmailMessage()
    msg['Subject'] = f'ALERT: {len(failed_checks)} Website(s) Down'
    msg['From'] = EMAIL_CONFIG["from_email"]
    msg['To'] = EMAIL_CONFIG["to_email"]
    
    body = f"{len(failed_checks)} websites are currently unreachable:\n\n"
    
    for check_config, result in failed_checks:
        url = check_config["config"]["url"]
        body += f"- {url}\n  Status: {result.status}\n  Message: {result.message}\n\n"
    
    msg.set_content(body)
    
    try:
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["username"], EMAIL_CONFIG["password"])
        server.send_message(msg)
        server.quit()
        print(f"Alert email sent to {EMAIL_CONFIG['to_email']}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    """Main function to run checks and send alerts if needed."""
    print(f"Checking {len(WEBSITES)} websites...")
    results = check_websites()
    
    # Split results into succeeded and failed checks
    succeeded = []
    failed = []
    
    for check_result in results:
        check_config, result = check_result
        if result.status == "success":
            succeeded.append(check_result)
        else:
            failed.append(check_result)
    
    # Print summary
    print(f"Results: {len(succeeded)}/{len(results)} succeeded, {len(failed)} failed")
    
    # Send alerts for failures
    if failed:
        print("Failures detected, sending alert email...")
        send_alert_email(failed)
    
    # Exit with non-zero code if any checks failed
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(main())
```

### SSL Certificate Expiration Monitor

This example checks SSL certificates for multiple domains and reports any that are expiring soon:

```python
#!/usr/bin/env python3
"""
Script to check SSL certificates for multiple domains and report those expiring soon.
"""

import sys
import csv
from datetime import datetime
from monitorpy.core import run_check_batch

def load_domains_from_csv(csv_file):
    """Load domain list from a CSV file."""
    domains = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                domains.append({
                    'domain': row.get('domain'),
                    'port': int(row.get('port', 443)),
                    'name': row.get('name', row.get('domain'))
                })
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    return domains

def check_certificates(domains):
    """Check SSL certificates for all domains."""
    check_configs = [
        {
            "id": domain['name'],
            "plugin_type": "ssl_certificate",
            "config": {
                "hostname": domain['domain'],
                "port": domain['port'],
                "warning_days": 30,
                "critical_days": 14,
                "timeout": 30
            }
        }
        for domain in domains
    ]
    
    # Process in batches of 10 with up to 5 concurrent workers
    results = run_check_batch(check_configs, batch_size=10, max_workers=5)
    return results

def generate_report(results):
    """Generate a report of certificate statuses."""
    report = []
    
    for check_config, result in results:
        domain_id = check_config['id']
        hostname = check_config['config']['hostname']
        
        # Extract expiry information
        days_remaining = None
        valid_until = None
        issuer = None
        if result.raw_data:
            days_remaining = result.raw_data.get('days_remaining')
            valid_until = result.raw_data.get('valid_until')
            issuer = result.raw_data.get('issuer')
        
        report.append({
            'id': domain_id,
            'hostname': hostname,
            'status': result.status,
            'message': result.message,
            'days_remaining': days_remaining,
            'valid_until': valid_until,
            'issuer': issuer
        })
    
    return report

def write_csv_report(report, output_file):
    """Write the report to a CSV file."""
    fieldnames = ['id', 'hostname', 'status', 'days_remaining', 
                 'valid_until', 'issuer', 'message']
    
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report)
        print(f"Report written to {output_file}")
    except Exception as e:
        print(f"Error writing report: {e}")

def main():
    """Main function to run certificate checks and generate a report."""
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} DOMAINS_CSV OUTPUT_CSV")
        return 1
    
    csv_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print(f"Loading domains from {csv_file}...")
    domains = load_domains_from_csv(csv_file)
    print(f"Checking certificates for {len(domains)} domains...")
    
    results = check_certificates(domains)
    
    # Generate and write report
    report = generate_report(results)
    write_csv_report(report, output_file)
    
    # Count certificates expiring soon (warning or error status)
    expiring_soon = sum(1 for item in report if item['status'] in ['warning', 'error'])
    
    if expiring_soon > 0:
        print(f"WARNING: {expiring_soon} certificates are expiring soon!")
        return 1
    else:
        print("All certificates are valid and not expiring soon.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
```

## API Integration Examples

### Laravel Controller Using Batch API

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class MonitoringController extends Controller
{
    protected $apiBaseUrl;
    protected $apiToken;
    
    public function __construct()
    {
        $this->apiBaseUrl = config('services.monitorpy.url');
        $this->apiToken = config('services.monitorpy.token');
    }
    
    public function checkMultipleSites(Request $request)
    {
        $urls = $request->input('urls', []);
        
        if (empty($urls)) {
            return response()->json(['error' => 'No URLs provided'], 400);
        }
        
        // Prepare check configurations
        $checks = [];
        foreach ($urls as $i => $url) {
            $checks[] = [
                'plugin_type' => 'website_status',
                'config' => [
                    'url' => $url,
                    'timeout' => 30,
                    'expected_status' => 200
                ]
            ];
        }
        
        // Send batch request to MonitorPy API
        try {
            $response = Http::withToken($this->apiToken)
                ->timeout(60)
                ->post("{$this->apiBaseUrl}/api/v1/batch/run-ad-hoc", [
                    'checks' => $checks,
                    'max_workers' => 10,
                    'timeout' => 30
                ]);
            
            if ($response->successful()) {
                $results = $response->json();
                return response()->json($results);
            } else {
                return response()->json([
                    'error' => 'MonitorPy API error', 
                    'details' => $response->json()
                ], $response->status());
            }
        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to contact MonitorPy API',
                'message' => $e->getMessage()
            ], 500);
        }
    }
    
    public function dashboardData()
    {
        // Get stored check IDs from database
        $checkIds = \App\Models\MonitoredSite::pluck('check_id')->toArray();
        
        if (empty($checkIds)) {
            return response()->json(['error' => 'No monitored sites configured'], 400);
        }
        
        // Run all checks in parallel
        try {
            $response = Http::withToken($this->apiToken)
                ->timeout(60)
                ->post("{$this->apiBaseUrl}/api/v1/batch/run", [
                    'checks' => $checkIds
                ]);
            
            if ($response->successful()) {
                $results = $response->json();
                
                // Process results for dashboard display
                $processedResults = $this->processDashboardResults($results);
                
                return response()->json($processedResults);
            } else {
                return response()->json([
                    'error' => 'MonitorPy API error', 
                    'details' => $response->json()
                ], $response->status());
            }
        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to contact MonitorPy API',
                'message' => $e->getMessage()
            ], 500);
        }
    }
    
    private function processDashboardResults($results)
    {
        // Calculate summary statistics
        $total = count($results['results'] ?? []);
        $success = 0;
        $warning = 0;
        $error = 0;
        
        $siteResults = [];
        
        foreach ($results['results'] ?? [] as $result) {
            // Update counters
            switch ($result['result']['status'] ?? '') {
                case 'success':
                    $success++;
                    break;
                case 'warning':
                    $warning++;
                    break;
                case 'error':
                    $error++;
                    break;
            }
            
            // Get site information from database
            $site = \App\Models\MonitoredSite::where('check_id', $result['check_id'])->first();
            
            if ($site) {
                $siteResults[] = [
                    'id' => $site->id,
                    'name' => $site->name,
                    'url' => $site->url,
                    'status' => $result['result']['status'] ?? 'unknown',
                    'message' => $result['result']['message'] ?? '',
                    'response_time' => $result['result']['response_time'] ?? 0,
                    'last_check' => now()->toIso8601String()
                ];
            }
        }
        
        return [
            'summary' => [
                'total' => $total,
                'success' => $success,
                'warning' => $warning,
                'error' => $error,
                'health' => $total > 0 ? round(($success / $total) * 100) : 0
            ],
            'sites' => $siteResults
        ];
    }
}
```

### Node.js Batch Processing

```javascript
// monitorpy-client.js
const axios = require('axios');

class MonitorPyClient {
  constructor(config) {
    this.config = {
      baseUrl: 'http://localhost:5000',
      apiToken: null,
      ...config
    };
    
    this.axios = axios.create({
      baseURL: this.config.baseUrl,
      timeout: 60000,
      headers: this.config.apiToken ? {
        'Authorization': `Bearer ${this.config.apiToken}`
      } : {}
    });
  }
  
  async batchCheck(checks, options = {}) {
    const defaultOptions = {
      maxWorkers: 10,
      timeout: 30
    };
    
    const requestOptions = { ...defaultOptions, ...options };
    
    try {
      const response = await this.axios.post('/api/v1/batch/run-ad-hoc', {
        checks,
        max_workers: requestOptions.maxWorkers,
        timeout: requestOptions.timeout
      });
      
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(`API Error (${error.response.status}): ${JSON.stringify(error.response.data)}`);
      } else if (error.request) {
        throw new Error('No response received from MonitorPy API');
      } else {
        throw new Error(`Error preparing request: ${error.message}`);
      }
    }
  }
  
  // Helper to run website checks
  async checkWebsites(urls, options = {}) {
    const checks = urls.map(url => ({
      plugin_type: 'website_status',
      config: {
        url,
        timeout: options.timeout || 30,
        expected_status: options.expectedStatus || 200,
        follow_redirects: options.followRedirects !== false
      }
    }));
    
    return this.batchCheck(checks, options);
  }
  
  // Helper to run SSL checks
  async checkSSLCertificates(hostnames, options = {}) {
    const checks = hostnames.map(hostname => ({
      plugin_type: 'ssl_certificate',
      config: {
        hostname,
        warning_days: options.warningDays || 30,
        critical_days: options.criticalDays || 14
      }
    }));
    
    return this.batchCheck(checks, options);
  }
}

module.exports = MonitorPyClient;

// Example usage
async function main() {
  const client = new MonitorPyClient({
    baseUrl: 'http://localhost:5000',
    apiToken: 'your_jwt_token'
  });
  
  try {
    // Check multiple websites in parallel
    const websiteResults = await client.checkWebsites([
      'https://example.com',
      'https://example.org',
      'https://github.com'
    ]);
    
    console.log('Website Check Results:');
    console.log(JSON.stringify(websiteResults, null, 2));
    
    // Check multiple SSL certificates in parallel
    const sslResults = await client.checkSSLCertificates([
      'example.com',
      'github.com',
      'gitlab.com'
    ], { warningDays: 60 });
    
    console.log('SSL Certificate Check Results:');
    console.log(JSON.stringify(sslResults, null, 2));
  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
```

## Advanced Example: Multi-Service Health Dashboard

This example combines different check types for a comprehensive health dashboard:

```python
#!/usr/bin/env python3
"""
Script to check the health of multiple services and generate a dashboard.
"""

import sys
import json
import time
import argparse
from datetime import datetime
from monitorpy.core import run_check_batch

def load_services(config_file):
    """Load service configurations from a JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)

def create_check_configs(services):
    """Create check configurations for all services."""
    check_configs = []
    
    # Process website services
    for service in services.get('websites', []):
        check_configs.append({
            "id": service['id'],
            "plugin_type": "website_status",
            "config": {
                "url": service['url'],
                "timeout": service.get('timeout', 30),
                "expected_status": service.get('expected_status', 200),
                "follow_redirects": service.get('follow_redirects', True),
                "expected_content": service.get('expected_content'),
                "unexpected_content": service.get('unexpected_content')
            }
        })
    
    # Process SSL certificates
    for cert in services.get('ssl_certificates', []):
        check_configs.append({
            "id": cert['id'],
            "plugin_type": "ssl_certificate",
            "config": {
                "hostname": cert['hostname'],
                "port": cert.get('port', 443),
                "warning_days": cert.get('warning_days', 30),
                "critical_days": cert.get('critical_days', 14)
            }
        })
    
    # Process mail servers
    for mail in services.get('mail_servers', []):
        check_configs.append({
            "id": mail['id'],
            "plugin_type": "mail_server",
            "config": {
                "hostname": mail['hostname'],
                "protocol": mail.get('protocol', 'smtp'),
                "port": mail.get('port'),
                "use_ssl": mail.get('use_ssl', False),
                "resolve_mx": mail.get('resolve_mx', True)
            }
        })
    
    # Process DNS records
    for dns in services.get('dns_records', []):
        check_configs.append({
            "id": dns['id'],
            "plugin_type": "dns",
            "config": {
                "domain": dns['domain'],
                "record_type": dns.get('record_type', 'A'),
                "expected_value": dns.get('expected_value'),
                "subdomain": dns.get('subdomain')
            }
        })
    
    return check_configs

def run_health_checks(check_configs, max_workers, batch_size):
    """Run all health checks in batches."""
    return run_check_batch(check_configs, batch_size, max_workers)

def generate_dashboard(results, services, output_file):
    """Generate an HTML dashboard from check results."""
    # Group results by service type
    grouped_results = {
        'websites': [],
        'ssl_certificates': [],
        'mail_servers': [],
        'dns_records': []
    }
    
    # Process results
    for check_config, result in results:
        service_id = check_config['id']
        service_type = None
        service_name = service_id
        
        # Find service type and name
        for service_group, services_list in services.items():
            for service in services_list:
                if service['id'] == service_id:
                    service_type = service_group
                    service_name = service.get('name', service_id)
                    break
            if service_type:
                break
        
        # Skip if service type unknown
        if not service_type:
            continue
        
        # Store processed result
        processed_result = {
            'id': service_id,
            'name': service_name,
            'status': result.status,
            'message': result.message,
            'response_time': result.response_time,
            'raw_data': result.raw_data
        }
        
        # Add service-specific data
        if service_type == 'websites':
            service = next((s for s in services['websites'] if s['id'] == service_id), None)
            if service:
                processed_result['url'] = service['url']
        
        elif service_type == 'ssl_certificates':
            service = next((s for s in services['ssl_certificates'] if s['id'] == service_id), None)
            if service:
                processed_result['hostname'] = service['hostname']
                if result.raw_data:
                    processed_result['days_remaining'] = result.raw_data.get('days_remaining')
                    processed_result['valid_until'] = result.raw_data.get('valid_until')
        
        # Add to grouped results
        grouped_results[service_type].append(processed_result)
    
    # Generate HTML
    html = generate_html_dashboard(grouped_results)
    
    # Write to file or stdout
    if output_file:
        with open(output_file, 'w') as f:
            f.write(html)
        print(f"Dashboard written to {output_file}")
    else:
        print(html)

def generate_html_dashboard(grouped_results):
    """Generate HTML dashboard from grouped results."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate summary statistics
    total_checks = sum(len(group) for group in grouped_results.values())
    successful_checks = sum(
        1 for group in grouped_results.values() 
        for result in group if result['status'] == 'success'
    )
    health_percentage = int((successful_checks / total_checks * 100) if total_checks > 0 else 0)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Service Health Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .summary {{ display: flex; margin-bottom: 20px; }}
        .summary-box {{ flex: 1; padding: 15px; margin: 10px; border-radius: 5px; color: white; text-align: center; }}
        .success {{ background-color: #28a745; }}
        .warning {{ background-color: #ffc107; color: #212529; }}
        .error {{ background-color: #dc3545; }}
        .unknown {{ background-color: #6c757d; }}
        .timestamp {{ text-align: right; color: #666; margin-bottom: 20px; }}
        .service-group {{ margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
        tr:hover {{ background-color: #f1f1f1; }}
        .status-badge {{ padding: 5px 10px; border-radius: 20px; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>Service Health Dashboard</h1>
        <div class="timestamp">Last updated: {now}</div>
        
        <!-- Summary -->
        <div class="summary">
            <div class="summary-box {health_percentage >= 90 and 'success' or health_percentage >= 70 and 'warning' or 'error'}">
                <h2>Overall Health</h2>
                <div style="font-size: 2em;">{health_percentage}%</div>
                <div>{successful_checks}/{total_checks} services healthy</div>
            </div>
            
            <div class="summary-box success">
                <h2>Healthy</h2>
                <div style="font-size: 2em;">{successful_checks}</div>
            </div>
            
            <div class="summary-box warning">
                <h2>Warnings</h2>
                <div style="font-size: 2em;">{sum(1 for group in grouped_results.values() for result in group if result['status'] == 'warning')}</div>
            </div>
            
            <div class="summary-box error">
                <h2>Errors</h2>
                <div style="font-size: 2em;">{sum(1 for group in grouped_results.values() for result in group if result['status'] == 'error')}</div>
            </div>
        </div>
    """
    
    # Websites section
    if grouped_results['websites']:
        html += """
        <div class="service-group">
            <h2>Websites</h2>
            <table>
                <tr>
                    <th>Name</th>
                    <th>URL</th>
                    <th>Status</th>
                    <th>Response Time</th>
                    <th>Message</th>
                </tr>
        """
        
        for result in grouped_results['websites']:
            status_class = result['status']
            html += f"""
                <tr>
                    <td>{result['name']}</td>
                    <td>{result.get('url', 'N/A')}</td>
                    <td><span class="status-badge {status_class}">{result['status'].upper()}</span></td>
                    <td>{result['response_time']:.3f}s</td>
                    <td>{result['message']}</td>
                </tr>
            """
        
        html += "</table></div>"
    
    # SSL Certificates section
    if grouped_results['ssl_certificates']:
        html += """
        <div class="service-group">
            <h2>SSL Certificates</h2>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Hostname</th>
                    <th>Status</th>
                    <th>Expires In</th>
                    <th>Valid Until</th>
                </tr>
        """
        
        for result in grouped_results['ssl_certificates']:
            status_class = result['status']
            days_remaining = result.get('days_remaining', 'N/A')
            valid_until = result.get('valid_until', 'N/A')
            
            html += f"""
                <tr>
                    <td>{result['name']}</td>
                    <td>{result.get('hostname', 'N/A')}</td>
                    <td><span class="status-badge {status_class}">{result['status'].upper()}</span></td>
                    <td>{days_remaining} days</td>
                    <td>{valid_until}</td>
                </tr>
            """
        
        html += "</table></div>"
    
    # Mail Servers section
    if grouped_results['mail_servers']:
        html += """
        <div class="service-group">
            <h2>Mail Servers</h2>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Response Time</th>
                    <th>Message</th>
                </tr>
        """
        
        for result in grouped_results['mail_servers']:
            status_class = result['status']
            html += f"""
                <tr>
                    <td>{result['name']}</td>
                    <td><span class="status-badge {status_class}">{result['status'].upper()}</span></td>
                    <td>{result['response_time']:.3f}s</td>
                    <td>{result['message']}</td>
                </tr>
            """
        
        html += "</table></div>"
    
    # DNS Records section
    if grouped_results['dns_records']:
        html += """
        <div class="service-group">
            <h2>DNS Records</h2>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Response Time</th>
                    <th>Message</th>
                </tr>
        """
        
        for result in grouped_results['dns_records']:
            status_class = result['status']
            html += f"""
                <tr>
                    <td>{result['name']}</td>
                    <td><span class="status-badge {status_class}">{result['status'].upper()}</span></td>
                    <td>{result['response_time']:.3f}s</td>
                    <td>{result['message']}</td>
                </tr>
            """
        
        html += "</table></div>"
    
    html += """
    </div>
</body>
</html>
    """
    
    return html

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate a health dashboard for multiple services")
    parser.add_argument("config", help="JSON configuration file with service definitions")
    parser.add_argument("--output", help="Output HTML file (default: stdout)")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for checks")
    parser.add_argument("--max-workers", type=int, default=5, help="Maximum worker threads")
    args = parser.parse_args()
    
    # Load service configurations
    services = load_services(args.config)
    
    # Create check configurations
    check_configs = create_check_configs(services)
    
    print(f"Running health checks for {len(check_configs)} services...")
    start_time = time.time()
    
    # Run checks
    results = run_health_checks(check_configs, args.max_workers, args.batch_size)
    
    # Print timing information
    duration = time.time() - start_time
    print(f"Checks completed in {duration:.2f} seconds")
    
    # Generate dashboard
    generate_dashboard(results, services, args.output)
    
    # Calculate overall health
    total = len(results)
    success = sum(1 for _, result in results if result.status == "success")
    warning = sum(1 for _, result in results if result.status == "warning")
    error = sum(1 for _, result in results if result.status == "error")
    
    health_percentage = (success / total * 100) if total > 0 else 0
    
    print(f"\nSummary: {success}/{total} services healthy ({health_percentage:.1f}%)")
    print(f"  Success: {success}, Warning: {warning}, Error: {error}")
    
    # Exit with status code based on health
    if error > 0:
        return 2
    elif warning > 0:
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())
```

With a services.json configuration file:

```json
{
  "websites": [
    {
      "id": "main-website",
      "name": "Company Website",
      "url": "https://example.com",
      "expected_status": 200,
      "expected_content": "Welcome"
    },
    {
      "id": "api-service",
      "name": "API Service",
      "url": "https://api.example.com/health",
      "expected_status": 200
    }
  ],
  "ssl_certificates": [
    {
      "id": "main-ssl",
      "name": "Main Website SSL",
      "hostname": "example.com",
      "warning_days": 30,
      "critical_days": 14
    },
    {
      "id": "api-ssl",
      "name": "API SSL",
      "hostname": "api.example.com"
    }
  ],
  "mail_servers": [
    {
      "id": "company-mail",
      "name": "Company Mail",
      "hostname": "example.com",
      "protocol": "smtp"
    }
  ],
  "dns_records": [
    {
      "id": "website-dns",
      "name": "Website A Record",
      "domain": "example.com",
      "record_type": "A"
    },
    {
      "id": "mail-dns",
      "name": "Mail MX Record",
      "domain": "example.com",
      "record_type": "MX"
    }
  ]
}
```