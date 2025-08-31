#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Account Management - Module 3
==============================

Account settings and capital management for position sizing calculations.
Loads account configuration from .env file with reasonable defaults.

Key Features:
- Account size and buying power management
- Risk per trade settings from environment
- Margin requirement validation
- Capital allocation tracking
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

from .risk_management import Position, PortfolioMetrics

logger = logging.getLogger("options_trader.account")

# Default account settings
DEFAULT_ACCOUNT_SIZE = 100000.0  # $100K default
DEFAULT_RISK_PER_TRADE = 0.02   # 2% default risk per trade
DEFAULT_MARGIN_MULTIPLIER = 2.0  # 2:1 margin


@dataclass
class AccountSettings:
    """Account configuration and capital management."""
    total_capital: float
    risk_per_trade_pct: float = 0.02  # 2% risk per trade
    margin_multiplier: float = 2.0    # 2:1 margin
    available_buying_power: float = field(init=False)
    reserved_capital: float = 0.0     # Capital reserved for existing positions
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """Calculate available buying power."""
        self.available_buying_power = (self.total_capital - self.reserved_capital) * self.margin_multiplier
        
        logger.debug(f"Account initialized: ${self.total_capital:,.0f} capital, "
                    f"{self.risk_per_trade_pct*100:.1f}% risk per trade, "
                    f"${self.available_buying_power:,.0f} buying power")


@dataclass
class MarginValidation:
    """Margin requirement validation result."""
    is_valid: bool
    required_margin: float
    available_margin: float
    margin_utilization_pct: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class CapitalAllocation:
    """Capital allocation for a specific position."""
    symbol: str
    contracts: int
    capital_required: float
    margin_required: float
    risk_capital: float
    percentage_of_account: float
    is_affordable: bool
    

class AccountManager:
    """
    Account management for position sizing and capital allocation.
    
    Loads account settings from environment variables and provides
    capital allocation and margin validation for trading decisions.
    """
    
    def __init__(self, account_settings: Optional[AccountSettings] = None):
        """
        Initialize account manager.
        
        Args:
            account_settings: Optional account settings. If None, loads from environment.
        """
        self.settings = account_settings or self.load_settings()
        self._validate_settings()
        
        logger.info(f"AccountManager initialized: ${self.settings.total_capital:,.0f} account, "
                   f"{self.settings.risk_per_trade_pct*100:.1f}% risk per trade")
    
    @classmethod
    def load_settings(cls) -> AccountSettings:
        """Load account settings from environment variables."""
        # Load from environment with fallback to defaults
        total_capital = float(os.getenv("ACCOUNT_SIZE", DEFAULT_ACCOUNT_SIZE))
        risk_per_trade = float(os.getenv("RISK_PER_TRADE", DEFAULT_RISK_PER_TRADE))
        margin_multiplier = float(os.getenv("MARGIN_MULTIPLIER", DEFAULT_MARGIN_MULTIPLIER))
        
        logger.debug(f"Loading account settings from environment: "
                    f"ACCOUNT_SIZE=${total_capital:,.0f}, "
                    f"RISK_PER_TRADE={risk_per_trade*100:.1f}%, "
                    f"MARGIN_MULTIPLIER={margin_multiplier:.1f}x")
        
        settings = AccountSettings(
            total_capital=total_capital,
            risk_per_trade_pct=risk_per_trade,
            margin_multiplier=margin_multiplier
        )
        
        return settings
    
    def _validate_settings(self) -> None:
        """Validate account settings for reasonableness."""
        if self.settings.total_capital <= 0:
            raise ValueError(f"Account size must be positive: ${self.settings.total_capital}")
        
        if not (0.001 <= self.settings.risk_per_trade_pct <= 0.10):
            logger.warning(f"Risk per trade {self.settings.risk_per_trade_pct*100:.1f}% is outside "
                          "recommended range (0.1% - 10.0%)")
        
        if not (1.0 <= self.settings.margin_multiplier <= 4.0):
            logger.warning(f"Margin multiplier {self.settings.margin_multiplier:.1f}x is outside "
                          "typical range (1.0x - 4.0x)")
        
        logger.debug("Account settings validation passed")
    
    def get_available_capital(self) -> float:
        """Get available capital for new positions."""
        return max(0, self.settings.total_capital - self.settings.reserved_capital)
    
    def get_available_buying_power(self) -> float:
        """Get available buying power including margin."""
        available_capital = self.get_available_capital()
        return available_capital * self.settings.margin_multiplier
    
    def get_max_risk_per_trade(self) -> float:
        """Get maximum dollar risk per trade based on account settings."""
        return self.settings.total_capital * self.settings.risk_per_trade_pct
    
    def calculate_capital_allocation(self, symbol: str, contracts: int, net_debit: float,
                                   max_loss: float) -> CapitalAllocation:
        """
        Calculate capital allocation for a proposed position.
        
        Args:
            symbol: Position symbol
            contracts: Number of contracts
            net_debit: Net debit per contract
            max_loss: Maximum loss per contract
            
        Returns:
            CapitalAllocation with detailed capital requirements
        """
        # Calculate capital requirements
        capital_required = contracts * net_debit
        risk_capital = contracts * max_loss
        
        # For calendar spreads, margin requirement is typically the net debit
        margin_required = capital_required
        
        # Calculate as percentage of account
        percentage_of_account = (risk_capital / self.settings.total_capital) * 100
        
        # Check if affordable
        available_capital = self.get_available_capital()
        is_affordable = capital_required <= available_capital
        
        allocation = CapitalAllocation(
            symbol=symbol,
            contracts=contracts,
            capital_required=capital_required,
            margin_required=margin_required,
            risk_capital=risk_capital,
            percentage_of_account=percentage_of_account,
            is_affordable=is_affordable
        )
        
        logger.debug(f"Capital allocation for {symbol}: {contracts} contracts, "
                    f"${capital_required:,.0f} required, ${risk_capital:,.0f} at risk "
                    f"({percentage_of_account:.1f}% of account), affordable={is_affordable}")
        
        return allocation
    
    def validate_margin_requirements(self, symbol: str, contracts: int, net_debit: float,
                                   strategy_type: str = "calendar_spread") -> MarginValidation:
        """
        Validate margin requirements for a proposed position.
        
        Args:
            symbol: Position symbol
            contracts: Number of contracts
            net_debit: Net debit per contract
            strategy_type: Type of options strategy
            
        Returns:
            MarginValidation with margin compliance assessment
        """
        errors = []
        warnings = []
        
        # Calculate margin requirement based on strategy type
        if strategy_type == "calendar_spread":
            # Calendar spreads: margin = net debit (typically)
            required_margin = contracts * net_debit
        else:
            # Conservative estimate for other strategies
            required_margin = contracts * net_debit * 1.5
        
        # Get available margin capacity
        available_margin = self.get_available_buying_power()
        
        # Calculate utilization
        margin_utilization_pct = (required_margin / self.settings.available_buying_power) * 100
        
        # Validation checks
        is_valid = True
        
        if required_margin > available_margin:
            errors.append(f"Insufficient margin: ${required_margin:,.0f} required, "
                         f"${available_margin:,.0f} available")
            is_valid = False
        
        if margin_utilization_pct > 75:
            warnings.append(f"High margin utilization: {margin_utilization_pct:.1f}%")
        
        if required_margin > self.settings.total_capital:
            errors.append("Position margin exceeds total account value")
            is_valid = False
        
        logger.debug(f"Margin validation for {symbol}: required=${required_margin:,.0f}, "
                    f"available=${available_margin:,.0f}, utilization={margin_utilization_pct:.1f}%, "
                    f"valid={is_valid}")
        
        return MarginValidation(
            is_valid=is_valid,
            required_margin=required_margin,
            available_margin=available_margin,
            margin_utilization_pct=margin_utilization_pct,
            errors=errors,
            warnings=warnings
        )
    
    def update_reserved_capital(self, positions: List[Position]) -> None:
        """
        Update reserved capital based on current positions.
        
        Args:
            positions: List of current portfolio positions
        """
        total_reserved = sum(pos.net_debit * pos.contracts for pos in positions)
        self.settings.reserved_capital = total_reserved
        
        # Recalculate buying power
        self.settings.available_buying_power = (
            (self.settings.total_capital - self.settings.reserved_capital) * 
            self.settings.margin_multiplier
        )
        
        logger.debug(f"Updated reserved capital: ${total_reserved:,.0f}, "
                    f"available buying power: ${self.settings.available_buying_power:,.0f}")
    
    def get_position_size_recommendation(self, max_loss_per_contract: float,
                                       signal_strength: int = 2) -> Dict[str, Any]:
        """
        Get position size recommendation based on account settings.
        
        Args:
            max_loss_per_contract: Maximum loss per contract
            signal_strength: Signal strength (1-3)
            
        Returns:
            Dictionary with position size recommendations
        """
        # Calculate based on risk per trade
        max_risk = self.get_max_risk_per_trade()
        
        # Adjust for signal strength
        signal_multipliers = {1: 0.5, 2: 0.75, 3: 1.0}
        risk_multiplier = signal_multipliers.get(signal_strength, 0.75)
        adjusted_risk = max_risk * risk_multiplier
        
        # Calculate recommended contracts
        if max_loss_per_contract > 0:
            recommended_contracts = max(1, int(adjusted_risk / max_loss_per_contract))
        else:
            recommended_contracts = 0
        
        recommendation = {
            "recommended_contracts": recommended_contracts,
            "max_risk_per_trade": max_risk,
            "adjusted_risk": adjusted_risk,
            "signal_multiplier": risk_multiplier,
            "capital_required": recommended_contracts * max_loss_per_contract,
            "risk_percentage": (adjusted_risk / self.settings.total_capital) * 100
        }
        
        logger.debug(f"Position size recommendation: {recommended_contracts} contracts, "
                    f"${adjusted_risk:,.0f} risk ({recommendation['risk_percentage']:.1f}% of account)")
        
        return recommendation
    
    def can_afford_position(self, capital_required: float, margin_required: float = None) -> bool:
        """
        Check if account can afford a position.
        
        Args:
            capital_required: Capital needed for position
            margin_required: Margin needed (optional, defaults to capital_required)
            
        Returns:
            True if position is affordable
        """
        if margin_required is None:
            margin_required = capital_required
        
        available_capital = self.get_available_capital()
        available_margin = self.get_available_buying_power()
        
        can_afford = (capital_required <= available_capital and 
                     margin_required <= available_margin)
        
        logger.debug(f"Affordability check: capital_required=${capital_required:,.0f}, "
                    f"available=${available_capital:,.0f}, can_afford={can_afford}")
        
        return can_afford
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get comprehensive account summary."""
        available_capital = self.get_available_capital()
        available_margin = self.get_available_buying_power()
        utilization_pct = (self.settings.reserved_capital / self.settings.total_capital) * 100
        
        return {
            "total_capital": self.settings.total_capital,
            "reserved_capital": self.settings.reserved_capital,
            "available_capital": available_capital,
            "available_buying_power": available_margin,
            "utilization_percentage": utilization_pct,
            "risk_per_trade_pct": self.settings.risk_per_trade_pct * 100,
            "max_risk_per_trade": self.get_max_risk_per_trade(),
            "margin_multiplier": self.settings.margin_multiplier,
            "last_updated": self.settings.last_updated
        }