"""
User model for the MonitorPy FastAPI implementation.

This module defines the SQLAlchemy User model and Pydantic schemas.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, String, Boolean, DateTime, func
from passlib.context import CryptContext

from monitorpy.fastapi_api.database import Base

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """
    SQLAlchemy model representing a user with API access.
    
    This is used for API authentication.
    """
    
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
        """
        Set the password hash from a plaintext password.
        
        Args:
            password: Plaintext password
        """
        self.password_hash = pwd_context.hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        Check if the provided password matches the stored hash.
        
        Args:
            password: Plaintext password to check
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return pwd_context.verify(password, self.password_hash)
    
    def generate_api_key(self) -> str:
        """
        Generate a new API key for this user.
        
        Returns:
            str: The new API key
        """
        self.api_key = str(uuid.uuid4())
        return self.api_key


# Pydantic models for request/response validation
class UserBase(BaseModel):
    """Base model for user data."""
    
    username: str
    email: EmailStr
    is_admin: bool = False


class UserCreate(UserBase):
    """Model for creating a new user."""
    
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Model for updating an existing user."""
    
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_admin: Optional[bool] = None


class UserInDB(UserBase):
    """Model for user data from database."""
    
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        
        orm_mode = True


class UserWithApiKey(UserInDB):
    """User model including the API key."""
    
    api_key: Optional[str] = None


class Token(BaseModel):
    """Model for authentication token."""
    
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class TokenData(BaseModel):
    """Model for token payload data."""
    
    username: Optional[str] = None
    user_id: Optional[str] = None