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

# Create initialization script for the admin user
COPY <<EOF /app/init_admin.py
#!/usr/bin/env python3
"""
Initialize the database with an admin user on container startup.
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from monitorpy.fastapi_api.database import SessionLocal, Base, engine
    from monitorpy.fastapi_api.models.user import User
    
    # Create tables if they don't exist
    logger.info("Creating database tables if they don't exist")
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            # Create admin user
            logger.info("Creating default admin user")
            admin = User(
                username="admin",
                email="admin@example.com",
                is_admin=True
            )
            admin.set_password("adminpassword")
            
            # Generate API key
            api_key = admin.generate_api_key()
            
            # Save to database
            db.add(admin)
            db.commit()
            
            logger.info(f"Admin user created with API key: {api_key}")
            
            # Save API key to file for easy access
            with open("/data/admin_api_key.txt", "w") as f:
                f.write(f"Admin API Key: {api_key}\n")
        else:
            logger.info("Admin user already exists")
            
            # Ensure admin has an API key
            if not admin.api_key:
                api_key = admin.generate_api_key()
                db.commit()
                logger.info(f"Generated new API key for admin: {api_key}")
                
                # Save API key to file
                with open("/data/admin_api_key.txt", "w") as f:
                    f.write(f"Admin API Key: {api_key}\n")
            else:
                logger.info(f"Admin user has API key: {admin.api_key}")
                
                # Save API key to file
                with open("/data/admin_api_key.txt", "w") as f:
                    f.write(f"Admin API Key: {admin.api_key}\n")
    finally:
        db.close()
except Exception as e:
    logger.error(f"Error initializing admin user: {e}")
EOF

RUN chmod +x /app/init_admin.py

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

# Create entrypoint script to manage database paths
COPY <<EOF /entrypoint.sh
#!/bin/bash

echo "MonitorPy container starting..."

# Ensure the database is properly linked
if [ -f /data/monitorpy.db ] && [ ! -L /app/monitorpy.db ]; then
    # If DB exists in /data but /app has a real file, back it up and create link
    if [ -f /app/monitorpy.db ]; then
        echo "Found real file at /app/monitorpy.db, backing up and creating symlink to /data/monitorpy.db"
        mv /app/monitorpy.db /app/monitorpy.db.bak
    fi
    echo "Creating symlink from /app/monitorpy.db to /data/monitorpy.db"
    ln -sf /data/monitorpy.db /app/monitorpy.db
elif [ -f /app/monitorpy.db ] && [ ! -f /data/monitorpy.db ]; then
    # If DB exists in /app but not in /data, move it
    echo "Found DB in /app but not in /data, moving it to /data"
    cp /app/monitorpy.db /data/monitorpy.db
    rm /app/monitorpy.db
    ln -sf /data/monitorpy.db /app/monitorpy.db
elif [ ! -f /data/monitorpy.db ] && [ ! -f /app/monitorpy.db ]; then
    # If DB doesn't exist at all, create empty one in /data
    echo "No database found, initializing empty DB in /data"
    touch /data/monitorpy.db
    ln -sf /data/monitorpy.db /app/monitorpy.db
fi

# Initialize admin user
echo "Initializing default admin user..."
python /app/init_admin.py

# Display admin API key if available
if [ -f /data/admin_api_key.txt ]; then
    echo "----------------------------------------"
    echo "Admin credentials created!"
    cat /data/admin_api_key.txt
    echo "Username: admin"
    echo "Password: adminpassword"
    echo "----------------------------------------"
fi

# Continue with original command
echo "Starting services..."
# Check if arguments are empty, if so run supervisord
if [ $# -eq 0 ]; then
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
else
    exec "$@"
fi
EOF

RUN chmod +x /entrypoint.sh

# Make the test script executable
RUN chmod +x /app/api_test.py

# Expose port
EXPOSE 8000

# Set health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Command to run supervisor which will start both Redis and the app
ENTRYPOINT ["/entrypoint.sh"]
# No CMD needed - entrypoint will handle it