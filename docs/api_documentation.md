# MonitorPy API Documentation

## Overview

MonitorPy provides a modern REST API built with FastAPI that exposes all monitoring functionality. The API supports:

- Comprehensive OpenAPI documentation (Swagger UI)
- JSON request/response format
- JWT-based authentication
- Pagination, filtering, and sorting for list endpoints
- Support for parallel check execution
- Async/await for improved performance
- Redis integration for caching and background tasks

## Base URL

All API endpoints are prefixed with `/api/v1/`.

## Authentication

The API uses JWT (JSON Web Token) for authentication:

1. Obtain a token by sending credentials to `/api/v1/auth/token` or `/api/v1/auth/login`
2. Include the token in subsequent requests in the `Authorization` header:
   ```
   Authorization: Bearer <your_token>
   ```

### Authentication Endpoints

#### `POST /api/v1/auth/token`

OAuth2 password flow authentication.

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJ...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "admin",
    "email": "user@example.com",
    "is_admin": true
  }
}
```

#### `POST /api/v1/auth/login`

Alternative login endpoint accepting regular JSON.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:** Same as the token endpoint.

## Check Endpoints

Checks represent monitoring configurations that can be executed.

### `GET /api/v1/checks`

Get a list of all configured checks.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `enabled`: Filter by enabled status (true/false)
- `plugin_type`: Filter by plugin type

**Response:**
```json
{
  "checks": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Example Website Check",
      "plugin_type": "website",
      "config": {
        "url": "https://example.com",
        "expected_status": 200
      },
      "enabled": true,
      "schedule": "every 5 minutes",
      "last_run": "2023-04-01T12:00:00Z",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-04-01T12:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 1,
  "pages": 1
}
```

### `GET /api/v1/checks/{check_id}`

Get a specific check configuration.

**Response:** A single check object.

### `POST /api/v1/checks`

Create a new check configuration.

**Request Body:**
```json
{
  "name": "New Website Check",
  "plugin_type": "website",
  "config": {
    "url": "https://example.com",
    "expected_status": 200
  },
  "enabled": true,
  "schedule": "every 5 minutes"
}
```

**Response:** The created check object.

### `PUT /api/v1/checks/{check_id}`

Update an existing check configuration.

**Request Body:**
```json
{
  "name": "Updated Website Check",
  "config": {
    "url": "https://example.com",
    "expected_status": 200,
    "timeout": 30
  }
}
```

**Response:** The updated check object.

### `DELETE /api/v1/checks/{check_id}`

Delete a check configuration.

**Response:** HTTP 204 No Content

### `POST /api/v1/checks/{check_id}/run`

Run a check immediately and store the result.

**Response:** The check result object.

### `POST /api/v1/checks/run`

Run an ad-hoc check without storing configuration.

**Request Body:**
```json
{
  "plugin_type": "website",
  "config": {
    "url": "https://example.com",
    "expected_status": 200
  }
}
```

**Response:** The check result object.

## Result Endpoints

Results store the outcome of check executions.

### `GET /api/v1/results`

Get a list of check results.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `check_id`: Filter by check ID
- `status`: Filter by status (success, warning, error)
- `from_date`: Filter by execution date (ISO format)
- `to_date`: Filter by execution date (ISO format)

**Response:**
```json
{
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "check_id": "456e7890-e12b-34d5-a678-426614174000",
      "status": "success",
      "message": "Website responded with status 200",
      "response_time": 0.342,
      "raw_data": {
        "status_code": 200,
        "headers": {
          "content-type": "text/html"
        }
      },
      "executed_at": "2023-04-01T12:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 1,
  "pages": 1
}
```

### `GET /api/v1/results/{result_id}`

Get a specific check result.

**Response:** A single result object.

### `GET /api/v1/results/check/{check_id}`

Get results for a specific check.

**Query Parameters:** Same as for `GET /api/v1/results`

**Response:** Similar to `GET /api/v1/results` but filtered to a specific check.

### `GET /api/v1/results/summary`

Get a summary of check results.

**Query Parameters:**
- `period`: Time period for the summary (day, week, month)

**Response:**
```json
{
  "period": "day",
  "from_date": "2023-03-31T12:00:00Z",
  "to_date": "2023-04-01T12:00:00Z",
  "total_checks": 100,
  "statuses": {
    "success": {
      "count": 95,
      "percent": 95.0
    },
    "warning": {
      "count": 3,
      "percent": 3.0
    },
    "error": {
      "count": 2,
      "percent": 2.0
    }
  }
}
```

## Plugin Endpoints

Plugins provide different types of monitoring capabilities.

### `GET /api/v1/plugins`

Get a list of all available plugins.

**Response:**
```json
{
  "plugins": [
    {
      "name": "website",
      "description": "Check website availability and status",
      "required_config": {
        "url": "URL to check"
      },
      "optional_config": {
        "expected_status": "Expected HTTP status code (default: 200)",
        "timeout": "Request timeout in seconds (default: 10)"
      }
    }
  ],
  "count": 1
}
```

### `GET /api/v1/plugins/{plugin_name}`

Get information about a specific plugin.

**Response:** A single plugin object.

## Batch Endpoints

Batch operations allow executing multiple checks in parallel.

### `POST /api/v1/batch/run`

Run multiple checks in parallel.

**Request Body:**
```json
{
  "checks": ["check_id_1", "check_id_2", "check_id_3"],
  "max_workers": 5,
  "timeout": 30
}
```

**Response:**
```json
{
  "results": [
    {
      "check_id": "check_id_1",
      "result": {
        "status": "success",
        "message": "Website responded with status 200",
        "response_time": 0.342,
        "raw_data": {
          "status_code": 200,
          "headers": {
            "content-type": "text/html"
          }
        }
      }
    }
  ]
}
```

### `POST /api/v1/batch/run-ad-hoc`

Run multiple ad-hoc checks in parallel without storing results.

**Request Body:**
```json
{
  "checks": [
    {
      "plugin_type": "website",
      "config": {
        "url": "https://example.com",
        "expected_status": 200
      }
    },
    {
      "plugin_type": "dns",
      "config": {
        "domain": "example.com",
        "record_type": "A"
      }
    }
  ],
  "max_workers": 5,
  "timeout": 30
}
```

**Response:** Similar to `POST /api/v1/batch/run` but with ad-hoc check configs.

## API Documentation

Interactive API documentation is available at:

- Swagger UI: `/api/v1/docs`
- ReDoc: `/api/v1/redoc`

These documentation interfaces allow you to explore and test the API directly in your browser.

## Redis Integration

The API integrates with Redis for enhanced performance and reliability:

- Response caching for frequently accessed data
- Health check endpoint reports Redis availability status
- Graceful degradation when Redis is unavailable
- Type-safe caching with Pydantic models

For details on Redis usage, see [Redis Usage Documentation](./reference/redis_usage.md).