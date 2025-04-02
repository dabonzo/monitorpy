# MonitorPy API Reference

This document provides detailed information about the MonitorPy API endpoints, request formats, and response structures for Laravel integration.

## Base URL

All API endpoints are relative to the base MonitorPy API URL:

```
http://your-monitorpy-server:8000
```

## Authentication

Most API endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer your_jwt_token
```

See the [Authentication](authentication.md) section for details on obtaining tokens.

## Response Format

All API responses are returned in JSON format with a consistent structure:

```json
{
  "status": "success",  // or "error"
  "message": "Operation completed successfully",
  "data": { ... },  // Response data or null
  "meta": {  // Pagination info (when applicable)
    "page": 1,
    "per_page": 20,
    "total": 150
  }
}
```

## Error Handling

Error responses use HTTP status codes and include descriptive messages:

```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": {
    "hostname": ["The hostname field is required"]
  },
  "data": null
}
```

## Endpoints

### Health Check

```
GET /health
```

Returns the API health status. This endpoint doesn't require authentication.

**Response Example:**
```json
{
  "status": "success",
  "message": "API is operational",
  "data": {
    "version": "0.2.0",
    "uptime": "2d 4h 30m",
    "database": "connected"
  }
}
```

### Plugins

#### List Plugins

```
GET /plugins
```

Returns a list of available monitoring plugins.

**Parameters:**
- `?type=PLUGIN_TYPE` - Filter by plugin type

**Response Example:**
```json
{
  "status": "success",
  "data": {
    "plugins": [
      {
        "id": "website_status",
        "name": "Website Status",
        "description": "Checks website availability and content",
        "required_config": ["url"],
        "optional_config": ["timeout", "expected_status", "follow_redirects"]
      },
      {
        "id": "ssl_certificate",
        "name": "SSL Certificate",
        "description": "Checks SSL/TLS certificates",
        "required_config": ["hostname"],
        "optional_config": ["port", "timeout", "warning_days", "critical_days"]
      }
    ]
  }
}
```

#### Get Plugin Details

```
GET /plugins/{plugin_id}
```

Returns detailed information about a specific plugin.

**Response Example:**
```json
{
  "status": "success",
  "data": {
    "id": "website_status",
    "name": "Website Status",
    "description": "Checks website availability and content",
    "version": "1.2.0",
    "required_config": ["url"],
    "optional_config": [
      {
        "name": "timeout",
        "type": "integer",
        "default": 30,
        "description": "Request timeout in seconds"
      },
      {
        "name": "expected_status",
        "type": "integer",
        "default": 200,
        "description": "Expected HTTP status code"
      }
    ],
    "example_config": {
      "url": "https://example.com",
      "timeout": 30,
      "expected_status": 200
    }
  }
}
```

### Checks

#### List Checks

```
GET /checks
```

Returns a list of configured monitoring checks.

**Parameters:**
- `?plugin=PLUGIN_ID` - Filter by plugin type
- `?status=STATUS` - Filter by status (active, paused)
- `?page=PAGE` - Page number for pagination
- `?per_page=PER_PAGE` - Items per page (default: 20)

**Response Example:**
```json
{
  "status": "success",
  "data": {
    "checks": [
      {
        "id": 1,
        "name": "Example Website",
        "plugin": "website_status",
        "config": {
          "url": "https://example.com",
          "timeout": 30
        },
        "status": "active",
        "last_run": "2023-05-30T14:22:15Z",
        "last_result": "success",
        "created_at": "2023-05-01T09:15:22Z",
        "updated_at": "2023-05-30T14:22:15Z"
      }
    ]
  },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 45
  }
}
```

#### Create Check

```
POST /checks
```

Creates a new monitoring check.

**Request Body:**
```json
{
  "name": "Company Website",
  "plugin": "website_status",
  "config": {
    "url": "https://company.com",
    "timeout": 30,
    "expected_status": 200
  },
  "interval": 300,  // Check every 5 minutes
  "status": "active"
}
```

**Response Example:**
```json
{
  "status": "success",
  "message": "Check created successfully",
  "data": {
    "id": 46,
    "name": "Company Website",
    "plugin": "website_status",
    "config": {
      "url": "https://company.com",
      "timeout": 30,
      "expected_status": 200
    },
    "interval": 300,
    "status": "active",
    "created_at": "2023-05-31T10:25:30Z",
    "updated_at": "2023-05-31T10:25:30Z"
  }
}
```

#### Get Check Details

```
GET /checks/{check_id}
```

Returns detailed information about a specific check.

**Response Example:**
```json
{
  "status": "success",
  "data": {
    "id": 46,
    "name": "Company Website",
    "plugin": "website_status",
    "config": {
      "url": "https://company.com",
      "timeout": 30,
      "expected_status": 200
    },
    "interval": 300,
    "status": "active",
    "last_run": "2023-05-31T10:30:15Z",
    "last_result": "success",
    "last_result_data": {
      "status_code": 200,
      "response_time": 0.435,
      "content_match": true
    },
    "created_at": "2023-05-31T10:25:30Z",
    "updated_at": "2023-05-31T10:30:15Z"
  }
}
```

#### Update Check

```
PUT /checks/{check_id}
```

Updates an existing monitoring check.

**Request Body:**
```json
{
  "name": "Updated Website Name",
  "config": {
    "timeout": 60
  },
  "status": "paused"
}
```

**Response Example:**
```json
{
  "status": "success",
  "message": "Check updated successfully",
  "data": {
    "id": 46,
    "name": "Updated Website Name",
    "plugin": "website_status",
    "config": {
      "url": "https://company.com",
      "timeout": 60,
      "expected_status": 200
    },
    "interval": 300,
    "status": "paused",
    "updated_at": "2023-05-31T11:15:22Z"
  }
}
```

#### Delete Check

```
DELETE /checks/{check_id}
```

Deletes a monitoring check.

**Response Example:**
```json
{
  "status": "success",
  "message": "Check deleted successfully",
  "data": null
}
```

#### Run Check Now

```
POST /checks/{check_id}/run
```

Runs a check immediately and returns the result.

**Response Example:**
```json
{
  "status": "success",
  "message": "Check executed successfully",
  "data": {
    "check_id": 46,
    "executed_at": "2023-05-31T11:30:45Z",
    "duration": 0.523,
    "status": "success",
    "message": "Website is accessible",
    "raw_data": {
      "status_code": 200,
      "response_time": 0.523,
      "content_match": true,
      "redirect_count": 0
    }
  }
}
```

### Results

#### List Results

```
GET /results
```

Returns a list of check results.

**Parameters:**
- `?check_id=CHECK_ID` - Filter by check ID
- `?status=STATUS` - Filter by result status (success, warning, error)
- `?from=FROM_DATE` - Filter by date range start (ISO format)
- `?to=TO_DATE` - Filter by date range end (ISO format)
- `?page=PAGE` - Page number for pagination
- `?per_page=PER_PAGE` - Items per page (default: 20)

**Response Example:**
```json
{
  "status": "success",
  "data": {
    "results": [
      {
        "id": 1205,
        "check_id": 46,
        "check_name": "Company Website",
        "plugin": "website_status",
        "status": "success",
        "message": "Website is accessible",
        "response_time": 0.523,
        "executed_at": "2023-05-31T11:30:45Z"
      },
      {
        "id": 1195,
        "check_id": 46,
        "check_name": "Company Website",
        "plugin": "website_status",
        "status": "success",
        "message": "Website is accessible",
        "response_time": 0.487,
        "executed_at": "2023-05-31T11:25:45Z"
      }
    ]
  },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 185
  }
}
```

#### Get Result Details

```
GET /results/{result_id}
```

Returns detailed information about a specific check result.

**Response Example:**
```json
{
  "status": "success",
  "data": {
    "id": 1205,
    "check_id": 46,
    "check_name": "Company Website",
    "plugin": "website_status",
    "status": "success",
    "message": "Website is accessible",
    "response_time": 0.523,
    "raw_data": {
      "url": "https://company.com",
      "status_code": 200,
      "expected_status": 200,
      "status_match": true,
      "content_match": true,
      "content_issues": [],
      "response_headers": {
        "server": "nginx/1.20.0",
        "content-type": "text/html; charset=UTF-8",
        "date": "Wed, 31 May 2023 11:30:45 GMT"
      },
      "response_size": 45320,
      "redirect_history": []
    },
    "executed_at": "2023-05-31T11:30:45Z"
  }
}
```

### Users

#### Current User

```
GET /api/v1/users/me
```

Returns information about the currently authenticated user, including their API key.

**Response Example:**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "username": "admin",
  "email": "admin@example.com",
  "is_admin": true,
  "api_key": "45a201ab-b8f7-4c2d-aeef-3d449c2b78f9",
  "created_at": "2023-01-15T08:30:00Z",
  "updated_at": "2023-05-20T14:22:10Z"
}
```

#### List Users (Admin Only)

```
GET /api/v1/users
```

Returns a list of all users in the system. This endpoint requires admin privileges.

**Parameters:**
- `?skip=0` - Number of records to skip
- `?limit=100` - Maximum number of records to return

**Response Example:**
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "username": "admin",
    "email": "admin@example.com",
    "is_admin": true,
    "created_at": "2023-01-15T08:30:00Z",
    "updated_at": "2023-05-20T14:22:10Z"
  },
  {
    "id": "a97cc10b-32cc-1234-b456-9e02b2c3d123",
    "username": "monitor",
    "email": "monitor@example.com",
    "is_admin": false,
    "created_at": "2023-02-20T10:15:30Z",
    "updated_at": "2023-05-25T09:45:22Z"
  }
]
```

#### Get User Details (Admin Only)

```
GET /api/v1/users/{user_id}
```

Returns detailed information about a specific user. This endpoint requires admin privileges.

**Response Example:**
```json
{
  "id": "a97cc10b-32cc-1234-b456-9e02b2c3d123",
  "username": "monitor",
  "email": "monitor@example.com",
  "is_admin": false,
  "created_at": "2023-02-20T10:15:30Z",
  "updated_at": "2023-05-25T09:45:22Z"
}
```

#### Create User (Admin Only)

```
POST /api/v1/users
```

Creates a new user. This endpoint requires admin privileges.

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "secure_password",
  "is_admin": false
}
```

