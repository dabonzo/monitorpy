# API Modernization

## Overview

MonitorPy has modernized its API implementation by migrating from Flask to FastAPI. This document outlines the changes, benefits, and migration process.

## Migration from Flask to FastAPI

### Motivation

The migration from Flask to FastAPI was motivated by several factors:

- **Improved Developer Experience**: FastAPI provides automatic API documentation, request validation, and dependency injection
- **Performance**: FastAPI's asynchronous capabilities offer better performance under load
- **Type Safety**: Integration with Pydantic provides strong type checking and validation
- **Modern Features**: Support for async/await, dependency injection, and OpenAPI documentation

### Key Changes

1. **API Implementation**:
   - Replaced Flask with FastAPI for all API endpoints
   - Migrated from Flask's route decorators to FastAPI's router approach
   - Added comprehensive request and response models using Pydantic

2. **Authentication and Authorization**:
   - Updated JWT authentication to use FastAPI's security utilities
   - Improved token validation and user authentication flow
   - Added role-based access control with admin and regular user roles
   - Implemented API key authentication for service integrations
   - Added admin-only user management API

3. **Database Integration**:
   - Modernized SQLAlchemy integration with FastAPI's dependency injection
   - Improved database session management

4. **Caching**:
   - Added Redis integration for response caching
   - Implemented a generic caching system for Pydantic models

5. **Documentation**:
   - Added automatic OpenAPI documentation with Swagger UI
   - Improved API reference documentation

## Directory Structure

The new FastAPI implementation is organized as follows:

```
monitorpy/
├── fastapi_api/
│   ├── main.py           # FastAPI application
│   ├── routes/           # API route handlers
│   │   ├── auth.py       # Authentication routes
│   │   ├── batch.py      # Batch processing routes
│   │   ├── checks.py     # Check configuration routes
│   │   ├── health.py     # Health check routes
│   │   ├── plugins.py    # Plugin information routes
│   │   ├── results.py    # Check results routes
│   │   └── users.py      # User management routes (admin only)
│   ├── models/           # Database models and Pydantic schemas
│   │   ├── check.py      # Check models
│   │   ├── result.py     # Result models
│   │   └── user.py       # User models
│   ├── database.py       # Database configuration
│   ├── deps.py           # Dependency injection components
│   ├── config.py         # Application configuration
│   └── redis.py          # Redis integration for caching
```

## Benefits of FastAPI

The FastAPI implementation provides several advantages:

1. **Automatic Documentation**:
   - Interactive API documentation via Swagger UI at `/api/v1/docs`
   - Alternative ReDoc interface at `/api/v1/redoc`

2. **Request Validation**:
   - Automatic validation of request bodies, query parameters, and path parameters
   - Clear error messages when validation fails

3. **Type Safety**:
   - Pydantic models ensure type safety throughout the codebase
   - Type hints improve IDE support and reduce bugs

4. **Performance**:
   - Async/await support for I/O-bound operations
   - Starlette ASGI server for better performance
   - Redis caching for frequently accessed data

5. **Dependency Injection**:
   - Clean separation of concerns
   - Improved testability with easy mocking of dependencies

## Integration with Redis

The FastAPI implementation includes Redis integration for caching:

- Response caching for frequently accessed data
- Type-safe caching with Pydantic models
- Graceful degradation when Redis is unavailable
- Foundation for background task processing

Redis integration can be configured through environment variables:

```
REDIS_URL=redis://redis:6379/0
USE_REDIS_CACHE=true
CACHE_EXPIRATION=300  # Cache TTL in seconds
```

## Migrating from Flask

For users who have integrated with the previous Flask API:

1. **Endpoint URLs**: All API endpoint URLs remain the same (`/api/v1/...`)
2. **Request/Response Format**: JSON request and response formats remain consistent
3. **Authentication**: JWT tokens continue to work with the same format
4. **Port Change**: The default port has changed from 5000 to 8000

## Running the FastAPI API

To run the FastAPI API:

```bash
# Using the provided script
./run_fastapi.py

# Directly with uvicorn
uvicorn monitorpy.fastapi_api.main:app --host 0.0.0.0 --port 8000 --reload

# Using the CLI
monitorpy api --host 0.0.0.0 --port 8000 --reload
```

## Docker Support

Docker support has been updated for the FastAPI implementation:

```bash
# Using docker-compose
docker-compose up

# Building and running the API container
docker build -f docker/api/Dockerfile -t monitorpy-api .
docker run -p 8000:8000 monitorpy-api
```

## Testing

The FastAPI implementation includes comprehensive tests:

- Unit tests for API endpoints
- Authentication testing
- Mock database and Redis for isolated testing

To run the tests:

```bash
pytest tests/test_fastapi*.py
```

## User Management

The FastAPI implementation includes a comprehensive user management system:

### User Roles

- **Regular Users**: Can access monitoring features but cannot manage other users
- **Admin Users**: Have full access, including user management capabilities

### User Management API

Admin-only endpoints for managing users:

- List users
- Create new users
- Update existing users
- Delete users
- Generate API keys

### API Authentication Methods

Two authentication methods are supported:

1. **JWT Token Authentication**:
   - Obtained via `/api/v1/auth/token` or `/api/v1/auth/login`
   - Used in Authorization header: `Authorization: Bearer <token>`
   - Expires after configurable time period

2. **API Key Authentication**:
   - More suitable for service-to-service communication
   - Generated by admin users via the user management API
   - Used in X-API-Key header: `X-API-Key: <api_key>`
   - Does not expire by default

### Initial Admin Setup

A convenient script is provided to create the first admin user:

```bash
./create_admin.py
```

For more details, see the [User Management](../reference/user_management.md) documentation.