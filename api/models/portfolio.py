"""
Portfolio Models for Phase 5.2
Portfolio tracking and management system
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from enum import Enum

# =====================================================================================
# Enums
# =====================================================================================

class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    EXPIRED = "expired"
    ASSIGNED = "assigned"

class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"

class TradeAction(str, Enum):
    BUY_TO_OPEN = "buy_to_open"
    SELL_TO_OPEN = "sell_to_open"
    BUY_TO_CLOSE = "buy_to_close"
    SELL_TO_CLOSE = "sell_to_close"

class StrategyType(str, Enum):
    CALENDAR_SPREAD = "calendar_spread"
    ATM_STRADDLE = "atm_straddle"
    IRON_CONDOR = "iron_condor"
    COVERED_CALL = "covered_call"
    PROTECTIVE_PUT = "protective_put"
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    SHORT_CALL = "short_call"
    SHORT_PUT = "short_put"

# =====================================================================================
# Request Models
# =====================================================================================

class CreatePortfolioRequest(BaseModel):
    """Create new portfolio request"""
    name: str = Field(..., min_length=1, max_length=100, description="Portfolio name")
    description: Optional[str] = Field(None, max_length=500, description="Portfolio description")
    initial_capital: Decimal = Field(..., gt=0, description="Initial portfolio capital")

class UpdatePortfolioRequest(BaseModel):
    """Update portfolio request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class AddPositionRequest(BaseModel):
    """Add position to portfolio request"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Underlying symbol")
    strategy_type: StrategyType = Field(..., description="Options strategy type")
    legs: List['OptionLegRequest'] = Field(..., min_items=1, description="Option legs")
    entry_date: date = Field(..., description="Position entry date")
    notes: Optional[str] = Field(None, max_length=1000, description="Position notes")

class OptionLegRequest(BaseModel):
    """Option leg request"""
    option_type: OptionType = Field(..., description="Call or Put")
    strike_price: Decimal = Field(..., gt=0, description="Strike price")
    expiration_date: date = Field(..., description="Expiration date")
    action: TradeAction = Field(..., description="Trade action")
    contracts: int = Field(..., gt=0, description="Number of contracts")
    premium: Decimal = Field(..., gt=0, description="Premium per contract")

class ClosePositionRequest(BaseModel):
    """Close position request"""
    exit_date: date = Field(..., description="Position exit date")
    exit_premium: Optional[Decimal] = Field(None, description="Exit premium")
    notes: Optional[str] = Field(None, max_length=1000, description="Closing notes")

# =====================================================================================
# Response Models
# =====================================================================================

class OptionLegResponse(BaseModel):
    """Option leg response"""
    id: UUID
    option_type: OptionType
    strike_price: Decimal
    expiration_date: date
    action: TradeAction
    contracts: int
    premium: Decimal
    current_value: Optional[Decimal] = None
    delta: Optional[Decimal] = None
    gamma: Optional[Decimal] = None
    theta: Optional[Decimal] = None
    vega: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

class PositionResponse(BaseModel):
    """Position response"""
    id: UUID
    symbol: str
    strategy_type: StrategyType
    status: PositionStatus
    legs: List[OptionLegResponse]
    entry_date: date
    exit_date: Optional[date] = None
    entry_cost: Decimal
    exit_value: Optional[Decimal] = None
    current_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Optional[Decimal] = None
    total_pnl: Decimal
    days_to_expiration: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary response"""
    id: UUID
    name: str
    description: Optional[str]
    user_id: UUID
    initial_capital: Decimal
    current_value: Decimal
    total_invested: Decimal
    available_cash: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal
    total_return_pct: Decimal
    positions_count: int
    open_positions_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PortfolioDetailResponse(BaseModel):
    """Detailed portfolio response"""
    id: UUID
    name: str
    description: Optional[str]
    user_id: UUID
    initial_capital: Decimal
    current_value: Decimal
    total_invested: Decimal
    available_cash: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal
    total_return_pct: Decimal
    positions: List[PositionResponse]
    risk_metrics: 'RiskMetricsResponse'
    performance_metrics: 'PerformanceMetricsResponse'
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RiskMetricsResponse(BaseModel):
    """Portfolio risk metrics"""
    total_delta: Decimal
    total_gamma: Decimal
    total_theta: Decimal
    total_vega: Decimal
    portfolio_beta: Optional[Decimal] = None
    var_1d: Optional[Decimal] = None  # Value at Risk (1 day)
    max_loss: Decimal
    concentration_risk: Dict[str, Decimal]  # By symbol
    
class PerformanceMetricsResponse(BaseModel):
    """Portfolio performance metrics"""
    win_rate: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: Decimal
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Decimal
    calmar_ratio: Optional[Decimal] = None
    trades_count: int
    winning_trades: int
    losing_trades: int

class PortfolioAnalyticsResponse(BaseModel):
    """Portfolio analytics response"""
    daily_pnl: List[Dict[str, Any]]  # Date and P&L data
    monthly_returns: List[Dict[str, Any]]
    strategy_breakdown: Dict[StrategyType, Dict[str, Any]]
    symbol_allocation: Dict[str, Decimal]
    expiration_calendar: List[Dict[str, Any]]

# =====================================================================================
# Internal Models
# =====================================================================================

class PortfolioInDB(BaseModel):
    """Portfolio database model"""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    initial_capital: Decimal
    current_value: Decimal
    total_invested: Decimal
    available_cash: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PositionInDB(BaseModel):
    """Position database model"""
    id: UUID
    portfolio_id: UUID
    symbol: str
    strategy_type: StrategyType
    status: PositionStatus
    entry_date: date
    exit_date: Optional[date]
    entry_cost: Decimal
    exit_value: Optional[Decimal]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OptionLegInDB(BaseModel):
    """Option leg database model"""
    id: UUID
    position_id: UUID
    option_type: OptionType
    strike_price: Decimal
    expiration_date: date
    action: TradeAction
    contracts: int
    premium: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# =====================================================================================
# Analytics Models
# =====================================================================================

class PnLCalculation(BaseModel):
    """P&L calculation model"""
    entry_cost: Decimal
    current_value: Decimal
    exit_value: Optional[Decimal]
    unrealized_pnl: Decimal
    realized_pnl: Optional[Decimal]
    total_pnl: Decimal

class Greeks(BaseModel):
    """Options Greeks model"""
    delta: Decimal
    gamma: Decimal
    theta: Decimal
    vega: Decimal
    rho: Optional[Decimal] = None

class PositionGreeks(BaseModel):
    """Position-level Greeks"""
    symbol: str
    position_id: UUID
    total_delta: Decimal
    total_gamma: Decimal
    total_theta: Decimal
    total_vega: Decimal
    legs: List[Dict[str, Any]]

# Update forward references
OptionLegRequest.model_rebuild()
AddPositionRequest.model_rebuild()
PortfolioDetailResponse.model_rebuild()
RiskMetricsResponse.model_rebuild()
PerformanceMetricsResponse.model_rebuild()