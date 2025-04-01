# Redis Integration Guide

MonitorPy integrates Redis for enhanced performance and scalability. This guide explains how Redis is used in the application and how to leverage it for your custom functionality.

## Key Features

1. **Response Caching**: Improve API performance by caching frequently accessed data
2. **Type-safe Caching**: Generic caching system that works with Pydantic models
3. **Graceful Degradation**: Automatic fallback when Redis is unavailable
4. **Dependency Injection**: Redis is available as a FastAPI dependency

## Configuration

Redis settings are configured through environment variables:

```yaml
# In docker-compose.yml or .env file
REDIS_URL=redis://redis:6379/0
USE_REDIS_CACHE=true
CACHE_EXPIRATION=300  # Cache expiration in seconds
```

## Basic Usage

### Direct Redis Access

Use the Redis client directly when you need low-level control:

```python
from monitorpy.fastapi_api.redis import get_redis
from fastapi import Depends

@router.get("/items/{item_id}")
async def get_item(item_id: str, redis: Redis = Depends(get_redis)):
    # Use Redis directly
    cached_item = redis.get(f"item:{item_id}")
    if cached_item:
        return json.loads(cached_item)
        
    # Fetch from database if not cached
    # ...
```

### Model Caching

For more structured caching, use the `RedisCache` class with Pydantic models:

```python
from monitorpy.fastapi_api.redis import RedisCache
from pydantic import BaseModel

class Item(BaseModel):
    id: str
    name: str
    description: str
    
# Create a cache for Items
item_cache = RedisCache[Item](Item, prefix="item")

@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str):
    # Try to get from cache
    cached_item = item_cache.get(item_id)
    if cached_item:
        return cached_item
        
    # Fetch from database
    db_item = fetch_item_from_db(item_id)
    item = Item(**db_item)
    
    # Cache the result
    item_cache.set(item_id, item)
    
    return item
```

## Advanced Patterns

### Cache Invalidation

Cache invalidation is crucial when data changes:

```python
@router.put("/items/{item_id}")
async def update_item(item_id: str, item: Item):
    # Update in database
    update_item_in_db(item_id, item)
    
    # Invalidate cache
    item_cache.delete(item_id)
    
    return {"status": "success"}
```

### Batch Operations

For efficient operations, consider batching Redis commands:

```python
# Get multiple items at once
def get_multiple_items(item_ids: List[str]):
    # Create a pipeline for batched operations
    pipeline = redis_client.pipeline()
    
    # Add commands to the pipeline
    for item_id in item_ids:
        pipeline.get(f"item:{item_id}")
    
    # Execute all commands in a single round-trip
    results = pipeline.execute()
    
    return results
```

### Background Tasks

Redis can be used with FastAPI background tasks:

```python
from fastapi import BackgroundTasks

@router.post("/items/")
async def create_item(item: Item, background_tasks: BackgroundTasks):
    # Store item in database
    db_item = store_item_in_db(item)
    
    # Schedule a background task
    background_tasks.add_task(process_item_async, db_item.id)
    
    return {"status": "success", "id": db_item.id}
    
def process_item_async(item_id: str):
    # Process the item in the background
    # This runs after the response is sent
    process_item(item_id)
    
    # Update cache after processing
    processed_item = get_processed_item(item_id)
    item_cache.set(item_id, processed_item)
```

## Best Practices

1. **Cache Selectively**: Cache only frequently accessed, relatively static data
2. **Set Appropriate TTLs**: Choose expiration times based on data volatility
3. **Handle Failures Gracefully**: Always have a fallback when Redis is unavailable
4. **Monitor Cache Hit Rates**: Track performance to optimize caching strategy
5. **Be Careful with Mutable Data**: Consider the implications of eventual consistency

## Health Monitoring

The API provides Redis status in the health check endpoint:

```
GET /api/v1/health
```

Response:
```json
{
  "status": "ok",
  "message": "MonitorPy API is running",
  "timestamp": "2023-04-02T12:34:56.789",
  "redis_available": true,
  "cache_enabled": true
}
```

## Disabling Redis

To disable Redis caching temporarily:

```
USE_REDIS_CACHE=false
```

The application will continue to function normally without caching.