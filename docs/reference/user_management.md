# User Management

This document describes the user management functionality in MonitorPy.

## Overview

MonitorPy includes a comprehensive user management system with the following features:

- User authentication via JWT tokens and API keys
- Role-based access control (admin and regular users)
- Admin-only user management API
- API key generation and management

## User Roles

MonitorPy supports two user roles:

- **Regular Users**: Can access monitoring features, but cannot manage other users
- **Admin Users**: Have full access, including user management capabilities

## Creating the First Admin User

To create the first admin user, use the provided script:

```bash
# Interactive usage
./create_admin.py

# Command-line usage
./create_admin.py --username admin --email admin@example.com --password securepassword
```

This script will create a new admin user and generate an API key automatically.

## User Management API (Admin Only)

The following API endpoints are available for user management:

| Endpoint | Method | Description | Admin Only |
|----------|--------|-------------|------------|
| `/api/v1/users/` | GET | List all users | Yes |
| `/api/v1/users/{user_id}` | GET | Get user details | Yes |
| `/api/v1/users/` | POST | Create a new user | Yes |
| `/api/v1/users/{user_id}` | PUT | Update a user | Yes |
| `/api/v1/users/{user_id}` | DELETE | Delete a user | Yes |
| `/api/v1/users/{user_id}/api-key` | POST | Generate a new API key | Yes |
| `/api/v1/users/me` | GET | Get current user info | No |

### Example Requests

#### List Users (Admin)

```bash
curl -X GET "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer $TOKEN"
```

#### Create User (Admin)

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "securepassword",
    "is_admin": false
  }'
```

#### Generate API Key (Admin)

```bash
curl -X POST "http://localhost:8000/api/v1/users/USER_ID/api-key" \
  -H "Authorization: Bearer $TOKEN"
```

#### Get Current User Info

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

## API Authentication

There are two ways to authenticate with the API:

### 1. JWT Token Authentication

```bash
# Get JWT token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -d "username=your_email@example.com&password=yourpassword"

# Use the token
curl -X GET "http://localhost:8000/api/v1/checks" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. API Key Authentication

```bash
curl -X GET "http://localhost:8000/api/v1/checks" \
  -H "X-API-Key: YOUR_API_KEY"
```

## Security Best Practices

- Always use HTTPS in production
- Rotate API keys regularly
- Limit the number of admin users
- Use strong passwords
- Enable authentication in production environments

## Integrating with External Systems

For integrating with external systems, API keys are recommended over JWT tokens as they don't expire. However, API keys should be treated as sensitive information and stored securely.

## Docker Environment Variables

You can configure authentication behavior with environment variables in docker-compose.yml:

```yaml
environment:
  # Authentication configuration
  - SECRET_KEY=your_secret_key_for_jwt
  - JWT_SECRET_KEY=your_jwt_secret_key
  - AUTH_REQUIRED=true  # Enable/disable authentication
  - JWT_TOKEN_EXPIRE_MINUTES=10080  # 7 days
```

## Troubleshooting

### Authentication Issues

- Error 401 (Unauthorized): Check your token or API key
- Error 403 (Forbidden): You don't have permission to access this resource (admin rights needed)

### User Management Issues

- Cannot delete your own account: This is by design for security reasons
- Email or username already exists: Choose a different one