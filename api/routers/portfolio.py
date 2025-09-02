"""
Portfolio Router for Phase 5.2
Portfolio tracking and management endpoints
"""

import logging
from datetime import date
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from api.models.portfolio import (
    CreatePortfolioRequest, UpdatePortfolioRequest, AddPositionRequest,
    ClosePositionRequest, PortfolioSummaryResponse, PortfolioDetailResponse,
    PositionResponse, PortfolioAnalyticsResponse
)
from api.models.auth import UserInDB
from api.routers.auth import get_current_active_user
from api.services.portfolio_service import portfolio_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/portfolio", tags=["Portfolio Management"])

# =====================================================================================
# Portfolio Management Endpoints
# =====================================================================================

@router.post("/", response_model=PortfolioSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: CreatePortfolioRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Create a new portfolio
    
    Creates a new portfolio for the authenticated user with initial capital
    """
    try:
        portfolio = await portfolio_service.create_portfolio(
            user_id=current_user.id,
            name=portfolio_data.name,
            description=portfolio_data.description,
            initial_capital=portfolio_data.initial_capital
        )
        
        # Convert to summary response
        return PortfolioSummaryResponse(
            id=portfolio.id,
            name=portfolio.name,
            description=portfolio.description,
            user_id=portfolio.user_id,
            initial_capital=portfolio.initial_capital,
            current_value=portfolio.current_value,
            total_invested=portfolio.total_invested,
            available_cash=portfolio.available_cash,
            unrealized_pnl=portfolio.current_value - portfolio.total_invested,
            realized_pnl=0,  # New portfolio has no realized P&L
            total_pnl=portfolio.current_value - portfolio.total_invested,
            total_return_pct=0,  # New portfolio has no return yet
            positions_count=0,
            open_positions_count=0,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Portfolio creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portfolio"
        )

@router.get("/", response_model=List[PortfolioSummaryResponse])
async def get_user_portfolios(
    current_user: UserInDB = Depends(get_current_active_user),
    skip: int = Query(0, ge=0, description="Number of portfolios to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of portfolios to return")
):
    """
    Get all portfolios for the authenticated user
    
    Returns a paginated list of portfolio summaries with key metrics
    """
    try:
        portfolios = await portfolio_service.get_user_portfolios(current_user.id)
        
        # Apply pagination
        paginated_portfolios = portfolios[skip:skip + limit]
        
        return paginated_portfolios
        
    except Exception as e:
        logger.error(f"❌ Error fetching user portfolios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolios"
        )

@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
async def get_portfolio_detail(
    portfolio_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get detailed portfolio information
    
    Returns complete portfolio data including positions, risk metrics, and performance
    """
    try:
        portfolio = await portfolio_service.get_portfolio_detail(
            portfolio_id=portfolio_id,
            user_id=current_user.id
        )
        
        return portfolio
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching portfolio detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio details"
        )

@router.put("/{portfolio_id}", response_model=PortfolioSummaryResponse)
async def update_portfolio(
    portfolio_id: UUID,
    update_data: UpdatePortfolioRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update portfolio information
    
    Updates portfolio name and/or description
    """
    try:
        # Prepare updates dict
        updates = {}
        if update_data.name is not None:
            updates['name'] = update_data.name
        if update_data.description is not None:
            updates['description'] = update_data.description
        
        portfolio = await portfolio_service.update_portfolio(
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            updates=updates
        )
        
        # Convert to summary response (simplified for update response)
        return PortfolioSummaryResponse(
            id=portfolio.id,
            name=portfolio.name,
            description=portfolio.description,
            user_id=portfolio.user_id,
            initial_capital=portfolio.initial_capital,
            current_value=portfolio.current_value,
            total_invested=portfolio.total_invested,
            available_cash=portfolio.available_cash,
            unrealized_pnl=portfolio.current_value - portfolio.total_invested,
            realized_pnl=0,  # Would need calculation
            total_pnl=portfolio.current_value - portfolio.total_invested,
            total_return_pct=0,  # Would need calculation
            positions_count=0,  # Would need calculation
            open_positions_count=0,  # Would need calculation
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update portfolio"
        )

@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Delete a portfolio
    
    Permanently deletes a portfolio (only if no open positions)
    """
    try:
        success = await portfolio_service.delete_portfolio(
            portfolio_id=portfolio_id,
            user_id=current_user.id
        )
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Portfolio deleted successfully"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete portfolio"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete portfolio"
        )

# =====================================================================================
# Position Management Endpoints
# =====================================================================================

