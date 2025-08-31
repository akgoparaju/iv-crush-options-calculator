#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trade Construction Engine - Module 2
====================================

Calendar spread construction and trade validation for earnings IV crush strategy.
Transforms analysis signals into concrete executable trades with risk/reward metrics.

Core Components:
- CalendarTrade: Complete trade specification dataclass
- CalendarTradeConstructor: Build and validate calendar spreads
- TradeValidator: Feasibility and risk assessment
- OptionQuote: Option pricing data structure

Preserves all existing functionality while adding trade construction capabilities.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

# Conditional imports for optional dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

from .utils import ensure_numeric_cols, nearest_strike_row

logger = logging.getLogger("options_trader.trade_construction")


@dataclass
class OptionQuote:
    """Complete option quote with pricing and Greeks data."""
    symbol: str
    strike: float
    expiration: str
    option_type: str  # 'call' or 'put'
    bid: float
    ask: float
    last_price: float
    implied_volatility: float
    volume: int = 0
    open_interest: int = 0
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price from bid/ask or use last price."""
        if self.bid > 0 and self.ask > 0 and self.ask >= self.bid:
            return (self.bid + self.ask) / 2.0
        return self.last_price if self.last_price > 0 else 0.0
    
    @property
    def spread_width(self) -> float:
        """Calculate bid/ask spread width."""
        if self.bid > 0 and self.ask > 0:
            return self.ask - self.bid
        return 0.0
    
    @property
    def spread_percentage(self) -> float:
        """Calculate spread as percentage of mid price."""
        mid = self.mid_price
        if mid > 0:
            return (self.spread_width / mid) * 100
        return 0.0


@dataclass
class CalendarTrade:
    """Complete calendar spread trade specification."""
    symbol: str
    underlying_price: float
    strike: float
    front_expiration: str
    back_expiration: str
    front_option: OptionQuote
    back_option: OptionQuote
    trade_type: str = "call_calendar"  # 'call_calendar' or 'put_calendar'
    
    # Trade Economics
    net_debit: float = field(init=False)
    max_profit: Optional[float] = field(init=False, default=None)
    max_loss: float = field(init=False)
    breakeven_range: Tuple[float, float] = field(init=False, default=(0.0, 0.0))
    
    # Risk Metrics
    profit_probability: Optional[float] = field(init=False, default=None)
    risk_reward_ratio: Optional[float] = field(init=False, default=None)
    days_to_expiration_front: int = field(init=False, default=0)
    days_to_expiration_back: int = field(init=False, default=0)
    
    # Trade Validation
    is_valid: bool = field(init=False, default=True)
    validation_errors: List[str] = field(init=False, default_factory=list)
    
    def __post_init__(self):
        """Calculate derived fields after initialization."""
        self.net_debit = self._calculate_net_debit()
        self.max_loss = self.net_debit  # Maximum loss is the debit paid
        self.breakeven_range = self._calculate_breakeven_range()
        self.days_to_expiration_front = self._calculate_dte(self.front_expiration)
        self.days_to_expiration_back = self._calculate_dte(self.back_expiration)
        
    def _calculate_net_debit(self) -> float:
        """Calculate net debit: buy back option, sell front option."""
        return self.back_option.mid_price - self.front_option.mid_price
    
    def _calculate_breakeven_range(self) -> Tuple[float, float]:
        """Approximate breakeven range for calendar spread."""
        # Simplified calculation - in practice would need full Greeks
        spread_value = abs(self.back_option.mid_price - self.front_option.mid_price)
        lower_be = self.strike - (spread_value * 0.5)
        upper_be = self.strike + (spread_value * 0.5)
        return (lower_be, upper_be)
    
    def _calculate_dte(self, expiration: str) -> int:
        """Calculate days to expiration."""
        try:
            exp_date = datetime.strptime(expiration, "%Y-%m-%d").date()
            today = datetime.now().date()
            return (exp_date - today).days
        except Exception:
            return 0
    
    @property
    def expected_profit_range(self) -> Tuple[float, float]:
        """Expected profit range (conservative, optimistic)."""
        # Simplified - would be enhanced with P&L modeling
        conservative = self.net_debit * 0.3  # 30% profit
        optimistic = self.net_debit * 1.0    # 100% profit
        return (conservative, optimistic)
    
    @property
    def capital_requirement(self) -> float:
        """Capital required for the trade (net debit)."""
        return abs(self.net_debit) if self.net_debit > 0 else 0.0


class CalendarTradeConstructor:
    """
    Calendar spread construction engine.
    
    Builds optimal calendar spreads from analysis signals and option chains,
    following the established architectural patterns from Module 1.
    """
    
    def __init__(self, data_service):
        """Initialize with data service for option chain access."""
        self.data_service = data_service
        self.logger = logging.getLogger("options_trader.trade_construction")
        
        # Configuration parameters (could be moved to config file)
        self.config = {
            "max_spread_percentage": 15.0,  # Maximum bid/ask spread as % of mid
            "min_open_interest": 10,        # Minimum open interest
            "min_volume": 5,               # Minimum daily volume
            "target_back_dte": 30,         # Target back month DTE
            "dte_tolerance": 7,            # DTE selection tolerance
            "preferred_option_type": "call" # Default to call calendars
        }
    
    def build_optimal_calendar(self, symbol: str, analysis_result: Dict[str, Any], 
                             earnings_date: Optional[datetime] = None) -> Optional[CalendarTrade]:
        """
        Build optimal calendar spread from analysis results.
        
        Args:
            symbol: Stock symbol
            analysis_result: Results from analyze_symbol() 
            earnings_date: Earnings date for expiration selection
            
        Returns:
            CalendarTrade object or None if no valid trade found
        """
        try:
            self.logger.debug(f"Building optimal calendar for {symbol}")
            
            # Extract data from analysis result
            underlying_price = float(analysis_result.get("price", 0))
            if underlying_price <= 0:
                self.logger.warning(f"Invalid underlying price for {symbol}: {underlying_price}")
                return None
            
            expirations = analysis_result.get("expirations", [])
            if len(expirations) < 2:
                self.logger.warning(f"Need at least 2 expirations for calendar spread, found {len(expirations)}")
                return None
            
            # Select optimal expiration pair
            front_exp, back_exp = self._select_expiration_pair(expirations, earnings_date)
            if not front_exp or not back_exp:
                self.logger.warning(f"Could not select valid expiration pair for {symbol}")
                return None
            
            # Select optimal strike (ATM or nearest)
            strike = self._select_optimal_strike(underlying_price, expirations)
            if strike <= 0:
                self.logger.warning(f"Could not select valid strike for {symbol}")
                return None
            
            # Build the calendar spread
            calendar_trade = self._construct_calendar_spread(
                symbol, underlying_price, strike, front_exp, back_exp
            )
            
            if calendar_trade and self._validate_trade(calendar_trade):
                self.logger.info(f"Built calendar spread for {symbol}: ${calendar_trade.net_debit:.2f} debit")
                return calendar_trade
            else:
                self.logger.warning(f"Calendar trade validation failed for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to build calendar for {symbol}: {e}")
            return None
    
    def _select_expiration_pair(self, expirations: List[Dict], 
                              earnings_date: Optional[datetime] = None) -> Tuple[Optional[str], Optional[str]]:
        """Select front and back expirations for calendar spread."""
        try:
            # Extract expiration dates
            exp_dates = []
            for exp_data in expirations:
                if "expiration" in exp_data:
                    exp_dates.append(exp_data["expiration"])
            
            if len(exp_dates) < 2:
                return None, None
            
            # Sort by expiration date
            exp_dates.sort()
            
            # If earnings date provided, front exp must contain earnings
            if earnings_date:
                front_exp = None
                for exp_str in exp_dates:
                    exp_date = datetime.strptime(exp_str, "%Y-%m-%d")
                    if exp_date >= earnings_date:
                        front_exp = exp_str
                        break
            else:
                # Use first available expiration
                front_exp = exp_dates[0]
            
            if not front_exp:
                return None, None
            
            # Select back expiration (~30 days later)
            front_date = datetime.strptime(front_exp, "%Y-%m-%d")
            target_date = front_date + timedelta(days=self.config["target_back_dte"])
            
            best_back = None
            min_diff = float('inf')
            
            for exp_str in exp_dates:
                if exp_str <= front_exp:  # Must be later than front
                    continue
                exp_date = datetime.strptime(exp_str, "%Y-%m-%d")
                diff = abs((exp_date - target_date).days)
                if diff < min_diff:
                    min_diff = diff
                    best_back = exp_str
            
            self.logger.debug(f"Selected expiration pair: front={front_exp}, back={best_back}")
            return front_exp, best_back
            
        except Exception as e:
            self.logger.error(f"Failed to select expiration pair: {e}")
            return None, None
    
    def _select_optimal_strike(self, underlying_price: float, expirations: List[Dict]) -> float:
        """Select optimal strike (ATM or nearest available)."""
        try:
            # Look for ATM strike in first expiration
            if not expirations:
                return 0.0
            
            first_exp = expirations[0]
            if "atm_strike_call" in first_exp:
                return float(first_exp["atm_strike_call"])
            
            # Fallback: round to nearest common strike increment
            if underlying_price < 25:
                increment = 2.5
            elif underlying_price < 200:
                increment = 5.0
            else:
                increment = 10.0
            
            atm_strike = round(underlying_price / increment) * increment
            self.logger.debug(f"Selected ATM strike: {atm_strike}")
            return atm_strike
            
        except Exception as e:
            self.logger.error(f"Failed to select optimal strike: {e}")
            return 0.0
    
    def _construct_calendar_spread(self, symbol: str, underlying_price: float,
                                 strike: float, front_exp: str, back_exp: str) -> Optional[CalendarTrade]:
        """Construct calendar spread from option quotes."""
        try:
            # Get option chains for both expirations
            front_chain, _ = self.data_service.get_chain(symbol, front_exp)
            back_chain, _ = self.data_service.get_chain(symbol, back_exp)
            
            if not front_chain or not back_chain:
                self.logger.warning(f"Could not get option chains for {symbol}")
                return None
            
            # Find options at the selected strike
            front_option = self._find_option_at_strike(front_chain, strike, self.config["preferred_option_type"])
            back_option = self._find_option_at_strike(back_chain, strike, self.config["preferred_option_type"])
            
            if not front_option or not back_option:
                self.logger.warning(f"Could not find options at strike {strike} for {symbol}")
                return None
            
            # Create calendar trade
            calendar_trade = CalendarTrade(
                symbol=symbol,
                underlying_price=underlying_price,
                strike=strike,
                front_expiration=front_exp,
                back_expiration=back_exp,
                front_option=front_option,
                back_option=back_option,
                trade_type=f"{self.config['preferred_option_type']}_calendar"
            )
            
            return calendar_trade
            
        except Exception as e:
            self.logger.error(f"Failed to construct calendar spread for {symbol}: {e}")
            return None
    
    def _find_option_at_strike(self, chain, target_strike: float, option_type: str) -> Optional[OptionQuote]:
        """Find option at specific strike in option chain."""
        try:
            # Select calls or puts
            if option_type.lower() == "call":
                options_df = ensure_numeric_cols(chain.calls.copy()) if hasattr(chain, 'calls') else None
            else:
                options_df = ensure_numeric_cols(chain.puts.copy()) if hasattr(chain, 'puts') else None
            
            if options_df is None or options_df.empty:
                return None
            
            # Find nearest strike
            option_row = nearest_strike_row(options_df, target_strike)
            if option_row is None:
                return None
            
            # Create OptionQuote object
            option_quote = OptionQuote(
                symbol=f"{chain.symbol if hasattr(chain, 'symbol') else 'UNKNOWN'}",
                strike=float(option_row.get("strike", target_strike)),
                expiration="",  # Will be set by caller
                option_type=option_type,
                bid=float(option_row.get("bid", 0)),
                ask=float(option_row.get("ask", 0)),
                last_price=float(option_row.get("lastPrice", 0)),
                implied_volatility=float(option_row.get("impliedVolatility", 0)),
                volume=int(option_row.get("volume", 0)),
                open_interest=int(option_row.get("openInterest", 0))
            )
            
            return option_quote
            
        except Exception as e:
            self.logger.error(f"Failed to find option at strike {target_strike}: {e}")
            return None
    
    def _validate_trade(self, trade: CalendarTrade) -> bool:
        """Validate trade feasibility and risk parameters."""
        try:
            validation_errors = []
            
            # Check basic trade structure
            if trade.net_debit <= 0:
                validation_errors.append("Invalid calendar: net debit must be positive")
            
            # Check spread widths
            if trade.front_option.spread_percentage > self.config["max_spread_percentage"]:
                validation_errors.append(f"Front option spread too wide: {trade.front_option.spread_percentage:.1f}%")
            
            if trade.back_option.spread_percentage > self.config["max_spread_percentage"]:
                validation_errors.append(f"Back option spread too wide: {trade.back_option.spread_percentage:.1f}%")
            
            # Check liquidity
            if trade.front_option.open_interest < self.config["min_open_interest"]:
                validation_errors.append(f"Front option low OI: {trade.front_option.open_interest}")
            
            if trade.back_option.open_interest < self.config["min_open_interest"]:
                validation_errors.append(f"Back option low OI: {trade.back_option.open_interest}")
            
            # Check time structure
            if trade.days_to_expiration_front >= trade.days_to_expiration_back:
                validation_errors.append("Invalid expiration structure: front must expire before back")
            
            # Update trade validation status
            trade.validation_errors = validation_errors
            trade.is_valid = len(validation_errors) == 0
            
            if validation_errors:
                self.logger.warning(f"Trade validation failed for {trade.symbol}: {'; '.join(validation_errors)}")
            
            return trade.is_valid
            
        except Exception as e:
            self.logger.error(f"Trade validation error for {trade.symbol}: {e}")
            return False


class TradeValidator:
    """
    Trade validation and risk assessment utilities.
    
    Provides comprehensive validation of calendar trades including:
    - Liquidity assessment
    - Spread width validation  
    - Risk/reward analysis
    - Market structure checks
    """
    
    def __init__(self):
        self.logger = logging.getLogger("options_trader.trade_validator")
    
    def assess_trade_quality(self, trade: CalendarTrade) -> Dict[str, Any]:
        """Comprehensive trade quality assessment."""
        try:
            assessment = {
                "overall_score": 0.0,  # 0-100 score
                "liquidity_score": 0.0,
                "spread_score": 0.0, 
                "structure_score": 0.0,
                "risk_score": 0.0,
                "warnings": [],
                "recommendations": []
            }
            
            # Liquidity assessment
            liquidity_score = self._assess_liquidity(trade)
            assessment["liquidity_score"] = liquidity_score
            
            # Spread assessment  
            spread_score = self._assess_spreads(trade)
            assessment["spread_score"] = spread_score
            
            # Structure assessment
            structure_score = self._assess_structure(trade)
            assessment["structure_score"] = structure_score
            
            # Risk assessment
            risk_score = self._assess_risk(trade)
            assessment["risk_score"] = risk_score
            
            # Overall score (weighted average)
            assessment["overall_score"] = (
                liquidity_score * 0.3 +
                spread_score * 0.2 +
                structure_score * 0.3 +
                risk_score * 0.2
            )
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Failed to assess trade quality: {e}")
            return {"overall_score": 0.0, "error": str(e)}
    
    def _assess_liquidity(self, trade: CalendarTrade) -> float:
        """Assess trade liquidity (0-100 score)."""
        score = 0.0
        
        # Open Interest scoring
        front_oi = trade.front_option.open_interest
        back_oi = trade.back_option.open_interest
        
        if front_oi >= 100 and back_oi >= 100:
            score += 40
        elif front_oi >= 50 and back_oi >= 50:
            score += 25
        elif front_oi >= 10 and back_oi >= 10:
            score += 10
        
        # Volume scoring  
        front_vol = trade.front_option.volume
        back_vol = trade.back_option.volume
        
        if front_vol >= 50 and back_vol >= 50:
            score += 30
        elif front_vol >= 20 and back_vol >= 20:
            score += 20
        elif front_vol >= 5 and back_vol >= 5:
            score += 10
        
        # Bid/ask presence
        if (trade.front_option.bid > 0 and trade.front_option.ask > 0 and
            trade.back_option.bid > 0 and trade.back_option.ask > 0):
            score += 30
        
        return min(score, 100.0)
    
    def _assess_spreads(self, trade: CalendarTrade) -> float:
        """Assess bid/ask spread quality (0-100 score)."""
        front_spread_pct = trade.front_option.spread_percentage
        back_spread_pct = trade.back_option.spread_percentage
        
        # Score based on spread percentages
        score = 100.0
        
        # Penalize wide spreads
        if front_spread_pct > 20:
            score -= 50
        elif front_spread_pct > 10:
            score -= 25
        elif front_spread_pct > 5:
            score -= 10
        
        if back_spread_pct > 20:
            score -= 50
        elif back_spread_pct > 10:
            score -= 25
        elif back_spread_pct > 5:
            score -= 10
        
        return max(score, 0.0)
    
    def _assess_structure(self, trade: CalendarTrade) -> float:
        """Assess trade structure quality (0-100 score)."""
        score = 100.0
        
        # Check expiration structure
        if trade.days_to_expiration_front >= trade.days_to_expiration_back:
            score -= 100  # Fatal error
            return 0.0
        
        # Optimal DTE ranges
        front_dte = trade.days_to_expiration_front
        back_dte = trade.days_to_expiration_back
        dte_spread = back_dte - front_dte
        
        # Prefer front month 7-21 DTE
        if 7 <= front_dte <= 21:
            score += 0  # No bonus, this is expected
        elif front_dte < 7:
            score -= 20  # Too close to expiration
        elif front_dte > 45:
            score -= 30  # Too far out
        
        # Prefer ~30 day spread
        if 25 <= dte_spread <= 35:
            score += 0  # Optimal
        elif 20 <= dte_spread <= 40:
            score -= 10  # Acceptable
        else:
            score -= 25  # Suboptimal
        
        return max(score, 0.0)
    
    def _assess_risk(self, trade: CalendarTrade) -> float:
        """Assess risk characteristics (0-100 score, higher = better risk profile)."""
        score = 100.0
        
        # Risk/reward assessment
        max_loss = trade.max_loss
        expected_profit = sum(trade.expected_profit_range) / 2
        
        if expected_profit > 0:
            risk_reward = expected_profit / max_loss
            if risk_reward >= 1.0:
                score += 0  # Good risk/reward
            elif risk_reward >= 0.5:
                score -= 10
            elif risk_reward >= 0.25:
                score -= 25
            else:
                score -= 40
        else:
            score -= 50  # No expected profit
        
        # Capital efficiency
        if max_loss > 10.0:  # More than $10 per contract
            score -= 20
        
        return max(score, 0.0)