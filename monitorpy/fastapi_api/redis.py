"""
Redis configuration for MonitorPy FastAPI implementation.

Provides Redis client configuration, cache utilities, and background task queue.
"""

import os
import json
from typing import Any, Optional, TypeVar, Generic, Type, Dict, Union, List
from fastapi import Depends

from redis import Redis
from pydantic import BaseModel

from monitorpy.fastapi_api.config import settings
from monitorpy.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RedisClient:
    """Redis client connection manager."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one Redis connection."""
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._client = None
        return cls._instance
    
    @property
    def client(self) -> Redis:
        """Get Redis client, initializing if needed."""
        if self._client is None:
            try:
                self._client = Redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    retry_on_timeout=True
                )
                logger.info(f"Connected to Redis at {settings.REDIS_URL}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                # Return a dummy client that won't raise errors when methods are called
                self._client = DummyRedis()
        return self._client
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        return self.client.get(key)
    
    def set(self, key: str, value: str, expiration: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration in seconds."""
        return self.client.set(key, value, ex=expiration)
    
    def delete(self, key: str) -> int:
        """Delete value from Redis."""
        return self.client.delete(key)


class DummyRedis:
    """
    Dummy Redis client that acts as a no-op when Redis is unavailable.
    Prevents application from crashing when Redis is down.
    """
    
    def get(self, key: str) -> None:
        """Dummy get operation."""
        logger.debug(f"DummyRedis: get({key})")
        return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Dummy set operation."""
        logger.debug(f"DummyRedis: set({key}, {value}, ex={ex})")
        return True
    
    def delete(self, key: str) -> int:
        """Dummy delete operation."""
        logger.debug(f"DummyRedis: delete({key})")
        return 0


class RedisCache(Generic[T]):
    """
    Generic Redis cache manager that can store and retrieve Pydantic models.
    """
    
    def __init__(self, model_class: Type[T], prefix: str = "cache"):
        """
        Initialize the cache.
        
        Args:
            model_class: The Pydantic model class to cache
            prefix: Redis key prefix
        """
        self.model_class = model_class
        self.prefix = prefix
        self.redis = RedisClient()
        self.expiration = settings.CACHE_EXPIRATION
    
    def _get_key(self, key: str) -> str:
        """Generate a Redis key with prefix."""
        return f"{self.prefix}:{key}"
    
    def get(self, key: str) -> Optional[T]:
        """
        Get a cached value and deserialize it.
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized object or None if not found
        """
        if not settings.USE_REDIS_CACHE:
            return None
            
        try:
            value = self.redis.get(self._get_key(key))
            if value:
                data = json.loads(value)
                return self.model_class.parse_obj(data)
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
        return None
    
    def set(self, key: str, value: T) -> bool:
        """
        Serialize and cache a value.
        
        Args:
            key: Cache key
            value: Object to cache
            
        Returns:
            True if successful, False otherwise
        """
        if not settings.USE_REDIS_CACHE:
            return False
            
        try:
            if isinstance(value, BaseModel):
                data = value.dict()
            else:
                data = value
            return self.redis.set(
                self._get_key(key),
                json.dumps(data),
                expiration=self.expiration
            )
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a cached value.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not settings.USE_REDIS_CACHE:
            return False
            
        try:
            return bool(self.redis.delete(self._get_key(key)))
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False


def get_redis() -> Redis:
    """
    Dependency to get Redis client.
    
    Returns:
        Redis client
    """
    return RedisClient().client