**Response Example:**
```json
{
  "id": "b87dc10b-12cc-5678-c789-1e02b2c3d456",
  "username": "newuser",
  "email": "newuser@example.com",
  "is_admin": false,
  "created_at": "2023-06-01T15:30:00Z",
  "updated_at": "2023-06-01T15:30:00Z"
}
```

#### Update User (Admin Only)

```
PUT /api/v1/users/{user_id}
```

Updates an existing user. This endpoint requires admin privileges.

**Request Body:**
```json
{
  "username": "updated_username",
  "email": "updated_email@example.com",
  "password": "new_password",
  "is_admin": true
}
```

**Response Example:**
```json
{
  "id": "b87dc10b-12cc-5678-c789-1e02b2c3d456",
  "username": "updated_username",
  "email": "updated_email@example.com",
  "is_admin": true,
  "created_at": "2023-06-01T15:30:00Z",
  "updated_at": "2023-06-01T16:45:00Z"
}
```

#### Delete User (Admin Only)

```
DELETE /api/v1/users/{user_id}
```

Deletes a user. This endpoint requires admin privileges.

**Response Status:** 204 No Content

#### Generate API Key (Admin Only)

```
POST /api/v1/users/{user_id}/api-key
```

Generates a new API key for a user. This endpoint requires admin privileges.

**Response Example:**
```json
{
  "id": "b87dc10b-12cc-5678-c789-1e02b2c3d456",
  "username": "updated_username",
  "email": "updated_email@example.com",
  "is_admin": true,
  "api_key": "98f7e1cd-a6b5-4d3c-bfe2-2a1b9c8d7e6f",
  "created_at": "2023-06-01T15:30:00Z",
  "updated_at": "2023-06-01T17:20:00Z"
}
```

## Batch Operations

```
POST /batch
```

Performs multiple operations in a single request.

**Request Body:**
```json
{
  "operations": [
    {
      "method": "GET",
      "path": "/checks/1"
    },
    {
      "method": "GET", 
      "path": "/checks/2"
    },
    {
      "method": "POST",
      "path": "/checks",
      "body": {
        "name": "New Check",
        "plugin": "ssl_certificate",
        "config": {
          "hostname": "example.com"
        }
      }
    }
  ]
}
```

**Response Example:**
```json
{
  "status": "success",
  "data": {
    "results": [
      {
        "status": "success",
        "data": { /* check 1 data */ }
      },
      {
        "status": "success",
        "data": { /* check 2 data */ }
      },
      {
        "status": "success",
        "message": "Check created successfully",
        "data": { /* new check data */ }
      }
    ]
  }
}
```

## Webhooks

MonitorPy supports webhooks for real-time notifications. Configure webhook endpoints in the API settings.