# Advanced SSL Certificate Monitoring

This document covers advanced usage and techniques for the SSL certificate monitoring plugin in MonitorPy.

## Working with Raw Results

The `CheckResult` object returned by the SSL plugin contains detailed information in its `raw_data` attribute. Understanding this structure allows for advanced analysis and custom processing.

### Raw Data Structure

```python
result = run_check("ssl_certificate", config)
raw_data = result.raw_data

# Structure of raw_data for SSL certificate checks:
{
    "hostname": "example.com",           # Hostname checked
    "port": 443,                         # Port used
    "not_before": "2023-01-01T00:00:00", # Certificate validity start date
    "not_after": "2024-01-01T00:00:00",  # Certificate validity end date
    "days_until_expiration": 180,        # Days until certificate expires
    "subject": {                         # Certificate subject information
        "commonName": "example.com",
        "organizationName": "Example Inc",
        # ...
    },
    "issuer": {                          # Certificate issuer information
        "commonName": "ExampleCA",
        "organizationName": "Example CA Inc",
        # ...
    },
    "version": 3,                        # Certificate version
    "serial_number": "12:34:56:78:...",  # Certificate serial number
    "alternative_names": [               # Subject Alternative Names (SANs)
        "example.com",
        "www.example.com"
    ]
}
```

If `check_chain` is enabled, additional fields may be present:

```python
{
    # ...other fields...
    "cipher": ["TLS_AES_256_GCM_SHA384", "TLSv1.3", 256],  # Cipher suite details
    "protocol": "TLSv1.3"                # TLS protocol version
}
```

## Certificate Analysis

### Analyzing Certificate Chain and Trust

```python
from monitorpy import run_check
import ssl
import socket
from datetime import datetime

def analyze_certificate_chain(hostname, port=443):
    """Perform detailed analysis of certificate chain and trust."""
    config = {
        "hostname": hostname,
        "port": port,
        "check_chain": True
    }
    
    result = run_check("ssl_certificate", config)
    
    if not result.is_success():
        print(f"Certificate check failed: {result.message}")
        return None
    
    # Basic certificate information
    print(f"\nCertificate Analysis for {hostname}:{port}")
    print(f"Valid from: {result.raw_data['not_before']}")
    print(f"Valid until: {result.raw_data['not_after']}")
    print(f"Days until expiration: {result.raw_data['days_until_expiration']}")
    
    # Subject information
    subject = result.raw_data.get("subject", {})
    print("\nSubject Information:")
    for key, value in subject.items():
        print(f"  {key}: {value}")
    
    # Issuer information
    issuer = result.raw_data.get("issuer", {})
    print("\nIssuer Information:")
    for key, value in issuer.items():
        print(f"  {key}: {value}")
    
    # Alternative names
    alt_names = result.raw_data.get("alternative_names", [])
    print(f"\nSubject Alternative Names: {len(alt_names)}")
    for name in alt_names:
        print(f"  {name}")
    
    # TLS protocol and cipher information
    if "protocol" in result.raw_data:
        print(f"\nTLS Protocol: {result.raw_data['protocol']}")
    if "cipher" in result.raw_data:
        cipher_info = result.raw_data['cipher']
        print(f"Cipher Suite: {cipher_info[0]}")
        print(f"Protocol: {cipher_info[1]}")
        print(f"Bit Strength: {cipher_info[2]}")
    
    # Perform additional checks
    print("\nSecurity Assessment:")
    
    # Check for modern TLS version
    if "protocol" in result.raw_data:
        protocol = result.raw_data["protocol"]
        if protocol in ["TLSv1.2", "TLSv1.3"]:
            print("✅ Modern TLS protocol in use")
        else:
            print(f"⚠️ Outdated TLS protocol: {protocol}")
    
    # Check for strong cipher
    if "cipher" in result.raw_data and result.raw_data['cipher'][2] >= 256:
        print("✅ Strong cipher strength (≥256 bits)")
    else:
        print("⚠️ Weak cipher strength (<256 bits)")
    
    # Check certificate validity period
    days_left = result.raw_data['days_until_expiration']
    if days_left > 365:
        print("✅ Long validity period (>1 year)")
    elif days_left > 90:
        print("✅ Adequate validity period (>90 days)")
    elif days_left > 30:
        print("⚠️ Certificate expires soon (<90 days)")
    else:
        print("❌ Critical: Certificate expires very soon (<30 days)")
    
    # Check issuer
    issuer_cn = issuer.get("commonName", "")
    if "Let's Encrypt" in issuer_cn:
        print("ℹ️ Let's Encrypt certificate (90-day validity)")
    
    return result.raw_data

# Example usage
certificate_data = analyze_certificate_chain("example.com")
```

### Certificate Transparency Verification

```python
from monitorpy import run_check
import requests
import base64
import hashlib
import json

def verify_certificate_transparency(hostname, port=443):
    """Verify if a certificate is properly logged in Certificate Transparency logs."""
    # First, get the certificate
    config = {
        "hostname": hostname,
        "port": port
    }
    
    result = run_check("ssl_certificate", config)
    
    if not result.is_success():
        print(f"Certificate check failed: {result.message}")
        return None
    
    # We need to make a direct connection to get the certificate in PEM format
    import socket
    import ssl
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # Make connection
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get the certificate in DER format
                cert_der = ssock.getpeercert(binary_form=True)
                
                # Calculate the SHA-256 hash
                cert_hash = hashlib.sha256(cert_der).digest()
                
                # Encode the hash in base64
                cert_hash_b64 = base64.b64encode(cert_hash).decode('utf-8')
                
                # Look up the certificate in Certificate Transparency logs
                response = requests.get(
                    f"https://crt.sh/?q={cert_hash_b64}&output=json"
                )
                
                if response.status_code == 200:
                    try:
                        ct_data = response.json()
                        
                        if ct_data:
                            print(f"Certificate for {hostname} found in CT logs:")
                            print(f"Total entries: {len(ct_data)}")
                            
                            # Show some details of the first entry
                            if len(ct_data) > 0:
                                entry = ct_data[0]
                                print(f"  ID: {entry.get('id')}")
                                print(f"  Issuer: {entry.get('issuer_name', 'Unknown')}")
                                print(f"  Not Before: {entry.get('not_before')}")
                                print(f"  Not After: {entry.get('not_after')}")
                            
                            return True
                        else:
                            print(f"Certificate for {hostname} NOT found in Certificate Transparency logs!")
                            print("This may indicate the certificate was not properly logged.")
                            return False
                    except ValueError:
                        print("Error parsing CT logs response")
                        return None
                else:
                    print(f"Error querying CT logs: {response.status_code}")
                    return None
    except Exception as e:
        print(f"Error in CT verification: {str(e)}")
        return None

# Example usage
verify_certificate_transparency("example.com")
```

## TLS Configuration Analysis

### TLS Security Scanner

```python
from monitorpy import run_check
import socket
import ssl
from datetime import datetime

def analyze_tls_security(hostname, port=443):
    """Analyze the TLS security configuration of a server."""
    # Base configuration
    base_config = {
        "hostname": hostname,
        "port": port,
        "check_chain": True
    }
    
    # Get the basic certificate information
    result = run_check("ssl_certificate", base_config)
    
    if not result.is_success():
        print(f"Initial certificate check failed: {result.message}")
        return None
    
    # Start building the security report
    security_report = {
        "hostname": hostname,
        "port": port,
        "timestamp": datetime.now().isoformat(),
        "certificate": {
            "subject": result.raw_data.get("subject", {}),
            "issuer": result.raw_data.get("issuer", {}),
            "valid_from": result.raw_data.get("not_before"),
            "valid_until": result.raw_data.get("not_after"),
            "days_until_expiration": result.raw_data.get("days_until_expiration"),
            "alternative_names": result.raw_data.get("alternative_names", [])
        },
        "tls_versions": {},
        "cipher_suites": {},
        "security_issues": []
    }
    
    # Test supported TLS versions
    tls_versions = [
        ("SSLv3", ssl.PROTOCOL_SSLv23),  # Actually tries various protocols
        ("TLSv1", ssl.PROTOCOL_TLSv1),
        ("TLSv1.1", ssl.PROTOCOL_TLSv1_1),
        ("TLSv1.2", ssl.PROTOCOL_TLSv1_2)
    ]
    
    # Python 3.6+ has TLS 1.3 support
    if hasattr(ssl, "PROTOCOL_TLSv1_3"):
        tls_versions.append(("TLSv1.3", ssl.PROTOCOL_TLSv1_3))
    
    # Test each TLS version
    print(f"\nTesting TLS versions for {hostname}:{port}")
    for version_name, version_const in tls_versions:
        try:
            context = ssl.SSLContext(version_const)
            
            # Try to establish a connection
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Connection succeeded, get the version actually used
                    actual_version = ssock.version()
                    cipher = ssock.cipher()
                    
                    print(f"✅ {actual_version} supported with cipher: {cipher[0]}")
                    
                    # Store in report
                    security_report["tls_versions"][actual_version] = True
                    
                    if cipher[0] not in security_report["cipher_suites"]:
                        security_report["cipher_suites"][cipher[0]] = {
                            "protocol": cipher[1],
                            "bits": cipher[2]
                        }
        except ssl.SSLError as e:
            if "unsupported protocol" in str(e).lower() or "wrong version" in str(e).lower():
                print(f"❌ {version_name} not supported")
                security_report["tls_versions"][version_name] = False
            else:
                print(f"❓ {version_name} test error: {str(e)}")
        except (socket.timeout, ConnectionRefusedError) as e:
            print(f"❗ Connection error during {version_name} test: {str(e)}")
            break
        except Exception as e:
            print(f"❗ Unexpected error during {version_name} test: {str(e)}")
    
    # Analyze security issues
    print("\nSecurity Analysis:")
    
    # Issue: Old TLS versions supported
    if security_report["tls_versions"].get("SSLv3", False) or \
       security_report["tls_versions"].get("TLSv1", False) or \
       security_report["tls_versions"].get("TLSv1.1", False):
        issue = "Server supports outdated and insecure TLS versions (SSLv3, TLSv1, TLSv1.1)"
        print(f"⚠️ {issue}")
        security_report["security_issues"].append(issue)
    
    # Issue: Modern TLS not supported
    if not security_report["tls_versions"].get("TLSv1.2", False) and \
       not security_report["tls_versions"].get("TLSv1.3", False):
        issue = "Server does not support modern TLS versions (TLSv1.2, TLSv1.3)"
        print(f"❌ {issue}")
        security_report["security_issues"].append(issue)
    
    # Issue: Certificate expiring soon
    days_left = security_report["certificate"]["days_until_expiration"]
    if days_left < 30:
        issue = f"Certificate expires very soon ({days_left} days)"
        print(f"❌ {issue}")
        security_report["security_issues"].append(issue)
    elif days_left < 60:
        issue = f"Certificate expires soon ({days_left} days)"
        print(f"⚠️ {issue}")
        security_report["security_issues"].append(issue)
    
    # Overall security score
    weak_ciphers = sum(1 for cipher, details in security_report["cipher_suites"].items() 
                     if details["bits"] < 128)
    
    old_tls = sum(1 for version, supported in security_report["tls_versions"].items() 
                if supported and version in ["SSLv3", "TLSv1", "TLSv1.1"])
    
    modern_tls = security_report["tls_versions"].get("TLSv1.2", False) or \
                security_report["tls_versions"].get("TLSv1.3", False)
    
    # Calculate score (simple algorithm)
    score = 100
    score -= len(security_report["security_issues"]) * 10  # -10 for each issue
    score -= weak_ciphers * 15  # -15 for each weak cipher
    score -= old_tls * 10  # -10 for each old TLS version
    if not modern_tls:
        score -= 30  # -30 if no modern TLS
    
    # Ensure score stays in 0-100 range
    score = max(0, min(100, score))
    
    security_report["security_score"] = score
    
    # Print summary
    print(f"\nTLS Security Score: {score}/100")
    if score >= 90:
        print("🔒 Excellent - Server has strong TLS configuration")
    elif score >= 70:
        print("🔒 Good - Server has acceptable TLS configuration")
    elif score >= 50:
        print("⚠️ Fair - Server has some TLS security issues")
    else:
        print("❌ Poor - Server has major TLS security vulnerabilities")
    
    return security_report

# Example usage
security_report = analyze_tls_security("example.com")
```

## Certificate Rotation Monitoring

### Track Certificate Changes Over Time

```python
from monitorpy import run_check
import json
import os
from datetime import datetime
import hashlib

def monitor_certificate_changes(hostname, port=443, history_dir="cert_history"):
    """Track certificate changes over time."""
    # Ensure history directory exists
    os.makedirs(history_dir, exist_ok=True)
    
    # File to store certificate history
    history_file = os.path.join(
        history_dir, 
        f"{hostname.replace('.', '_')}_{port}_history.json"
    )
    
    # Create a history array if the file doesn't exist
    if not os.path.exists(history_file):
        with open(history_file, 'w') as f:
            json.dump([], f)
    
    # Load existing history
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    # Get current certificate
    config = {
        "hostname": hostname,
        "port": port,
        "check_chain": True
    }
    
    result = run_check("ssl_certificate", config)
    
    if not result.is_success() and result.status != "warning":
        print(f"Certificate check failed: {result.message}")
        
        # Still record the failure in history
        history.append({
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "message": result.message
        })
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
        return None
    
    # Extract certificate data
    cert_data = {
        "timestamp": datetime.now().isoformat(),
        "status": result.status,
        "subject": result.raw_data.get("subject", {}),
        "issuer": result.raw_data.get("issuer", {}),
        "not_before": result.raw_data.get("not_before", ""),
        "not_after": result.raw_data.get("not_after", ""),
        "days_until_expiration": result.raw_data.get("days_until_expiration", 0),
        "serial_number": result.raw_data.get("serial_number", ""),
        "alternative_names": result.raw_data.get("alternative_names", [])
    }
    
    # Calculate a fingerprint for the certificate (simplified)
    fingerprint_data = f"{cert_data['serial_number']}:{cert_data['not_before']}:{cert_data['not_after']}"
    fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
    cert_data['fingerprint'] = fingerprint
    
    # Check if this is a new or changed certificate
    is_new_cert = True
    
    if history:
        # Get the most recent certificate
        last_cert = history[-1]
        
        # Compare fingerprints if available
        if 'fingerprint' in last_cert and last_cert['fingerprint'] == fingerprint:
            is_new_cert = False
            print(f"Certificate unchanged since last check ({last_cert['timestamp']})")
        else:
            print("Certificate has changed since last check!")
            
            # Show what changed
            if 'serial_number' in last_cert and last_cert['serial_number'] != cert_data['serial_number']:
                print(f"Serial number changed: {last_cert['serial_number']} -> {cert_data['serial_number']}")
                
            if 'not_after' in last_cert and last_cert['not_after'] != cert_data['not_after']:
                print(f"Expiration date changed: {last_cert['not_after']} -> {cert_data['not_after']}")
                
            if 'issuer' in last_cert and last_cert['issuer'] != cert_data['issuer']:
                print("Issuer changed!")
                
            # Calculate remaining lifetime of new certificate
            print(f"New certificate expires in {cert_data['days_until_expiration']} days")
    else:
        print(f"First time checking certificate for {hostname}:{port}")
    
    # Add entry to history if it's a new certificate
    if is_new_cert:
        history.append(cert_data)
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    # Report on certificate rotation frequency if we have enough history
    if len(history) > 1:
        print("\nCertificate Rotation History:")
        for i, entry in enumerate(history):
            print(f"{i+1}. {entry.get('timestamp', 'Unknown')} - Valid until: {entry.get('not_after', 'Unknown')}")
    
    return cert_data

# Example usage
current_cert = monitor_certificate_changes("example.com")
```

## Multi-Domain Management

### Create a Certificate Inventory

