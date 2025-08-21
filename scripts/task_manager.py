#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from celery_config import app
from tasks import track_single_product, track_all_products, daily_monitoring


def show_worker_status():
    """Show Celery worker status"""
    print("🔍 Celery Worker Status")
    print("-" * 50)

    try:
        inspect = app.control.inspect()

        # Check active workers
        stats = inspect.stats()
        if not stats:
            print("❌ No active workers found")
            return

        print(f"✅ Active workers: {len(stats)}")
        for worker, worker_stats in stats.items():
            print(f"  {worker}: {worker_stats.get('total', 'N/A')} tasks processed")

        # Check active tasks
        active = inspect.active()
        if active:
            total_active = sum(len(tasks) for tasks in active.values())
            print(f"🔄 Active tasks: {total_active}")
        else:
            print("🔄 Active tasks: 0")

        # Check scheduled tasks
        scheduled = inspect.scheduled()
        if scheduled:
            total_scheduled = sum(len(tasks) for tasks in scheduled.values())
            print(f"⏰ Scheduled tasks: {total_scheduled}")
        else:
            print("⏰ Scheduled tasks: 0")

    except Exception as e:
        print(f"❌ Error checking worker status: {str(e)}")


def trigger_manual_tracking(asin: str = None):
    """Trigger manual product tracking"""
    if asin:
        print(f"🚀 Triggering background tracking for {asin}")
        task = track_single_product.delay(asin)
        print(f"✅ Task started with ID: {task.id}")
    else:
        print("🚀 Triggering background tracking for all products")
        task = track_all_products.delay()
        print(f"✅ Task started with ID: {task.id}")

    return task.id


def trigger_daily_monitoring():
    """Trigger daily monitoring task"""
    print("🚀 Triggering daily monitoring task")
    task = daily_monitoring.delay()
    print(f"✅ Task started with ID: {task.id}")
    return task.id


def check_task_status(task_id: str):
    """Check status of a specific task"""
    print(f"🔍 Checking task status: {task_id}")

    try:
        task_result = app.AsyncResult(task_id)

        print(f"Status: {task_result.status}")
        print(f"Ready: {task_result.ready()}")

        if task_result.ready():
            if task_result.successful():
                print("✅ Task completed successfully")
                result = task_result.result
                if isinstance(result, dict):
                    print(f"Result: {result.get('message', 'No message')}")
            elif task_result.failed():
                print("❌ Task failed")
                print(f"Error: {task_result.info}")
        else:
            print("🔄 Task still running...")

    except Exception as e:
        print(f"❌ Error checking task status: {str(e)}")


def show_scheduled_tasks():
    """Show configured scheduled tasks"""
    print("📅 Scheduled Tasks Configuration")
    print("-" * 50)

    for name, task_info in app.conf.beat_schedule.items():
        print(f"Task: {name}")
        print(f"  Function: {task_info['task']}")
        print(f"  Schedule: {task_info['schedule']}")
        print(f"  Queue: tracking")
        print()


def purge_all_tasks():
    """Purge all pending tasks"""
    print("🗑️  Purging all pending tasks...")

    try:
        purged = app.control.purge()
        total_purged = sum(purged.values()) if purged else 0
        print(f"✅ Purged {total_purged} tasks")
    except Exception as e:
        print(f"❌ Error purging tasks: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Amazon Insights Task Manager")
    parser.add_argument(
        "command",
        choices=[
            "status",
            "track",
            "track-all",
            "daily",
            "check",
            "scheduled",
            "purge",
        ],
        help="Task management command",
    )
    parser.add_argument("--asin", help="ASIN for single product tracking")
    parser.add_argument("--task-id", help="Task ID to check status")

    args = parser.parse_args()

    print(f"🚀 Amazon Insights Task Manager")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if args.command == "status":
        show_worker_status()

    elif args.command == "track":
        if args.asin:
            trigger_manual_tracking(args.asin)
        else:
            print("❌ --asin required for track command")
            return 1

    elif args.command == "track-all":
        trigger_manual_tracking()

    elif args.command == "daily":
        trigger_daily_monitoring()

    elif args.command == "check":
        if not args.task_id:
            print("❌ --task-id required for check command")
            return 1
        check_task_status(args.task_id)

    elif args.command == "scheduled":
        show_scheduled_tasks()

    elif args.command == "purge":
        purge_all_tasks()

    return 0


if __name__ == "__main__":
    exit(main())
