# CLI Usage

MonitorPy provides a command-line interface (CLI) for running monitoring checks. This document describes the available commands and options.

## Global Options

These options can be used with any MonitorPy command:

```
--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                      Set logging level (default: INFO)
--log-file LOG_FILE  Log file path (if not specified, logs to stdout only)
```

## Commands

### List Available Plugins

```bash
monitorpy list
```

This command displays all registered monitoring plugins along with their descriptions and configuration requirements.

### Website Monitoring

```bash
monitorpy website URL [OPTIONS]
```

Checks if a website is accessible and optionally verifies its content.

#### Options

```
URL                   URL to check
--timeout TIMEOUT     Request timeout in seconds (default: 30)
--status STATUS       Expected HTTP status code (default: 200)
--method METHOD       HTTP method (GET, POST, etc.) (default: GET)
--header HEADER       HTTP header in format 'Name: Value' (can be used multiple times)
--body BODY           Request body data
--content CONTENT     Content that should be present in the response
--no-content CONTENT  Content that should NOT be present in the response
--auth-username USERNAME
                      Username for basic authentication
--auth-password PASSWORD
                      Password for basic authentication
--no-verify           Disable SSL certificate verification
--no-redirect         Disable following redirects
-v, --verbose         Show detailed output
--json                Output results as JSON
```

#### Examples

Basic website check:
```bash
monitorpy website https://www.example.com
```

Check with specific content requirement:
```bash
monitorpy website https://www.example.com --content "Welcome to Example"
```

Check with custom HTTP header:
```bash
monitorpy website https://api.example.com --header "Authorization: Bearer token123"
```

POST request with JSON body:
```bash
monitorpy website https://api.example.com --method POST --body '{"key":"value"}' --header "Content-Type: application/json" --status 201
```

Output detailed results as JSON:
```bash
monitorpy website https://www.example.com --verbose --json
```

### SSL Certificate Monitoring

```bash
monitorpy ssl HOSTNAME [OPTIONS]
```

Checks the validity and expiration of an SSL certificate.

#### Options

```
HOSTNAME              Hostname or URL to check
--port PORT           Port number (default: 443)
--timeout TIMEOUT     Connection timeout in seconds (default: 30)
--warning WARNING     Warning threshold in days (default: 30)
--critical CRITICAL   Critical threshold in days (default: 14)
--check-chain         Check certificate chain
--no-verify-hostname  Disable hostname verification
-v, --verbose         Show detailed output
--json                Output results as JSON
```

#### Examples

Basic SSL check:
```bash
monitorpy ssl www.example.com
```

Check with custom thresholds:
```bash
monitorpy ssl www.example.com --warning 60 --critical 30
```

Check SSL on non-standard port:
```bash
monitorpy ssl www.example.com --port 8443
```

Check with certificate chain details:
```bash
monitorpy ssl www.example.com --check-chain --verbose
```

## Exit Codes

MonitorPy CLI commands return the following exit codes:

- `0`: Success (check passed)
- `1`: Warning (check has warnings)
- `2`: Error (check failed)
- Other non-zero: Command-line error or exception

These exit codes can be used in scripts to automate actions based on check results.