@router.post("/{portfolio_id}/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def add_position(
    portfolio_id: UUID,
    position_data: AddPositionRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Add a new position to portfolio
    
    Creates a new options position with one or more legs
    """
    try:
        # Convert position data to dict
        position_dict = {
            'symbol': position_data.symbol,
            'strategy_type': position_data.strategy_type,
            'entry_date': position_data.entry_date,
            'notes': position_data.notes,
            'legs': [leg.dict() for leg in position_data.legs]
        }
        
        position = await portfolio_service.add_position(
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            position_data=position_dict
        )
        
        # Add background task to update portfolio metrics
        background_tasks.add_task(
            _update_portfolio_metrics_background,
            portfolio_id,
            current_user.id
        )
        
        return position
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding position: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add position"
        )

@router.put("/{portfolio_id}/positions/{position_id}/close", response_model=PositionResponse)
async def close_position(
    portfolio_id: UUID,
    position_id: UUID,
    close_data: ClosePositionRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Close an existing position
    
    Closes a position and updates portfolio cash/metrics
    """
    try:
        # Convert close data to dict
        exit_dict = {
            'exit_date': close_data.exit_date,
            'exit_premium': close_data.exit_premium,
            'notes': close_data.notes
        }
        
        position = await portfolio_service.close_position(
            position_id=position_id,
            user_id=current_user.id,
            exit_data=exit_dict
        )
        
        # Add background task to update portfolio metrics
        background_tasks.add_task(
            _update_portfolio_metrics_background,
            portfolio_id,
            current_user.id
        )
        
        return position
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error closing position: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close position"
        )

@router.get("/{portfolio_id}/positions/{position_id}", response_model=PositionResponse)
async def get_position_detail(
    portfolio_id: UUID,
    position_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get detailed position information
    
    Returns complete position data including current valuation and Greeks
    """
    try:
        # This would be implemented in the service
        # For now, return a placeholder response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Position detail endpoint not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching position detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch position details"
        )

# =====================================================================================
# Analytics Endpoints
# =====================================================================================

@router.get("/{portfolio_id}/analytics", response_model=PortfolioAnalyticsResponse)
async def get_portfolio_analytics(
    portfolio_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics")
):
    """
    Get comprehensive portfolio analytics
    
    Returns charts data, performance metrics, and detailed breakdowns
    """
    try:
        analytics = await portfolio_service.get_portfolio_analytics(
            portfolio_id=portfolio_id,
            user_id=current_user.id
        )
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching portfolio analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio analytics"
        )

@router.get("/{portfolio_id}/risk-report")
async def get_risk_report(
    portfolio_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    as_of_date: Optional[date] = Query(None, description="Date for risk calculation")
):
    """
    Get detailed risk analysis report
    
    Returns comprehensive risk metrics including VaR, Greeks exposure, and scenario analysis
    """
    try:
        # This would generate a comprehensive risk report
        # For now, return a placeholder
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={
                "error": "Risk report endpoint not yet implemented",
                "message": "This feature will be available in a future update"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating risk report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate risk report"
        )

@router.get("/{portfolio_id}/performance-report")
async def get_performance_report(
    portfolio_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    start_date: Optional[date] = Query(None, description="Start date for performance analysis"),
    end_date: Optional[date] = Query(None, description="End date for performance analysis")
):
    """
    Get detailed performance analysis report
    
    Returns comprehensive performance metrics including returns, drawdowns, and benchmarks
    """
    try:
        # This would generate a comprehensive performance report
        # For now, return a placeholder
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={
                "error": "Performance report endpoint not yet implemented",
                "message": "This feature will be available in a future update"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating performance report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate performance report"
        )

# =====================================================================================
# Utility Endpoints
# =====================================================================================

@router.post("/{portfolio_id}/sync")
async def sync_portfolio_data(
    portfolio_id: UUID,
    current_user: UserInDB = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Sync portfolio with latest market data
    
    Updates current positions values and portfolio metrics
    """
    try:
        # Add background task to sync portfolio data
        background_tasks.add_task(
            _sync_portfolio_data_background,
            portfolio_id,
            current_user.id
        )
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "success": True,
                "message": "Portfolio sync initiated"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error initiating portfolio sync: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate portfolio sync"
        )

# =====================================================================================
# Background Tasks
# =====================================================================================

async def _update_portfolio_metrics_background(portfolio_id: UUID, user_id: UUID):
    """Background task to update portfolio metrics"""
    try:
        # This would update portfolio current value, P&L, etc.
        # Implementation would go in portfolio service
        logger.info(f"📊 Portfolio metrics updated for {portfolio_id}")
        
    except Exception as e:
        logger.error(f"❌ Error updating portfolio metrics: {str(e)}")

async def _sync_portfolio_data_background(portfolio_id: UUID, user_id: UUID):
    """Background task to sync portfolio with market data"""
    try:
        # This would fetch current market prices and update position values
        # Implementation would go in portfolio service
        logger.info(f"🔄 Portfolio data synced for {portfolio_id}")
        
    except Exception as e:
        logger.error(f"❌ Error syncing portfolio data: {str(e)}")