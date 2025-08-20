#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from celery_config import app
from src.monitoring.product_tracker import ProductTracker
from src.monitoring.anomaly_detector import AnomalyDetector
from src.models.product_models import DatabaseManager
from src.cache.redis_service import cache
from config.config import AMAZON_ASINS

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def track_single_product(self, asin: str) -> Dict:
    """Background task to track a single product"""
    try:
        logger.info(f"Starting background tracking for ASIN: {asin}")

        tracker = ProductTracker()
        success = tracker.track_single_product(asin)

        if success:
            summary = tracker.get_product_summary(asin)
            logger.info(
                f"Successfully tracked product {asin}: {summary.get('title', 'N/A')[:50]}..."
            )

            return {
                "success": True,
                "asin": asin,
                "message": f"Successfully tracked product {asin}",
                "summary": summary,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            logger.error(f"Failed to track product {asin}")
            return {
                "success": False,
                "asin": asin,
                "message": f"Failed to track product {asin}",
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"Error in background tracking for {asin}: {str(e)}")
        raise self.retry(exc=e)


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 300},
)
def track_all_products(self) -> Dict:
    """Background task to track all configured products"""
    try:
        logger.info(f"Starting batch tracking for {len(AMAZON_ASINS)} products")

        tracker = ProductTracker()
        results = tracker.track_all_products()

        successful = sum(1 for success in results.values() if success)
        failed = len(AMAZON_ASINS) - successful

        logger.info(
            f"Batch tracking completed: {successful}/{len(AMAZON_ASINS)} successful"
        )

        return {
            "success": True,
            "total_products": len(AMAZON_ASINS),
            "successful": successful,
            "failed": failed,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in batch tracking: {str(e)}")
        raise self.retry(exc=e)


@app.task
def daily_monitoring() -> Dict:
    """Daily scheduled monitoring task"""
    try:
        logger.info("Starting daily monitoring task")

        # Track all products
        tracking_result = track_all_products.delay()
        tracking_data = tracking_result.get(timeout=3600)  # Wait up to 1 hour

        # Generate alerts summary
        detector = AnomalyDetector()
        alerts_summary = detector.get_recent_alerts_summary(24)

        # Log summary
        logger.info(
            f"Daily monitoring completed: {tracking_data['successful']}/{tracking_data['total_products']} products tracked"
        )
        logger.info(
            f"Total alerts in last 24h: {alerts_summary.get('total_alerts', 0)}"
        )

        return {
            "success": True,
            "tracking_results": tracking_data,
            "alerts_summary": alerts_summary,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in daily monitoring: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.task
def cleanup_old_data(days_to_keep: int = 90) -> Dict:
    """Clean up old data from database"""
    try:
        logger.info(f"Starting data cleanup - keeping last {days_to_keep} days")

        db_manager = DatabaseManager()
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        with db_manager.get_session() as session:
            from src.models.product_models import ProductSnapshot, PriceAlert

            # Delete old snapshots
            old_snapshots = (
                session.query(ProductSnapshot)
                .filter(ProductSnapshot.scraped_at < cutoff_date)
                .delete()
            )

            # Delete old alerts
            old_alerts = (
                session.query(PriceAlert)
                .filter(PriceAlert.triggered_at < cutoff_date)
                .delete()
            )

            session.commit()

        logger.info(
            f"Cleanup completed: removed {old_snapshots} snapshots, {old_alerts} alerts"
        )

        return {
            "success": True,
            "snapshots_deleted": old_snapshots,
            "alerts_deleted": old_alerts,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in data cleanup: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.task
def cleanup_expired_cache() -> Dict:
    """Clean up expired cache entries"""
    try:
        logger.info("Starting cache cleanup")

        if not cache.enabled or not cache.client:
            return {
                "success": False,
                "message": "Cache not available",
                "timestamp": datetime.now().isoformat(),
            }

        # Get cache info before cleanup
        info_before = cache.get_info()

        # Redis automatically handles expired keys, but we can trigger cleanup
        # This task mainly serves as a health check
        cache_health = cache.get_info()

        logger.info(
            f"Cache cleanup completed. Cache health: {cache_health.get('connected', False)}"
        )

        return {
            "success": True,
            "cache_connected": cache_health.get("connected", False),
            "memory_used": cache_health.get("memory_used", "N/A"),
            "total_keys": cache_health.get("total_keys", 0),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in cache cleanup: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def process_anomaly_alerts(self, asin: str, anomalies: List[Dict]) -> Dict:
    """Process anomaly alerts for a specific product"""
    try:
        logger.info(f"Processing {len(anomalies)} anomalies for ASIN: {asin}")

        # Here you could integrate with notification services
        # For now, we just log the alerts

        for anomaly in anomalies:
            logger.warning(
                f"Anomaly detected for {asin}: {anomaly.get('message', 'Unknown')}"
            )

        return {
            "success": True,
            "asin": asin,
            "anomalies_processed": len(anomalies),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error processing anomaly alerts for {asin}: {str(e)}")
        raise self.retry(exc=e)


# Task to manually trigger full system update
@app.task
def manual_full_update() -> Dict:
    """Manually triggered full system update"""
    try:
        logger.info("Starting manual full system update")

        # Clear relevant caches
        cache.delete_pattern("product:*")
        cache.delete_pattern("alerts:*")

        # Track all products
        tracking_result = track_all_products.delay()
        tracking_data = tracking_result.get(timeout=3600)

        # Update system status cache
        cache.delete("system:status")

        logger.info("Manual full update completed")

        return {
            "success": True,
            "tracking_results": tracking_data,
            "cache_cleared": True,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in manual full update: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
