# Mail Server Plugin Configuration

This document describes the configuration options for the mail server monitoring plugin in MonitorPy.

## Configuration Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `hostname` | string | Mail server hostname or domain to check |
| `protocol` | string | Mail protocol to check (smtp, imap, pop3) |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | integer | Protocol-specific | Server port (default depends on protocol and SSL/TLS settings) |
| `username` | string | None | Username for authentication |
| `password` | string | None | Password for authentication |
| `use_ssl` | boolean | False | Whether to use SSL connection |
| `use_tls` | boolean | False | Whether to use TLS connection (SMTP only) |
| `timeout` | integer | 30 | Connection timeout in seconds |
| `test_send` | boolean | False | Send a test email (SMTP only) |
| `from_email` | string | None | From email address (for test email) |
| `to_email` | string | None | To email address (for test email) |
| `subject` | string | None | Email subject (for test email) |
| `message` | string | None | Email message body (for test email) |
| `resolve_mx` | boolean | False | Resolve MX records for domain and check the highest priority server |

## Protocol Specifics

### SMTP

SMTP (Simple Mail Transfer Protocol) is used for sending emails. When checking SMTP servers:

- Default ports: 25 (plain), 465 (SSL), 587 (TLS)
- Authentication is optional but commonly used
- `use_tls` enables STARTTLS, which upgrades a plain connection to encrypted
- `use_ssl` creates an encrypted connection from the start
- `test_send` enables sending a test email to verify full delivery functionality

### IMAP

IMAP (Internet Message Access Protocol) is used for retrieving emails. When checking IMAP servers:

- Default ports: 143 (plain), 993 (SSL)
- Authentication is typically required
- When authenticated, the plugin will check mailbox access

### POP3

POP3 (Post Office Protocol) is used for retrieving emails. When checking POP3 servers:

- Default ports: 110 (plain), 995 (SSL)
- Authentication is typically required
- When authenticated, the plugin will check mailbox access

## MX Record Resolution

When `resolve_mx` is enabled, the plugin will:

1. Look up MX records for the provided domain
2. Sort them by priority (lowest priority first)
3. Use the highest priority (lowest number) mail server for the check

This is useful when you know the domain but not the specific mail server hostname.

## Configuration Examples

### Basic SMTP Check

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "smtp"
}
```

### SMTP with Authentication

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "port": 587,
    "use_tls": True,
    "username": "user@example.com",
    "password": "password123"
}
```

### SMTP with Test Email

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "port": 587,
    "use_tls": True,
    "username": "user@example.com",
    "password": "password123",
    "test_send": True,
    "from_email": "user@example.com",
    "to_email": "recipient@example.com",
    "subject": "Test Email",
    "message": "This is a test email sent by MonitorPy"
}
```

### MX Record Resolution

```python
config = {
    "hostname": "example.com",  # Domain, not server
    "protocol": "smtp",
    "resolve_mx": True
}
```

### IMAP with SSL

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "imap",
    "port": 993,
    "use_ssl": True,
    "username": "user@example.com",
    "password": "password123"
}
```

### POP3 with SSL

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "pop3",
    "use_ssl": True,
    "username": "user@example.com",
    "password": "password123"
}
```

### Basic Check with Timeout

```python
config = {
    "hostname": "mail.example.com",
    "protocol": "smtp",
    "timeout": 10
}
```