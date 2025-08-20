#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Celery Worker startup script
Run with: python3 worker.py worker --loglevel=info
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from celery_config import app

if __name__ == '__main__':
    app.start()