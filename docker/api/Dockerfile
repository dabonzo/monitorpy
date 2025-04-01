FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for API
RUN pip install --no-cache-dir fastapi uvicorn pydantic python-jose python-multipart \
    sqlalchemy pyyaml

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app

# Copy application
COPY . .

# Command to run the application
CMD ["python", "run_fastapi.py"]