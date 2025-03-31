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