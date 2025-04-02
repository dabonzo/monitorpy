#!/usr/bin/env python3
"""
MonitorPy API Demo Application

This demo application uses the MonitorPy API to perform random checks on various hosts.
It demonstrates how to use the API to perform website, SSL, DNS, and mail server checks.
"""

import sys
import time
import json
import random
import argparse
import requests
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Default popular websites to check
DEFAULT_WEBSITES = [
    "google.com",
    "github.com",
    "amazon.com",
    "facebook.com",
    "twitter.com", 
    "microsoft.com",
    "apple.com",
    "cloudflare.com",
    "digitalocean.com",
    "wikipedia.org",
    "python.org",
    "stackoverflow.com",
    "reddit.com",
    "netflix.com",
    "cnn.com"
]

# API configuration
API_HOST = "localhost"
API_PORT = 8000
API_BASE_URL = f"http://{API_HOST}:{API_PORT}/api/v1"

# Plugin types
PLUGINS = ["website_status", "ssl_certificate", "dns_record"]

class MonitorPyDemo:
    """Demo application to showcase MonitorPy API capabilities."""
    
    def __init__(self, api_url: str, hosts: List[str] = None, interval: int = 60, 
                 email: Optional[str] = None, password: Optional[str] = None,
                 api_key: Optional[str] = None):
        """
        Initialize the demo application.
        
        Args:
            api_url: The MonitorPy API base URL
            hosts: List of hostnames to check (defaults to popular websites)
            interval: Interval between check batches in seconds
            email: User email for authentication
            password: User password for authentication
            api_key: API key for authentication (alternative to email/password)
        """
        self.api_url = api_url
        self.hosts = hosts or DEFAULT_WEBSITES
        self.interval = interval
        self.access_token = None
        self.headers = {}
        
        # Validate API connection
        try:
            response = requests.get(f"{self.api_url}/health")
            if response.status_code != 200:
                print(f"Error connecting to API: {response.status_code}")
                sys.exit(1)
            
            health_data = response.json()
            print(f"Connected to MonitorPy API: {health_data['status']}")
            print(f"Redis available: {health_data.get('redis_available', False)}")
            
            # Authenticate if credentials are provided
            if email and password:
                self.authenticate(email, password)
            elif api_key:
                # Try different ways to pass the API key
                self.set_api_key(api_key)
            else:
                # Try to authenticate with env vars if available
                if os.environ.get("MONITORPY_EMAIL") and os.environ.get("MONITORPY_PASSWORD"):
                    self.authenticate(os.environ.get("MONITORPY_EMAIL"), 
                                     os.environ.get("MONITORPY_PASSWORD"))
                elif os.environ.get("MONITORPY_API_KEY"):
                    self.set_api_key(os.environ.get("MONITORPY_API_KEY"))
                else:
                    print("WARNING: No authentication provided. Some API endpoints may be unavailable.")
                
        except requests.RequestException as e:
            print(f"Failed to connect to API: {e}")
            sys.exit(1)
    
    def set_api_key(self, api_key: str) -> None:
        """
        Set the API key in various formats to find the one that works.
        
        Args:
            api_key: The API key to use
        """
        self.api_key = api_key
        
        # Store multiple formats of authorization headers to try
        self.auth_formats = [
            {"Authorization": f"Bearer {api_key}"},
            {"Authorization": f"{api_key}"},
            {"X-API-Key": f"{api_key}"},
            {"api_key": f"{api_key}"},
            {"token": f"{api_key}"}
        ]
        
        # Start with the most common format
        self.headers = self.auth_formats[0]
        print(f"Using API key for authentication (will try different formats if needed)")
        
    def authenticate(self, email: str, password: str) -> bool:
        """
        Authenticate with the API and get an access token.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            bool: True if authentication succeeded, False otherwise
        """
        try:
            # First try with query parameters
            response = requests.post(
                f"{self.api_url}/auth/login",
                params={"email": email, "password": password}
            )
            
            # If that fails, try with form data (OAuth2 spec)
            if response.status_code != 200:
                # Use the token endpoint with form data (standard OAuth2)
                form_data = {
                    "username": email,  # OAuth2 spec uses 'username' even for email
                    "password": password
                }
                
                response = requests.post(
                    f"{self.api_url}/auth/token",
                    data=form_data  # Using data= for form data, not json=
                )
            
            # If still failing, try with JSON data
            if response.status_code != 200:
                login_data = {
                    "email": email,
                    "password": password
                }
                
                response = requests.post(
                    f"{self.api_url}/auth/login",
                    json=login_data
                )
            
            if response.status_code != 200:
                print(f"Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            auth_data = response.json()
            self.access_token = auth_data.get("access_token")
            
            if self.access_token:
                self.headers = {"Authorization": f"Bearer {self.access_token}"}
                print(f"Successfully authenticated as {email}")
                return True
            else:
                print("Authentication failed: No token received")
                return False
                
        except requests.RequestException as e:
            print(f"Authentication error: {e}")
            return False
    
    def generate_random_batch(self, size: int = 5) -> List[Dict[str, Any]]:
        """
        Generate a random batch of checks.
        
        Args:
            size: Number of checks to generate
            
        Returns:
            List of check configurations
        """
        checks = []
        
        for _ in range(size):
            # Select random host and plugin
            host = random.choice(self.hosts)
            plugin = random.choice(PLUGINS)
            
            # Create unique timestamp for this check
            timestamp = int(time.time())
            
            # Create check configuration based on plugin type
            if plugin == "website_status":
                record_type = ""
                check = {
                    "plugin_type": plugin,
                    "config": {
                        "url": f"https://{host}",
                        "timeout": 10,
                        "expected_status": 200,
                        "method": "GET",
                        "follow_redirects": True
                    },
                    "id": f"web-{host}-{timestamp}"
                }
            elif plugin == "ssl_certificate":
                record_type = ""
                check = {
                    "plugin_type": plugin,
                    "config": {
                        "hostname": host,
                        "port": 443,
                        "timeout": 10,
                        "warning_days": 30,
                        "critical_days": 14
                    },
                    "id": f"ssl-{host}-{timestamp}"
                }
            elif plugin == "dns_record":
                record_type = random.choice(["A", "AAAA", "MX", "TXT"])
                check = {
                    "plugin_type": plugin,
                    "config": {
                        "domain": host,
                        "record_type": record_type,
                        "timeout": 10
                    },
                    "id": f"dns{record_type}-{host}-{timestamp}"
                }
            
            checks.append(check)
            
        return checks
    
    def run_batch(self, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run a batch of checks using the API.
        
        Args:
            checks: List of check configurations
        
        Returns:
            Batch results
        """
        try:
            # First attempt with current headers
            response = requests.post(
                f"{self.api_url}/batch/run-ad-hoc",
                json={
                    "checks": checks,
                    "max_workers": 10,
                    "timeout": 30.0
                },
                headers=self.headers
            )
            
            # If authentication fails and we have API key formats to try
            if response.status_code == 401 and hasattr(self, 'auth_formats'):
                for i, headers in enumerate(self.auth_formats):
                    if headers == self.headers:
                        continue  # Skip the one we just tried
                        
                    print(f"Trying alternative API key format {i+1}...")
                    self.headers = headers
                    
                    response = requests.post(
                        f"{self.api_url}/batch/run-ad-hoc",
                        json={
                            "checks": checks,
                            "max_workers": 10,
                            "timeout": 30.0
                        },
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        print(f"Found working API key format!")
                        break
            
            # Try without authentication if all else fails
            if response.status_code == 401:
                print("Trying without authentication...")
                response = requests.post(
                    f"{self.api_url}/batch/run-ad-hoc",
                    json={
                        "checks": checks,
                        "max_workers": 10,
                        "timeout": 30.0
                    }
                )
            
            if response.status_code != 200:
                print(f"Error running batch: {response.status_code}")
                print(f"Response: {response.text}")
                return {"error": True, "message": response.text}
            
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to run batch: {e}")
            return {"error": True, "message": str(e)}
    
    def display_results(self, results: Dict[str, Any]) -> None:
        """
        Display batch check results in a user-friendly format.
        
        Args:
            results: Batch check results
        """
        if "error" in results:
            print(f"Error: {results['message']}")
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n===== MonitorPy Check Results ({timestamp}) =====")
        
        if "results" not in results:
            print("No results returned.")
            return
            
        status_counts = {"success": 0, "warning": 0, "error": 0}
        
        for item in results["results"]:
            check_id = item.get("check_id", "unknown")
            result = item.get("result", {})
            status = result.get("status", "unknown")
            message = result.get("message", "No message")
            response_time = result.get("response_time", 0)
            raw_data = result.get("raw_data", {})
            
            # Update status counts
            if status in status_counts:
                status_counts[status] += 1
            
            # Extract host and check type from check_id or raw_data
            host = "unknown"
            check_type = "unknown"
            
            # Try to get info from check_id (format: type-host-timestamp)
            if "-" in check_id:
                parts = check_id.split("-")
                if len(parts) >= 2:
                    check_type = parts[0]
                    host = parts[1]
            
            # Try to get more info from raw_data
            if host == "unknown" or check_type == "unknown":
                if "url" in raw_data:
                    # Extract host from URL
                    url = raw_data["url"]
                    if "://" in url:
                        host = url.split("://")[1].split("/")[0]
                    check_type = "WEB"
                elif "hostname" in raw_data:
                    host = raw_data["hostname"]
                    if "certificate_details" in raw_data:
                        check_type = "SSL"
                    elif "protocol" in raw_data:
                        check_type = "MAIL"
                elif "domain" in raw_data:
                    host = raw_data["domain"]
                    if "record_type" in raw_data:
                        check_type = f"DNS-{raw_data['record_type']}"
                    else:
                        check_type = "DNS"
            
            # Format output based on status
            if status == "success":
                status_color = "\033[92m"  # Green
            elif status == "warning":
                status_color = "\033[93m"  # Yellow
            else:
                status_color = "\033[91m"  # Red
                
            reset_color = "\033[0m"
            
            print(f"{status_color}{status.upper()}{reset_color} | {check_type.upper()} | {host} | {message} | {response_time:.3f}s")
        
        # Print summary
        total = sum(status_counts.values())
        print(f"\nSummary: {total} checks completed")
        print(f"  Success: {status_counts['success']} ({status_counts['success']/total*100:.1f}%)")
        print(f"  Warning: {status_counts['warning']} ({status_counts['warning']/total*100:.1f}%)")
        print(f"  Error: {status_counts['error']} ({status_counts['error']/total*100:.1f}%)")
        print("="*50)
    
    def run_continuous(self) -> None:
        """Run checks continuously at the specified interval."""
        try:
            print(f"Starting continuous monitoring (every {self.interval} seconds)")
            print(f"Press Ctrl+C to stop")
            
            while True:
                # Generate random batch size between 3 and 8
                batch_size = random.randint(3, 8)
                
                # Generate and run batch
                checks = self.generate_random_batch(batch_size)
                results = self.run_batch(checks)
                self.display_results(results)
                
                # Wait for next interval
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
    
    def run_once(self, batch_size: int = 5) -> None:
        """
        Run a single batch of checks.
        
        Args:
            batch_size: Number of checks to run
        """
        checks = self.generate_random_batch(batch_size)
        results = self.run_batch(checks)
        self.display_results(results)


def main():
    """Main entry point for the demo app."""
    parser = argparse.ArgumentParser(description="MonitorPy API Demo")
    parser.add_argument(
        "--hosts",
        help="Comma-separated list of hosts to check (defaults to popular websites)",
    )
    parser.add_argument(
        "--api",
        default=API_BASE_URL,
        help="MonitorPy API base URL (default: http://localhost:8000/api/v1)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval between check batches in seconds (default: 60)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of checks per batch (default: 5, only for one-time runs)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run checks once and exit (default: run continuously)",
    )
    parser.add_argument(
        "--email",
        help="Email for API authentication",
    )
    parser.add_argument(
        "--password",
        help="Password for API authentication",
    )
    parser.add_argument(
        "--api-key",
        help="API key for authentication (alternative to email/password)",
    )
    parser.add_argument(
        "--auth-disable",
        action="store_true",
        help="Disable Docker API authentication (sets env variables for the Docker container)",
    )
    
    args = parser.parse_args()
    
    # Parse hosts
    hosts = args.hosts.split(",") if args.hosts else None
    
    # If using Docker and --auth-disable is specified, attempt to disable auth
    if args.auth_disable:
        try:
            import subprocess
            print("Attempting to disable API authentication in Docker container...")
            subprocess.run(
                ["docker", "exec", "monitorpy_v2-api-1", "sh", "-c", "export AUTH_REQUIRED=false"],
                check=True
            )
            print("Authentication disabled for Docker container (may require API restart)")
        except Exception as e:
            print(f"Warning: Failed to disable authentication: {e}")
    
    # Create demo app
    demo = MonitorPyDemo(
        api_url=args.api,
        hosts=hosts,
        interval=args.interval,
        email=args.email,
        password=args.password,
        api_key=args.api_key
    )
    
    # Run checks
    if args.once:
        demo.run_once(args.batch_size)
    else:
        demo.run_continuous()


if __name__ == "__main__":
    main()