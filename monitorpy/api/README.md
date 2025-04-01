# MonitorPy API

The MonitorPy API provides a RESTful interface to the MonitorPy monitoring system, allowing you to:
- Retrieve available monitoring plugins
- Create, update, and delete check configurations
- Execute checks on demand
- View historical check results

## API Endpoints

### Health Check
- `GET /api/v1/health`: Get API health status

### Plugins
- `GET /api/v1/plugins`: List all available monitoring plugins
- `GET /api/v1/plugins/:plugin_name`: Get details about a specific plugin

### Checks
- `GET /api/v1/checks`: List all configured checks (paginated)
- `GET /api/v1/checks/:check_id`: Get a specific check configuration
- `POST /api/v1/checks`: Create a new check configuration
- `PUT /api/v1/checks/:check_id`: Update an existing check configuration
- `DELETE /api/v1/checks/:check_id`: Delete a check configuration
- `POST /api/v1/checks/:check_id/run`: Run a check immediately and store the result
- `POST /api/v1/checks/run`: Run an ad-hoc check without storing configuration

### Results
- `GET /api/v1/results`: List check results (paginated)
- `GET /api/v1/results/:result_id`: Get a specific check result
- `GET /api/v1/results/check/:check_id`: Get results for a specific check
- `GET /api/v1/results/summary`: Get a summary of check results

## Running the API

### Using Docker

The easiest way to run the API is using Docker Compose:

```bash
docker-compose up
```

This will start the API, a PostgreSQL database, and Adminer for database management.

### Running Locally

To run the API locally:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up the environment:
   ```bash
   export FLASK_ENV=development
   export DATABASE_URL=sqlite:///monitorpy.db
   ```

3. Run the API:
   ```bash
   python -m monitorpy.api.run
   ```

## Database Support

The API supports multiple database backends:

- **SQLite** (default): Suitable for simple deployments and development
- **PostgreSQL**: Recommended for production use
- **MySQL/MariaDB**: Also supported for production use

Configure the database connection using the `DATABASE_URL` environment variable.

## Authentication

Authentication is optional and can be enabled by setting `AUTH_REQUIRED=true`. When enabled, API endpoints require either:

- JWT token authentication (`Authorization: Bearer <token>`)
- API key authentication (`X-API-Key: <api-key>`)

### Managing Users

Use the CLI to manage users. These commands work both inside and outside of Docker:

#### Create a User

```bash
# Using the Python module directly
python -m monitorpy.cli user create --username admin --email admin@example.com --password secure_password --admin

# Inside Docker container
docker-compose exec api python -m monitorpy.cli user create --username admin --email admin@example.com --password secure_password --admin
```

#### List Users

```bash
python -m monitorpy.cli user list
# Show API keys
python -m monitorpy.cli user list --show-keys
```

#### Generate API Key

```bash
python -m monitorpy.cli user generate-key admin
```

#### Reset Password

```bash
python -m monitorpy.cli user reset-password admin --password new_password
```

#### Delete User

```bash
python -m monitorpy.cli user delete admin
```

### Logging In

To get a JWT token for authentication:

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'
```

This returns a JWT token and user data that can be used for subsequent requests:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "...",
    "username": "admin",
    "email": "admin@example.com",
    "is_admin": true,
    "created_at": "...",
    "updated_at": "..."
  }
}
```

Use the token in requests:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." http://localhost:5000/api/v1/checks
```

## API Examples

### Creating a Check

```bash
curl -X POST http://localhost:5000/api/v1/checks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example Website",
    "plugin_type": "website_status",
    "config": {
      "url": "https://example.com",
      "timeout": 30,
      "expected_status": 200
    },
    "schedule": "every 5 minutes"
  }'
```

### Running a Check

```bash
curl -X POST http://localhost:5000/api/v1/checks/run \
  -H "Content-Type: application/json" \
  -d '{
    "plugin_type": "ssl_certificate",
    "config": {
      "hostname": "example.com",
      "port": 443
    }
  }'
```

### Retrieving Results

```bash
curl http://localhost:5000/api/v1/results?check_id=123&status=error
```