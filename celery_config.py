#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from celery import Celery
from celery.schedules import crontab

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from config.config import REDIS_URL

# Create Celery app
app = Celery("amazon_insights")

# Configure Celery
app.conf.update(
    # Broker settings (using Redis)
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    # Task routing
    task_routes={
        "tasks.track_single_product": {"queue": "tracking"},
        "tasks.track_all_products": {"queue": "batch_tracking"},
        "tasks.daily_monitoring": {"queue": "scheduled"},
        "tasks.cleanup_old_data": {"queue": "maintenance"},
    },
    # Beat schedule (periodic tasks)
    beat_schedule={
        "daily-product-tracking": {
            "task": "tasks.daily_monitoring",
            "schedule": crontab(hour=2, minute=0),  # Run at 2:00 AM daily
        },
        "weekly-data-cleanup": {
            "task": "tasks.cleanup_old_data",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3:00 AM
        },
        "hourly-cache-cleanup": {
            "task": "tasks.cleanup_expired_cache",
            "schedule": crontab(minute=0),  # Every hour
        },
    },
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)
