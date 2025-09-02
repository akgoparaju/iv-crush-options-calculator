"""
Pydantic models for API responses
Professional response formatting for analysis results
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime

class AnalysisOverview(BaseModel):
    """Analysis overview information"""
    symbol: str = Field(..., description="Stock symbol analyzed")
    current_price: float = Field(..., description="Current stock price")
    data_source: str = Field(..., description="Data source provider")
    analysis_mode: str = Field(..., description="Analysis mode (LIVE/DEMO)")
    expirations_checked: int = Field(..., description="Number of expirations analyzed")
    timestamp: datetime = Field(..., description="Analysis timestamp")

class ModuleStatus(BaseModel):
    """Status of analysis modules"""
    earnings_analysis: bool = Field(..., description="Earnings analysis enabled")
    trade_construction: bool = Field(..., description="Trade construction enabled")
    position_sizing: bool = Field(..., description="Position sizing enabled")  
    trading_decision: bool = Field(..., description="Trading decision enabled")

class EarningsAnalysis(BaseModel):
    """Earnings analysis results"""
    next_earnings_date: Optional[str] = Field(None, description="Next earnings date")
    days_to_earnings: Optional[int] = Field(None, description="Days until earnings")
    earnings_timing: Optional[str] = Field(None, description="BMO/AMC timing")
    entry_window: Optional[Dict[str, Any]] = Field(None, description="Entry timing window")
    exit_window: Optional[Dict[str, Any]] = Field(None, description="Exit timing window")
    trading_signals: Optional[Dict[str, Any]] = Field(None, description="Trading signals")

class TradeConstruction(BaseModel):
    """Trade construction results"""
    calendar_trade: Optional[Dict[str, Any]] = Field(None, description="Calendar spread details")
    straddle_construction: Optional[Dict[str, Any]] = Field(None, description="Straddle construction details")
    quality_assessment: Optional[Dict[str, Any]] = Field(None, description="Trade quality metrics")
    greeks_analysis: Optional[Dict[str, Any]] = Field(None, description="Greeks calculations")
    pnl_analysis: Optional[Dict[str, Any]] = Field(None, description="P&L scenario analysis")

class PositionSizing(BaseModel):
    """Position sizing results"""
    recommended_position: Optional[Dict[str, Any]] = Field(None, description="Recommended position size")
    kelly_analysis: Optional[Dict[str, Any]] = Field(None, description="Kelly criterion analysis")
    risk_assessment: Optional[Dict[str, Any]] = Field(None, description="Risk assessment")
    portfolio_impact: Optional[Dict[str, Any]] = Field(None, description="Portfolio impact analysis")

class TradingDecision(BaseModel):
    """Trading decision results"""
    decision: Optional[str] = Field(None, description="Trading decision (RECOMMENDED/CONSIDER/AVOID)")
    confidence: Optional[float] = Field(None, description="Decision confidence percentage")
    signal_strength: Optional[str] = Field(None, description="Signal strength summary")
    reasoning: Optional[List[str]] = Field(None, description="Decision reasoning")
    risk_warnings: Optional[List[str]] = Field(None, description="Risk warnings")

class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    
    # Response metadata
    success: bool = Field(..., description="Analysis success status")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(..., description="Response timestamp")
    execution_time_ms: float = Field(..., description="Analysis execution time in milliseconds")
    
    # Analysis results
    overview: AnalysisOverview = Field(..., description="Analysis overview")
    module_status: ModuleStatus = Field(..., description="Analysis modules status")
    
    # Optional analysis sections (based on request)
    earnings_analysis: Optional[EarningsAnalysis] = Field(None, description="Earnings analysis results")
    trade_construction: Optional[TradeConstruction] = Field(None, description="Trade construction results")
    position_sizing: Optional[PositionSizing] = Field(None, description="Position sizing results")
    trading_decision: Optional[TradingDecision] = Field(None, description="Trading decision results")
    
    # Additional metadata
    disclaimers: List[str] = Field(default_factory=list, description="Risk disclaimers")
    data_freshness: Optional[datetime] = Field(None, description="Data freshness timestamp")
    cache_hit: bool = Field(default=False, description="Whether result was served from cache")
    
    class Config:
        # Example for API documentation
        schema_extra = {
            "example": {
                "success": True,
                "message": "Analysis completed successfully",
                "timestamp": "2025-01-01T12:00:00Z",
                "execution_time_ms": 2500.0,
                "overview": {
                    "symbol": "AAPL",
                    "current_price": 185.50,
                    "data_source": "yahoo",
                    "analysis_mode": "LIVE",
                    "expirations_checked": 2,
                    "timestamp": "2025-01-01T12:00:00Z"
                },
                "module_status": {
                    "earnings_analysis": True,
                    "trade_construction": True,
                    "position_sizing": True,
                    "trading_decision": True
                },
                "disclaimers": [
                    "This analysis is for educational purposes only",
                    "Not financial advice - consult with a financial advisor"
                ],
                "cache_hit": False
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(default=False, description="Success status (always False)")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status (healthy/unhealthy)")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    
    # Optional detailed information
    system_info: Optional[Dict[str, Any]] = Field(None, description="System information")
    dependencies: Optional[Dict[str, Any]] = Field(None, description="Dependency status")
    cache_status: Optional[Dict[str, Any]] = Field(None, description="Cache service status")

class CacheResponse(BaseModel):
    """Cache operation response"""
    success: bool = Field(..., description="Operation success status")
    action: str = Field(..., description="Cache action performed")
    message: str = Field(..., description="Operation message")
    stats: Optional[Dict[str, Any]] = Field(None, description="Cache statistics")
    timestamp: datetime = Field(..., description="Operation timestamp")