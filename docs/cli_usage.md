# CLI Usage

MonitorPy provides a command-line interface (CLI) for running monitoring checks. This document describes the available commands and options.

## Global Options

These options can be used with any MonitorPy command:

```
--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                      Set logging level (default: INFO)
--log-file LOG_FILE  Log file path (if not specified, logs to stdout only)
--config CONFIG      Path to configuration file
```

## Command-Specific Parallel Options

All the monitoring commands support parallel execution when checking multiple targets:

```
--parallel           Run multiple checks in parallel (when using a file of targets)
--max-workers MAX    Maximum number of worker threads for parallel execution
```

Note: For DNS checks, use `--parallel-workers` instead of `--max-workers` to avoid confusion with the DNS-specific `--max-workers` parameter which is used for propagation checks within the DNS plugin.

The parallel execution mode is automatically used when providing a file of targets (--sites, --hosts, --servers, --domains), but adding the `--parallel` flag is recommended for clarity.

## Commands

### List Available Plugins

```bash
monitorpy list
```

This command displays all registered monitoring plugins along with their descriptions and configuration requirements.

### Website Monitoring

```bash
monitorpy website [URL] [OPTIONS]
```

Checks if a website is accessible and optionally verifies its content. The URL is optional when using the --sites option for checking multiple URLs.

#### Options

```
URL                   URL to check (optional when using --sites)
--sites SITES_FILE    File containing URLs to check (one per line)
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
--parallel            Run checks in parallel (when using --sites)
--max-workers MAX     Maximum number of worker threads (default: auto)
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
monitorpy ssl [HOSTNAME] [OPTIONS]
```

Checks the validity and expiration of an SSL certificate. The HOSTNAME is optional when using the --hosts option for checking multiple hosts.

#### Options

```
HOSTNAME              Hostname or URL to check (optional when using --hosts)
--hosts HOSTS_FILE    File containing hostnames to check (one per line)
--port PORT           Port number (default: 443)
--timeout TIMEOUT     Connection timeout in seconds (default: 30)
--warning WARNING     Warning threshold in days (default: 30)
--critical CRITICAL   Critical threshold in days (default: 14)
--check-chain         Check certificate chain
--no-verify-hostname  Disable hostname verification
--parallel            Run checks in parallel (when using --hosts)
--max-workers MAX     Maximum number of worker threads (default: auto)
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

Check multiple SSL certificates in parallel:
```bash
# Create a file with hostnames, one per line
echo -e "example.com\ngithub.com\ngoogle.com" > hostnames.txt

# Check all certificates in parallel
monitorpy ssl --hosts hostnames.txt --parallel --max-workers 10 --verbose
```

### DNS Record Monitoring

```bash
monitorpy dns [DOMAIN] [OPTIONS]
```

Checks DNS records and their propagation. The DOMAIN is optional when using the --domains option for checking multiple domains.

#### Options

```
DOMAIN                Domain name to check (optional when using --domains)
--domains DOMAINS_FILE File containing domains to check (one per line)
--type RECORD_TYPE    DNS record type (A, AAAA, MX, CNAME, TXT, NS, etc.) (default: A)
--value VALUE         Expected record value
--subdomain SUBDOMAIN Subdomain to check (e.g., 'www')
--nameserver NAMESERVER Specific nameserver to query
--timeout TIMEOUT     Query timeout in seconds (default: 10)
--check-propagation   Check DNS propagation across multiple resolvers
--resolvers RESOLVERS Custom DNS resolvers to check (space-separated list of IP addresses)
--threshold THRESHOLD Propagation threshold percentage (0-100) (default: 80)
--check-authoritative Check if response is from an authoritative server
--check-dnssec        Check DNSSEC validation
--max-workers MAX     Maximum number of concurrent workers for propagation checks (default: 10)
--parallel            Run checks in parallel (when using --domains)
--parallel-workers MAX Maximum number of worker threads for parallel domain checks
-v, --verbose         Show detailed output
--json                Output results as JSON
```

#### Examples

Basic DNS check:
```bash
monitorpy dns example.com
```

Check specific record type:
```bash
monitorpy dns example.com --type MX
```

Check with expected value:
```bash
monitorpy dns example.com --type A --value "93.184.216.34"
```

Check propagation across resolvers:
```bash
monitorpy dns example.com --check-propagation --threshold 90
```

Check multiple domains in parallel:
```bash
# Create a file with domains
echo -e "example.com\ngithub.com\ngoogle.com" > domains.txt

# Check all domains in parallel (note the use of --parallel-workers instead of --max-workers)
monitorpy dns --domains domains.txt --parallel --parallel-workers 10 --type A
```

### Mail Server Monitoring

```bash
monitorpy mail [HOSTNAME] [OPTIONS]
```

Checks mail server connectivity and functionality. The HOSTNAME is optional when using the --servers option for checking multiple servers.

#### Options

```
HOSTNAME              Mail server hostname (optional when using --servers)
--servers SERVERS_FILE File containing server hostnames to check (one per line)
--protocol PROTOCOL   Mail protocol to check (smtp, imap, pop3) (default: smtp)
--port PORT           Server port (defaults to standard port for protocol)
--username USERNAME   Username for authentication
--password PASSWORD   Password for authentication
--ssl                 Use SSL connection
--tls                 Use TLS connection (SMTP only)
--timeout TIMEOUT     Connection timeout in seconds (default: 30)
--send-test           Send test email (SMTP only)
--from FROM_EMAIL     From email address (for test email)
--to TO_EMAIL         To email address (for test email)
--basic-check         Perform basic connectivity check without authentication
--no-resolve-mx       Don't resolve MX records for domain (resolve_mx is enabled by default)
--parallel            Run checks in parallel (when using --servers)
--max-workers MAX     Maximum number of worker threads (default: auto)
-v, --verbose         Show detailed output
--json                Output results as JSON
```

#### Examples

Basic mail server check:
```bash
monitorpy mail smtp.example.com
```

Check with authentication:
```bash
monitorpy mail mail.example.com --protocol imap --username user@example.com --password secret
```

Check SMTP with SSL:
```bash
monitorpy mail smtp.example.com --ssl --port 465
```

Send test email:
```bash
monitorpy mail smtp.example.com --send-test --from sender@example.com --to recipient@example.com
```

Check multiple mail servers in parallel:
```bash
# Create a file with mail servers
echo -e "smtp.gmail.com\nsmtp.yahoo.com\nsmtp.outlook.com" > mailservers.txt

# Check all mail servers in parallel
monitorpy mail --servers mailservers.txt --parallel --max-workers 5 --protocol smtp --basic-check
```

## Exit Codes

MonitorPy CLI commands return the following exit codes:

- `0`: Success (check passed)
- `1`: Warning (check has warnings)
- `2`: Error (check failed)
- Other non-zero: Command-line error or exception

These exit codes can be used in scripts to automate actions based on check results.
