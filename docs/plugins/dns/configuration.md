# DNS Plugin Configuration

This document describes the configuration options for the DNS monitoring plugin in MonitorPy.

## Configuration Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `domain` | string | Domain name to check (e.g., "example.com") |
| `record_type` | string | DNS record type (e.g., "A", "AAAA", "MX", "CNAME", "TXT") |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `expected_value` | string or list | None | Expected record value(s) to check against |
| `subdomain` | string | None | Subdomain to check (e.g., "www" for "www.example.com") |
| `nameserver` | string or list | System default | Specific nameserver(s) to query |
| `timeout` | integer | 10 | Query timeout in seconds |
| `check_propagation` | boolean | False | Check DNS propagation across multiple resolvers |
| `resolvers` | list | Default public resolvers | Custom DNS resolvers to use for propagation checks |
| `propagation_threshold` | float | 80.0 | Percentage threshold for propagation success (0-100) |
| `check_authoritative` | boolean | False | Check if response is from an authoritative server |
| `check_dnssec` | boolean | False | Check DNSSEC validation |
| `max_workers` | integer | 10 | Maximum number of concurrent workers for propagation checks |

## Record Types

The `record_type` parameter supports all standard DNS record types, including:

| Record Type | Description | Example Value |
|-------------|-------------|---------------|
| `A` | IPv4 address | "192.0.2.1" |
| `AAAA` | IPv6 address | "2001:db8::1" |
| `MX` | Mail exchange | "10 mail.example.com" |
| `CNAME` | Canonical name (alias) | "example.net" |
| `TXT` | Text record | "v=spf1 include:_spf.example.com ~all" |
| `NS` | Nameserver | "ns1.example.com" |
| `SOA` | Start of authority | "ns1.example.com hostmaster.example.com 2023010101 7200 3600 1209600 86400" |
| `PTR` | Pointer record | "example.com" |
| `SRV` | Service record | "0 5 5060 sip.example.com" |
| `CAA` | Certificate authority authorization | "0 issue \"letsencrypt.org\"" |

## Expected Value Format

The `expected_value` parameter format depends on the record type:

- **A/AAAA records**: IP address as a string (e.g., "192.0.2.1")
- **MX records**: Priority and hostname (e.g., "10 mail.example.com")
- **CNAME/NS/PTR records**: Hostname (e.g., "example.net")
- **TXT records**: Text content as a string (e.g., "v=spf1 include:_spf.example.com ~all")
- **Multiple values**: A list of strings for multiple expected values

## Propagation Checking

When `check_propagation` is enabled, the plugin checks DNS resolution across multiple DNS resolvers to verify proper propagation.

### Default Public Resolvers

If no custom resolvers are specified, the plugin uses these public DNS resolvers:

- Google DNS (8.8.8.8, 8.8.4.4)
- Cloudflare DNS (1.1.1.1, 1.0.0.1)
- Quad9 (9.9.9.9, 149.112.112.112)
- OpenDNS (208.67.222.222, 208.67.220.220)

### Custom Resolvers

You can specify custom resolvers using the `resolvers` parameter:

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "check_propagation": True,
    "resolvers": [
        "8.8.8.8",
        "1.1.1.1",
        "9.9.9.9",
        "208.67.222.222"
    ]
}
```

## Configuration Examples

### Basic A Record Check

```python
config = {
    "domain": "example.com",
    "record_type": "A"
}
```

### A Record with Expected Value

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "expected_value": "192.0.2.1"
}
```

### Subdomain Check

```python
config = {
    "domain": "example.com",
    "subdomain": "www",
    "record_type": "A"
}
```

### MX Record Check

```python
config = {
    "domain": "example.com",
    "record_type": "MX",
    "expected_value": [
        "10 mail.example.com",
        "20 backup-mail.example.com"
    ]
}
```

### Propagation Check

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "check_propagation": True,
    "propagation_threshold": 90
}
```

### DNSSEC Validation

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "check_dnssec": True
}
```

### Authoritative Check

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "check_authoritative": True
}
```

### Custom Nameserver

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "nameserver": "192.0.2.53"
}
```

### Comprehensive Check

```python
config = {
    "domain": "example.com",
    "record_type": "A",
    "expected_value": "192.0.2.1",
    "check_propagation": True,
    "check_authoritative": True,
    "check_dnssec": True,
    "timeout": 5
}
```