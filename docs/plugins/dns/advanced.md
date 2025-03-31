# Advanced DNS Monitoring

This document covers advanced usage and techniques for the DNS monitoring plugin in MonitorPy.

## Working with Raw Results

The `CheckResult` object returned by the DNS plugin contains detailed information in its `raw_data` attribute. Understanding this structure allows for advanced analysis and custom processing.

### Raw Data Structure

```python
result = run_check("dns_record", config)
raw_data = result.raw_data

# Structure of raw_data for DNS checks:
{
    "domain": "example.com",           # Domain checked
    "record_type": "A",                # Record type checked
    "records": ["192.0.2.1"],          # List of record values found
    "expected_value": "192.0.2.1",     # Expected value (if specified)
    "expected_value_match": True,      # Whether values matched
    "query_time": 0.045,               # Time taken for query in seconds
    "nameserver": "8.8.8.8",           # Nameserver used
    "ttl": 3600,                       # TTL (Time to Live) value
    
    # Propagation data (if check_propagation=True)
    "propagation": {
        "status": "success",           # Status of propagation check
        "total_count": 8,              # Total resolvers checked
        "successful_count": 8,          # Resolvers that responded
        "consistent_count": 8,         # Resolvers with consistent results
        "percentage": 100.0,           # Percentage of consistency
        "threshold": 80,               # Threshold for success
        "resolvers": [                 # Details for each resolver
            {
                "resolver": "8.8.8.8",
                "name": "Google",
                "provider": "Google DNS",
                "status": "success",
                "response_time": 0.045,
                "records": ["192.0.2.1"],
                "match": true
            },
            # More resolvers...
        ]
    },
    
    # DNSSEC data (if check_dnssec=True)
    "dnssec": {
        "is_valid": true,              # DNSSEC validation success
        "is_signed": true,             # Whether domain is DNSSEC-signed
        "flags": "QR RD RA AD"         # DNS flags (AD indicates DNSSEC validation)
    },
    
    # Authoritative data (if check_authoritative=True)
    "authoritative": {
        "is_authoritative": true,      # Whether response is authoritative
        "nameserver": "ns1.example.com", # Authoritative nameserver
        "flags": "QR AA RD"            # DNS flags (AA indicates authoritative)
    }
}
```

### Processing DNS Data

Example of advanced processing of DNS check results:

```python
from monitorpy import run_check
import json
from datetime import datetime

def analyze_dns_results(domain, record_type):
    """Perform comprehensive DNS analysis and export results."""
    config = {
        "domain": domain,
        "record_type": record_type,
        "check_propagation": True,
        "check_dnssec": True,
        "check_authoritative": True
    }
    
    result = run_check("dns_record", config)
    
    # Create a report with timestamp
    timestamp = datetime.now().isoformat()
    report = {
        "timestamp": timestamp,
        "domain": domain,
        "record_type": record_type,
        "status": result.status,
        "message": result.message,
        "response_time": result.response_time,
        "records": result.raw_data.get("records", []),
        "ttl": result.raw_data.get("ttl", "unknown")
    }
    
    # Add propagation analysis
    if "propagation" in result.raw_data:
        prop_data = result.raw_data["propagation"]
        report["propagation"] = {
            "percentage": prop_data.get("percentage", 0),
            "consistent_count": prop_data.get("consistent_count", 0),
            "total_count": prop_data.get("total_count", 0),
            "inconsistent_resolvers": []
        }
        
        # Find inconsistent resolvers
        for resolver in prop_data.get("resolvers", []):
            if not resolver.get("match", True):
                report["propagation"]["inconsistent_resolvers"].append({
                    "name": resolver.get("name", resolver.get("resolver", "Unknown")),
                    "values": resolver.get("records", [])
                })
    
    # Add DNSSEC analysis
    if "dnssec" in result.raw_data:
        dnssec_data = result.raw_data["dnssec"]
        report["dnssec"] = {
            "is_valid": dnssec_data.get("is_valid", False),
            "is_signed": dnssec_data.get("is_signed", False),
            "flags": dnssec_data.get("flags", "")
        }
    
    # Add authoritative analysis
    if "authoritative" in result.raw_data:
        auth_data = result.raw_data["authoritative"]
        report["authoritative"] = {
            "is_authoritative": auth_data.get("is_authoritative", False),
            "nameserver": auth_data.get("nameserver", "Unknown"),
            "flags": auth_data.get("flags", "")
        }
    
    # Save report to file
    filename = f"dns_report_{domain.replace('.', '_')}_{record_type}_{timestamp.replace(':', '-')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

# Example usage
report = analyze_dns_results("example.com", "A")
print(f"DNS analysis complete. Report saved as {filename}")
```

## Custom DNS Checker Classes

You can extend the DNS plugin's functionality by creating custom checker classes:

```python
from monitorpy.plugins.dns_plugin import DNSRecordPlugin
from monitorpy.core import register_plugin, CheckResult
import dns.resolver

@register_plugin("dns_health")
class DNSHealthPlugin(DNSRecordPlugin):
    """
    Extended DNS health checking plugin that performs comprehensive checks.
    """
    
    @classmethod
    def get_required_config(cls):
        return ["domain"]
    
    @classmethod
    def get_optional_config(cls):
        # Add our own optional configs
        standard_optional = super().get_optional_config()
        return standard_optional + [
            "check_all_record_types",
            "check_reverse_dns",
            "check_glue_records"
        ]
    
    def run_check(self):
        """Run comprehensive DNS health checks."""
        domain = self.config["domain"]
        results = []
        overall_status = CheckResult.STATUS_SUCCESS
        
        # Standard record types to check
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "SOA"]
        
        # Check all standard record types
        for record_type in record_types:
            # Create a sub-configuration for this check
            sub_config = {
                "domain": domain,
                "record_type": record_type,
                "timeout": self.config.get("timeout", 10)
            }
            
            # Add propagation/authoritative/dnssec checks if requested
            for key in ["check_propagation", "check_authoritative", "check_dnssec"]:
                if key in self.config:
                    sub_config[key] = self.config[key]
            
            # Run the standard DNS check
            result = super().run_check_with_config(sub_config)
            results.append({
                "record_type": record_type,
                "status": result.status,
                "message": result.message,
                "records": result.raw_data.get("records", [])
            })
            
            # Update overall status (success → warning → error)
            if result.status == CheckResult.STATUS_ERROR:
                overall_status = CheckResult.STATUS_ERROR
            elif result.status == CheckResult.STATUS_WARNING and overall_status != CheckResult.STATUS_ERROR:
                overall_status = CheckResult.STATUS_WARNING
        
        # Check reverse DNS if requested
        if self.config.get("check_reverse_dns", False):
            # Implement reverse DNS checking for A/AAAA records
            pass
        
        # Check glue records if requested
        if self.config.get("check_glue_records", False):
            # Implement glue record checking
            pass
        
        # Determine overall message
        if overall_status == CheckResult.STATUS_SUCCESS:
            message = f"All DNS checks passed for {domain}"
        elif overall_status == CheckResult.STATUS_WARNING:
            message = f"Some DNS checks produced warnings for {domain}"
        else:
            message = f"DNS health check failed for {domain}"
        
        # Return comprehensive result
        return CheckResult(
            status=overall_status,
            message=message,
            response_time=sum(r.get("response_time", 0) for r in results),
            raw_data={
                "domain": domain,
                "checks": results
            }
        )
    
    def run_check_with_config(self, config):
        """Helper method to run a check with a specific config."""
        # Create a new plugin instance with the specified config
        plugin = DNSRecordPlugin(config)
        return plugin.run_check()
```

## Integrating with DNS Services

### Route 53 Integration

Example of checking DNS against AWS Route 53 records:

```python
import boto3
from monitorpy import run_check

def check_against_route53(domain, hosted_zone_id):
    """Check actual DNS against Route 53 records."""
    # Initialize Route 53 client
    route53 = boto3.client('route53')
    
    # Get records from Route 53
    response = route53.list_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        StartRecordName=domain,
        StartRecordType='A',
        MaxItems='100'
    )
    
    route53_records = {}
    for record_set in response['ResourceRecordSets']:
        if record_set['Name'].rstrip('.') == domain:
            record_type = record_set['Type']
            values = [r['Value'] for r in record_set['ResourceRecords']]
            route53_records[record_type] = values
    
    # Check each record type against actual DNS
    results = {}
    for record_type, expected_values in route53_records.items():
        config = {
            "domain": domain,
            "record_type": record_type,
            "expected_value": expected_values,
            "check_propagation": True
        }
        
        result = run_check("dns_record", config)
        
        results[record_type] = {
            "status": result.status,
            "message": result.message,
            "expected": expected_values,
            "actual": result.raw_data.get("records", []),
            "propagation": result.raw_data.get("propagation", {}).get("percentage", 0)
        }
    
    return results

# Example usage
results = check_against_route53("example.com", "Z1PA6795UKMFR9")

# Print summary
for record_type, check_result in results.items():
    status_icon = "✅" if check_result["status"] == "success" else "❌"
    print(f"{status_icon} {record_type}: {check_result['message']}")
    print(f"  Propagation: {check_result['propagation']}%")
    print(f"  Expected: {', '.join(check_result['expected'])}")
    print(f"  Actual: {', '.join(check_result['actual'])}")
```

