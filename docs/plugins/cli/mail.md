# Mail Server CLI Commands

The MonitorPy CLI provides a powerful interface for checking mail server connectivity and functionality.

## Basic Syntax

```bash
monitorpy mail HOSTNAME [OPTIONS]
```

Where `HOSTNAME` is the mail server hostname or domain you want to check.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--protocol PROTOCOL` | Mail protocol to check (smtp, imap, pop3) | smtp |
| `--port PORT` | Server port (protocol-specific default) | Protocol default |
| `--username USERNAME` | Username for authentication | None |
| `--password PASSWORD` | Password for authentication | None |
| `--ssl` | Use SSL connection | False |
| `--tls` | Use TLS connection (SMTP only) | False |
| `--timeout SECONDS` | Connection timeout in seconds | 30 |
| `--send-test` | Send test email (SMTP only) | False |
| `--from FROM_EMAIL` | From email address (for test email) | None |
| `--to TO_EMAIL` | To email address (for test email) | None |
| `--basic-check` | Perform basic connectivity check without authentication | False |
| `--resolve-mx` | Resolve MX records for domain and check the highest priority server | False |
| `-v, --verbose` | Show detailed output | False |
| `--json` | Output results as JSON | False |

## Common Usage Patterns

### Basic SMTP Server Check

Check if an SMTP server is accessible:

```bash
monitorpy mail mail.example.com --protocol smtp
```

### Check with MX Record Resolution

When you know the domain but not the mail server hostname:

```bash
monitorpy mail example.com --protocol smtp --resolve-mx
```

### SMTP with Authentication

Check SMTP server with login credentials:

```bash
monitorpy mail mail.example.com --protocol smtp --username user@example.com --password yourpassword
```

### SMTP with TLS

Test a secure SMTP connection with TLS:

```bash
monitorpy mail mail.example.com --protocol smtp --tls --port 587
```

### SMTP with SSL

Test a secure SMTP connection with SSL:

```bash
monitorpy mail mail.example.com --protocol smtp --ssl --port 465
```

### Send Test Email

Verify full email delivery by sending a test message:

```bash
monitorpy mail mail.example.com --protocol smtp --username user@example.com --password yourpassword --send-test --from user@example.com --to recipient@example.com
```

### Check IMAP Server

Test IMAP server connectivity and authentication:

```bash
monitorpy mail mail.example.com --protocol imap --username user@example.com --password yourpassword
```

### Check IMAP with SSL

Test secure IMAP connection:

```bash
monitorpy mail mail.example.com --protocol imap --ssl --port 993 --username user@example.com --password yourpassword
```

### Check POP3 Server

Test POP3 server connectivity and authentication:

```bash
monitorpy mail mail.example.com --protocol pop3 --username user@example.com --password yourpassword
```

### Detailed Output

Show detailed information about the mail server:

```bash
monitorpy mail mail.example.com --protocol smtp --verbose
```

### JSON Output for Automation

Get machine-readable JSON output:

```bash
monitorpy mail mail.example.com --protocol smtp --json
```

## Example Output

### SMTP Basic Check Success Output

```
SUCCESS: SMTP server mail.example.com:25 is operational. Supports: STARTTLS, AUTH, SIZE, 8BITMIME, PIPELINING
Response time: 0.0821 seconds
```

### SMTP Basic Check Verbose Output

```
SUCCESS: SMTP server mail.example.com:25 is operational. Supports: STARTTLS, AUTH, SIZE, 8BITMIME, PIPELINING
Response time: 0.0821 seconds

Raw data:
{
  "hostname": "mail.example.com",
  "port": 25,
  "protocol": "smtp",
  "supports_tls": true,
  "local_address": "192.0.2.2",
  "remote_address": "192.0.2.1",
  "ehlo_code": 250,
  "ehlo_message": "mail.example.com Hello client",
  "extensions": {
    "SIZE": "10240000",
    "STARTTLS": "",
    "AUTH": "PLAIN LOGIN",
    "8BITMIME": "",
    "PIPELINING": ""
  }
}
```

### SMTP Authentication Success Output

```
SUCCESS: SMTP server check successful, authenticated as user@example.com
Response time: 0.1542 seconds
```

### SMTP Send Test Email Output

```
SUCCESS: SMTP server check successful, test email sent from user@example.com to recipient@example.com
Response time: 0.3245 seconds
```

### IMAP Authentication Success Output

```
SUCCESS: IMAP server check successful, authenticated as user@example.com, INBOX contains 42 messages
Response time: 0.0976 seconds
```

### POP3 Authentication Success Output

```
SUCCESS: POP3 server check successful, authenticated as user@example.com, 15 messages in mailbox
Response time: 0.0834 seconds
```

### MX Resolution Output

```
SUCCESS: SMTP server for example.com (using mail.example.com:25) is operational. Supports: STARTTLS, SIZE, 8BITMIME
Response time: 0.1123 seconds
```

### Error Output (Connection Issues)

```
ERROR: Connection error checking SMTP server mail.example.com:25: Connection refused
Response time: 0.0000 seconds
```

### Error Output (Authentication Failure)

```
ERROR: SMTP authentication failed for user user@example.com
Response time: 0.0934 seconds
```

## Exit Codes

The `mail` command returns the following exit codes:

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

3. **"Authentication failed"**
   
   The provided username/password is incorrect. Check the credentials and try again.

4. **"TLS/SSL handshake failed"**
   
   There was an issue establishing a secure connection. This could be due to protocol version mismatches or certificate issues.

5. **"Error resolving MX records"**
   
   When using `--resolve-mx`, there was an issue finding MX records for the domain. Make sure the domain is correct and has proper MX records configured.

### Debugging Tips

1. **Check Basic Connectivity First**
   
   Start with a basic connectivity check before trying authentication:
   
   ```bash
   monitorpy mail mail.example.com --protocol smtp --basic-check
   ```

2. **Test with Verbose Output**
   
   Use the `--verbose` flag to see detailed information about the connection:
   
   ```bash
   monitorpy mail mail.example.com --protocol smtp --verbose
   ```

3. **Check Port Configuration**
   
   Make sure you're using the correct port for the protocol and encryption type:
   
   - SMTP: 25 (plain), 465 (SSL), 587 (TLS)
   - IMAP: 143 (plain), 993 (SSL)
   - POP3: 110 (plain), 995 (SSL)

4. **Test with a Known Working Mail Client**
   
   If MonitorPy is failing, test the same server with a regular mail client to see if the issue is with the server or with MonitorPy.

5. **Check Firewall Rules**
   
   Ensure that your firewall allows outbound connections to the mail server ports you're trying to use.