"""
Screening Models for Phase 5.3
Market screening and alert system models
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# =====================================================================================
# Enums and Constants
# =====================================================================================

class ScreeningFrequency(str, Enum):
    """Screening frequency options"""
    REAL_TIME = "real_time"
    EVERY_5_MIN = "every_5_min"
    EVERY_15_MIN = "every_15_min"
    EVERY_30_MIN = "every_30_min"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"

class AlertType(str, Enum):
    """Alert notification types"""
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"

class ScreeningCriteria(str, Enum):
    """Available screening criteria"""
    IV_RANK = "iv_rank"
    IV_PERCENTILE = "iv_percentile"
    VOLUME = "volume"
    PRICE_RANGE = "price_range"
    MARKET_CAP = "market_cap"
    EARNINGS_DATE = "earnings_date"
    TERM_STRUCTURE = "term_structure"
    IV_RV_RATIO = "iv_rv_ratio"
    DELTA_NEUTRAL = "delta_neutral"
    LIQUIDITY_SCORE = "liquidity_score"

class OpportunityRank(str, Enum):
    """Opportunity ranking levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

# =====================================================================================
# Request Models
# =====================================================================================

class ScreeningCriteriaFilter(BaseModel):
    """Individual screening criteria filter"""
    criteria: ScreeningCriteria
    operator: str = Field(..., description="Comparison operator: >=, <=, ==, !=, between")
    value: Union[float, int, str, List[Union[float, int]]] = Field(..., description="Filter value or range")
    weight: float = Field(1.0, ge=0.1, le=10.0, description="Criteria weight in scoring")

    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = ['>=', '<=', '==', '!=', '>', '<', 'between', 'in', 'not_in']
        if v not in valid_operators:
            raise ValueError(f'Invalid operator: {v}. Must be one of {valid_operators}')
        return v

class CreateScreenRequest(BaseModel):
    """Create a new market screen"""
    name: str = Field(..., min_length=1, max_length=100, description="Screen name")
    description: Optional[str] = Field(None, max_length=500, description="Screen description")
    criteria: List[ScreeningCriteriaFilter] = Field(..., min_items=1, description="Screening criteria")
    symbols: Optional[List[str]] = Field(None, description="Specific symbols to screen (optional)")
    frequency: ScreeningFrequency = Field(default=ScreeningFrequency.HOURLY)
    is_active: bool = Field(default=True, description="Whether screen is active")
    alert_threshold: int = Field(default=5, ge=1, le=100, description="Minimum opportunities to trigger alert")

class UpdateScreenRequest(BaseModel):
    """Update existing screen"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    criteria: Optional[List[ScreeningCriteriaFilter]] = Field(None, min_items=1)
    symbols: Optional[List[str]] = Field(None)
    frequency: Optional[ScreeningFrequency] = Field(None)
    is_active: Optional[bool] = Field(None)
    alert_threshold: Optional[int] = Field(None, ge=1, le=100)

class CreateAlertRequest(BaseModel):
    """Create a new alert configuration"""
    screen_id: UUID = Field(..., description="Associated screen ID")
    alert_types: List[AlertType] = Field(..., min_items=1, description="Alert notification methods")
    conditions: Dict[str, Any] = Field(..., description="Alert trigger conditions")
    is_active: bool = Field(default=True)

class UpdateAlertRequest(BaseModel):
    """Update alert configuration"""
    alert_types: Optional[List[AlertType]] = Field(None, min_items=1)
    conditions: Optional[Dict[str, Any]] = Field(None)
    is_active: Optional[bool] = Field(None)

# =====================================================================================
# Response Models
# =====================================================================================

class ScreeningResult(BaseModel):
    """Individual screening result for a symbol"""
    symbol: str
    current_price: Decimal
    score: float = Field(..., ge=0, le=100, description="Overall opportunity score")
    rank: OpportunityRank
    criteria_scores: Dict[str, float] = Field(..., description="Individual criteria scores")
    market_data: Dict[str, Any] = Field(..., description="Relevant market data")
    opportunity_details: Dict[str, Any] = Field(..., description="Opportunity-specific details")
    timestamp: datetime

    class Config:
        json_encoders = {
            Decimal: lambda d: float(d),
            datetime: lambda dt: dt.isoformat()
        }

class ScreenResponse(BaseModel):
    """Screen configuration response"""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    criteria: List[ScreeningCriteriaFilter]
    symbols: Optional[List[str]]
    frequency: ScreeningFrequency
    is_active: bool
    alert_threshold: int
    last_run: Optional[datetime]
    results_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ScreeningResultsResponse(BaseModel):
    """Complete screening results"""
    screen_id: UUID
    screen_name: str
    total_symbols: int
    opportunities_found: int
    results: List[ScreeningResult]
    execution_time: float = Field(..., description="Execution time in seconds")
    timestamp: datetime
    next_run: Optional[datetime]

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class AlertResponse(BaseModel):
    """Alert configuration response"""
    id: UUID
    screen_id: UUID
    user_id: UUID
    alert_types: List[AlertType]
    conditions: Dict[str, Any]
    is_active: bool
    last_triggered: Optional[datetime]
    trigger_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class AlertNotification(BaseModel):
    """Alert notification details"""
    id: UUID
    alert_id: UUID
    screen_name: str
    opportunities_count: int
    top_opportunities: List[ScreeningResult] = Field(..., max_items=5)
    message: str
    alert_types: List[AlertType]
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# =====================================================================================
# Internal Models (Database)
# =====================================================================================

class ScreenInDB(BaseModel):
    """Screen as stored in database"""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    criteria: List[Dict[str, Any]]  # JSON stored criteria
    symbols: Optional[List[str]]
    frequency: str
    is_active: bool
    alert_threshold: int
    last_run: Optional[datetime]
    results_count: int
    created_at: datetime
    updated_at: datetime

class AlertInDB(BaseModel):
    """Alert as stored in database"""
    id: UUID
    screen_id: UUID
    user_id: UUID
    alert_types: List[str]
    conditions: Dict[str, Any]
    is_active: bool
    last_triggered: Optional[datetime]
    trigger_count: int
    created_at: datetime
    updated_at: datetime

class ScreeningResultInDB(BaseModel):
    """Screening result as stored in database"""
    id: UUID
    screen_id: UUID
    symbol: str
    current_price: Decimal
    score: float
    rank: str
    criteria_scores: Dict[str, float]
    market_data: Dict[str, Any]
    opportunity_details: Dict[str, Any]
    timestamp: datetime

    class Config:
        json_encoders = {
            Decimal: lambda d: float(d),
            datetime: lambda dt: dt.isoformat()
        }

# =====================================================================================
# Analytics Models
# =====================================================================================

class ScreeningAnalytics(BaseModel):
    """Screening performance analytics"""
    screen_id: UUID
    screen_name: str
    total_runs: int
    avg_opportunities_per_run: float
    success_rate: float = Field(..., description="Percentage of runs that found opportunities")
    avg_execution_time: float
    most_frequent_symbols: List[str]
    performance_by_criteria: Dict[str, Dict[str, Any]]
    historical_performance: List[Dict[str, Any]] = Field(..., description="Performance over time")
    recommendations: List[str] = Field(..., description="Optimization recommendations")

class MarketOverviewResponse(BaseModel):
    """Market-wide screening overview"""
    total_symbols_scanned: int
    total_opportunities: int
    opportunities_by_rank: Dict[OpportunityRank, int]
    top_sectors: List[Dict[str, Any]] = Field(..., max_items=10)
    market_conditions: Dict[str, Any]
    trending_strategies: List[str]
    volatility_environment: str
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }