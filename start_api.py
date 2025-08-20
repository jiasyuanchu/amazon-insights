#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Check if API key is configured
    api_key = os.getenv('FIRECRAWL_API_KEY')
    if not api_key:
        print("❌ FIRECRAWL_API_KEY not found in environment variables")
        print("Please create a .env file with your Firecrawl API key:")
        print("FIRECRAWL_API_KEY=your_api_key_here")
        exit(1)
    
    print("🚀 Starting Amazon Insights API Server...")
    print("📖 API Documentation: http://localhost:8001/docs")
    print("📚 ReDoc Documentation: http://localhost:8001/redoc")
    print("🔍 Health Check: http://localhost:8001/health")
    print()
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )