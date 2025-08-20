import sys
import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import tasks
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from tasks import track_single_product, track_all_products, daily_monitoring, manual_full_update

router = APIRouter(prefix="/api/v1/tasks", tags=["Background Tasks"])

@router.post("/track/{asin}")
async def trigger_track_single(asin: str):
    """
    Trigger background tracking for single product
    """
    try:
        # Trigger Celery task
        task = track_single_product.delay(asin)
        
        return {
            "success": True,
            "task_id": task.id,
            "message": f"Background tracking started for {asin}",
            "status_url": f"/api/v1/tasks/status/{task.id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track-all")
async def trigger_track_all():
    """
    Trigger background tracking for all products
    """
    try:
        # Trigger Celery task
        task = track_all_products.delay()
        
        return {
            "success": True,
            "task_id": task.id,
            "message": "Background tracking started for all products",
            "status_url": f"/api/v1/tasks/status/{task.id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/daily-monitoring")
async def trigger_daily_monitoring():
    """
    Manually trigger daily monitoring task
    """
    try:
        # Trigger Celery task
        task = daily_monitoring.delay()
        
        return {
            "success": True,
            "task_id": task.id,
            "message": "Daily monitoring task started",
            "status_url": f"/api/v1/tasks/status/{task.id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/full-update")
async def trigger_full_update():
    """
    Trigger full system update (clear cache + track all)
    """
    try:
        # Trigger Celery task
        task = manual_full_update.delay()
        
        return {
            "success": True,
            "task_id": task.id,
            "message": "Full system update started",
            "status_url": f"/api/v1/tasks/status/{task.id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of a background task
    """
    try:
        from celery_config import app
        
        # Get task result
        task_result = app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
            "successful": task_result.successful() if task_result.ready() else None,
            "failed": task_result.failed() if task_result.ready() else None,
        }
        
        # Add result if available
        if task_result.ready():
            if task_result.successful():
                response["result"] = task_result.result
            elif task_result.failed():
                response["error"] = str(task_result.info)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_tasks():
    """
    Get list of active background tasks
    """
    try:
        from celery_config import app
        
        # Get active tasks from all workers
        inspect = app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return {"active_tasks": [], "workers": []}
        
        # Format response
        formatted_tasks = []
        workers = list(active_tasks.keys())
        
        for worker, tasks in active_tasks.items():
            for task in tasks:
                formatted_tasks.append({
                    "worker": worker,
                    "task_id": task["id"],
                    "task_name": task["name"],
                    "args": task["args"],
                    "kwargs": task["kwargs"],
                    "started": task.get("time_start"),
                })
        
        return {
            "active_tasks": formatted_tasks,
            "workers": workers,
            "total_active": len(formatted_tasks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scheduled")
async def get_scheduled_tasks():
    """
    Get scheduled tasks information
    """
    try:
        from celery_config import app
        
        # Get scheduled tasks
        scheduled_tasks = []
        for name, task_info in app.conf.beat_schedule.items():
            scheduled_tasks.append({
                "name": name,
                "task": task_info["task"],
                "schedule": str(task_info["schedule"]),
                "enabled": True  # All tasks are enabled by default
            })
        
        return {
            "scheduled_tasks": scheduled_tasks,
            "total_scheduled": len(scheduled_tasks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))