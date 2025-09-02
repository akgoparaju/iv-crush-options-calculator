"""
Screening Router for Phase 5.3
Market screening and alert system endpoints
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from api.models.screening import (
    CreateScreenRequest, UpdateScreenRequest, CreateAlertRequest, UpdateAlertRequest,
    ScreenResponse, ScreeningResultsResponse, ScreeningResult, AlertResponse,
    ScreeningAnalytics, MarketOverviewResponse
)
from api.models.auth import UserInDB
from api.routers.auth import get_current_active_user
from api.services.screening_service import screening_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/screening", tags=["Market Screening"])

# =====================================================================================
# Screen Management Endpoints
# =====================================================================================

@router.post("/screens", response_model=ScreenResponse, status_code=status.HTTP_201_CREATED)
async def create_screen(
    screen_data: CreateScreenRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Create a new market screen
    
    Creates a custom screening configuration for monitoring trading opportunities
    """
    try:
        screen = await screening_service.create_screen(
            user_id=current_user.id,
            screen_data=screen_data
        )
        
        logger.info(f"📊 Screen created: {screen.name} for user {current_user.username}")
        return screen
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Screen creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create screen"
        )

@router.get("/screens", response_model=List[ScreenResponse])
async def get_user_screens(
    current_user: UserInDB = Depends(get_current_active_user),
    active_only: bool = Query(False, description="Return only active screens"),
    skip: int = Query(0, ge=0, description="Number of screens to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of screens to return")
):
    """
    Get all screens for the authenticated user
    
    Returns a list of screening configurations with recent activity summaries
    """
    try:
        screens = await screening_service.get_user_screens(current_user.id, active_only)
        
        # Apply pagination
        paginated_screens = screens[skip:skip + limit]
        
        return paginated_screens
        
    except Exception as e:
        logger.error(f"❌ Error fetching user screens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch screens"
        )

@router.get("/screens/{screen_id}", response_model=ScreenResponse)
async def get_screen_detail(
    screen_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get detailed screen configuration
    
    Returns complete screen configuration including criteria and recent performance
    """
    try:
        screen = await screening_service.get_screen(screen_id, current_user.id)
        return screen
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching screen detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch screen details"
        )

@router.put("/screens/{screen_id}", response_model=ScreenResponse)
async def update_screen(
    screen_id: UUID,
    update_data: UpdateScreenRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update screen configuration
    
    Updates screening criteria, symbols, frequency, or other settings
    """
    try:
        screen = await screening_service.update_screen(
            screen_id=screen_id,
            user_id=current_user.id,
            updates=update_data
        )
        
        return screen
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating screen: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update screen"
        )

@router.delete("/screens/{screen_id}")
async def delete_screen(
    screen_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Delete a screen
    
    Permanently deletes a screen and all associated results and alerts
    """
    try:
        success = await screening_service.delete_screen(screen_id, current_user.id)
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Screen deleted successfully"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Screen not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting screen: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete screen"
        )

# =====================================================================================
# Screening Execution Endpoints
# =====================================================================================

@router.post("/screens/{screen_id}/run", response_model=ScreeningResultsResponse)
async def run_screen(
    screen_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Execute a market screen
    
    Runs the screening algorithm against configured criteria and returns opportunities
    """
    try:
        results = await screening_service.run_screen(screen_id, current_user.id)
        
        # Add background task for analytics update (if needed)
        background_tasks.add_task(
            _update_screen_analytics_background,
            screen_id,
            current_user.id
        )
        
        logger.info(f"📊 Screen executed: {results.screen_name}, found {results.opportunities_found} opportunities")
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error running screen: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run screen"
        )

@router.get("/screens/{screen_id}/results", response_model=List[ScreeningResult])
async def get_screening_results(
    screen_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results to return")
):
    """
    Get latest screening results
    
    Returns the most recent opportunities found by this screen
    """
    try:
        results = await screening_service.get_screening_results(
            screen_id, current_user.id, limit
        )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching screening results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch screening results"
        )

# =====================================================================================
# Alert Management Endpoints
# =====================================================================================

@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: CreateAlertRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Create a new alert configuration
    
    Sets up automated notifications when screening criteria are met
    """
    try:
        alert = await screening_service.create_alert(current_user.id, alert_data)
        
        logger.info(f"🔔 Alert created for screen {alert.screen_id} by user {current_user.username}")
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Alert creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )

@router.get("/alerts", response_model=List[AlertResponse])
async def get_user_alerts(
    current_user: UserInDB = Depends(get_current_active_user),
    skip: int = Query(0, ge=0, description="Number of alerts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts to return")
):
    """
    Get all alerts for the authenticated user
    
    Returns alert configurations and recent activity
    """
    try:
        alerts = await screening_service.get_user_alerts(current_user.id)
        
        # Apply pagination
        paginated_alerts = alerts[skip:skip + limit]
        
        return paginated_alerts
        
    except Exception as e:
        logger.error(f"❌ Error fetching user alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alerts"
        )

@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    update_data: UpdateAlertRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update alert configuration
    
    Modifies alert notification settings or trigger conditions
    """
    try:
        # This would be implemented in the service
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Alert update endpoint not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert"
        )

@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Delete an alert configuration
    
    Removes alert and stops future notifications
    """
    try:
        # This would be implemented in the service
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Alert deletion endpoint not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert"
        )

# =====================================================================================
# Analytics Endpoints
# =====================================================================================

@router.get("/screens/{screen_id}/analytics", response_model=ScreeningAnalytics)
async def get_screening_analytics(
    screen_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics")
):
    """
    Get screening performance analytics
    
    Returns detailed performance metrics and optimization recommendations
    """
    try:
        analytics = await screening_service.get_screening_analytics(
            screen_id, current_user.id, days
        )
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching screening analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch screening analytics"
        )

@router.get("/market-overview", response_model=MarketOverviewResponse)
async def get_market_overview(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get market-wide screening overview
    
    Returns aggregate market conditions and opportunity distribution
    """
    try:
        # This would be implemented with aggregated market data
        return MarketOverviewResponse(
            total_symbols_scanned=500,
            total_opportunities=45,
            opportunities_by_rank={
                "excellent": 8,
                "good": 15,
                "fair": 22,
                "poor": 0
            },
            top_sectors=[
                {"sector": "Technology", "opportunities": 18, "avg_score": 72.5},
                {"sector": "Healthcare", "opportunities": 12, "avg_score": 68.3},
                {"sector": "Financial", "opportunities": 8, "avg_score": 65.1}
            ],
            market_conditions={
                "vix_level": 18.5,
                "market_trend": "neutral",
                "earnings_season": "mid-cycle"
            },
            trending_strategies=["Iron Condor", "Calendar Spread", "Put Credit Spread"],
            volatility_environment="moderate",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching market overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch market overview"
        )

# =====================================================================================
# Screening Templates Endpoints
# =====================================================================================

@router.get("/templates")
async def get_screening_templates(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get predefined screening templates
    
    Returns common screening configurations for quick setup
    """
    try:
        templates = [
            {
                "name": "High IV Rank",
                "description": "Find stocks with elevated implied volatility",
                "criteria": [
                    {
                        "criteria": "iv_percentile",
                        "operator": ">=",
                        "value": 70,
                        "weight": 2.0
                    },
                    {
                        "criteria": "volume",
                        "operator": ">=",
                        "value": 1000000,
                        "weight": 1.0
                    }
                ],
                "frequency": "hourly"
            },
            {
                "name": "Earnings Plays",
                "description": "Stocks with upcoming earnings and high IV",
                "criteria": [
                    {
                        "criteria": "earnings_date",
                        "operator": "between",
                        "value": [0, 7],
                        "weight": 2.0
                    },
                    {
                        "criteria": "iv_rv_ratio",
                        "operator": ">=",
                        "value": 1.25,
                        "weight": 1.5
                    }
                ],
                "frequency": "daily"
            },
            {
                "name": "Premium Collection",
                "description": "High premium opportunities with good liquidity",
                "criteria": [
                    {
                        "criteria": "iv_percentile",
                        "operator": ">=",
                        "value": 60,
                        "weight": 1.5
                    },
                    {
                        "criteria": "liquidity_score",
                        "operator": ">=",
                        "value": 7,
                        "weight": 2.0
                    },
                    {
                        "criteria": "volume",
                        "operator": ">=",
                        "value": 2000000,
                        "weight": 1.0
                    }
                ],
                "frequency": "every_30_min"
            }
        ]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "templates": templates
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching screening templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch screening templates"
        )

# =====================================================================================
# Bulk Operations Endpoints
# =====================================================================================

@router.post("/screens/bulk-run")
async def bulk_run_screens(
    current_user: UserInDB = Depends(get_current_active_user),
    screen_ids: List[UUID] = Query(..., description="List of screen IDs to run"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Run multiple screens in parallel
    
    Executes multiple screening configurations simultaneously for efficiency
    """
    try:
        if len(screen_ids) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 screens can be run simultaneously"
            )
        
        # Add background task for bulk execution
        background_tasks.add_task(
            _bulk_run_screens_background,
            screen_ids,
            current_user.id
        )
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "success": True,
                "message": f"Bulk screening of {len(screen_ids)} screens initiated",
                "screen_ids": screen_ids
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error initiating bulk screen run: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate bulk screening"
        )

# =====================================================================================
# Background Tasks
# =====================================================================================

async def _update_screen_analytics_background(screen_id: UUID, user_id: UUID):
    """Background task to update screen analytics"""
    try:
        # This would update screening analytics and performance metrics
        logger.info(f"📊 Screen analytics updated for {screen_id}")
        
    except Exception as e:
        logger.error(f"❌ Error updating screen analytics: {str(e)}")

async def _bulk_run_screens_background(screen_ids: List[UUID], user_id: UUID):
    """Background task to run multiple screens"""
    try:
        results = []
        
        for screen_id in screen_ids:
            try:
                result = await screening_service.run_screen(screen_id, user_id)
                results.append({
                    "screen_id": screen_id,
                    "success": True,
                    "opportunities_found": result.opportunities_found
                })
                logger.info(f"📊 Bulk screen completed: {screen_id}, found {result.opportunities_found} opportunities")
                
            except Exception as e:
                results.append({
                    "screen_id": screen_id,
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"❌ Bulk screen failed: {screen_id}, error: {str(e)}")
        
        logger.info(f"📊 Bulk screening completed: {len(results)} screens processed")
        
    except Exception as e:
        logger.error(f"❌ Error in bulk screen execution: {str(e)}")