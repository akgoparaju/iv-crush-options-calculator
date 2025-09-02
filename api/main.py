"""
FastAPI Web Layer for Advanced Options Trading Calculator
Professional REST API wrapping existing analysis engine
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / '.env')

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from api.routers import analysis, health, auth, portfolio, screening, education
from api.services.cache_service import CacheService
from api.services.database_service import database_service

# Configure logging
Path('logs').mkdir(exist_ok=True)  # Create logs directory if it doesn't exist
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global cache service instance
cache_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    global cache_service
    
    # Startup
    logger.info("🚀 Starting Advanced Options Trading API...")
    
    # Initialize cache service
    try:
        cache_service = CacheService()
        await cache_service.connect()
        logger.info("✅ Cache service connected")
    except Exception as e:
        logger.warning(f"⚠️  Cache service unavailable: {e}")
        cache_service = None
    
    # Initialize database service
    try:
        await database_service.connect()
        logger.info("✅ Database service connected")
    except Exception as e:
        logger.error(f"❌ Database service failed: {e}")
        raise
    
    # Make services available to the app
    app.state.cache = cache_service
    app.state.database = database_service
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down Advanced Options Trading API...")
    if cache_service:
        await cache_service.disconnect()
        logger.info("✅ Cache service disconnected")
    
    await database_service.disconnect()
    logger.info("✅ Database service disconnected")

# Create FastAPI application with lifespan management
app = FastAPI(
    title="Advanced Options Trading Calculator API",
    description="Professional REST API for educational options analysis",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:3002",  # React dev server (alternate port)
        "http://localhost:8000",  # FastAPI server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(portfolio.router, prefix="/api", tags=["Portfolio Management"])
app.include_router(screening.router, prefix="/api", tags=["Market Screening"])
app.include_router(education.router, prefix="/api", tags=["Educational Content"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Advanced Options Trading Calculator API",
        "version": "2.0.0",
        "description": "Professional REST API for educational options analysis",
        "docs": "/docs",
        "health": "/api/health",
        "timestamp": datetime.utcnow().isoformat(),
        "disclaimer": "This API is for educational purposes only. Not financial advice."
    }

# API information endpoint
@app.get("/api")
async def api_info():
    """API information and available endpoints"""
    return {
        "api_version": "2.0.0",
        "endpoints": {
            "health": "/api/health",
            "analysis": "/api/analyze",
            "documentation": "/docs"
        },
        "features": {
            "earnings_analysis": True,
            "trade_construction": True,
            "position_sizing": True,
            "trading_decisions": True,
            "user_authentication": True,  # Phase 5.1
            "portfolio_tracking": True,   # Phase 5.2
            "automated_screening": True,  # Phase 5.3
            "educational_content": True,  # Phase 5.4
            "real_time_updates": False,   # Phase 5.5+
            "production_infrastructure": False  # Phase 5.5
        },
        "supported_modules": [
            "earnings",
            "trade_construction", 
            "position_sizing",
            "trading_decision"
        ],
        "cache_available": cache_service is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )