# Production Deployment Guide

This guide covers how to deploy the MonitorPy API in a production environment, including integration with control panels like CloudAdmin or ISPConfig.

## Deployment Options

There are several ways to deploy MonitorPy in production:

1. **Systemd Service** (Recommended)
2. Docker Container
3. Supervisor Process
4. Manual Execution

## Systemd Service Deployment

### 1. Install MonitorPy

First, install MonitorPy and its dependencies:

```bash
# Clone the repository
git clone https://github.com/yourusername/monitorpy.git /opt/monitorpy

# Install dependencies
cd /opt/monitorpy
pip install -e .
pip install gunicorn psycopg2-binary flask flask-sqlalchemy flask-migrate flask-jwt-extended flask-marshmallow marshmallow-sqlalchemy flask-cors
```

### 2. Create a WSGI Entry Point

Create a WSGI file for running the application with Gunicorn:

```bash
nano /opt/monitorpy/monitorpy/api/wsgi.py
```

Add the following content:

```python
"""
WSGI entry point for the MonitorPy API.
"""

from monitorpy.api import create_app
from monitorpy.api.config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == "__main__":
    app.run()
```

### 3. Create a Systemd Service File

Create a systemd service file to manage the API service:

```bash
sudo nano /etc/systemd/system/monitorpy-api.service
```

Add the following content (customize as needed):

```ini
[Unit]
Description=MonitorPy API Service
After=network.target postgresql.service
Requires=postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/monitorpy
Environment="DATABASE_URL=postgresql://monitorpy:your_secure_password@localhost/monitorpy"
Environment="FLASK_ENV=production"
Environment="SECRET_KEY=your_secure_secret_key"
Environment="JWT_SECRET_KEY=your_secure_jwt_key"
Environment="AUTH_REQUIRED=true"
ExecStart=/usr/local/bin/gunicorn monitorpy.api.wsgi:app -w 4 -b 0.0.0.0:5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Adjust the following parameters as needed:
- `User` and `Group`: Set to the appropriate service user
- `DATABASE_URL`: Configure for your database
- `SECRET_KEY` and `JWT_SECRET_KEY`: Generate secure random keys
- Worker count (`-w 4`): Adjust based on server resources

### 4. Create the Database

Create a PostgreSQL database for MonitorPy:

```bash
sudo -u postgres psql -c "CREATE USER monitorpy WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "CREATE DATABASE monitorpy OWNER monitorpy;"
```

### 5. Enable and Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable monitorpy-api
sudo systemctl start monitorpy-api
```

Check the service status:

```bash
sudo systemctl status monitorpy-api
```

## Integration with Control Panels

### ISPConfig Integration

To integrate with ISPConfig, add a reverse proxy configuration to your web server:

#### Nginx Configuration

Add to your site configuration in ISPConfig:

```nginx
location /monitoring/api/ {
    proxy_pass http://localhost:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

#### Apache Configuration

Add to your VirtualHost configuration in ISPConfig:

```apache
ProxyPass /monitoring/api/ http://localhost:5000/
ProxyPassReverse /monitoring/api/ http://localhost:5000/
```

### CloudAdmin Integration

Similar to ISPConfig, add a reverse proxy configuration through the CloudAdmin interface:

1. Navigate to your website configuration
2. Add a custom Nginx or Apache directive similar to the examples above
3. Apply the configuration

## Security Considerations

For production deployments, ensure you:

1. **Enable Authentication**: Set `AUTH_REQUIRED=true` in the service configuration
2. **Use HTTPS**: Place the API behind HTTPS using a reverse proxy
3. **Restrict Access**: Limit access to the API endpoints as needed
4. **Use Strong Passwords**: For database and API users
5. **Regular Updates**: Keep the system updated with security patches

## Monitoring the Service

To ensure the API remains available, you can monitor it using:

```bash
# View logs
sudo journalctl -u monitorpy-api -f

# Check status
sudo systemctl status monitorpy-api
```

## Backup and Maintenance

Regularly backup your database:

```bash
# For PostgreSQL
pg_dump -U monitorpy monitorpy > monitorpy_backup_$(date +%Y%m%d).sql
```

## Upgrading

To upgrade the MonitorPy API:

1. Stop the service: `sudo systemctl stop monitorpy-api`
2. Update the code: `cd /opt/monitorpy && git pull`
3. Upgrade dependencies: `pip install -e . --upgrade`
4. Start the service: `sudo systemctl start monitorpy-api`

## Troubleshooting

If the service fails to start, check the logs:

```bash
sudo journalctl -u monitorpy-api -e
```

Common issues include:
- Database connection problems
- Permission issues
- Missing dependencies

## Using SQLite in Production

While PostgreSQL is recommended for production, you can use SQLite for smaller deployments:

```ini
Environment="DATABASE_URL=sqlite:////opt/monitorpy/data/monitorpy.db"
```

Ensure the directory has appropriate permissions:

```bash
mkdir -p /opt/monitorpy/data
chown www-data:www-data /opt/monitorpy/data
```