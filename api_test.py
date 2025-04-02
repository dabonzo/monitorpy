#!/usr/bin/env python3
"""
API test script to add to container for debugging authentication.
"""

import logging
import argparse
import uuid
import os
from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from passlib.context import CryptContext
from sqlalchemy.sql import func

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:////data/monitorpy.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """Database model for a user."""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False)
    api_key = Column(String(64), unique=True, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def set_password(self, password: str) -> None:
        """Set the password hash."""
        self.password_hash = pwd_context.hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check password against hash."""
        return pwd_context.verify(password, self.password_hash)
    
    def generate_api_key(self) -> str:
        """Generate a new API key."""
        self.api_key = str(uuid.uuid4())
        return self.api_key

    def __repr__(self):
        """String representation."""
        return f"<User {self.username}, email={self.email}, api_key={self.api_key}>"

def create_tables():
    """Create database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def list_users():
    """List all users in the database."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            logger.info("No users found in the database")
            return
        
        logger.info(f"Found {len(users)} users:")
        for user in users:
            logger.info(f"Username: {user.username}, Email: {user.email}, API Key: {user.api_key}, Admin: {user.is_admin}")
    finally:
        db.close()

def create_user(username, email, password, is_admin=True):
    """Create a new user."""
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing:
            logger.error(f"User with username '{username}' or email '{email}' already exists")
            return
        
        # Create new user
        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
        user.generate_api_key()
        
        db.add(user)
        db.commit()
        
        logger.info(f"Created user '{username}' with API key: {user.api_key}")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
    finally:
        db.close()

def reset_api_key(username):
    """Reset API key for a user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.error(f"User '{username}' not found")
            return
        
        new_key = user.generate_api_key()
        db.commit()
        
        logger.info(f"Reset API key for '{username}': {new_key}")
        return new_key
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting API key: {e}")
    finally:
        db.close()

def test_auth_api(api_key, host="localhost", port=8000):
    """Test authentication with the API."""
    import httpx
    
    api_url = f"http://{host}:{port}/api/v1"
    
    # Test health endpoint first
    try:
        response = httpx.get(f"{api_url}/health")
        logger.info(f"Health check: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"Health data: {response.json()}")
        else:
            logger.error(f"Health check failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to API: {e}")
        return False
    
    # Test API key auth
    headers = {"X-API-Key": api_key}
    
    try:
        # Try plugins endpoint (requires auth)
        logger.info(f"Testing API key authentication with: {api_key}")
        response = httpx.get(f"{api_url}/plugins", headers=headers)
        
        if response.status_code == 200:
            plugins = response.json()
            logger.info(f"Authentication successful! Found {len(plugins)} plugins")
            return True
        else:
            logger.error(f"Authentication failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error testing API: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="API Authentication Test Utility")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List users command
    list_parser = subparsers.add_parser("list", help="List all users")
    
    # Create user command
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("--username", required=True, help="Username")
    create_parser.add_argument("--email", required=True, help="Email address")
    create_parser.add_argument("--password", required=True, help="Password")
    create_parser.add_argument("--admin", action="store_true", help="Create as admin")
    
    # Reset API key command
    reset_parser = subparsers.add_parser("reset-key", help="Reset API key for a user")
    reset_parser.add_argument("--username", required=True, help="Username")
    
    # Test API command
    test_parser = subparsers.add_parser("test", help="Test API authentication")
    test_parser.add_argument("--api-key", required=True, help="API key to test")
    test_parser.add_argument("--host", default="localhost", help="API host")
    test_parser.add_argument("--port", type=int, default=8000, help="API port")
    
    args = parser.parse_args()
    
    # Create tables if they don't exist
    create_tables()
    
    if args.command == "list":
        list_users()
    elif args.command == "create":
        create_user(args.username, args.email, args.password, args.admin)
    elif args.command == "reset-key":
        reset_api_key(args.username)
    elif args.command == "test":
        test_auth_api(args.api_key, args.host, args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()