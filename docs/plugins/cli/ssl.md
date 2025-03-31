# SSL CLI Commands

The MonitorPy CLI provides a powerful interface for checking SSL certificate validity and expiration.

## Basic Syntax

```bash
monitorpy ssl HOSTNAME [OPTIONS]
```

Where `HOSTNAME` is the domain name you want to check.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--port PORT` | Port number for the SSL connection | 443 |
| `--timeout TIMEOUT` | Connection timeout in seconds | 30 |
| `--warning WARNING` | Warning threshold in days | 30 |
| `--critical CRITICAL` | Critical threshold in days | 14 |
| `--check-chain` | Check certificate chain details | False |
| `--no-verify-hostname` | Disable hostname verification | False |
| `-v, --verbose` | Show detailed output | False |
| `--json` | Output results as JSON | False |

## Common Usage Patterns

### Basic SSL Certificate Check

Check if an SSL certificate is valid and not expiring soon:

```bash
monitorpy ssl example.com
```

### Custom Warning Thresholds

Set custom warning and critical thresholds for certificate expiration:

```bash
monitorpy ssl example.com --warning 60 --critical 30
```

### Check Certificate on Non-Standard Port

Verify an SSL certificate on a non-standard port:

```bash
monitorpy ssl example.com --port 8443
```

### Detailed Certificate Information

Get detailed information about a certificate:

```bash
monitorpy ssl example.com --check-chain --verbose
```

### Disable Hostname Verification

Check certificate without verifying the hostname:

```bash
monitorpy ssl example.com --no-verify-hostname
```

### JSON Output for Automation

Get machine-readable JSON output:

```bash
monitorpy ssl example.com --json
```

## Example Output

### Success Output (Basic)

```
SUCCESS: Certificate valid until 2025-05-15T12:00:00Z (365 days remaining)
Response time: 0.2345 seconds
```

### Success Output (Verbose)

```
SUCCESS: Certificate valid until 2025-05-15T12:00:00Z (365 days remaining)
Response time: 0.2345 seconds

Raw data:
{
  "hostname": "example.com",
  "port": 443,
  "not_before": "2023-05-15T12:00:00Z",
  "not_after": "2025-05-15T12:00:00Z",
  "days_until_expiration": 365,
  "subject": {
    "commonName": "example.com",
    "organizationName": "Example Inc",
    "countryName": "US"
  },
  "issuer": {
    "commonName": "Example CA",
    "organizationName": "Example Certificate Authority",
    "countryName": "US"
  },
  "version": 3,
  "serial_number": "1234567890",
  "alternative_names": [
    "example.com",
    "www.example.com",
    "api.example.com"
  ]
}
```

### Warning Output (Expiring Soon)

```
WARNING: Certificate expiration approaching - 25 days left
Response time: 0.2345 seconds
```

### Error Output (Critical Expiration)

```
ERROR: Certificate expires very soon - 10 days left
Response time: 0.2345 seconds
```

### Error Output (Expired Certificate)

```
ERROR: Certificate expired on 2023-01-01T00:00:00Z
Response time: 0.2345 seconds
```

### Error Output (Connection Issues)

```
ERROR: Connection error: Connection timed out
Response time: 0.0000 seconds
```

## Exit Codes

The `ssl` command returns the following exit codes:

- `0`: Success (check passed)
- `1`: Warning (check has warnings)
- `2`: Error (check failed)
- Other non-zero: Command-line error or exception

## Troubleshooting

### Common Issues

1. **"Connection refused"**
   
   The server is not accepting connections on the specified port. Verify the port number and check if the server is running.

2. **"Connection timed out"**
   
   The server is taking too long to respond. Try increasing the timeout with `--timeout 60`.

3. **"Certificate hostname doesn't match"**
   
   The hostname in the certificate doesn't match the hostname you're checking. You can use `--no-verify-hostname` to bypass this check, but this may indicate a misconfigured certificate.

4. **"Self-signed certificate"**
   
   The server is using a self-signed certificate that isn't trusted by the system. This is expected for self-signed certificates.

5. **"Expired certificate"**
   
   The certificate has already expired. The server administrator should renew the certificate as soon as possible.
   
6. **"Unsupported algorithm"**
   
   The certificate uses encryption algorithms not supported by your system. This might indicate an outdated or insecure certificate.