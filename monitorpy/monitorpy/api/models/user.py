"""
User model for the MonitorPy API.

This module defines the User model for API authentication.
"""

import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from monitorpy.api.extensions import db


class User(db.Model):
    """
    Model representing a user with API access.
    
    This is used for API authentication when AUTH_REQUIRED is enabled.
    """
    
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.String(64), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, username, email, password, is_admin=False):
        """
        Initialize a new User.
        
        Args:
            username: Username for login
            email: User's email address
            password: Password in plaintext (will be hashed)
            is_admin: Whether the user has admin privileges
        """
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.set_password(password)
        self.is_admin = is_admin
        
    def set_password(self, password):
        """
        Set the password hash from a plaintext password.
        
        Args:
            password: Plaintext password
        """
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """
        Check if the provided password matches the stored hash.
        
        Args:
            password: Plaintext password to check
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def generate_api_key(self):
        """
        Generate a new API key for this user.
        
        Returns:
            str: The new API key
        """
        self.api_key = str(uuid.uuid4())
        return self.api_key
    
    def to_dict(self, include_api_key=False):
        """
        Convert the user to a dictionary.
        
        Args:
            include_api_key: Whether to include the API key
            
        Returns:
            dict: User data
        """
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_api_key and self.api_key:
            data['api_key'] = self.api_key
            
        return data
    
    def __repr__(self):
        """Get string representation."""
        return f"<User {self.username}>"