# MonitorPy Docker Guide

This guide explains how to use MonitorPy with Docker.

## Using the Official Docker Image

The easiest way to get started is to use the pre-built Docker image:

```bash
# Pull the image
docker pull ghcr.io/dabonzo/monitorpy:latest

# Or if you prefer Docker Hub
docker pull dabonzo/monitorpy:latest
```

## Running with Docker

### Basic Usage

```bash
docker run -p 8000:8000 -v monitorpy_data:/data ghcr.io/dabonzo/monitorpy:latest
```

### With Environment Variables

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:////data/monitorpy.db \
  -e SECRET_KEY=your_secret_key \
  -e JWT_SECRET_KEY=your_jwt_secret \
  -e AUTH_REQUIRED=true \
  -v monitorpy_data:/data \
  ghcr.io/dabonzo/monitorpy:latest
```

## Using with Docker Compose

The repository includes a `docker-compose.yml` file that sets up:

- MonitorPy API service
- PostgreSQL database
- Redis cache
- Adminer for database management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down
```

## Creating an Admin User

To create an admin user within the Docker container:

```bash
docker exec -it monitorpy_container_name python create_admin.py
```

Or when running with docker-compose:

```bash
docker-compose exec api python create_admin.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:////data/monitorpy.db` |
| `SECRET_KEY` | Secret key for session security | `dev_secret_key_change_me_in_production` |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | `dev_jwt_key_change_me_in_production` |
| `AUTH_REQUIRED` | Enable/disable authentication | `false` |
| `DISABLE_AUTH` | Completely disable auth checks | `false` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `USE_REDIS_CACHE` | Enable/disable Redis caching | `true` |
| `CACHE_EXPIRATION` | Cache TTL in seconds | `300` |

## Building Your Own Image

If you want to build your own Docker image:

```bash
git clone https://github.com/dabonzo/monitorpy.git
cd monitorpy
docker build -t monitorpy:local .
```

## Automatic Docker Builds

MonitorPy uses GitHub Actions for automatic Docker image builds. The workflow:

1. Builds and publishes images on:
   - Pushes to the `main` branch
   - Releases with version tags (v*.*.*)
   - Pull requests (build only, no push)

2. Publishes to:
   - GitHub Container Registry: `ghcr.io/dabonzo/monitorpy`
   - Docker Hub: `dabonzo/monitorpy`

3. Creates the following image tags:
   - `latest`: Most recent build from main branch
   - Semantic versions: `v1.0.0`, `v1.0`, `v1` (when tagged with version)
   - Git SHA: `sha-abc123` (commit hash)
   - Branch name: `main`, `feature-xyz`, etc.

### Triggering a New Image Build

To trigger a new image build:

```bash
# For a standard build from the main branch:
git push origin main

# For a versioned release:
git tag v1.0.0
git push origin v1.0.0
```

## Testing the API

Once the container is running, you can test the API:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# API documentation (via browser)
open http://localhost:8000/api/v1/docs
```

## Production Best Practices

For production deployment:

1. **Change default secrets**: Set strong values for `SECRET_KEY` and `JWT_SECRET_KEY`
2. **Enable authentication**: Set `AUTH_REQUIRED=true`
3. **Use a proper database**: Configure PostgreSQL or MySQL
4. **Set up proper networking**: Use a reverse proxy like Nginx
5. **Set up monitoring**: Monitor container health
6. **Use volumes**: Mount volumes for persistent data

## Running in Swarm or Kubernetes

For orchestrated environments, use configs or secrets for sensitive information and adjust the Docker Compose file accordingly.