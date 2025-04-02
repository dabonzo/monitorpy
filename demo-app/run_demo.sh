#!/bin/bash
#
# Run the MonitorPy Python demo application with Docker networking
#

# Get the correct Docker API host - default to host.docker.internal
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # On Linux, use the Docker gateway IP
  DOCKER_HOST=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+')
else
  # On macOS and Windows, use the special DNS name
  DOCKER_HOST="host.docker.internal"
fi

# Default values
INTERVAL=30
BATCH_SIZE=5
RUN_ONCE=""
AUTH_DISABLE=""
EMAIL=""
PASSWORD=""
API_KEY=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --interval=*)
      INTERVAL="${1#*=}"
      shift
      ;;
    --batch-size=*)
      BATCH_SIZE="${1#*=}"
      shift
      ;;
    --once)
      RUN_ONCE="--once"
      shift
      ;;
    --hosts=*)
      HOSTS="${1#*=}"
      shift
      ;;
    --email=*)
      EMAIL="${1#*=}"
      shift
      ;;
    --password=*)
      PASSWORD="${1#*=}"
      shift
      ;;
    --api-key=*)
      API_KEY="${1#*=}"
      shift
      ;;
    --auth-disable)
      AUTH_DISABLE="--auth-disable"
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

# Update Docker container ENV vars to disable auth if needed
if [[ "$AUTH_DISABLE" == "--auth-disable" ]]; then
  echo "Attempting to modify Docker container environment..."
  
  # Directly modify the FastAPI settings to disable auth
  echo "Modifying FastAPI authentication settings..."
  docker exec monitorpy_v2-api-1 python -c "
# Create a patch for FastAPI dependencies
import os
from pathlib import Path

# Try to find and patch the dependencies file
deps_file = '/app/monitorpy/fastapi_api/deps.py'
if os.path.exists(deps_file):
    print(f'Found deps.py at {deps_file}')
    
    # Read the file content
    with open(deps_file, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'DISABLE_AUTH_FOR_DEMO' not in content:
        # Create backup
        with open(f'{deps_file}.bak', 'w') as f:
            f.write(content)
        
        # Patch the get_current_user function to always bypass auth
        # Find the get_current_user function
        if 'async def get_current_user' in content:
            # Add a bypass at the start of the function
            content = content.replace(
                'async def get_current_user(',
                '# DISABLE_AUTH_FOR_DEMO\\nasync def get_current_user(',
            )
            
            # Find the function body and replace it
            content = content.replace(
                'credentials_exception = HTTPException(',
                '# For demo purposes, return a demo user without token validation\\nreturn {\"username\": \"demo\"}\\n\\n    # Original code below\\n    credentials_exception = HTTPException(',
            )
            
            # Write the patched content
            with open(deps_file, 'w') as f:
                f.write(content)
            
            print('Successfully patched deps.py to bypass auth')
        else:
            print('Could not find get_current_user function to patch')
    else:
        print('File already patched')
else:
    print(f'Could not find deps.py at {deps_file}')
" || echo "Failed to patch FastAPI authentication"
  
  # Set environment variable in the Docker container
  docker exec monitorpy_v2-api-1 sh -c 'echo "export AUTH_REQUIRED=false" >> /etc/profile' || echo "Failed to update Docker environment"
  
  # Try to modify the container environment directly
  echo "Setting AUTH_REQUIRED=false in Docker container..."
  docker exec -e AUTH_REQUIRED=false monitorpy_v2-api-1 sh -c 'echo "AUTH_REQUIRED=$AUTH_REQUIRED"'
  
  # Restart the container to apply changes
  echo "Restarting API container to apply changes..."
  docker restart monitorpy_v2-api-1
  # Wait for the container to be ready
  sleep 5
  
  echo "Authentication should now be disabled for the demo"
fi

# Set hosts parameter if provided
if [ ! -z "$HOSTS" ]; then
  HOSTS_PARAM="--hosts $HOSTS"
else
  HOSTS_PARAM=""
fi

# Set authentication parameters if provided
if [ ! -z "$EMAIL" ] && [ ! -z "$PASSWORD" ]; then
  AUTH_PARAM="--email $EMAIL --password $PASSWORD"
elif [ ! -z "$API_KEY" ]; then
  AUTH_PARAM="--api-key $API_KEY"
else
  AUTH_PARAM=""
fi

echo "Starting MonitorPy Python Demo..."
echo "Connecting to API at http://${DOCKER_HOST}:8000/api/v1"

# Try to create a demo user in the Docker container
if [ -z "$AUTH_PARAM" ]; then
  echo "No authentication provided. Attempting to create demo user..."
  # Try to create a demo user
  API_KEY=$(docker exec monitorpy_v2-api-1 python -c "
from monitorpy.fastapi_api.database import SessionLocal
from monitorpy.fastapi_api.models.user import User
import os

# Create database session
db = SessionLocal()
api_key = None
try:
    # Check if the demo user already exists
    user = db.query(User).filter(User.email == 'demo@example.com').first()
    if not user:
        # Create demo user
        user = User()
        user.username = 'demo'
        user.email = 'demo@example.com'
        user.set_password('demopass')
        user.is_admin = True
        
        # Save to database
        db.add(user)
        db.commit()
        print('Demo user created: demo@example.com / demopass')
    else:
        print('Demo user already exists: demo@example.com / demopass')
    
    # Generate API key if needed
    if not user.api_key:
        api_key = user.generate_api_key()
        db.commit()
        print(f'API key generated: {api_key}')
    else:
        api_key = user.api_key
        print(f'Using existing API key: {api_key}')
    
finally:
    db.close()

# Print so we can capture in shell
if api_key:
    print(f'APIKEY:{api_key}')
" || echo "Failed to create demo user. You may need to provide authentication.")

  # Check if we got an API key in the output
  if [[ "$API_KEY" == *"APIKEY:"* ]]; then
    # Extract just the API key from the output
    EXTRACTED_KEY=$(echo "$API_KEY" | grep "APIKEY:" | sed 's/APIKEY://g')
    echo "Using API key authentication: ${EXTRACTED_KEY:0:10}..."
    AUTH_PARAM="--api-key $EXTRACTED_KEY"
  else
    # If no API key, use email/password
    echo "Using username/password authentication"
    AUTH_PARAM="--email demo@example.com --password demopass"
  fi
fi

# Ensure pip is installed and install requests if needed
python3 -m pip install --user requests >/dev/null 2>&1

# Run the demo
python3 ./demo_checker.py \
  --api "http://${DOCKER_HOST}:8000/api/v1" \
  --interval $INTERVAL \
  --batch-size $BATCH_SIZE \
  $RUN_ONCE \
  $HOSTS_PARAM \
  $AUTH_PARAM \
  $AUTH_DISABLE