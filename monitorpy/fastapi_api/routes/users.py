"""
User management routes for the MonitorPy FastAPI implementation.

This module provides endpoints for managing users (admin only).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from monitorpy.fastapi_api.database import get_db
from monitorpy.fastapi_api.deps import get_admin_user, get_current_user
from monitorpy.fastapi_api.models.user import (
    User, UserCreate, UserInDB, UserUpdate, UserWithApiKey
)
from monitorpy.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[UserInDB])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        List of users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/me", response_model=UserWithApiKey)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get information about the current authenticated user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Current user information with API key
    """
    user = db.query(User).filter(User.id == current_user.get("id")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/{user_id}", response_model=UserInDB)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get information about a specific user (admin only).
    
    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        User information
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only).
    
    Args:
        user_data: User data
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Created user information
    """
    # Check if username or email already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        is_admin=user_data.is_admin
    )
    user.set_password(user_data.password)
    
    # Generate API key
    user.generate_api_key()
    
    # Save to database
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User {user.username} created by admin {current_user.get('username')}")
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user due to constraint violation"
        )


@router.put("/{user_id}", response_model=UserInDB)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update a user (admin only).
    
    Args:
        user_id: User ID
        user_data: User data to update
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Updated user information
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_data.username is not None:
        # Check if new username is unique
        if (user_data.username != user.username and 
                db.query(User).filter(User.username == user_data.username).first()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = user_data.username
    
    if user_data.email is not None:
        # Check if new email is unique
        if (user_data.email != user.email and 
                db.query(User).filter(User.email == user_data.email).first()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = user_data.email
    
    if user_data.password is not None:
        user.set_password(user_data.password)
    
    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin
    
    # Save changes
    try:
        db.commit()
        db.refresh(user)
        
        logger.info(f"User {user.username} updated by admin {current_user.get('username')}")
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update user due to constraint violation"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user (admin only).
    
    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        db: Database session
    """
    # Prevent deleting yourself
    if user_id == current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    db.delete(user)
    db.commit()
    
    logger.info(f"User {user.username} deleted by admin {current_user.get('username')}")


@router.post("/{user_id}/api-key", response_model=UserWithApiKey)
async def generate_api_key(
    user_id: str,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new API key for a user (admin only).
    
    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        User with new API key
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate new API key
    api_key = user.generate_api_key()
    
    # Save changes
    db.commit()
    db.refresh(user)
    
    logger.info(f"New API key generated for {user.username} by admin {current_user.get('username')}")
    return user