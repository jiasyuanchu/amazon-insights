import sys
import os
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.cache.redis_service import cache, CacheKeyBuilder

router = APIRouter(prefix="/api/v1/cache", tags=["Cache Management"])


@router.get("/info", response_model=Dict[str, Any])
async def get_cache_info():
    """
    Get cache system information
    """
    try:
        return cache.get_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear/{pattern}")
async def clear_cache_pattern(pattern: str):
    """
    Clear cache matching pattern
    """
    try:
        if pattern == "all":
            result = cache.flush_all()
            return {
                "message": "All cache cleared" if result else "Cache clear failed",
                "success": result,
            }

        deleted_count = cache.delete_pattern(f"*{pattern}*")
        return {
            "message": f"Cleared {deleted_count} cache entries matching pattern: {pattern}",
            "deleted_count": deleted_count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear/product/{asin}")
async def clear_product_cache(asin: str):
    """
    Clear cache for specific product
    """
    try:
        keys_cleared = []

        # Clear product summary
        summary_key = CacheKeyBuilder.product_summary(asin)
        if cache.delete(summary_key):
            keys_cleared.append(summary_key)

        # Clear product history (common limit values)
        for limit in [10, 20, 30, 50, 100]:
            history_key = CacheKeyBuilder.product_history(asin, limit)
            if cache.delete(history_key):
                keys_cleared.append(history_key)

        # Clear related alert cache
        for hours in [24, 48, 72]:
            alert_key = CacheKeyBuilder.alerts_by_asin(asin, hours)
            if cache.delete(alert_key):
                keys_cleared.append(alert_key)

        # Clear all products summary cache
        all_summary_key = CacheKeyBuilder.all_products_summary()
        if cache.delete(all_summary_key):
            keys_cleared.append(all_summary_key)

        return {
            "message": f"Cleared cache for product {asin}",
            "keys_cleared": keys_cleared,
            "count": len(keys_cleared),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_cache_stats():
    """
    Get cache statistics information
    """
    try:
        info = cache.get_info()

        if not info.get("connected", False):
            return {"error": "Cache not connected", "info": info}

        # Try to get information for some cache keys
        sample_keys = [
            CacheKeyBuilder.all_products_summary(),
            CacheKeyBuilder.system_status(),
            CacheKeyBuilder.alerts_summary(24),
        ]

        key_stats = {}
        for key in sample_keys:
            exists = cache.exists(key)
            ttl = cache.ttl(key) if exists else -1
            key_stats[key] = {
                "exists": exists,
                "ttl": ttl,
                "ttl_hours": round(ttl / 3600, 2) if ttl > 0 else ttl,
            }

        return {"cache_info": info, "sample_keys": key_stats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
