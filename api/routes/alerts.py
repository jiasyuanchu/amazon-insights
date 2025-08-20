import sys
import os
from fastapi import APIRouter, HTTPException
from typing import List

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.models.schemas import Alert, AlertsSummary
from src.monitoring.anomaly_detector import AnomalyDetector
from src.models.product_models import DatabaseManager

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

# Initialize components
detector = AnomalyDetector()
db_manager = DatabaseManager()

@router.get("/", response_model=AlertsSummary)
async def get_alerts_summary(hours: int = 24):
    """
    Get recent alerts summary
    """
    try:
        summary = detector.get_recent_alerts_summary(hours)
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        
        # Get recent alerts details
        recent_alerts_data = db_manager.get_recent_alerts(hours)
        recent_alerts = []
        
        for alert in recent_alerts_data:
            recent_alerts.append(Alert(
                id=alert.id,
                asin=alert.asin,
                alert_type=alert.alert_type,
                old_value=alert.old_value,
                new_value=alert.new_value,
                change_percentage=alert.change_percentage,
                message=alert.message,
                triggered_at=alert.triggered_at.isoformat()
            ))
        
        return AlertsSummary(
            total_alerts=summary['total_alerts'],
            by_type=summary['by_type'],
            by_asin=summary['by_asin'],
            recent_alerts=recent_alerts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent", response_model=List[Alert])
async def get_recent_alerts(hours: int = 24, limit: int = 50):
    """
    Get recent alerts list
    """
    try:
        recent_alerts_data = db_manager.get_recent_alerts(hours)
        
        alerts = []
        for alert in recent_alerts_data[:limit]:
            alerts.append(Alert(
                id=alert.id,
                asin=alert.asin,
                alert_type=alert.alert_type,
                old_value=alert.old_value,
                new_value=alert.new_value,
                change_percentage=alert.change_percentage,
                message=alert.message,
                triggered_at=alert.triggered_at.isoformat()
            ))
        
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{asin}", response_model=List[Alert])
async def get_alerts_by_asin(asin: str, hours: int = 24):
    """
    Get alerts for specific ASIN
    """
    try:
        recent_alerts_data = db_manager.get_recent_alerts(hours)
        
        alerts = []
        for alert in recent_alerts_data:
            if alert.asin == asin:
                alerts.append(Alert(
                    id=alert.id,
                    asin=alert.asin,
                    alert_type=alert.alert_type,
                    old_value=alert.old_value,
                    new_value=alert.new_value,
                    change_percentage=alert.change_percentage,
                    message=alert.message,
                    triggered_at=alert.triggered_at.isoformat()
                ))
        
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))