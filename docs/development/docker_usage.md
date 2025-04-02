# Using MonitorPy API with Docker

This guide explains how to deploy and use the MonitorPy API with Docker, making it easy to run the monitoring system without installing dependencies directly on your host machine.

## Quick Start

The MonitorPy project includes a ready-to-use Docker Compose configuration that sets up the API service, a database, Redis, and an administration interface.

For the simplest deployment, use the pre-built Docker images:

```bash
# Use Docker Hub image
docker run -p 8000:8000 bonzodock/monitorpy:latest

# Or GitHub Container Registry
docker run -p 8000:8000 ghcr.io/dabonzo/monitorpy:latest
```

The container automatically:
- Creates a default admin user (admin@example.com / adminpassword)
- Generates an API key for authentication 
- Displays these credentials at startup
- Sets up a SQLite database in a persistent volume

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Starting the API

1. Clone the repository:

```bash
git clone https://github.com/yourusername/monitorpy.git
cd monitorpy
```

2. Start the Docker services:

```bash
docker-compose up
```

This will start:
- The MonitorPy API on port 5000
- A PostgreSQL database on port 5432
- Adminer (database management tool) on port 8080

### Accessing the API

Once running, you can access:

- API: http://localhost:5000
- API Health Check: http://localhost:5000/health
- Database Admin: http://localhost:8080

## Database Configuration

The Docker setup supports three database options:

### SQLite (Default)

This is the default configuration and requires no additional setup. Data is stored in a volume mounted to `/data/monitorpy.db` in the container.

### PostgreSQL

To use PostgreSQL:

1. In `docker-compose.yml`, uncomment the PostgreSQL DATABASE_URL in the api service environment:

```yaml
# PostgreSQL (uncomment to use):
- DATABASE_URL=postgresql://monitorpy:monitorpy@db:5432/monitorpy
```

The PostgreSQL service is enabled by default in the docker-compose.yml file.

### MySQL

To use MySQL:

1. In `docker-compose.yml`, uncomment:
   - The MySQL service section
   - The MySQL DATABASE_URL in the api service environment
   - The mysql_data volume
   - The mysql dependency in the depends_on list

```yaml
# MySQL (uncomment to use):
- DATABASE_URL=mysql+pymysql://monitorpy:monitorpy@mysql:3306/monitorpy
```

## Docker Compose Configuration

The included `docker-compose.yml` provides:

```yaml
services:
  api:
    build:
      context: .
      dockerfile: docker/api/Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      # Default: SQLite database
      - DATABASE_URL=sqlite:////data/monitorpy.db
      # PostgreSQL (uncomment to use):
      # - DATABASE_URL=postgresql://monitorpy:monitorpy@db:5432/monitorpy
      # MySQL (uncomment to use):
      # - DATABASE_URL=mysql+pymysql://monitorpy:monitorpy@mysql:3306/monitorpy
    volumes:
      - ./:/app
      - monitorpy_data:/data
```

## Environment Variables

You can customize the API service by setting environment variables in the docker-compose.yml file:

- `FLASK_ENV`: Set to `development` or `production`
- `DATABASE_URL`: Connection string for the database
- `SECRET_KEY`: Secret key for session management
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `AUTH_REQUIRED`: Set to `true` or `false` to enable/disable authentication

## Building Custom Images

To build a custom Docker image:

```bash
docker build -t monitorpy-api -f docker/api/Dockerfile .
```

## Production Deployment

For production deployments, consider the following adjustments:

1. Use a production-grade database like PostgreSQL
2. Set `FLASK_ENV=production`
3. Use secure, random values for `SECRET_KEY` and `JWT_SECRET_KEY`
4. Enable authentication by setting `AUTH_REQUIRED=true`
5. Use a reverse proxy (like Nginx) to handle HTTPS

Example production `docker-compose.yml` excerpt:

```yaml
api:
  image: monitorpy-api:latest
  restart: always
  ports:
    - "5000:5000"
  environment:
    - FLASK_ENV=production
    - DATABASE_URL=postgresql://monitorpy:secure_password@db:5432/monitorpy
    - SECRET_KEY=your_secure_random_key
    - JWT_SECRET_KEY=your_secure_random_jwt_key
    - AUTH_REQUIRED=true
  volumes:
    - monitorpy_data:/data
  depends_on:
    - db
```

## Troubleshooting

### Container Logs

View container logs:

```bash
docker-compose logs api
docker-compose logs db
```

### Database Connection Issues

If the API can't connect to the database:

1. Check that the database service is running:
   ```bash
   docker-compose ps
   ```

2. Verify the DATABASE_URL environment variable is correct
3. Ensure the database user has appropriate permissions

### Persisting Data

For persistent data storage, the Docker setup includes volumes:

- `postgres_data`: PostgreSQL data files
- `mysql_data`: MySQL data files (when enabled)
- `monitorpy_data`: For SQLite database and other persistent data

## Advanced Usage

### Running Tests in Docker

To run the test suite in Docker:

```bash
docker-compose exec api pytest tests/
```

### API Development

For development, you can mount your local code into the container:

```yaml
volumes:
  - ./:/app  # Mounts local directory to /app in container
```

### Accessing the PostgreSQL CLI

```bash
docker-compose exec db psql -U monitorpy -d monitorpy
```

### Accessing the MySQL CLI

```bash
docker-compose exec mysql mysql -u monitorpy -p monitorpy
```

### Backup and Restore

Backup PostgreSQL database:

```bash
docker-compose exec db pg_dump -U monitorpy monitorpy > backup.sql
```

Restore PostgreSQL database:

```bash
cat backup.sql | docker-compose exec -T db psql -U monitorpy -d monitorpy
```