FROM python:3.10-slim as build

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for API
RUN pip install --no-cache-dir fastapi uvicorn pydantic python-jose python-multipart \
    sqlalchemy pyyaml redis passlib email-validator pydantic-settings httpx

# Create a smaller final image
FROM python:3.10-slim

# Set metadata
LABEL maintainer="dabonzo"
LABEL description="MonitorPy - A plugin-based monitoring system"
LABEL version="1.0.0"

# Install Redis, Supervisor, and diagnostics tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    redis-server supervisor curl sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create data directory
RUN mkdir -p /data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV REDIS_URL=redis://localhost:6379/0
ENV USE_REDIS_CACHE=true
ENV AUTH_REQUIRED=false
ENV DISABLE_AUTH=true
ENV DATABASE_URL=sqlite:////data/monitorpy.db

# Copy installed packages from build stage
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy application
COPY monitorpy /app/monitorpy
COPY run_fastapi.py /app/
COPY create_admin.py /app/
COPY setup.py /app/
COPY requirements.txt /app/
COPY api_test.py /app/

# Make the test script executable
RUN chmod +x /app/api_test.py

# Configure Supervisor
RUN mkdir -p /etc/supervisor/conf.d
COPY <<EOF /etc/supervisor/conf.d/supervisord.conf
[supervisord]
nodaemon=true
user=root
loglevel=info

[program:redis]
command=redis-server
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:monitorpy]
command=python /app/run_fastapi.py
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
EOF

# Create data directories with proper permissions
RUN mkdir -p /data && \
    mkdir -p /var/lib/redis && \
    chown -R redis:redis /var/lib/redis && \
    chmod 770 /var/lib/redis

# Expose port
EXPOSE 8000

# Set health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Command to run supervisor which will start both Redis and the app
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]