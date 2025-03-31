# Website Plugin Configuration

This document describes the configuration options for the website monitoring plugin in MonitorPy.

## Configuration Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | URL to check (must start with http:// or https://) |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | integer | 30 | Request timeout in seconds |
| `expected_status` | integer | 200 | Expected HTTP status code |
| `method` | string | GET | HTTP method (GET, POST, etc.) |
| `headers` | dictionary | {} | Dictionary of HTTP headers to send |
| `body` | string | None | Request body for POST/PUT requests |
| `auth_username` | string | None | Username for basic authentication |
| `auth_password` | string | None | Password for basic authentication |
| `verify_ssl` | boolean | True | Whether to verify SSL certificates |
| `follow_redirects` | boolean | True | Whether to follow HTTP redirects |
| `expected_content` | string | None | Content that should be present in the response |
| `unexpected_content` | string | None | Content that should NOT be present in the response |

## HTTP Methods

The `method` parameter supports standard HTTP methods:

- `GET`: Retrieve data from the server
- `POST`: Submit data to the server
- `PUT`: Update a resource on the server
- `DELETE`: Remove a resource from the server
- `HEAD`: Retrieve headers only
- `OPTIONS`: Get supported methods for a resource
- `PATCH`: Apply partial modifications to a resource

## Status Codes

The `expected_status` parameter can be set to any standard HTTP status code. Common values include:

- `200`: OK
- `201`: Created
- `204`: No Content
- `301`: Moved Permanently
- `302`: Found (temporary redirect)
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Content Checking

When using `expected_content` or `unexpected_content`, the plugin will check the response body for the specified text:

- If `expected_content` is specified, the check will produce a warning if the text is not found
- If `unexpected_content` is specified, the check will produce a warning if the text is found

These checks operate independently of the status code check, meaning a website can return the expected status code but still generate a warning if content checks fail.

## Configuration Examples

### Basic Website Check

```python
config = {
    "url": "https://www.example.com",
    "timeout": 10,
    "expected_status": 200
}
```

### Content Verification

```python
config = {
    "url": "https://www.example.com",
    "expected_content": "Welcome to Example",
    "unexpected_content": "Error"
}
```

### Basic Authentication

```python
config = {
    "url": "https://private.example.com",
    "auth_username": "user",
    "auth_password": "pass"
}
```

### Custom Headers and POST Request

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

### Disabling Redirect Following

```python
config = {
    "url": "https://example.com/redirect",
    "follow_redirects": False,
    "expected_status": 302  # Expect a redirect status
}
```

### Ignoring SSL Certificate Errors

```python
config = {
    "url": "https://self-signed.example.com",
    "verify_ssl": False
}
```

### Comprehensive Check

```python
config = {
    "url": "https://api.example.com/data",
    "method": "POST",
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    },
    "body": '{"key": "value"}',
    "expected_status": 201,
    "expected_content": "success",
    "timeout": 5,
    "verify_ssl": True,
    "follow_redirects": True
}
```