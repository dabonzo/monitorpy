# DNS CLI Commands

The MonitorPy CLI provides a powerful interface for checking DNS records and propagation.

## Basic Syntax

```bash
monitorpy dns DOMAIN [OPTIONS]
```

Where `DOMAIN` is the domain name you want to check.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--type RECORD_TYPE` | DNS record type (A, AAAA, MX, CNAME, TXT, NS, etc.) | A |
| `--value VALUE` | Expected record value | None |
| `--subdomain SUBDOMAIN` | Subdomain to check (e.g., 'www') | None |
| `--nameserver IP` | Specific nameserver to query | System default |
| `--timeout SECONDS` | Query timeout in seconds | 10 |
| `--check-propagation` | Check DNS propagation across multiple resolvers | False |
| `--resolvers IP [IP...]` | Custom DNS resolvers to check (space-separated list) | Default public resolvers |
| `--threshold PERCENTAGE` | Propagation threshold percentage | 80 |
| `--check-authoritative` | Check if response is from an authoritative server | False |
| `--check-dnssec` | Check DNSSEC validation | False |
| `--max-workers COUNT` | Maximum workers for propagation checks | 10 |
| `-v, --verbose` | Show detailed output | False |
| `--json` | Output results as JSON | False |

## Common Usage Patterns

### Basic DNS Check

Check if a domain has A records:

```bash
monitorpy dns example.com
```

### Check Specific Record Type

```bash
monitorpy dns example.com --type MX
```

### Check with Expected Value

```bash
monitorpy dns example.com --type A --value 192.0.2.1
```

### Check a Subdomain

```bash
monitorpy dns example.com --type A --subdomain www
```

### Check DNS Propagation

```bash
monitorpy dns example.com --check-propagation
```

### Check with Custom Resolvers

```bash
monitorpy dns example.com --check-propagation --resolvers 8.8.8.8 1.1.1.1 9.9.9.9
```

### Check DNSSEC Validation

```bash
monitorpy dns example.com --check-dnssec
```

### Check Authoritative Response

```bash
monitorpy dns example.com --check-authoritative
```

### Comprehensive DNS Health Check

```bash
monitorpy dns example.com --type A --value 192.0.2.1 --check-propagation --check-dnssec --check-authoritative --verbose
```

### JSON Output for Automation

```bash
monitorpy dns example.com --check-propagation --json
```
These command-line options correspond to configuration parameters documented in detail in the [Advanced Configuration Guide](../reference/advanced_configuration.md).

## Example Output

### Success Output (Basic)

```
SUCCESS: DNS A record for example.com matches expected value. Values: 192.0.2.1
Response time: 0.0452 seconds
```

### Verbose Output

```
SUCCESS: DNS A record for example.com matches expected value. Values: 192.0.2.1
Response time: 0.0452 seconds

Raw data:
{
  "domain": "example.com",
  "record_type": "A",
  "records": [
    "192.0.2.1"
  ],
  "expected_value": "192.0.2.1",
  "expected_value_match": true,
  "query_time": 0.0452,
  "nameserver": "8.8.8.8",
  "ttl": 3600,
  "propagation": {
    "status": "success",
    "total_count": 8,
    "successful_count": 8,
    "consistent_count": 8,
    "percentage": 100.0,
    "threshold": 80,
    "resolvers": [
      {
        "resolver": "8.8.8.8",
        "name": "Google",
        "provider": "Google DNS",
        "status": "success",
        "response_time": 0.045,
        "records": ["192.0.2.1"],
        "match": true
      }
```

### Error Output (Record Mismatch)

```
ERROR: DNS A record check for example.com has issues: Expected value '192.0.2.2' not found. Values: 192.0.2.1
Response time: 0.0389 seconds
```

### Error Output (No Records)

```
ERROR: No A records found for nonexistent.example.com
Response time: 0.0512 seconds
```

### Error Output (Domain Doesn't Exist)

```
ERROR: Domain nonexistent-domain.com does not exist
Response time: 0.0356 seconds
```

### Warning Output (Propagation Issues)

```
WARNING: DNS A record for example.com matches expected value but has issues: Partial propagation: 75.0% (6/8 resolvers). Values: 192.0.2.1
Response time: 0.2534 seconds
```

## Exit Codes

The `dns` command returns the following exit codes:

- `0`: Success (check passed)
- `1`: Warning (check has warnings)
- `2`: Error (check failed)
- Other non-zero: Command-line error or exception

## Dependencies

The DNS monitoring functionality requires the `dnspython` package:

```bash
pip install dnspython
```

If this package is not installed, the command will display an error message with installation instructions.

## Troubleshooting

### Common Issues

1. **"dnspython library is not installed"**
   
   ```
   Error: The dnspython package is required for DNS checks.
   Please install it with: pip install dnspython
   ```
   
   Solution: Install the required package with `pip install dnspython`

2. **"Invalid record type"**
   
   ```
   ERROR: Invalid record type: XYZ. Must be one of: A, AAAA, MX, CNAME, TXT, NS, SOA, PTR, SRV, CAA...
   ```
   
   Solution: Use a valid DNS record type. See [Record Types](#options) for the list of supported types.

3. **"Connection timeout"**
   
   ```
   ERROR: Connection error: Connection timed out
   ```
   
   Solution: Try increasing the timeout with `--timeout 30` or check network connectivity.

4. **"Resolvers specification is invalid"**
   
   ```
   ERROR: Invalid resolver IP address: 8.8.8
   ```
   
   Solution: Make sure all resolver IPs are valid (e.g., `8.8.8.8` not `8.8.8`),
      // More resolvers...
    ]
  }
}