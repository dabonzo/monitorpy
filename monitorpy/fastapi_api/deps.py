"""
Dependency functions for FastAPI endpoints.

This module provides dependency injection functions for FastAPI routes,
including database and authentication.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from monitorpy.fastapi_api.config import settings
from monitorpy.fastapi_api.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current authenticated user.
    
    Args:
        token: JWT token
        
    Returns:
        Dict with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        return {"username": username}
    except JWTError:
        raise credentials_exception