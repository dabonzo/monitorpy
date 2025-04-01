FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY monitorpy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for API
RUN pip install --no-cache-dir flask flask-sqlalchemy flask-migrate flask-jwt-extended \
    flask-marshmallow marshmallow-sqlalchemy flask-cors gunicorn

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONPATH=/app

# Copy application
COPY . .

# Command to run the application
CMD ["python", "-m", "monitorpy.monitorpy.api.run"]