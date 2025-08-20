import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis
import pickle
from functools import wraps

from config.config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, REDIS_URL,
    CACHE_ENABLED, CACHE_DEFAULT_TTL, CACHE_LONG_TTL, CACHE_SHORT_TTL
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheKeyBuilder:
    """Cache key builder"""
    
    @staticmethod
    def product_summary(asin: str) -> str:
        return f"product:summary:{asin}"
    
    @staticmethod
    def product_raw_data(asin: str) -> str:
        return f"product:raw:{asin}"
    
    @staticmethod
    def product_history(asin: str, limit: int = 20) -> str:
        return f"product:history:{asin}:{limit}"
    
    @staticmethod
    def all_products_summary() -> str:
        return "products:all:summary"
    
    @staticmethod
    def alerts_summary(hours: int = 24) -> str:
        return f"alerts:summary:{hours}"
    
    @staticmethod
    def alerts_by_asin(asin: str, hours: int = 24) -> str:
        return f"alerts:asin:{asin}:{hours}"
    
    @staticmethod
    def system_status() -> str:
        return "system:status"

class RedisCache:
    """Redis cache service"""
    
    def __init__(self):
        self.enabled = CACHE_ENABLED
        self.client = None
        
        if self.enabled:
            try:
                # Try to connect to Redis
                self.client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=REDIS_DB,
                    password=REDIS_PASSWORD,
                    decode_responses=False,  # Use binary mode to support pickle
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
                
                # Test connection
                self.client.ping()
                logger.info("Redis cache initialized successfully")
                
            except Exception as e:
                logger.warning(f"Redis connection failed: {str(e)}. Cache disabled.")
                self.enabled = False
                self.client = None
        else:
            logger.info("Redis cache disabled by configuration")
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data"""
        try:
            return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
            return None
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data"""
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Deserialization error: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = CACHE_DEFAULT_TTL) -> bool:
        """Set cache"""
        if not self.enabled or not self.client:
            return False
        
        try:
            serialized_data = self._serialize(value)
            if serialized_data is None:
                return False
            
            result = self.client.setex(key, ttl, serialized_data)
            if result:
                logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return result
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache"""
        if not self.enabled or not self.client:
            return None
        
        try:
            data = self.client.get(key)
            if data is None:
                logger.debug(f"Cache miss: {key}")
                return None
            
            result = self._deserialize(data)
            if result is not None:
                logger.debug(f"Cache hit: {key}")
            return result
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete cache"""
        if not self.enabled or not self.client:
            return False
        
        try:
            result = self.client.delete(key)
            if result:
                logger.debug(f"Cache deleted: {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete cache keys matching pattern"""
        if not self.enabled or not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cache pattern deleted: {pattern}, count: {deleted}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Cache pattern delete error for pattern {pattern}: {str(e)}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if cache exists"""
        if not self.enabled or not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get remaining expiration time"""
        if not self.enabled or not self.client:
            return -1
        
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {str(e)}")
            return -1
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time"""
        if not self.enabled or not self.client:
            return False
        
        try:
            result = self.client.expire(key, ttl)
            if result:
                logger.debug(f"Cache expire set: {key} (TTL: {ttl}s)")
            return result
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {str(e)}")
            return False
    
    def flush_all(self) -> bool:
        """Clear all cache"""
        if not self.enabled or not self.client:
            return False
        
        try:
            result = self.client.flushdb()
            logger.info("All cache flushed")
            return result
        except Exception as e:
            logger.error(f"Cache flush error: {str(e)}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get cache information"""
        if not self.enabled or not self.client:
            return {"enabled": False, "connected": False}
        
        try:
            info = self.client.info()
            return {
                "enabled": True,
                "connected": True,
                "memory_used": info.get('used_memory_human', 'N/A'),
                "total_keys": info.get('db0', {}).get('keys', 0) if 'db0' in info else 0,
                "redis_version": info.get('redis_version', 'N/A')
            }
        except Exception as e:
            logger.error(f"Cache info error: {str(e)}")
            return {"enabled": True, "connected": False, "error": str(e)}

# Global cache instance
cache = RedisCache()

def cached(ttl: int = CACHE_DEFAULT_TTL, key_prefix: str = ""):
    """Cache decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache.enabled:
                return func(*args, **kwargs)
            
            # Build cache key
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{':'.join(str(arg) for arg in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute original function
            result = func(*args, **kwargs)
            
            # Store to cache
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator