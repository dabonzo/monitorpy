"""
Health check endpoints for the MonitorPy FastAPI implementation.

This module defines API endpoints for health checks.
"""

import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from monitorpy.fastapi_api.redis import RedisCache, get_redis
from redis import Redis


router = APIRouter()


class HealthStatus(BaseModel):
    """Health status response model."""
    
    status: str
    message: str
    timestamp: str
    redis_available: bool
    cache_enabled: bool


# Create a Redis cache for health checks
health_cache = RedisCache[HealthStatus](HealthStatus, prefix="health")


@router.get("", response_model=HealthStatus)
async def health_check(redis: Redis = Depends(get_redis)):
    """
    Simple health check endpoint.
    
    Returns information about the API status.
    Uses Redis for caching if available.
    """
    # Try to get from cache first
    cached_status = health_cache.get("status")
    if cached_status:
        return cached_status
    
    # Generate new status
    redis_available = True
    try:
        # Test Redis connection
        redis.ping()
    except Exception:
        redis_available = False
    
    # Create response
    status = HealthStatus(
        status="ok",
        message="MonitorPy API is running",
        timestamp=datetime.datetime.utcnow().isoformat(),
        redis_available=redis_available,
        cache_enabled=health_cache.redis.client.get("dummy_test") != "connection_failed"
    )
    
    # Cache the result
    health_cache.set("status", status)
    
    return status