```python
from monitorpy import run_check
import pandas as pd
from datetime import datetime
import concurrent.futures
import time
import json
import os

def build_certificate_inventory(domains, output_file="certificate_inventory.xlsx"):
    """Build a comprehensive certificate inventory for multiple domains."""
    inventory = []
    errors = []
    
    def check_domain(domain_info):
        """Check a single domain and return inventory data."""
        domain = domain_info["domain"] if isinstance(domain_info, dict) else domain_info
        port = domain_info.get("port", 443) if isinstance(domain_info, dict) else 443
        
        print(f"Checking {domain}:{port}...")
        
        try:
            config = {
                "hostname": domain,
                "port": port,
                "check_chain": True
            }
            
            start_time = time.time()
            result = run_check("ssl_certificate", config)
            duration = time.time() - start_time
            
            if not result.is_success() and result.status != "warning":
                errors.append({
                    "domain": domain,
                    "port": port,
                    "status": result.status,
                    "message": result.message
                })
                return None
            
            # Common certificate data
            cert_data = {
                "domain": domain,
                "port": port,
                "status": result.status,
                "issuer_name": result.raw_data.get("issuer", {}).get("commonName", "Unknown"),
                "issuer_org": result.raw_data.get("issuer", {}).get("organizationName", "Unknown"),
                "subject_name": result.raw_data.get("subject", {}).get("commonName", "Unknown"),
                "subject_org": result.raw_data.get("subject", {}).get("organizationName", "Unknown"),
                "valid_from": result.raw_data.get("not_before", ""),
                "valid_until": result.raw_data.get("not_after", ""),
                "days_until_expiry": result.raw_data.get("days_until_expiration", 0),
                "serial_number": result.raw_data.get("serial_number", ""),
                "alt_names_count": len(result.raw_data.get("alternative_names", [])),
                "chain_verified": "check_chain" in config and config["check_chain"],
                "query_time_secs": duration,
                "check_date": datetime.now().strftime('%Y-%m-%d')
            }
            
            # Get TLS version if available
            if "protocol" in result.raw_data:
                cert_data["tls_version"] = result.raw_data["protocol"]
            
            # Get cipher details if available
            if "cipher" in result.raw_data:
                cert_data["cipher_suite"] = result.raw_data["cipher"][0]
                cert_data["cipher_strength_bits"] = result.raw_data["cipher"][2]
            
            return cert_data
            
        except Exception as e:
            errors.append({
                "domain": domain,
                "port": port,
                "status": "error",
                "message": str(e)
            })
            return None
    
    # Use multithreading to check domains in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_domain, domain) for domain in domains]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                inventory.append(result)
    
    # Create a DataFrame for the inventory
    if inventory:
        df = pd.DataFrame(inventory)
        
        # Sort by expiration
        df = df.sort_values("days_until_expiry")
        
        # Save to Excel
        df.to_excel(output_file, index=False)
        print(f"\nCertificate inventory saved to {output_file}")
        
        # Create a summary by issuer
        print("\nCertificates by Issuer:")
        issuer_counts = df['issuer_name'].value_counts()
        for issuer, count in issuer_counts.items():
            print(f"  {issuer}: {count}")
        
        # Create a summary by expiration
        print("\nCertificates by Expiration:")
        print(f"  Expired: {len(df[df['days_until_expiry'] <= 0])}")
        print(f"  Expires within 30 days: {len(df[(df['days_until_expiry'] > 0) & (df['days_until_expiry'] <= 30)])}")
        print(f"  Expires within 90 days: {len(df[(df['days_until_expiry'] > 30) & (df['days_until_expiry'] <= 90)])}")
        print(f"  Expires after 90 days: {len(df[df['days_until_expiry'] > 90])}")
    
    # Report on errors
    if errors:
        print(f"\n{len(errors)} domains had errors:")
        for error in errors:
            print(f"  {error['domain']}:{error['port']} - {error['message']}")
        
        # Save errors to JSON
        with open("certificate_inventory_errors.json", "w") as f:
            json.dump(errors, f, indent=2)
    
    return {
        "inventory": inventory,
        "errors": errors
    }

# Example usage
domains = [
    "example.com",
    {"domain": "example.org", "port": 443},
    {"domain": "example.net", "port": 8443},
    "google.com",
    "github.com",
    "microsoft.com"
]

inventory_results = build_certificate_inventory(domains)
```

## Advanced Monitoring System

Here's a more complete example of a certificate monitoring system:
```python
import concurrent.futures
import json
import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.message import EmailMessage

import pandas as pd

from monitorpy import run_check

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("certificate_monitor.log"), logging.StreamHandler()])
logger = logging.getLogger("certificate_monitor")


class CertificateMonitor:
    """Advanced certificate monitoring system."""

    def __init__(self, config_file):
        """Initialize with a configuration file."""
        self.config_file = config_file
        self.domains = []
        self.notification_config = {}
        self.check_interval = 86400  # Default: daily
        self.history_dir = "certificate_history"
        self.report_dir = "certificate_reports"

        # Create directories if they don't exist
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)

        # Load configuration
        self.load_config()

    def load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            self.domains = config.get("domains", [])
            self.notification_config = config.get("notifications", {})
            self.check_interval = config.get("check_interval", 86400)

            logger.info(f"Loaded configuration with {len(self.domains)} domains")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise

    def check_certificate(self, domain_info):
        """Check a single domain's certificate."""
        domain = domain_info["domain"] if isinstance(domain_info, dict) else domain_info
        port = domain_info.get("port", 443) if isinstance(domain_info, dict) else 443
        name = domain_info.get("name", f"{domain}:{port}") if isinstance(domain_info, dict) else f"{domain}:{port}"

        logger.info(f"Checking certificate for {name}")

        # Set up configuration
        config = {"hostname": domain, "port": port, "check_chain": True,
                  "warning_days": domain_info.get("warning_days", 30) if isinstance(domain_info, dict) else 30,
                  "critical_days": domain_info.get("critical_days", 14) if isinstance(domain_info, dict) else 14}

        try:
            # Run the check
            result = run_check("ssl_certificate", config)

            # Basic result data
            cert_data = {"timestamp": datetime.now().isoformat(), "domain": domain, "port": port, "name": name,
                         "status": result.status, "message": result.message,
                         "days_until_expiration": result.raw_data.get("days_until_expiration",
                                                                      0) if result.is_success() or result.status == "warning" else 0,
                         "not_after": result.raw_data.get("not_after",
                                                          "") if result.is_success() or result.status == "warning" else "",
                         "issuer": result.raw_data.get("issuer", {}).get("commonName",
                                                                         "Unknown") if result.is_success() or result.status == "warning" else "Unknown"}

            # Check for changes
            changes = self.check_for_changes(name, cert_data)
            cert_data["changes"] = changes

            # Save history
            self.save_certificate_history(name, cert_data)

            # Send notifications if needed
            if changes or result.status != "success":
                self.send_notification(name, cert_data, changes)

            return cert_data

        except Exception as e:
            logger.error(f"Error checking certificate for {name}: {str(e)}")
            cert_data = {"timestamp": datetime.now().isoformat(), "domain": domain, "port": port, "name": name,
                         "status": "error", "message": f"Exception: {str(e)}", "days_until_expiration": 0,
                         "not_after": "", "issuer": "Unknown", "changes": []}

            # Save history even for errors
            self.save_certificate_history(name, cert_data)

            # Send error notification
            self.send_notification(name, cert_data, [])

            return cert_data

    def check_for_changes(self, name, current_data):
        """Check if certificate has changed from previous state."""
        history_file = os.path.join(self.history_dir, f"{name.replace(':', '_').replace('.', '_')}_history.json")

        if not os.path.exists(history_file):
            return []  # No history to compare against

        try:
            with open(history_file, 'r') as f:
                history = json.load(f)

            if not history:
                return []

            # Get the most recent entry
            last_entry = history[-1]
            changes = []

            # Check for status change
            if last_entry.get("status") != current_data.get("status"):
                changes.append({"type": "status", "old": last_entry.get("status"), "new": current_data.get("status")})

            # Check for expiration date change
            if last_entry.get("not_after") != current_data.get("not_after"):
                changes.append(
                    {"type": "expiration", "old": last_entry.get("not_after"), "new": current_data.get("not_after")})

            # Check for issuer change
            if last_entry.get("issuer") != current_data.get("issuer"):
                changes.append({"type": "issuer", "old": last_entry.get("issuer"), "new": current_data.get("issuer")})

            return changes

        except Exception as e:
            logger.error(f"Error checking for changes: {str(e)}")
            return []

    def save_certificate_history(self, name, cert_data):
        """Save certificate history for a domain."""
        history_file = os.path.join(self.history_dir, f"{name.replace(':', '_').replace('.', '_')}_history.json")

        try:
            # Load existing history or create new one
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []

            # Add current data to history
            history.append(cert_data)

            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving certificate history for {name}: {str(e)}")

    def send_notification(self, name, cert_data, changes):
        """Send notification about certificate issues or changes."""
        if not self.notification_config:
            return

        # Determine notification level
        if cert_data["status"] == "error":
            level = "CRITICAL"
        elif cert_data["status"] == "warning" or changes:
            level = "WARNING"
        else:
            return  # Don't notify for successful checks without changes

        # Build notification message
        message = f"{level} Certificate Alert: {name}\n\n"
        message += f"Status: {cert_data['status'].upper()}\n"
        message += f"Message: {cert_data['message']}\n"

        if cert_data["days_until_expiration"] > 0:
            message += f"Expires in: {cert_data['days_until_expiration']} days ({cert_data['not_after']})\n"

        if changes:
            message += "\nChanges detected:\n"
            for change in changes:
                message += f"- {change['type'].capitalize()} changed: {change['old']} → {change['new']}\n"

        message += f"\nTimestamp: {cert_data['timestamp']}"

        # Send email notification if configured
        if self.notification_config.get("email", {}).get("enabled", False):
            self.send_email_notification(level, name, message)

        # Send webhook notification if configured
        if self.notification_config.get("webhook", {}).get("enabled", False):
            self.send_webhook_notification(level, name, message)

        logger.info(f"Sent {level} notification for {name}")

    def send_email_notification(self, level, name, message):
        """Send email notification."""
        try:
            email_config = self.notification_config.get("email", {})

            if not email_config.get("smtp_server") or not email_config.get("from_address") or not email_config.get(
                    "to_addresses"):
                logger.warning("Incomplete email configuration, skipping email notification")
                return

            msg = EmailMessage()
            msg["Subject"] = f"{level} Certificate Alert: {name}"
            msg["From"] = email_config["from_address"]
            msg["To"] = ", ".join(email_config["to_addresses"])
            msg.set_content(message)

            # Send the email
            with smtplib.SMTP(email_config["smtp_server"], email_config.get("smtp_port", 25)) as server:
                if email_config.get("use_tls", False):
                    server.starttls()

                if email_config.get("username") and email_config.get("password"):
                    server.login(email_config["username"], email_config["password"])

                server.send_message(msg)

            logger.info(f"Sent email notification to {', '.join(email_config['to_addresses'])}")

        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")

    def send_webhook_notification(self, level, name, message):
        """Send webhook notification."""
        try:
            import requests

            webhook_config = self.notification_config.get("webhook", {})
            webhook_url = webhook_config.get("url")

            if not webhook_url:
                logger.warning("Missing webhook URL, skipping webhook notification")
                return

            payload = {"level": level, "name": name, "message": message}

            # Add additional fields if configured
            if webhook_config.get("include_timestamp", True):
                payload["timestamp"] = datetime.now().isoformat()

            if webhook_config.get("include_source", True):
                payload["source"] = "MonitorPy Certificate Monitor"

            response = requests.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Webhook notification failed with status {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")

    def run_checks(self):
        """Run certificate checks for all configured domains."""
        results = []

        # Use thread pool for parallel checks
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_domain = {executor.submit(self.check_certificate, domain): domain for domain in self.domains}

            for future in concurrent.futures.as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    cert_data = future.result()
                    results.append(cert_data)
                except Exception as e:
                    logger.error(f"Unhandled exception checking {domain}: {str(e)}")

        # Generate report
        self.generate_report(results)

        return results

    def generate_report(self, results):
        """Generate a report summarizing certificate status."""
        # Create a timestamp for the report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Prepare report summary
        summary = {"timestamp": datetime.now().isoformat(), "total_domains": len(results),
                   "status_counts": {"success": sum(1 for r in results if r["status"] == "success"),
                                     "warning": sum(1 for r in results if r["status"] == "warning"),
                                     "error": sum(1 for r in results if r["status"] == "error")},
                   "expiration_summary": {"expired": sum(1 for r in results if r["days_until_expiration"] <= 0),
                                          "expires_within_30_days": sum(
                                              1 for r in results if 0 < r["days_until_expiration"] <= 30),
                                          "expires_within_90_days": sum(
                                              1 for r in results if 30 < r["days_until_expiration"] <= 90),
                                          "expires_after_90_days": sum(
                                              1 for r in results if r["days_until_expiration"] > 90)},
                   "changed_certificates": sum(1 for r in results if r.get("changes"))}

        # Save detailed JSON report
        json_report_file = os.path.join(self.report_dir, f"certificate_report_{timestamp}.json")

        with open(json_report_file, 'w') as f:
            json.dump({"summary": summary, "results": results}, f, indent=2)

        # Save Excel report with key information
        excel_report_file = os.path.join(self.report_dir, f"certificate_report_{timestamp}.xlsx")

        # Convert results to DataFrame
        df = pd.DataFrame([{"Domain": r["domain"], "Port": r["port"], "Name": r["name"], "Status": r["status"],
                            "Message": r["message"], "Days Until Expiration": r["days_until_expiration"],
                            "Expiration Date": r["not_after"], "Issuer": r["issuer"], "Changed": bool(r.get("changes")),
                            "Timestamp": r["timestamp"]} for r in results])

        # Sort by expiration (warning/critical first)
        df = df.sort_values(by=["Status", "Days Until Expiration"])

        # Save to Excel
        df.to_excel(excel_report_file, index=False)

        # Log summary
        logger.info(f"Certificate check summary:")
        logger.info(f"  Total domains: {summary['total_domains']}")
        logger.info(
            f"  Success: {summary['status_counts']['success']}, Warning: {summary['status_counts']['warning']}, Error: {summary['status_counts']['error']}")
        logger.info(
            f"  Expiration: {summary['expiration_summary']['expired']} expired, {summary['expiration_summary']['expires_within_30_days']} within 30 days")
        logger.info(f"  Changed certificates: {summary['changed_certificates']}")
        logger.info(f"  Reports saved to {json_report_file} and {excel_report_file}")

    def run_monitoring_loop(self):
        """Run continuous certificate monitoring."""
        logger.info("Starting certificate monitoring loop")

        while True:
            try:
                self.run_checks()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")

            # Log next check time
            next_check = datetime.now() + timedelta(seconds=self.check_interval)
            logger.info(f"Next check scheduled at: {next_check.isoformat()}")

            # Sleep until next check
            time.sleep(self.check_interval)


# Example usage
if __name__ == "__main__":
    monitor = CertificateMonitor("certificate_monitor_config.json")
    monitor.run_monitoring_loop()

```

### Example Configuration File

Here's an example configuration file (`certificate_monitor_config.json`):

```json
{
  "domains": [
    {
      "name": "Main Website",
      "domain": "example.com",
      "port": 443,
      "warning_days": 45,
      "critical_days": 15
    },
    {
      "name": "API Endpoint",
      "domain": "api.example.com",
      "port": 443,
      "warning_days": 60,
      "critical_days": 30
    },
    {
      "name": "Admin Portal",
      "domain": "admin.example.com",
      "port": 8443,
      "warning_days": 90,
      "critical_days": 30
    },
    "example.org",
    "example.net"
  ],
  "check_interval": 86400,
  "notifications": {
    "email": {
      "enabled": true,
      "smtp_server": "smtp.example.com",
      "smtp_port": 587,
      "use_tls": true,
      "username": "alerts@example.com",
      "password": "your-password",
      "from_address": "alerts@example.com",
      "to_addresses": ["admin@example.com", "security@example.com"]
    },
    "webhook": {
      "enabled": true,
      "url": "https://hooks.example.com/certificate-alerts",
      "include_timestamp": true,
      "include_source": true
    }
  }
}
```
