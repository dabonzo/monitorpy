FROM python:3.10-slim as build

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for API
RUN pip install --no-cache-dir fastapi uvicorn pydantic python-jose python-multipart \
    sqlalchemy pyyaml redis passlib email-validator pydantic-settings

# Create a smaller final image
FROM python:3.10-slim

# Set metadata
LABEL maintainer="dabonzo"
LABEL description="MonitorPy - A plugin-based monitoring system"
LABEL version="1.0.0"

# Create app directory
WORKDIR /app

# Create data directory
RUN mkdir -p /data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy installed packages from build stage
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy application
COPY monitorpy /app/monitorpy
COPY run_fastapi.py /app/
COPY create_admin.py /app/
COPY setup.py /app/
COPY requirements.txt /app/

# Add non-root user
RUN groupadd -r monitorpy && \
    useradd -r -g monitorpy -d /app -s /bin/bash monitorpy && \
    chown -R monitorpy:monitorpy /app /data

# Switch to non-root user
USER monitorpy

# Expose port
EXPOSE 8000

# Set health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Command to run the application
CMD ["python", "run_fastapi.py"]