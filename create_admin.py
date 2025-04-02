#!/usr/bin/env python3
"""
Create an administrator user for MonitorPy FastAPI.

This script creates a new admin user if one doesn't already exist.
"""

import argparse
import os
import sys
from getpass import getpass

from monitorpy.fastapi_api.database import SessionLocal
from monitorpy.fastapi_api.models.user import User
from monitorpy.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


def create_admin_user(username, email, password, force=False):
    """
    Create a new admin user.
    
    Args:
        username: Admin username
        email: Admin email
        password: Admin password
        force: Force creation (overwrite if exists)
        
    Returns:
        bool: True if user created, False otherwise
    """
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if user already exists
        user = db.query(User).filter(User.username == username).first()
        
        if user and not force:
            print(f"User '{username}' already exists!")
            return False
        
        if user and force:
            # Update existing user
            user.email = email
            user.set_password(password)
            user.is_admin = True
            
            # Generate new API key
            api_key = user.generate_api_key()
            
            # Save changes
            db.commit()
            print(f"Admin user '{username}' updated successfully.")
            print(f"API Key: {api_key}")
            return True
        
        # Create new user
        user = User(
            username=username,
            email=email,
            is_admin=True
        )
        user.set_password(password)
        
        # Generate API key
        api_key = user.generate_api_key()
        
        # Save to database
        db.add(user)
        db.commit()
        
        print(f"Admin user '{username}' created successfully.")
        print(f"API Key: {api_key}")
        return True
    
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False
    
    finally:
        db.close()


def main():
    """Main function."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Create an admin user for MonitorPy API")
    parser.add_argument("--username", help="Admin username")
    parser.add_argument("--email", help="Admin email")
    parser.add_argument("--password", help="Admin password (use with caution)")
    parser.add_argument("--force", action="store_true", help="Update user if already exists")
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    
    # Get username
    username = args.username
    if not username:
        username = input("Enter admin username: ")
    
    # Get email
    email = args.email
    if not email:
        email = input("Enter admin email: ")
    
    # Get password
    password = args.password
    if not password:
        password = getpass("Enter admin password: ")
        confirm_password = getpass("Confirm password: ")
        
        if password != confirm_password:
            print("Passwords do not match!")
            return 1
    
    # Create admin user
    success = create_admin_user(username, email, password, args.force)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())