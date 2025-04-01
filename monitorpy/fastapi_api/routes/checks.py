"""
Check endpoints for the MonitorPy FastAPI implementation.

This module defines API endpoints for check operations.
"""

from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from monitorpy.core.registry import run_check as execute_check
from monitorpy.fastapi_api.database import get_db
from monitorpy.fastapi_api.deps import get_current_user
from monitorpy.fastapi_api.models import Check, CheckCreate, CheckUpdate, CheckInDB, Result, ResultInDB, PaginatedChecks
from monitorpy.fastapi_api.config import settings

router = APIRouter()


@router.get("", response_model=PaginatedChecks)
async def get_checks(
    page: int = Query(1, ge=1),
    per_page: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    enabled: Optional[bool] = None,
    plugin_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Get a list of all configured checks.
    
    Supports pagination and filtering by enabled status and plugin type.
    """
    # Create base query
    query = db.query(Check)
    
    # Apply filters
    if enabled is not None:
        query = query.filter(Check.enabled == enabled)
    
    if plugin_type is not None:
        query = query.filter(Check.plugin_type == plugin_type)
    
    # Get total count
    total = query.count()
    
    # Calculate pagination parameters
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    # Execute query with pagination
    checks = query.order_by(Check.created_at.desc()).offset(offset).limit(per_page).all()
    
    # Return paginated response
    return {
        "checks": checks,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    }


@router.get("/{check_id}", response_model=CheckInDB)
async def get_check(
    check_id: str,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Get a specific check configuration.
    """
    check = db.query(Check).get(check_id)
    
    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check not found",
        )
    
    return check


@router.post("", response_model=CheckInDB, status_code=status.HTTP_201_CREATED)
async def create_check(
    check_data: CheckCreate,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Create a new check configuration.
    """
    try:
        # Create new check
        check = Check()
        check.id = Check.id.default()
        check.name = check_data.name
        check.plugin_type = check_data.plugin_type
        check.set_config(check_data.config)
        check.enabled = check_data.enabled
        check.schedule = check_data.schedule
        
        db.add(check)
        db.commit()
        db.refresh(check)
        
        return check
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.put("/{check_id}", response_model=CheckInDB)
async def update_check(
    check_id: str,
    check_data: CheckUpdate,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Update an existing check configuration.
    """
    check = db.query(Check).get(check_id)
    
    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check not found",
        )
    
    try:
        # Update fields if provided
        if check_data.name is not None:
            check.name = check_data.name
        
        if check_data.plugin_type is not None:
            check.plugin_type = check_data.plugin_type
        
        if check_data.config is not None:
            check.set_config(check_data.config)
        
        if check_data.enabled is not None:
            check.enabled = check_data.enabled
        
        if check_data.schedule is not None:
            check.schedule = check_data.schedule
        
        db.commit()
        db.refresh(check)
        
        return check
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.delete("/{check_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_check(
    check_id: str,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Delete a check configuration.
    """
    check = db.query(Check).get(check_id)
    
    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check not found",
        )
    
    try:
        db.delete(check)
        db.commit()
        
        return None
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post("/{check_id}/run", response_model=ResultInDB)
async def run_check(
    check_id: str,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Run a check immediately and store the result.
    """
    check = db.query(Check).get(check_id)
    
    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check not found",
        )
    
    try:
        # Run the check
        config = check.get_config()
        check_result = execute_check(check.plugin_type, config)
        
        # Store the result
        result = Result.from_check_result(check_id, check_result)
        
        db.add(result)
        check.last_run = result.executed_at
        db.commit()
        db.refresh(result)
        
        return result
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running check: {str(e)}",
        )


@router.post("/run", response_model=Dict[str, Any])
async def run_ad_hoc_check(
    check_data: dict,
    current_user: Dict = Depends(get_current_user),
):
    """
    Run an ad-hoc check without storing configuration.
    """
    # Validate required fields
    if "plugin_type" not in check_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: plugin_type",
        )
    
    if "config" not in check_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: config",
        )
    
    try:
        # Run the check
        check_result = execute_check(check_data["plugin_type"], check_data["config"])
        
        # Return the result without storing
        return check_result.to_dict()
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running check: {str(e)}",
        )