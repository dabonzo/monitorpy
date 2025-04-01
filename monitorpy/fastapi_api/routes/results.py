"""
Result endpoints for the MonitorPy FastAPI implementation.

This module defines API endpoints for result operations.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from monitorpy.fastapi_api.database import get_db
from monitorpy.fastapi_api.deps import get_current_user
from monitorpy.fastapi_api.models import Result, ResultInDB, PaginatedResults
from monitorpy.fastapi_api.config import settings

router = APIRouter()


@router.get("", response_model=PaginatedResults)
async def get_results(
    page: int = Query(1, ge=1),
    per_page: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    check_id: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Get a list of check results.
    
    Supports pagination and filtering by check ID, status, and date range.
    """
    # Create base query
    query = db.query(Result)
    
    # Apply filters
    if check_id:
        query = query.filter(Result.check_id == check_id)
    
    if status:
        query = query.filter(Result.status == status)
    
    # Date filtering
    if from_date:
        try:
            from_date_obj = datetime.fromisoformat(from_date)
            query = query.filter(Result.executed_at >= from_date_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid from_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
            )
    
    if to_date:
        try:
            to_date_obj = datetime.fromisoformat(to_date)
            query = query.filter(Result.executed_at <= to_date_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid to_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
            )
    
    # Get total count
    total = query.count()
    
    # Calculate pagination parameters
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    # Execute query with pagination
    results = query.order_by(desc(Result.executed_at)).offset(offset).limit(per_page).all()
    
    # Return paginated response
    return {
        "results": results,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    }


@router.get("/{result_id}", response_model=ResultInDB)
async def get_result(
    result_id: str,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Get a specific check result.
    """
    result = db.query(Result).get(result_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found",
        )
    
    return result


@router.get("/check/{check_id}", response_model=PaginatedResults)
async def get_check_results(
    check_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Get results for a specific check.
    
    Supports pagination and filtering by status and date range.
    """
    # Create base query
    query = db.query(Result).filter(Result.check_id == check_id)
    
    # Apply filters
    if status:
        query = query.filter(Result.status == status)
    
    # Date filtering
    if from_date:
        try:
            from_date_obj = datetime.fromisoformat(from_date)
            query = query.filter(Result.executed_at >= from_date_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid from_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
            )
    
    if to_date:
        try:
            to_date_obj = datetime.fromisoformat(to_date)
            query = query.filter(Result.executed_at <= to_date_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid to_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
            )
    
    # Get total count
    total = query.count()
    
    # Calculate pagination parameters
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    # Execute query with pagination
    results = query.order_by(desc(Result.executed_at)).offset(offset).limit(per_page).all()
    
    # Return paginated response
    return {
        "results": results,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    }


@router.get("/summary")
async def get_results_summary(
    period: str = Query("day", regex="^(day|week|month)$"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Get a summary of check results.
    
    Provides counts and percentages by status for the specified time period.
    """
    # Calculate date range
    now = datetime.utcnow()
    
    if period == "week":
        from_date = now - timedelta(days=7)
    elif period == "month":
        from_date = now - timedelta(days=30)
    else:  # day or invalid input
        from_date = now - timedelta(days=1)
    
    # Get counts by status
    success_count = db.query(Result).filter(
        Result.status == "success",
        Result.executed_at >= from_date
    ).count()
    
    warning_count = db.query(Result).filter(
        Result.status == "warning",
        Result.executed_at >= from_date
    ).count()
    
    error_count = db.query(Result).filter(
        Result.status == "error",
        Result.executed_at >= from_date
    ).count()
    
    total_count = success_count + warning_count + error_count
    
    # Calculate percentages
    success_percent = (success_count / total_count * 100) if total_count > 0 else 0
    warning_percent = (warning_count / total_count * 100) if total_count > 0 else 0
    error_percent = (error_count / total_count * 100) if total_count > 0 else 0
    
    return {
        "period": period,
        "from_date": from_date.isoformat(),
        "to_date": now.isoformat(),
        "total_checks": total_count,
        "statuses": {
            "success": {
                "count": success_count,
                "percent": round(success_percent, 2)
            },
            "warning": {
                "count": warning_count,
                "percent": round(warning_percent, 2)
            },
            "error": {
                "count": error_count,
                "percent": round(error_percent, 2)
            }
        }
    }