#!/bin/bash

echo "🚀 Starting Amazon Insights Celery Services"
echo "============================================"

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running. Please start Redis first:"
    echo "   brew services start redis  # macOS"
    echo "   sudo systemctl start redis-server  # Ubuntu"
    exit 1
fi

# Start Celery worker in background
echo "🔄 Starting Celery Worker..."
celery -A celery_config worker --loglevel=info --detach --pidfile=celery_worker.pid --logfile=logs/celery_worker.log

# Start Celery Beat scheduler in background  
echo "⏰ Starting Celery Beat (Scheduler)..."
celery -A celery_config beat --loglevel=info --detach --pidfile=celery_beat.pid --logfile=logs/celery_beat.log

echo "✅ Celery services started successfully"
echo ""
echo "📊 To monitor tasks:"
echo "   python3 task_manager.py status"
echo "   python3 task_manager.py scheduled"
echo ""
echo "🛑 To stop services:"
echo "   ./stop_celery.sh"
echo ""
echo "📝 Logs location:"
echo "   Worker: logs/celery_worker.log"
echo "   Beat: logs/celery_beat.log"