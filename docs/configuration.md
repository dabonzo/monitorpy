# Configuration

This document describes the configuration options for each monitoring plugin in MonitorPy and general system configuration.

## General Configuration Structure

Each plugin in MonitorPy accepts a configuration dictionary that controls its behavior. When using the command-line interface, these configurations are specified as command-line arguments. If you're using MonitorPy programmatically, you'll pass these configurations as dictionaries.

## Website Status Plugin

The website status plugin (`website_status`) monitors website availability and content.

### Required Configuration

| Parameter | Description |
|-----------|-------------|
| `url` | URL to check (must start with http:// or https://) |

### Optional Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `timeout` | Request timeout in seconds | 30 |
| `expected_status` | Expected HTTP status code | 200 |
| `method` | HTTP method (GET, POST, etc.) | GET |
| `headers` | Dictionary of HTTP headers to send | {} |
| `body` | Request body for POST/PUT requests | None |
| `auth_username` | Username for basic authentication | None |
| `auth_password` | Password for basic authentication | None |
| `verify_ssl` | Whether to verify SSL certificates | True |
| `follow_redirects` | Whether to follow HTTP redirects | True |
| `expected_content` | Content that should be present in the response | None |
| `unexpected_content` | Content that should NOT be present in the response | None |

### Examples

Basic configuration:
```python
config = {
    "url": "https://www.example.com",
    "timeout": 10,
    "expected_status": 200
}
```

Content check configuration:
```python
config = {
    "url": "https://www.example.com",
    "expected_content": "Welcome to Example",
    "unexpected_content": "Error"
}
```

Authentication configuration:
```python
config = {
    "url": "https://private.example.com",
    "auth_username": "user",
    "auth_password": "pass"
}
```

Custom headers and POST request:
```python
config = {
    "url": "https://api.example.com/data",
    "method": "POST",
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    },
    "body": '{"key": "value"}',
    "expected_status": 201
}
```

## SSL Certificate Plugin

The SSL certificate plugin (`ssl_certificate`) checks SSL certificate validity and expiration.

### Required Configuration

| Parameter | Description |
|-----------|-------------|
| `hostname` | Hostname or URL to check |

### Optional Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `port` | Port number for the SSL connection | 443 |
| `timeout` | Connection timeout in seconds | 30 |
| `warning_days` | Days before expiration to trigger a warning | 30 |
| `critical_days` | Days before expiration to trigger a critical alert | 14 |
| `check_chain` | Whether to check certificate chain details | False |
| `verify_hostname` | Whether to verify the hostname in the certificate | True |

### Examples

Basic configuration:
```python
config = {
    "hostname": "www.example.com",
    "timeout": 10
}
```

Custom thresholds configuration:
```python
config = {
    "hostname": "www.example.com",
    "warning_days": 60,
    "critical_days": 30
}
```

Non-standard port configuration:
```python
config = {
    "hostname": "secure.example.com",
    "port": 8443
}
```

## Using Configuration Programmatically

When using MonitorPy from your code, you can pass configurations directly to the `run_check` function:

```python
from monitorpy import run_check

# Configure the check
config = {
    "url": "https://www.example.com",
    "timeout": 10,
    "expected_content": "Welcome"
}

# Run the check
result = run_check("website_status", config)

# Use the result
if result.is_success():
    print(f"Check passed: {result.message}")
else:
    print(f"Check failed: {result.message}")
```

## API Authentication Configuration

MonitorPy API supports optional authentication. When enabled, API endpoints require either JWT tokens or API keys.

### Enabling Authentication

Authentication is disabled by default in development but enabled in production. To control this:

1. Set the environment variable:
   ```bash
   export AUTH_REQUIRED=true
   ```

2. Or in the docker-compose.yml:
   ```yaml
   environment:
     - AUTH_REQUIRED=true
   ```

3. In configuration files:
   ```yaml
   api:
     auth_required: true
     jwt_secret_key: your_secret_key
     secret_key: your_flask_secret_key
   ```

### User Management

MonitorPy includes CLI commands for user management:

#### Create a User

```bash
# Create regular user
python -m monitorpy.cli user create --username user1 --email user1@example.com --password password

# Create admin user
python -m monitorpy.cli user create --username admin --email admin@example.com --password password --admin

# In Docker container
docker-compose exec api python -m monitorpy.cli user create --username admin --email admin@example.com --password password --admin
```

#### List, Update, and Delete Users

```bash
# List all users
python -m monitorpy.cli user list

# Show API keys
python -m monitorpy.cli user list --show-keys

# Reset password
python -m monitorpy.cli user reset-password username --password new_password

# Generate API key
python -m monitorpy.cli user generate-key username

# Delete user
python -m monitorpy.cli user delete username
```

### Using Authentication

When authentication is enabled, you can access the API using either JWT tokens or API keys:

```bash
# Get JWT token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# Use JWT token in subsequent requests
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:5000/api/v1/checks

# Alternatively, use API key
curl -H "X-API-Key: your-api-key" \
  http://localhost:5000/api/v1/checks
```
