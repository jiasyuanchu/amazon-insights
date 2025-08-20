#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from api.routes import products, alerts, system, cache, tasks, competitive

# Create FastAPI app
app = FastAPI(
    title="Amazon Insights API",
    description="Amazon Product Data Tracking System RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router)
app.include_router(alerts.router)
app.include_router(system.router)
app.include_router(cache.router)
app.include_router(tasks.router)
app.include_router(competitive.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(exc),
        },
    )


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Amazon Insights API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/system/health",
    }


# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
