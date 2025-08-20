import sys
import os
from fastapi import APIRouter, HTTPException
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.models.schemas import SystemStatus
from src.monitoring.product_tracker import ProductTracker
from src.api.firecrawl_client import FirecrawlClient
from src.models.product_models import DatabaseManager
from src.cache.redis_service import cache, CacheKeyBuilder, CACHE_SHORT_TTL
from config.config import AMAZON_ASINS, FIRECRAWL_API_KEY

router = APIRouter(prefix="/api/v1/system", tags=["System"])

@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """
    Get system status
    """
    # Try to get from cache
    cache_key = CacheKeyBuilder.system_status()
    cached_status = cache.get(cache_key)
    if cached_status:
        return cached_status
    
    try:
        # Check database connection
        database_connected = True
        try:
            db_manager = DatabaseManager()
            # Try a simple query
            db_manager.get_session().close()
        except:
            database_connected = False
        
        # Check Firecrawl availability
        firecrawl_available = True
        try:
            if not FIRECRAWL_API_KEY:
                firecrawl_available = False
            else:
                client = FirecrawlClient()
        except:
            firecrawl_available = False
        
        # Check cache availability
        cache_info = cache.get_info()
        cache_available = cache_info.get("connected", False)
        
        # Determine overall status
        if database_connected and firecrawl_available and cache_available:
            status = "healthy"
        elif database_connected and (firecrawl_available or cache_available):
            status = "degraded"
        else:
            status = "unhealthy"
        
        system_status = SystemStatus(
            status=status,
            database_connected=database_connected,
            firecrawl_available=firecrawl_available,
            monitored_asins=AMAZON_ASINS,
            last_check=datetime.now().isoformat()
        )
        
        # Cache result (5 minutes, system status changes infrequently but needs to be relatively real-time)
        cache.set(cache_key, system_status, 300)
        
        return system_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Simple health check endpoint
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@router.post("/test")
async def test_system():
    """
    Test all system components
    """
    try:
        results = {
            "database": False,
            "firecrawl": False,
            "overall": False
        }
        
        # Test database
        try:
            db_manager = DatabaseManager()
            session = db_manager.get_session()
            session.close()
            results["database"] = True
        except Exception as e:
            results["database_error"] = str(e)
        
        # Test Firecrawl
        try:
            if FIRECRAWL_API_KEY:
                client = FirecrawlClient()
                results["firecrawl"] = True
            else:
                results["firecrawl_error"] = "API key not configured"
        except Exception as e:
            results["firecrawl_error"] = str(e)
        
        results["overall"] = results["database"] and results["firecrawl"]
        
        return {
            "test_results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))