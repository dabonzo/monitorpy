"""
Dependency functions for FastAPI endpoints.

This module provides dependency injection functions for FastAPI routes,
including database and authentication.
"""

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyHeader
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional

from monitorpy.fastapi_api.config import settings
from monitorpy.fastapi_api.database import get_db
from monitorpy.utils.logging import get_logger

logger = get_logger(__name__)

# Check if authentication is disabled via environment variables
AUTH_DISABLED = os.environ.get("DISABLE_AUTH", "").lower() in ("true", "1", "yes", "y")

if AUTH_DISABLED:
    logger.warning("*** AUTHENTICATION DISABLED via DISABLE_AUTH environment variable ***")
    logger.warning("*** This should only be used for development and demos ***")

# Define security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token", auto_error=not AUTH_DISABLED)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Demo user for when auth is disabled
DEMO_USER = {"username": "demo", "id": "demo-user-id", "is_admin": True}


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db)
):
    """
    Get the current authenticated user.
    
    Args:
        token: JWT token
        api_key: API key from header
        db: Database session
        
    Returns:
        Dict with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    # If authentication is disabled, return a demo user
    if AUTH_DISABLED:
        logger.debug("Authentication disabled, returning demo user")
        return DEMO_USER
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try JWT token authentication
    if token:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=["HS256"]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            
            # Get full user data from database
            from monitorpy.fastapi_api.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_admin
                }
            else:
                raise credentials_exception
        except JWTError:
            logger.warning("Invalid JWT token")
    
    # Try API key authentication if provided
    if api_key:
        try:
            # Query the database for a user with this API key
            from monitorpy.fastapi_api.models.user import User
            
            user = db.query(User).filter(User.api_key == api_key).first()
            if user:
                logger.debug(f"Authenticated via API key as {user.username}")
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_admin
                }
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
    
    # If we get here, authentication failed
    raise credentials_exception


async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """
    Verify that the current user is an admin.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        dict: The user if they are an admin
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if AUTH_DISABLED:
        # When auth is disabled, the demo user is always an admin
        return current_user
        
    if not current_user.get("is_admin", False):
        logger.warning(f"Non-admin user {current_user.get('username')} attempted to access admin endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user