"""
Batch operation endpoints for the MonitorPy FastAPI implementation.

This module defines API endpoints for batch operations,
allowing multiple checks to be run in parallel.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from monitorpy.core.batch_runner import run_checks_in_parallel
from monitorpy.fastapi_api.database import get_db
from monitorpy.fastapi_api.deps import get_current_user
from monitorpy.fastapi_api.models import Check, Result

router = APIRouter()


class BatchRunRequest(BaseModel):
    """Model for batch run request."""
    
    checks: List[str]
    max_workers: Optional[int] = None
    timeout: Optional[float] = None


class AdHocCheckConfig(BaseModel):
    """Model for ad-hoc check configuration."""
    
    plugin_type: str
    config: Dict
    id: Optional[str] = None


class BatchRunAdHocRequest(BaseModel):
    """Model for batch run ad-hoc request."""
    
    checks: List[AdHocCheckConfig]
    max_workers: Optional[int] = None
    timeout: Optional[float] = None


@router.post("/run")
async def batch_run_checks(
    request: BatchRunRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
):
    """
    Run multiple checks in parallel.
    
    Executes multiple checks by ID in parallel and stores the results.
    """
    # Get all checks from database
    checks = db.query(Check).filter(Check.id.in_(request.checks)).all()
    
    if not checks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid checks found for the provided IDs",
        )
    
    # Convert checks to the format expected by run_checks_in_parallel
    check_configs = [
        {
            "id": check.id,
            "plugin_type": check.plugin_type,
            "config": check.get_config(),
        }
        for check in checks
    ]
    
    try:
        # Run the checks in parallel
        check_results = run_checks_in_parallel(
            check_configs, request.max_workers, request.timeout
        )
        
        # Store results in the database
        stored_results = []
        for check_config, result in check_results:
            try:
                check_id = check_config["id"]
                
                # Create and store result
                db_result = Result.from_check_result(check_id, result)
                db.add(db_result)
                
                # Update check's last run timestamp
                check = db.query(Check).get(check_id)
                if check:
                    check.last_run = db_result.executed_at
                
                stored_results.append(
                    {"check_id": check_id, "result": result.to_dict()}
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error storing result for check {check_config.get('id')}: {e}",
                )
        
        db.commit()
        
        return {"results": stored_results}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing batch checks: {str(e)}",
        )


@router.post("/run-ad-hoc")
async def batch_run_ad_hoc_checks(
    request: BatchRunAdHocRequest,
    current_user: Dict = Depends(get_current_user),
):
    """
    Run multiple ad-hoc checks in parallel without storing results.
    
    Executes multiple ad-hoc checks in parallel without storing
    the configurations or results.
    """
    # Convert model to dictionary format for run_checks_in_parallel
    check_configs = [check.dict() for check in request.checks]
    
    try:
        # Run the checks in parallel
        check_results = run_checks_in_parallel(
            check_configs, request.max_workers, request.timeout
        )
        
        # Format results without storing in database
        results = [
            {
                "plugin_type": check_config.get("plugin_type"),
                "id": check_config.get("id", f"ad-hoc-{i}"),
                "result": result.to_dict(),
            }
            for i, (check_config, result) in enumerate(check_results)
        ]
        
        return {"results": results}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing batch checks: {str(e)}",
        )