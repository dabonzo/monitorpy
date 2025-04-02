#!/usr/bin/env python3
"""
Test script for API key authentication with MonitorPy API.
"""

import sys
import requests
import argparse

def test_api_key(api_key, api_url="http://localhost:8000/api/v1"):
    """Test if an API key works for authentication."""
    print(f"Testing API key: {api_key[:8]}...")
    
    # First test health endpoint (which doesn't require auth)
    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200:
            print(f"Health check: OK - {response.status_code}")
            health_data = response.json()
            print(f"API version: {health_data.get('version', 'unknown')}")
            print(f"Redis available: {health_data.get('redis_available', False)}")
        else:
            print(f"Health check failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Connection error: {e}")
        return False
    
    # Test with X-API-Key header
    headers = {"X-API-Key": api_key}
    
    try:
        # Try to get the list of plugins (requires auth)
        print("\nTesting authentication with X-API-Key header...")
        print(f"Request headers: {headers}")
        response = requests.get(f"{api_url}/plugins", headers=headers)
        
        if response.status_code == 200:
            print(f"Authentication successful! Status: {response.status_code}")
            plugins = response.json()
            print(f"Found {len(plugins)} plugins")
            return True
        else:
            print(f"Authentication failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Let's try verbose debugging with the /users endpoint
            print("\nAttempting to access /users endpoint (admin only)...")
            response = requests.get(f"{api_url}/users", headers=headers)
            print(f"Users endpoint: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            return False
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return False

def test_basic_auth(username, password, api_url="http://localhost:8000/api/v1"):
    """Test username/password authentication."""
    print(f"\nTesting username/password authentication for: {username}")
    
    # Convert username to email if it's just "admin"
    email = "admin@example.com" if username == "admin" else username
    
    try:
        # First try with query parameters (this is how /login endpoint works)
        print("\nTrying login with query parameters...")
        response = requests.post(
            f"{api_url}/auth/login?email={email}&password={password}"
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data.get("access_token")
            print(f"Got access token: {token[:10]}...")
            
            # Test the token
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                print("\nTesting token authentication...")
                response = requests.get(f"{api_url}/plugins", headers=headers)
                print(f"Status with token: {response.status_code}")
                return True
        
        # Try with JSON login next
        login_data = {
            "email": email,
            "password": password
        }
        
        print("\nTrying login with JSON data...")
        response = requests.post(
            f"{api_url}/auth/login",
            json=login_data
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data.get("access_token")
            print(f"Got access token: {token[:10]}...")
            
            # Test the token
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                print("\nTesting token authentication...")
                response = requests.get(f"{api_url}/plugins", headers=headers)
                print(f"Status with token: {response.status_code}")
                return True
        
        # Try OAuth2 form-based login (for OAuth2, 'username' field is used for email as per spec)
        print("\nTrying OAuth2 token endpoint...")
        form_data = {
            "username": email,  # For OAuth2, the field is always 'username' even for emails
            "password": password
        }
        
        response = requests.post(
            f"{api_url}/auth/token",
            data=form_data
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("Success with OAuth2 token endpoint!")
            return True
            
        return False
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return False

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Test API key authentication with MonitorPy API")
    
    parser.add_argument("--api-key", help="API key to test")
    parser.add_argument("--username", help="Username/email for basic auth testing")
    parser.add_argument("--password", help="Password for basic auth testing")
    parser.add_argument(
        "--api",
        default="http://localhost:8000/api/v1",
        help="MonitorPy API base URL",
    )
    
    args = parser.parse_args()
    
    if args.api_key:
        test_api_key(args.api_key, args.api)
    elif args.username and args.password:
        test_basic_auth(args.username, args.password, args.api)
    else:
        print("Error: Must provide either --api-key or both --username and --password")
        sys.exit(1)

if __name__ == "__main__":
    main()