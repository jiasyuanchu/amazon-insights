#!/usr/bin/env python3
"""
Rate Limiting System for Amazon Insights API
Implements sliding window rate limiting with Redis backend
"""

import time
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

import redis
from fastapi import HTTPException, Request, Depends

from config.config import REDIS_URL
from src.auth.authentication import APIKey, RateLimitTier, get_current_api_key

logger = logging.getLogger(__name__)

class RateLimitWindow(str, Enum):
    MINUTE = "minute"
    HOUR = "hour" 
    DAY = "day"

class RateLimitConfig:
    """Rate limit configuration for different tiers"""
    
    TIER_LIMITS = {
        RateLimitTier.FREE: {
            RateLimitWindow.MINUTE: 60,
            RateLimitWindow.HOUR: 1000,
            RateLimitWindow.DAY: 10000
        },
        RateLimitTier.PRO: {
            RateLimitWindow.MINUTE: 300,
            RateLimitWindow.HOUR: 10000,
            RateLimitWindow.DAY: 100000
        },
        RateLimitTier.ENTERPRISE: {
            RateLimitWindow.MINUTE: 1000,
            RateLimitWindow.HOUR: 50000,
            RateLimitWindow.DAY: 1000000
        }
    }
    
    # Endpoint-specific weight multipliers
    ENDPOINT_WEIGHTS = {
        "/api/v1/products/track": 10,          # Expensive: external API call
        "/api/v1/competitive/analyze": 50,     # Very expensive: complex analysis
        "/api/v1/products/track-all": 100,     # Extremely expensive: batch operation
        "/api/v1/products/summary": 1,         # Cheap: cached read
        "/api/v1/competitive/groups": 1,       # Cheap: database read
        "/api/v1/system/health": 0.1,          # Nearly free: health check
    }

class RateLimiter:
    """Redis-based sliding window rate limiter"""
    
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)
        self.config = RateLimitConfig()
    
    async def check_rate_limit(self, api_key: APIKey, endpoint: str, request: Request) -> Dict[str, any]:
        """Check if request is within rate limits"""
        
        # Get endpoint weight
        weight = self._get_endpoint_weight(endpoint)
        
        # Check each time window
        rate_limit_info = {
            "allowed": True,
            "limits": {},
            "usage": {},
            "reset_times": {},
            "retry_after": None
        }
        
        for window in RateLimitWindow:
            limit = self.config.TIER_LIMITS[api_key.tier][window]
            usage, reset_time = self._check_window_limit(
                api_key.key_id, window, limit, weight
            )
            
            rate_limit_info["limits"][window.value] = limit
            rate_limit_info["usage"][window.value] = usage
            rate_limit_info["reset_times"][window.value] = reset_time
            
            # If any window is exceeded, deny request
            if usage > limit:
                rate_limit_info["allowed"] = False
                rate_limit_info["retry_after"] = reset_time
                break
        
        return rate_limit_info
    
    def _check_window_limit(self, key_id: str, window: RateLimitWindow, 
                           limit: int, weight: float) -> Tuple[int, int]:
        """Check rate limit for specific time window"""
        
        now = time.time()
        window_seconds = self._get_window_seconds(window)
        window_start = now - window_seconds
        
        # Redis key for this window
        redis_key = f"rate_limit:{key_id}:{window.value}"
        
        # Use Redis sorted set for sliding window
        pipe = self.redis.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(redis_key, 0, window_start)
        
        # Count current usage
        pipe.zcard(redis_key)
        
        # Add current request
        pipe.zadd(redis_key, {str(now): weight})
        
        # Set expiration
        pipe.expire(redis_key, window_seconds + 60)  # Extra buffer
        
        results = pipe.execute()
        current_usage = results[1] + weight  # Current count + new request weight
        
        # Calculate reset time
        reset_time = int(now + window_seconds)
        
        return int(current_usage), reset_time
    
    def _get_window_seconds(self, window: RateLimitWindow) -> int:
        """Get window duration in seconds"""
        window_map = {
            RateLimitWindow.MINUTE: 60,
            RateLimitWindow.HOUR: 3600,
            RateLimitWindow.DAY: 86400
        }
        return window_map[window]
    
    def _get_endpoint_weight(self, endpoint: str) -> float:
        """Get weight multiplier for endpoint"""
        # Extract base path without parameters
        base_path = endpoint.split('?')[0]
        
        # Check for exact matches first
        if base_path in self.config.ENDPOINT_WEIGHTS:
            return self.config.ENDPOINT_WEIGHTS[base_path]
        
        # Check for pattern matches
        for pattern, weight in self.config.ENDPOINT_WEIGHTS.items():
            if pattern in base_path:
                return weight
        
        # Default weight
        return 1.0
    
    async def get_rate_limit_status(self, api_key: APIKey) -> Dict[str, any]:
        """Get current rate limit status for API key"""
        
        status = {
            "key_id": api_key.key_id[:15] + "...",  # Masked key
            "tier": api_key.tier.value,
            "windows": {}
        }
        
        for window in RateLimitWindow:
            limit = self.config.TIER_LIMITS[api_key.tier][window]
            redis_key = f"rate_limit:{api_key.key_id}:{window.value}"
            
            # Get current usage
            current_usage = self.redis.zcard(redis_key)
            remaining = max(0, limit - current_usage)
            
            # Get reset time
            now = time.time()
            window_seconds = self._get_window_seconds(window)
            reset_time = int(now + window_seconds)
            
            status["windows"][window.value] = {
                "limit": limit,
                "used": current_usage,
                "remaining": remaining,
                "reset_at": reset_time,
                "reset_at_iso": datetime.fromtimestamp(reset_time).isoformat()
            }
        
        return status

# Global rate limiter instance
rate_limiter = RateLimiter()

# FastAPI dependency for rate limiting
async def check_rate_limit(request: Request, 
                          api_key: APIKey = Depends(get_current_api_key)) -> APIKey:
    """FastAPI dependency for rate limiting"""
    
    # Check rate limits
    rate_limit_info = await rate_limiter.check_rate_limit(
        api_key, request.url.path, request
    )
    
    if not rate_limit_info["allowed"]:
        # Add rate limit headers to error response
        headers = {
            "X-RateLimit-Limit": str(rate_limit_info["limits"]["minute"]),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(rate_limit_info["reset_times"]["minute"]),
            "X-RateLimit-Tier": api_key.tier.value,
            "Retry-After": str(rate_limit_info["retry_after"] - int(time.time()))
        }
        
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before making more requests.",
            headers=headers
        )
    
    # Add rate limit headers to successful response
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(rate_limit_info["limits"]["minute"]),
        "X-RateLimit-Remaining": str(rate_limit_info["limits"]["minute"] - rate_limit_info["usage"]["minute"]),
        "X-RateLimit-Reset": str(rate_limit_info["reset_times"]["minute"]),
        "X-RateLimit-Tier": api_key.tier.value
    }
    
    return api_key

# Utility functions
async def get_rate_limit_status(api_key: APIKey = Depends(get_current_api_key)) -> Dict[str, any]:
    """Get rate limit status for current API key"""
    return await rate_limiter.get_rate_limit_status(api_key)

def create_rate_limit_middleware():
    """Create FastAPI middleware for adding rate limit headers"""
    
    async def rate_limit_middleware(request: Request, call_next):
        response = await call_next(request)
        
        # Add rate limit headers if available
        if hasattr(request.state, 'rate_limit_headers'):
            for header, value in request.state.rate_limit_headers.items():
                response.headers[header] = value
        
        return response
    
    return rate_limit_middleware