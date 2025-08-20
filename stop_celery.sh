#!/bin/bash

echo "🛑 Stopping Amazon Insights Celery Services"
echo "==========================================="

# Stop Celery worker
if [ -f celery_worker.pid ]; then
    echo "🔄 Stopping Celery Worker..."
    kill -TERM `cat celery_worker.pid`
    rm celery_worker.pid
    echo "✅ Celery Worker stopped"
else
    echo "⚠️  Celery Worker PID file not found"
fi

# Stop Celery Beat
if [ -f celery_beat.pid ]; then
    echo "⏰ Stopping Celery Beat..."
    kill -TERM `cat celery_beat.pid`
    rm celery_beat.pid
    echo "✅ Celery Beat stopped"
else
    echo "⚠️  Celery Beat PID file not found"
fi

# Clean up any remaining processes
echo "🧹 Cleaning up remaining processes..."
pkill -f "celery.*amazon_insights" 2>/dev/null || true

echo "✅ All Celery services stopped"