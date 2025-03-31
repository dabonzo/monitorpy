# Website CLI Commands

The MonitorPy CLI provides a powerful interface for checking website availability and content.

## Basic Syntax

```bash
monitorpy website URL [OPTIONS]
```

Where `URL` is the website address you want to check.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--timeout SECONDS` | Request timeout in seconds | 30 |
| `--status STATUS` | Expected HTTP status code | 200 |
| `--method METHOD` | HTTP method (GET, POST, etc.) | GET |
| `--header HEADER` | HTTP header in format 'Name: Value' (can be used multiple times) | None |
| `--body BODY` | Request body data | None |
| `--content CONTENT` | Content that should be present in the response | None |
| `--no-content CONTENT` | Content that should NOT be present in the response | None |
| `--auth-username USERNAME` | Username for basic authentication | None |
| `--auth-password PASSWORD` | Password for basic authentication | None |
| `--no-verify` | Disable SSL certificate verification | False |
| `--no-redirect` | Disable following redirects | False |
| `-v, --verbose` | Show detailed output | False |
| `--json` | Output results as JSON | False |

## Common Usage Patterns

### Basic Website Check

Check if a website is accessible:

```bash
monitorpy website https://www.example.com
```

### Check with Custom Timeout

For potentially slow websites:

```bash
monitorpy website https://slow.example.com --timeout 60
```

### Check for Specific Status Code

Verify a specific HTTP status code:

```bash
monitorpy website https://www.example.com/not-found --status 404
```

### Check for Content

Verify that a website contains specific text:

```bash
monitorpy website https://www.example.com --content "Welcome to Example"
```

### Check for Absence of Content

Ensure that a website doesn't contain unwanted text:

```bash
monitorpy website https://www.example.com --no-content "Error" --no-content "Page not found"
```

### Check with Authentication

For password-protected websites:

```bash
monitorpy website https://private.example.com --auth-username user --auth-password pass
```

### POST Request with Custom Headers

Send a POST request with custom headers:

```bash
monitorpy website https://api.example.com \
  --method POST \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer token123" \
  --body '{"key":"value"}' \
  --status 201
```

### Disable SSL Verification

For websites with self-signed certificates:

```bash
monitorpy website https://self-signed.example.com --no-verify
```

### Disable Redirect Following

To check redirect behavior without following redirects:

```bash
monitorpy website https://example.com/redirect --no-redirect --status 302
```

### Detailed Output

Show detailed information about the response:

```bash
monitorpy website https://www.example.com --verbose
```

### JSON Output for Automation

Get machine-readable JSON output:

```bash
monitorpy website https://www.example.com --json
```
These command-line options correspond to configuration parameters documented in detail in the [Advanced Configuration Guide](../reference/advanced_configuration.md).

## Example Output

### Success Output (Basic)

```
SUCCESS: Website check successful. Status code: 200
Response time: 0.3456 seconds
```

### Success Output (Verbose)

```
SUCCESS: Website check successful. Status code: 200
Response time: 0.3456 seconds

Raw data:
{
  "url": "https://www.example.com",
  "status_code": 200,
  "expected_status": 200,
  "status_match": true,
  "content_match": true,
  "content_issues": [],
  "response_headers": {
    "Content-Type": "text/html; charset=UTF-8",
    "Server": "nginx",
    "Date": "Mon, 01 Jan 2025 12:00:00 GMT",
    "Content-Length": "12345"
  },
  "response_size": 12345,
  "redirect_history": []
}
```

### Error Output (Status Code Mismatch)

```
ERROR: Website check failed. Expected status: 200, actual: 404
Response time: 0.2345 seconds
```

### Warning Output (Content Issues)

```
WARNING: Website accessible but content issues detected: Expected content 'Welcome' not found
Response time: 0.3456 seconds
```

### Connection Error Output

```
ERROR: Connection error: Connection refused
Response time: 0.0000 seconds
```

## Exit Codes

The `website` command returns the following exit codes:

- `0`: Success (check passed)
- `1`: Warning (check has warnings)
- `2`: Error (check failed)
- Other non-zero: Command-line error or exception

## Troubleshooting

### Common Issues

1. **"Connection refused"**
   
   This usually means the server is not accessible or not running. Check if the URL is correct and the server is online.

2. **"Connection timed out"**
   
   The server is taking too long to respond. Try increasing the timeout with `--timeout 60`.

3. **"SSL Certificate Verification Failed"**
   
   The website has an invalid SSL certificate. You can bypass this check with `--no-verify`, but this is not recommended for production monitoring.

4. **"Basic authentication failed"**
   
   The provided username/password is incorrect. Check the credentials and try again.

5. **"Incorrect content type for JSON body"**
   
   When sending JSON data, make sure to include the `Content-Type: application/json` header:
   
   ```bash
   monitorpy website https://api.example.com --method POST \
     --header "Content-Type: application/json" \
     --body '{"key":"value"}'
   ```