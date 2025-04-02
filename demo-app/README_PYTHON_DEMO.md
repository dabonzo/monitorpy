# MonitorPy Python Demo Application

This demo application demonstrates how to use the MonitorPy API to perform various checks on websites, SSL certificates, and DNS records.

## Features

- Connects to the MonitorPy FastAPI backend
- Performs random checks on a list of popular websites
- Supports website status, SSL certificate, and DNS record checks
- Runs checks in batches using the batch API endpoint
- Displays results with color-coded status indicators
- Supports continuous monitoring or one-time checks

## Requirements

- Python 3.8+
- `requests` library
- Running MonitorPy API (via Docker or directly)

## Usage

Make the script executable:

```bash
chmod +x demo_checker.py
```

### Basic Usage

Run continuous checks every 60 seconds:

```bash
./demo_checker.py
```

### Options

- `--hosts`: Comma-separated list of hosts to check (defaults to popular websites)
- `--api`: MonitorPy API base URL (default: http://localhost:8000/api/v1)
- `--interval`: Interval between check batches in seconds (default: 60)
- `--batch-size`: Number of checks per batch (default: 5, only for one-time runs)
- `--once`: Run checks once and exit (default: run continuously)
- `--email`: Email for API authentication
- `--password`: Password for API authentication
- `--api-key`: API key for authentication (alternative to email/password)
- `--auth-disable`: Attempt to disable API authentication in Docker container

### Examples

Run a single batch of 10 checks:

```bash
./run_demo.sh --once --batch-size=10
```

Check specific hosts every 30 seconds:

```bash
./run_demo.sh --hosts=github.com,google.com,cloudflare.com --interval=30
```

Use default Docker container authentication (recommended):

```bash
# The Docker container creates a default admin user
./run_demo.sh --email=admin@example.com --password=adminpassword
```

Use API key authentication (displayed at container startup):

```bash
./run_demo.sh --api-key=your-api-key-here
```

Try to disable authentication (for development environments):

```bash
./run_demo.sh --auth-disable
```

## Output

The application displays results in a human-readable format:

```
===== MonitorPy Check Results (2025-04-02 12:34:56) =====
SUCCESS | WEBSITE | github.com | Website is reachable | 0.567s
WARNING | SSL | cloudflare.com | Certificate expires in 22 days | 0.345s
ERROR | DNS | example.com | Failed to resolve DNS record | 1.234s

Summary: 3 checks completed
  Success: 1 (33.3%)
  Warning: 1 (33.3%)
  Error: 1 (33.3%)
==================================================
```

## Using with Docker

If you're running the MonitorPy API with Docker, you may need to adjust the API host:

```bash
./demo_checker.py --api http://host.docker.internal:8000/api/v1
```