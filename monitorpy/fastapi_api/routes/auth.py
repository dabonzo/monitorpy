"""
Authentication routes for the MonitorPy FastAPI implementation.

This module provides endpoints for user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy.orm import Session

from monitorpy.fastapi_api.config import settings
from monitorpy.fastapi_api.database import get_db
from monitorpy.fastapi_api.models.user import User, Token
from monitorpy.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    Uses OAuth2 password flow for authentication.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not user.check_password(form_data.password):
        logger.warning(f"Failed login attempt for user {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id},
    )
    
    logger.info(f"User {user.email} logged in successfully")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }


@router.post("/login", response_model=Token)
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    Alternative login endpoint that accepts regular JSON.
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not user.check_password(password):
        logger.warning(f"Failed login attempt for user {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id},
    )
    
    logger.info(f"User {email} logged in successfully")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }