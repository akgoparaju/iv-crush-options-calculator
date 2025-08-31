#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Position Sizing Engine - Module 3
==================================

Fractional Kelly methodology with comprehensive risk management for options trading.
Integrates with Module 2 trade construction to determine optimal position sizes.

Key Features:
- Kelly Criterion calculation from P&L analysis
- Signal strength adjustments (3/3 = 100%, 2/3 = 75%, 1/3 = 50%)
- Account size integration from .env settings
- Risk constraint enforcement
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Conditional imports for dependencies
try:
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False

logger = logging.getLogger("options_trader.position_sizing")

# Signal-based Kelly fraction scaling
SIGNAL_SCALING = {
    3: {"name": "Strong Signal", "kelly_multiplier": 1.0, "max_position_pct": 0.05},
    2: {"name": "Moderate Signal", "kelly_multiplier": 0.75, "max_position_pct": 0.03},
    1: {"name": "Weak Signal", "kelly_multiplier": 0.50, "max_position_pct": 0.02}
}

# Default risk parameters (overrideable via .env)
DEFAULT_RISK_LIMITS = {
    "MAX_POSITION_PCT": 0.05,      # 5% max per position
    "MAX_CONCENTRATION_PCT": 0.20,  # 20% max per sector
    "MAX_DAILY_LOSS_PCT": 0.02,    # 2% max daily loss
    "MAX_PORTFOLIO_DELTA": 0.10,   # Net delta exposure limit
    "MIN_BUYING_POWER_PCT": 0.25   # Maintain 25% excess buying power
}


@dataclass
class KellyParameters:
    """Kelly criterion parameters calculated from P&L analysis."""
    win_rate: float              # Probability of profit from P&L scenarios
    avg_win: float              # Average profit from winning scenarios
    avg_loss: float             # Maximum loss (typically net debit)
    signal_strength: int        # Signal count (1-3)
    kelly_fraction: float = field(init=False)
    signal_multiplier: float = field(init=False)
    
    def __post_init__(self):
        """Calculate Kelly fraction using classic formula: f* = (bp - q) / b"""
        if self.avg_loss <= 0:
            logger.warning("Average loss must be positive for Kelly calculation")
            self.kelly_fraction = 0.0
        else:
            # Kelly formula: f* = (bp - q) / b
            # where b = avg_win/avg_loss, p = win_rate, q = 1-p
            b = self.avg_win / self.avg_loss
            p = self.win_rate
            q = 1 - p
            
            raw_kelly = (b * p - q) / b
            self.kelly_fraction = max(0.0, raw_kelly)  # Never go negative
            
        # Apply signal strength multiplier
        scaling = SIGNAL_SCALING.get(self.signal_strength, SIGNAL_SCALING[1])
        self.signal_multiplier = scaling["kelly_multiplier"]
        
        logger.debug(f"Kelly calculation: win_rate={self.win_rate:.3f}, avg_win=${self.avg_win:.2f}, "
                    f"avg_loss=${self.avg_loss:.2f}, raw_kelly={self.kelly_fraction:.4f}, "
                    f"signal_strength={self.signal_strength}, multiplier={self.signal_multiplier}")


@dataclass
class PositionSize:
    """Calculated position size with risk metrics."""
    symbol: str
    contracts: int
    capital_required: float
    account_risk_pct: float
    kelly_fraction: float
    signal_multiplier: float
    risk_adjusted_kelly: float
    max_loss: float
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    original_contracts: int = 0
    adjustment_reason: str = None
    
    
@dataclass
class ValidationResult:
    """Result of position size validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class FractionalKellyCalculator:
    """
    Fractional Kelly calculator for options position sizing.
    
    Integrates with Module 2 P&L analysis to determine optimal position sizes
    based on Kelly criterion, signal strength, and risk constraints.
    """
    
    def __init__(self):
        """Initialize Kelly calculator with risk parameters from environment."""
        self.risk_limits = self._load_risk_limits()
        logger.debug("FractionalKellyCalculator initialized")
    
    def _load_risk_limits(self) -> Dict[str, float]:
        """Load risk limits from environment variables with fallback to defaults."""
        limits = {}
        
        for key, default_value in DEFAULT_RISK_LIMITS.items():
            env_value = os.getenv(key)
            if env_value:
                try:
                    limits[key] = float(env_value)
                    logger.debug(f"Loaded {key} = {limits[key]} from environment")
                except ValueError:
                    logger.warning(f"Invalid {key} value in environment: {env_value}, using default {default_value}")
                    limits[key] = default_value
            else:
                limits[key] = default_value
                
        return limits
    
    def calculate_optimal_fraction(self, trade_data: Dict[str, Any], 
                                 pnl_analysis: Dict[str, Any], 
                                 account_size: float,
                                 signal_count: int = 2) -> PositionSize:
        """
        Calculate optimal position size using fractional Kelly methodology.
        
        Args:
            trade_data: Calendar trade specifications from Module 2
            pnl_analysis: P&L scenarios and statistics from Module 2
            account_size: Total account capital
            signal_count: Number of trading signals (1-3)
            
        Returns:
            PositionSize with recommended contracts and risk metrics
        """
        try:
            symbol = trade_data.get("symbol", "UNKNOWN")
            net_debit = trade_data.get("net_debit", 0.0)
            max_loss = trade_data.get("max_loss", net_debit)
            
            # Extract P&L statistics
            summary_stats = pnl_analysis.get("summary_stats", {})
            win_rate = summary_stats.get("win_rate", 0.0)
            avg_win = summary_stats.get("avg_profit", 0.0)
            max_profit = summary_stats.get("max_profit", 0.0)
            
            # Use max_profit as avg_win if avg_profit not available
            if avg_win <= 0 and max_profit > 0:
                avg_win = max_profit * 0.6  # Conservative estimate
                
            logger.debug(f"Position sizing inputs: symbol={symbol}, win_rate={win_rate:.3f}, "
                        f"avg_win=${avg_win:.2f}, max_loss=${max_loss:.2f}, "
                        f"account_size=${account_size:,.0f}, signals={signal_count}")
            
            # Calculate Kelly parameters
            kelly_params = KellyParameters(
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=max_loss,
                signal_strength=signal_count
            )
            
            # Apply signal strength adjustment
            risk_adjusted_kelly = kelly_params.kelly_fraction * kelly_params.signal_multiplier
            
            # Apply risk constraints
            constrained_kelly = self.apply_risk_constraints(
                risk_adjusted_kelly, signal_count, account_size
            )
            
            # Calculate position size
            position_capital = account_size * constrained_kelly
            raw_contracts = max(1, int(position_capital / max_loss)) if max_loss > 0 else 0
            
            # Apply practical constraints to prevent unrealistic position sizes
            # For low-premium strategies, limit contracts to reasonable amounts
            max_reasonable_contracts = min(10000, int(account_size / 1000))  # Max 10k contracts or 1 per $1k account
            contracts = min(raw_contracts, max_reasonable_contracts)
            
            # Track if position was adjusted
            was_adjusted = contracts < raw_contracts
            adjustment_reason = f"Reduced from {raw_contracts} to {contracts} contracts for practicality" if was_adjusted else None
            
            # Validate position
            validation = self.validate_position_size(
                contracts, max_loss, account_size, signal_count
            )
            
            position_size = PositionSize(
                symbol=symbol,
                contracts=contracts,
                capital_required=contracts * max_loss,
                account_risk_pct=constrained_kelly * 100,
                kelly_fraction=kelly_params.kelly_fraction,
                signal_multiplier=kelly_params.signal_multiplier,
                risk_adjusted_kelly=constrained_kelly,
                max_loss=max_loss,
                is_valid=validation.is_valid,
                validation_errors=validation.errors,
                original_contracts=raw_contracts,
                adjustment_reason=adjustment_reason
            )
            
            logger.info(f"Position calculated for {symbol}: {contracts} contracts, "
                       f"${position_size.capital_required:.0f} capital ({constrained_kelly*100:.1f}% of account)")
            
            return position_size
            
        except Exception as e:
            logger.error(f"Kelly calculation failed: {e}")
            return PositionSize(
                symbol=trade_data.get("symbol", "UNKNOWN"),
                contracts=0,
                capital_required=0.0,
                account_risk_pct=0.0,
                kelly_fraction=0.0,
                signal_multiplier=0.0,
                risk_adjusted_kelly=0.0,
                max_loss=0.0,
                is_valid=False,
                validation_errors=[f"Calculation failed: {str(e)}"]
            )
    
    def adjust_for_signal_strength(self, base_kelly: float, signal_count: int) -> float:
        """Apply signal strength multiplier to base Kelly fraction."""
        scaling = SIGNAL_SCALING.get(signal_count, SIGNAL_SCALING[1])
        adjusted = base_kelly * scaling["kelly_multiplier"]
        
        logger.debug(f"Signal adjustment: {signal_count} signals, "
                    f"multiplier={scaling['kelly_multiplier']}, "
                    f"adjusted_kelly={adjusted:.4f}")
        
        return adjusted
    
    def apply_risk_constraints(self, kelly_fraction: float, signal_count: int, 
                             account_size: float) -> float:
        """
        Apply risk constraints to Kelly fraction.
        
        Constraint hierarchy:
        1. Signal-based maximum position limits
        2. Account-based position limits  
        3. Absolute risk limits
        """
        # Get signal-based max position
        scaling = SIGNAL_SCALING.get(signal_count, SIGNAL_SCALING[1])
        signal_max = scaling["max_position_pct"]
        
        # Apply constraints in order of priority
        constrained = kelly_fraction
        
        # 1. Signal-based limit
        if constrained > signal_max:
            constrained = signal_max
            logger.debug(f"Applied signal-based limit: {signal_max*100:.1f}%")
        
        # 2. Account-based position limit
        account_max = self.risk_limits["MAX_POSITION_PCT"]
        if constrained > account_max:
            constrained = account_max  
            logger.debug(f"Applied account position limit: {account_max*100:.1f}%")
        
        # 3. Sanity checks
        if constrained > 0.20:  # Never risk more than 20% on a single position
            constrained = 0.20
            logger.warning("Applied emergency position limit: 20%")
            
        if constrained < 0.001:  # Minimum meaningful position
            constrained = 0.001
            logger.debug("Applied minimum position size: 0.1%")
        
        logger.debug(f"Risk constraints: kelly={kelly_fraction:.4f} -> constrained={constrained:.4f}")
        
        return constrained
    
    def validate_position_size(self, contracts: int, max_loss_per_contract: float,
                             account_size: float, signal_count: int) -> ValidationResult:
        """Validate calculated position size against risk parameters."""
        errors = []
        warnings = []
        
        total_risk = contracts * max_loss_per_contract
        risk_pct = (total_risk / account_size) * 100 if account_size > 0 else 0
        
        # Check position size limits
        scaling = SIGNAL_SCALING.get(signal_count, SIGNAL_SCALING[1])
        max_position_pct = scaling["max_position_pct"] * 100
        
        if risk_pct > max_position_pct:
            errors.append(f"Position risk {risk_pct:.1f}% exceeds {max_position_pct:.1f}% limit for {signal_count} signals")
        
        # Check account limits
        account_limit = self.risk_limits["MAX_POSITION_PCT"] * 100
        if risk_pct > account_limit:
            errors.append(f"Position risk {risk_pct:.1f}% exceeds account limit {account_limit:.1f}%")
            
        # Check minimum contract count
        if contracts <= 0:
            errors.append("Position size calculation resulted in zero contracts")
        
        # Warnings
        if risk_pct > 3.0:  # Warning at 3%
            warnings.append(f"Large position: {risk_pct:.1f}% of account at risk")
            
        if signal_count == 1:
            warnings.append("Weak signal: consider smaller position or wait for confirmation")
        
        is_valid = len(errors) == 0
        
        logger.debug(f"Position validation: {contracts} contracts, ${total_risk:.0f} risk "
                    f"({risk_pct:.1f}%), valid={is_valid}")
        
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)