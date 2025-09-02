"""
Analysis router - Main options analysis endpoints
Professional wrapper around existing options_trader functionality
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from datetime import datetime
import time
import asyncio
import logging
from typing import Optional

from api.models.requests import AnalysisRequest
from api.models.responses import AnalysisResponse, ErrorResponse
from api.services.analysis_service import AnalysisService
from api.services.cache_service import CacheService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize analysis service
analysis_service = AnalysisService()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_options(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """
    Perform comprehensive options analysis
    
    This endpoint wraps the existing options_trader.analyze_symbol functionality
    with professional API patterns, caching, and error handling.
    """
    start_time = time.time()
    request_timestamp = datetime.utcnow()
    
    try:
        logger.info(f"📊 Starting analysis for {request.symbol}")
        
        # Get cache service from app state
        cache_service = getattr(req.app.state, 'cache', None)
        
        # Check cache first if available
        cached_result = None
        if cache_service:
            try:
                cached_result = await cache_service.get_analysis(request)
                if cached_result:
                    logger.info(f"🎯 Cache hit for {request.symbol}")
                    execution_time = (time.time() - start_time) * 1000
                    cached_result.execution_time_ms = execution_time
                    cached_result.cache_hit = True
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
        
        # Perform analysis using existing backend
        try:
            analysis_result = await analysis_service.analyze_symbol(request)
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            
            # Build response
            response = AnalysisResponse(
                success=True,
                message="Analysis completed successfully",
                timestamp=request_timestamp,
                execution_time_ms=execution_time,
                overview=analysis_result["overview"],
                module_status=analysis_result["module_status"],
                earnings_analysis=analysis_result.get("earnings_analysis"),
                trade_construction=analysis_result.get("trade_construction"),
                position_sizing=analysis_result.get("position_sizing"),
                trading_decision=analysis_result.get("trading_decision"),
                disclaimers=analysis_result.get("disclaimers", [
                    "This analysis is for educational purposes only",
                    "Not financial advice - consult with a financial advisor",
                    "Past performance does not guarantee future results"
                ]),
                data_freshness=analysis_result.get("data_freshness"),
                cache_hit=False
            )
            
            # Cache the result in background if cache service available
            if cache_service:
                background_tasks.add_task(
                    cache_analysis_result, 
                    cache_service, 
                    request, 
                    response
                )
            
            logger.info(f"✅ Analysis completed for {request.symbol} in {execution_time:.0f}ms")
            return response
            
        except Exception as analysis_error:
            logger.error(f"❌ Analysis failed for {request.symbol}: {str(analysis_error)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "analysis_failed",
                    "message": f"Analysis failed for symbol {request.symbol}",
                    "details": str(analysis_error)
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred during analysis",
                "details": str(e)
            }
        )

@router.get("/analyze/{symbol}")
async def quick_analyze(
    symbol: str,
    req: Request,
    include_earnings: bool = False,
    include_trades: bool = False,
    use_demo: bool = False
):
    """
    Quick analysis endpoint with URL parameters
    Simplified interface for basic analysis requests
    """
    # Convert GET parameters to AnalysisRequest
    request = AnalysisRequest(
        symbol=symbol.upper().strip(),
        include_earnings=include_earnings,
        include_trade_construction=include_trades,
        include_position_sizing=False,
        include_trading_decision=False,
        use_demo=use_demo
    )
    
    # Use the main analysis endpoint
    background_tasks = BackgroundTasks()
    return await analyze_options(request, background_tasks, req)

@router.get("/symbols/{symbol}/basic")
async def basic_symbol_info(symbol: str):
    """
    Get basic symbol information without full analysis
    Useful for symbol validation and quick price lookup
    """
    try:
        # Use the analysis service to get basic info
        basic_info = await analysis_service.get_basic_symbol_info(symbol.upper().strip())
        return {
            "symbol": symbol.upper(),
            "current_price": basic_info.get("current_price"),
            "data_source": basic_info.get("data_source"),
            "last_updated": basic_info.get("last_updated"),
            "market_status": basic_info.get("market_status"),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to get basic info for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "symbol_not_found",
                "message": f"Could not retrieve information for symbol {symbol}",
                "details": str(e)
            }
        )

# Background task for caching
async def cache_analysis_result(
    cache_service: CacheService, 
    request: AnalysisRequest, 
    response: AnalysisResponse
):
    """Background task to cache analysis results"""
    try:
        await cache_service.cache_analysis(request, response)
        logger.debug(f"🎯 Cached analysis result for {request.symbol}")
    except Exception as e:
        logger.warning(f"Failed to cache result for {request.symbol}: {e}")

# Note: Exception handlers have been moved to main.py
# APIRouter doesn't support exception_handler decorator - only FastAPI app does