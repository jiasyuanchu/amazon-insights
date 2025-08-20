# Multi-stage Dockerfile for Amazon Insights

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data && \
    chown -R appuser:appuser /app

# Production target for API server
FROM base as production

USER appuser

EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]

# Worker target for Celery workers
FROM base as worker

USER appuser

CMD ["celery", "-A", "celery_config", "worker", "--loglevel=info", "--concurrency=4"]

# Scheduler target for Celery beat
FROM base as scheduler

USER appuser

CMD ["celery", "-A", "celery_config", "beat", "--loglevel=info"]

# Development target with additional tools
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    black \
    flake8 \
    mypy \
    jupyter \
    ipython

USER appuser

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]