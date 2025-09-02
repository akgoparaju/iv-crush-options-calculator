"""
Pydantic models for API requests
Professional validation for analysis parameters
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime
import re

class AnalysisRequest(BaseModel):
    """Request model for options analysis"""
    
    # Core parameters
    symbol: str = Field(
        ..., 
        description="Stock symbol (e.g., AAPL, TSLA)",
        min_length=1,
        max_length=10
    )
    
    # Analysis modules (matching CLI functionality)
    include_earnings: bool = Field(
        default=False,
        description="Include earnings calendar analysis and timing windows"
    )
    
    include_trade_construction: bool = Field(
        default=False, 
        description="Include calendar spread and straddle construction"
    )
    
    include_position_sizing: bool = Field(
        default=False,
        description="Include Kelly criterion position sizing and risk management"
    )
    
    include_trading_decision: bool = Field(
        default=False,
        description="Include automated trading decision engine"
    )
    
    # Advanced options
    expirations_to_check: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Number of expiration cycles to analyze"
    )
    
    trade_structure: Literal['calendar', 'straddle', 'auto'] = Field(
        default='calendar',
        description="Preferred trade structure (calendar spread, straddle, or auto-select)"
    )
    
    # Account parameters (for position sizing)
    account_size: Optional[float] = Field(
        default=None,
        gt=0,
        description="Account size in dollars for position sizing calculations"
    )
    
    risk_per_trade: Optional[float] = Field(
        default=None,
        gt=0,
        le=1,
        description="Risk per trade as decimal (e.g., 0.02 = 2%)"
    )
    
    # Demo mode
    use_demo: bool = Field(
        default=False,
        description="Use demo data instead of live market data"
    )
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format"""
        if not v:
            raise ValueError("Symbol cannot be empty")
        
        # Convert to uppercase and strip whitespace
        symbol = v.upper().strip()
        
        # Check for valid symbol format (letters only)
        if not re.match(r'^[A-Z]{1,10}$', symbol):
            raise ValueError("Symbol must contain only letters (1-10 characters)")
        
        return symbol
    
    @validator('risk_per_trade')
    def validate_risk_per_trade(cls, v, values):
        """Validate risk per trade parameter"""
        if v is not None:
            if v <= 0:
                raise ValueError("Risk per trade must be greater than 0")
            if v > 1:
                raise ValueError("Risk per trade must be <= 1 (100%)")
            if v > 0.10:  # Warning for high risk
                # This is just validation; warnings will be handled in business logic
                pass
        return v
    
    @validator('account_size')
    def validate_account_size(cls, v):
        """Validate account size parameter"""
        if v is not None:
            if v <= 0:
                raise ValueError("Account size must be greater than 0")
            if v < 1000:
                raise ValueError("Account size must be at least $1,000")
            if v > 10000000:  # $10M limit for validation
                raise ValueError("Account size exceeds maximum limit ($10,000,000)")
        return v
    
    class Config:
        # Example for API documentation
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "include_earnings": True,
                "include_trade_construction": True,
                "include_position_sizing": True,
                "include_trading_decision": True,
                "expirations_to_check": 2,
                "trade_structure": "calendar",
                "account_size": 100000.0,
                "risk_per_trade": 0.02,
                "use_demo": False
            }
        }

class HealthCheckRequest(BaseModel):
    """Request model for health check with optional details"""
    
    include_details: bool = Field(
        default=False,
        description="Include detailed system information in health check"
    )
    
    check_dependencies: bool = Field(
        default=False,
        description="Check external dependencies (data providers, cache)"
    )

class CacheRequest(BaseModel):
    """Request model for cache operations"""
    
    action: Literal['clear', 'stats', 'flush'] = Field(
        ...,
        description="Cache action to perform"
    )
    
    symbol: Optional[str] = Field(
        default=None,
        description="Symbol to clear from cache (optional, clears all if not provided)"
    )