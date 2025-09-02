"""
Health check router for monitoring and service status
Professional health endpoints for production monitoring
"""

from fastapi import APIRouter, Depends, Request
from datetime import datetime
import time
import psutil
import sys
import os
from typing import Dict, Any

from api.models.requests import HealthCheckRequest
from api.models.responses import HealthResponse

router = APIRouter()

# Service start time for uptime calculation
service_start_time = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint
    Returns service status and basic information
    """
    current_time = time.time()
    uptime = current_time - service_start_time
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="2.0.0",
        uptime_seconds=uptime
    )

@router.post("/health/detailed", response_model=HealthResponse)
async def detailed_health_check(request: HealthCheckRequest, req: Request):
    """
    Detailed health check with system information
    Includes system metrics and dependency status if requested
    """
    current_time = time.time()
    uptime = current_time - service_start_time
    
    response_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0",
        "uptime_seconds": uptime
    }
    
    # Add detailed system information if requested
    if request.include_details:
        response_data["system_info"] = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "disk_free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
            "process_memory_mb": round(psutil.Process().memory_info().rss / (1024**2), 2)
        }
    
    # Check dependencies if requested  
    if request.check_dependencies:
        dependencies = await check_dependencies(req)
        response_data["dependencies"] = dependencies
        
        # Check cache status
        cache_service = getattr(req.app.state, 'cache', None)
        if cache_service:
            try:
                cache_stats = await cache_service.get_stats()
                response_data["cache_status"] = {
                    "available": True,
                    "stats": cache_stats
                }
            except Exception as e:
                response_data["cache_status"] = {
                    "available": False,
                    "error": str(e)
                }
        else:
            response_data["cache_status"] = {
                "available": False,
                "error": "Cache service not initialized"
            }
    
    return HealthResponse(**response_data)

async def check_dependencies(request: Request) -> Dict[str, Any]:
    """
    Check status of external dependencies
    """
    dependencies = {}
    
    # Check if options_trader package is available
    try:
        import options_trader
        dependencies["options_trader"] = {
            "status": "available",
            "version": getattr(options_trader, '__version__', 'unknown')
        }
    except ImportError as e:
        dependencies["options_trader"] = {
            "status": "unavailable", 
            "error": str(e)
        }
    
    # Check data providers availability (basic import test)
    data_providers = ["yfinance", "requests", "pandas", "numpy"]
    for provider in data_providers:
        try:
            __import__(provider)
            dependencies[provider] = {"status": "available"}
        except ImportError:
            dependencies[provider] = {"status": "unavailable"}
    
    # Test database connectivity (if available)
    try:
        import asyncpg
        dependencies["postgresql"] = {"status": "driver_available"}
        # Note: Actual connection test would require database credentials
    except ImportError:
        dependencies["postgresql"] = {"status": "driver_unavailable"}
    
    return dependencies

@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint
    Returns 200 if service is ready to accept traffic
    """
    try:
        # Basic import test for core functionality
        import options_trader
        return {"status": "ready", "timestamp": datetime.utcnow()}
    except ImportError:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Service not ready - missing core dependencies"
        )

@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint  
    Returns 200 if service is alive (basic functionality)
    """
    return {"status": "alive", "timestamp": datetime.utcnow()}