## Performance Optimization

For checking large numbers of domains or records, you can use parallel processing:

```python
from concurrent.futures import ThreadPoolExecutor
from monitorpy import run_check
import time

def check_domain(domain_info):
    """Check a single domain with specified configuration."""
    domain = domain_info["domain"]
    record_type = domain_info.get("record_type", "A")
    
    config = {
        "domain": domain,
        "record_type": record_type,
        "timeout": 5  # Short timeout for better performance
    }
    
    # Add optional parameters if specified
    for key in ["expected_value", "check_propagation", "check_dnssec"]:
        if key in domain_info:
            config[key] = domain_info[key]
    
    start_time = time.time()
    result = run_check("dns_record", config)
    duration = time.time() - start_time
    
    return {
        "domain": domain,
        "record_type": record_type,
        "status": result.status,
        "message": result.message,
        "records": result.raw_data.get("records", []),
        "duration": duration
    }

def check_domains_in_parallel(domains, max_workers=10):
    """Check multiple domains in parallel."""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all checks
        futures = {executor.submit(check_domain, domain_info): domain_info for domain_info in domains}
        
        # Process results as they complete
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                domain_info = futures[future]
                results.append({
                    "domain": domain_info["domain"],
                    "record_type": domain_info.get("record_type", "A"),
                    "status": "error",
                    "message": f"Exception: {str(e)}",
                    "records": [],
                    "duration": 0
                })
    
    return results

# Example usage
domains_to_check = [
    {"domain": "example.com", "record_type": "A"},
    {"domain": "example.org", "record_type": "A"},
    {"domain": "example.net", "record_type": "A"},
    {"domain": "example.com", "record_type": "MX"},
    {"domain": "example.com", "record_type": "TXT"},
    # Add more domains...
]

results = check_domains_in_parallel(domains_to_check)

# Print summary
print(f"Checked {len(results)} domains:")
for result in sorted(results, key=lambda r: r["duration"]):
    status = "✅" if result["status"] == "success" else "⚠️" if result["status"] == "warning" else "❌"
    print(f"{status} {result['domain']} ({result['record_type']}): {result['message']} [{result['duration']:.3f}s]")
```

## Advanced DNS Health Monitoring System

Here's a more complete example of a DNS health monitoring system:

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
        logging.FileHandler("dns_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dns_monitor")

class DNSMonitor:
    """Advanced DNS monitoring system."""
    
    def __init__(self, config_file):
        """Initialize with a configuration file."""
        self.config_file = config_file
        self.domains = []
        self.notifications = {}
        self.state_dir = "dns_states"
        self.report_dir = "dns_reports"
        
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
                
            self.domains = config.get("domains", [])
            self.notifications = config.get("notifications", {})
            self.check_interval = config.get("check_interval", 3600)  # Default: 1 hour
            self.max_workers = config.get("max_workers", 10)
            
            logger.info(f"Loaded configuration with {len(self.domains)} domains")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def check_domain(self, domain_info):
        """Check a single domain."""
        domain = domain_info["domain"]
        record_type = domain_info.get("record_type", "A")
        name = domain_info.get("name", f"{domain} ({record_type})")
        
        logger.info(f"Checking {name}...")
        
        # Build configuration
        config = {
            "domain": domain,
            "record_type": record_type,
            "timeout": domain_info.get("timeout", 10)
        }
        
        # Add optional parameters
        for key in ["expected_value", "subdomain", "check_propagation", 
                  "check_dnssec", "check_authoritative", "propagation_threshold"]:
            if key in domain_info:
                config[key] = domain_info[key]
        
        try:
            # Run the check
            result = run_check("dns_record", config)
            
            # Check for changes from previous state
            changed = self.check_for_changes(name, domain, record_type, result)
            
            # Save current state
            self.save_state(name, domain, record_type, result)
            
            # Send notification if needed
            if changed or result.status != "success":
                self.send_notification(name, domain, record_type, result, changed)
            
            return {
                "name": name,
                "domain": domain,
                "record_type": record_type,
                "status": result.status,
                "message": result.message,
                "changed": changed
            }
            
        except Exception as e:
            logger.error(f"Error checking {name}: {str(e)}")
            return {
                "name": name,
                "domain": domain,
                "record_type": record_type,
                "status": "error",
                "message": f"Exception: {str(e)}",
                "changed": False
            }
    
    def check_for_changes(self, name, domain, record_type, result):
        """Check if DNS records have changed from previous state."""
        state_file = os.path.join(self.state_dir, f"{name.replace(' ', '_')}.json")
        
        if not os.path.exists(state_file):
            return False  # No previous state
        
        try:
            with open(state_file, 'r') as f:
                previous_state = json.load(f)
            
            previous_records = set(previous_state.get("records", []))
            current_records = set(result.raw_data.get("records", []))
            
            if previous_records != current_records:
                added = current_records - previous_records
                removed = previous_records - current_records
                
                logger.info(f"DNS change detected for {name}")
                if added:
                    logger.info(f"  Added records: {', '.join(added)}")
                if removed:
                    logger.info(f"  Removed records: {', '.join(removed)}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking changes for {name}: {str(e)}")
            return False
    
    def save_state(self, name, domain, record_type, result):
        """Save the current state for future comparison."""
        state_file = os.path.join(self.state_dir, f"{name.replace(' ', '_')}.json")
        
        try:
            state = {
                "name": name,
                "domain": domain,
                "record_type": record_type,
                "status": result.status,
                "message": result.message,
                "records": result.raw_data.get("records", []),
                "timestamp": datetime.now().isoformat()
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving state for {name}: {str(e)}")
    
    def send_notification(self, name, domain, record_type, result, changed):
        """Send notification for important changes."""
        # Implement notification logic here (email, webhook, etc.)
        pass
    
    def run_checks(self):
        """Run all configured DNS checks in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.check_domain, domain_info): domain_info 
                       for domain_info in self.domains}
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    domain_info = futures[future]
                    logger.error(f"Error in future for {domain_info.get('domain')}: {str(e)}")
        
        # Generate report
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results):
        """Generate a report of all DNS checks."""
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
            f"dns_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Generated report: {report_file}")
        
        # Log summary
        summary = report["summary"]
        logger.info(f"DNS check summary: {summary['total']} domains checked")
        logger.info(f"  Success: {summary['success']}, Warning: {summary['warning']}, Error: {summary['error']}")
        logger.info(f"  Changed: {summary['changed']}")
    
    def run_monitoring_loop(self):
        """Run continuous monitoring."""
        logger.info("Starting DNS monitoring loop")
        
        while True:
            try:
                self.run_checks()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
            
            next_check = datetime.now() + timedelta(seconds=self.check_interval)
            logger.info(f"Next check scheduled at: {next_check.isoformat()}")
            time.sleep(self.check_interval)

# Example configuration file (dns_monitor_config.json):
"""
{
    "domains": [
        {
            "name": "Main Website",
            "domain": "example.com",
            "record_type": "A",
            "expected_value": "192.0.2.1",
            "check_propagation": true
        },
        {
            "name": "Mail Service",
            "domain": "example.com",
            "record_type": "MX",
            "expected_value": "10 mail.example.com",
            "check_authoritative": true
        }
    ],
    "check_interval": 3600,
    "max_workers": 5,
    "notifications": {
        "email": {
            "enabled": true,
            "smtp_server": "smtp.example.com",
            "from_address": "dns-monitor@example.com",
            "to_addresses": ["admin@example.com"]
        },
        "webhook": {
            "enabled": true,
            "url": "https://hooks.example.com/dns-alerts"
        }
    }
}
"""

# Example usage
if __name__ == "__main__":
    monitor = DNSMonitor("dns_monitor_config.json")
    monitor.run_monitoring_loop()
```