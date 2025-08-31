#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Management Engine - Module 3
==================================

Portfolio risk management and position validation for options trading.
Enforces concentration limits, portfolio Greeks constraints, and compliance rules.

Key Features:
- Portfolio concentration limits (max 20% per sector/strategy)
- Greeks-based portfolio risk calculation
- Daily loss limits and drawdown protection
- Position tracking with JSON persistence
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger("options_trader.risk_management")

# Default portfolio position tracking file
POSITIONS_FILE = ".portfolio_positions.json"


@dataclass
class RiskLimits:
    """Portfolio risk limits loaded from environment variables."""
    max_position_pct: float = 0.05      # 5% max per position
    max_concentration_pct: float = 0.20  # 20% max per sector/strategy
    max_daily_loss_pct: float = 0.02    # 2% max daily loss
    max_portfolio_delta: float = 0.10   # Net delta exposure limit
    min_buying_power_pct: float = 0.25  # Maintain 25% excess buying power
    
    @classmethod
    def load_from_env(cls) -> 'RiskLimits':
        """Load risk limits from environment variables with fallback to defaults."""
        return cls(
            max_position_pct=float(os.getenv("MAX_POSITION_PCT", 0.05)),
            max_concentration_pct=float(os.getenv("MAX_CONCENTRATION_PCT", 0.20)),
            max_daily_loss_pct=float(os.getenv("MAX_DAILY_LOSS_PCT", 0.02)),
            max_portfolio_delta=float(os.getenv("MAX_PORTFOLIO_DELTA", 0.10)),
            min_buying_power_pct=float(os.getenv("MIN_BUYING_POWER_PCT", 0.25))
        )


@dataclass
class Position:
    """Individual portfolio position."""
    symbol: str
    contracts: int
    entry_date: str
    strategy_type: str = "calendar_spread"
    net_debit: float = 0.0
    max_loss: float = 0.0
    unrealized_pnl: float = 0.0
    net_delta: float = 0.0
    net_vega: float = 0.0
    net_theta: float = 0.0
    sector: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary for JSON serialization."""
        return {
            "symbol": self.symbol,
            "contracts": self.contracts,
            "entry_date": self.entry_date,
            "strategy_type": self.strategy_type,
            "net_debit": self.net_debit,
            "max_loss": self.max_loss,
            "unrealized_pnl": self.unrealized_pnl,
            "net_delta": self.net_delta,
            "net_vega": self.net_vega,
            "net_theta": self.net_theta,
            "sector": self.sector
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        """Create position from dictionary."""
        return cls(**data)


@dataclass
class PortfolioGreeks:
    """Portfolio-level Greeks aggregation."""
    net_delta: float = 0.0
    net_gamma: float = 0.0
    net_theta: float = 0.0
    net_vega: float = 0.0
    delta_dollars: float = 0.0
    theta_dollars: float = 0.0
    vega_dollars: float = 0.0
    position_count: int = 0
    
    
@dataclass
class PortfolioMetrics:
    """Portfolio performance and risk metrics."""
    total_capital_at_risk: float = 0.0
    portfolio_utilization_pct: float = 0.0
    concentration_by_sector: Dict[str, float] = field(default_factory=dict)
    concentration_by_strategy: Dict[str, float] = field(default_factory=dict)
    unrealized_pnl: float = 0.0
    daily_pnl: float = 0.0
    greeks: PortfolioGreeks = field(default_factory=PortfolioGreeks)
    

@dataclass
class RiskAssessment:
    """Risk compliance assessment result."""
    is_compliant: bool = True
    risk_score: float = 0.0  # 0-100 scale
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AdjustedPosition:
    """Position after risk adjustment."""
    original_contracts: int
    adjusted_contracts: int
    adjustment_reason: str
    capital_saved: float = 0.0


class RiskManagementEngine:
    """
    Portfolio risk management engine.
    
    Enforces position limits, portfolio concentration constraints,
    and provides comprehensive risk assessment for new positions.
    """
    
    def __init__(self, positions_file: str = POSITIONS_FILE):
        """Initialize risk management engine with position tracking."""
        self.positions_file = Path(positions_file)
        self.risk_limits = RiskLimits.load_from_env()
        self.current_positions = self._load_positions()
        
        logger.debug(f"RiskManagementEngine initialized with {len(self.current_positions)} positions")
        logger.debug(f"Risk limits: position={self.risk_limits.max_position_pct*100:.1f}%, "
                    f"concentration={self.risk_limits.max_concentration_pct*100:.1f}%, "
                    f"daily_loss={self.risk_limits.max_daily_loss_pct*100:.1f}%")
    
    def _load_positions(self) -> List[Position]:
        """Load current positions from JSON file."""
        if not self.positions_file.exists():
            logger.debug("No positions file found, starting with empty portfolio")
            return []
            
        try:
            with open(self.positions_file, 'r') as f:
                data = json.load(f)
                positions = [Position.from_dict(pos) for pos in data.get("positions", [])]
                logger.debug(f"Loaded {len(positions)} positions from {self.positions_file}")
                return positions
                
        except Exception as e:
            logger.warning(f"Failed to load positions from {self.positions_file}: {e}")
            return []
    
    def _save_positions(self) -> None:
        """Save current positions to JSON file."""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "positions": [pos.to_dict() for pos in self.current_positions]
            }
            
            with open(self.positions_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved {len(self.current_positions)} positions to {self.positions_file}")
            
        except Exception as e:
            logger.error(f"Failed to save positions to {self.positions_file}: {e}")
    
    def enforce_position_limits(self, proposed_contracts: int, max_loss_per_contract: float,
                               account_size: float, symbol: str) -> AdjustedPosition:
        """
        Enforce position size limits based on current portfolio state.
        
        Args:
            proposed_contracts: Requested position size
            max_loss_per_contract: Maximum loss per contract
            account_size: Total account value
            symbol: Symbol for new position
            
        Returns:
            AdjustedPosition with any necessary size reductions
        """
        original_contracts = proposed_contracts
        proposed_risk = proposed_contracts * max_loss_per_contract
        
        # Check individual position limit
        max_position_risk = account_size * self.risk_limits.max_position_pct
        if proposed_risk > max_position_risk:
            adjusted_contracts = int(max_position_risk / max_loss_per_contract)
            logger.warning(f"Position size reduced from {original_contracts} to {adjusted_contracts} "
                          f"contracts due to position limit ({self.risk_limits.max_position_pct*100:.1f}%)")
            
            return AdjustedPosition(
                original_contracts=original_contracts,
                adjusted_contracts=max(1, adjusted_contracts),
                adjustment_reason=f"Individual position limit ({self.risk_limits.max_position_pct*100:.1f}%)",
                capital_saved=proposed_risk - max_position_risk
            )
        
        # Check portfolio utilization
        current_risk = sum(pos.max_loss * pos.contracts for pos in self.current_positions)
        total_risk_after = current_risk + proposed_risk
        
        # Conservative limit: don't use more than 75% of account
        max_total_risk = account_size * 0.75
        if total_risk_after > max_total_risk:
            available_risk = max_total_risk - current_risk
            if available_risk > 0:
                adjusted_contracts = int(available_risk / max_loss_per_contract)
                logger.warning(f"Position size reduced from {original_contracts} to {adjusted_contracts} "
                              f"contracts due to portfolio utilization limit")
                
                return AdjustedPosition(
                    original_contracts=original_contracts,
                    adjusted_contracts=max(1, adjusted_contracts),
                    adjustment_reason="Portfolio utilization limit (75%)",
                    capital_saved=proposed_risk - available_risk
                )
            else:
                logger.error("Portfolio already at maximum utilization")
                return AdjustedPosition(
                    original_contracts=original_contracts,
                    adjusted_contracts=0,
                    adjustment_reason="Portfolio fully utilized",
                    capital_saved=proposed_risk
                )
        
        # No adjustment needed
        return AdjustedPosition(
            original_contracts=original_contracts,
            adjusted_contracts=original_contracts,
            adjustment_reason="No adjustment required"
        )
    
    def check_portfolio_concentration(self, symbol: str, strategy_type: str = "calendar_spread",
                                    position_risk: float = 0.0, account_size: float = 0.0) -> bool:
        """
        Check if adding new position violates concentration limits.
        
        Args:
            symbol: New position symbol
            strategy_type: Type of strategy
            position_risk: Dollar risk of new position
            account_size: Total account value
            
        Returns:
            True if position is within concentration limits
        """
        # Get current sector (simplified - in practice would use sector mapping)
        sector = self._get_symbol_sector(symbol)
        
        # Calculate current concentrations
        metrics = self.calculate_portfolio_metrics(account_size)
        
        # Check sector concentration
        current_sector_risk = metrics.concentration_by_sector.get(sector, 0.0)
        new_sector_risk = current_sector_risk + position_risk
        sector_pct = (new_sector_risk / account_size) * 100 if account_size > 0 else 0
        
        if sector_pct > self.risk_limits.max_concentration_pct * 100:
            logger.warning(f"Sector concentration limit exceeded: {sector} would be {sector_pct:.1f}% "
                          f"(limit: {self.risk_limits.max_concentration_pct*100:.1f}%)")
            return False
        
        # Check strategy concentration
        current_strategy_risk = metrics.concentration_by_strategy.get(strategy_type, 0.0)
        new_strategy_risk = current_strategy_risk + position_risk
        strategy_pct = (new_strategy_risk / account_size) * 100 if account_size > 0 else 0
        
        if strategy_pct > self.risk_limits.max_concentration_pct * 100:
            logger.warning(f"Strategy concentration limit exceeded: {strategy_type} would be {strategy_pct:.1f}% "
                          f"(limit: {self.risk_limits.max_concentration_pct*100:.1f}%)")
            return False
        
        return True
    
    def calculate_portfolio_greeks(self, account_size: float = 100000) -> PortfolioGreeks:
        """Calculate aggregate portfolio Greeks."""
        net_delta = sum(pos.net_delta * pos.contracts for pos in self.current_positions)
        net_theta = sum(pos.net_theta * pos.contracts for pos in self.current_positions)
        net_vega = sum(pos.net_vega * pos.contracts for pos in self.current_positions)
        
        # Estimate dollar Greeks (simplified calculation)
        delta_dollars = net_delta * account_size * 0.01  # 1% move impact
        theta_dollars = net_theta  # Already in dollars per day
        vega_dollars = net_vega * 0.01  # 1% vol move impact
        
        return PortfolioGreeks(
            net_delta=net_delta,
            net_theta=net_theta,
            net_vega=net_vega,
            delta_dollars=delta_dollars,
            theta_dollars=theta_dollars,
            vega_dollars=vega_dollars,
            position_count=len(self.current_positions)
        )
    
    def calculate_portfolio_metrics(self, account_size: float = 100000) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics."""
        # Calculate capital at risk
        total_risk = sum(pos.max_loss * pos.contracts for pos in self.current_positions)
        utilization_pct = (total_risk / account_size) * 100 if account_size > 0 else 0
        
        # Calculate concentrations by sector
        sector_risk = {}
        strategy_risk = {}
        
        for pos in self.current_positions:
            pos_risk = pos.max_loss * pos.contracts
            
            # Sector concentration
            sector = self._get_symbol_sector(pos.symbol)
            sector_risk[sector] = sector_risk.get(sector, 0) + pos_risk
            
            # Strategy concentration
            strategy_risk[pos.strategy_type] = strategy_risk.get(pos.strategy_type, 0) + pos_risk
        
        # Calculate P&L
        unrealized_pnl = sum(pos.unrealized_pnl * pos.contracts for pos in self.current_positions)
        
        # Get portfolio Greeks
        greeks = self.calculate_portfolio_greeks(account_size)
        
        return PortfolioMetrics(
            total_capital_at_risk=total_risk,
            portfolio_utilization_pct=utilization_pct,
            concentration_by_sector=sector_risk,
            concentration_by_strategy=strategy_risk,
            unrealized_pnl=unrealized_pnl,
            greeks=greeks
        )
    
    def validate_risk_compliance(self, symbol: str, contracts: int, max_loss: float,
                               account_size: float, net_delta: float = 0.0) -> RiskAssessment:
        """
        Comprehensive risk compliance validation for new position.
        
        Args:
            symbol: Position symbol
            contracts: Number of contracts
            max_loss: Maximum loss per contract
            account_size: Total account value
            net_delta: Position delta exposure
            
        Returns:
            RiskAssessment with compliance status and recommendations
        """
        violations = []
        warnings = []
        recommendations = []
        
        position_risk = contracts * max_loss
        risk_pct = (position_risk / account_size) * 100 if account_size > 0 else 0
        
        # Check position size limit
        if risk_pct > self.risk_limits.max_position_pct * 100:
            violations.append(f"Position size {risk_pct:.1f}% exceeds limit {self.risk_limits.max_position_pct*100:.1f}%")
        
        # Check concentration
        if not self.check_portfolio_concentration(symbol, "calendar_spread", position_risk, account_size):
            violations.append("Position would exceed concentration limits")
        
        # Check portfolio utilization
        current_risk = sum(pos.max_loss * pos.contracts for pos in self.current_positions)
        total_utilization = ((current_risk + position_risk) / account_size) * 100 if account_size > 0 else 0
        
        if total_utilization > 75:
            violations.append(f"Total portfolio utilization {total_utilization:.1f}% exceeds 75% limit")
        elif total_utilization > 60:
            warnings.append(f"High portfolio utilization: {total_utilization:.1f}%")
        
        # Check delta exposure
        portfolio_greeks = self.calculate_portfolio_greeks(account_size)
        projected_delta = portfolio_greeks.net_delta + (net_delta * contracts)
        # Delta exposure as percentage of account value
        # Delta represents dollar exposure per $1 move in underlying
        delta_exposure_pct = abs(projected_delta / account_size) * 100 if account_size > 0 else 0
        
        if delta_exposure_pct > self.risk_limits.max_portfolio_delta * 100:
            violations.append(f"Delta exposure {delta_exposure_pct:.1f}% exceeds {self.risk_limits.max_portfolio_delta*100:.1f}% limit")
        
        # Generate recommendations
        if risk_pct > 2:
            recommendations.append("Consider reducing position size for better risk management")
        
        if len(self.current_positions) >= 10:
            recommendations.append("Portfolio has many positions - consider closing some before adding new ones")
        
        # Calculate risk score (0-100)
        risk_score = min(100, max(0, 
            (risk_pct * 20) +  # Position size component
            (total_utilization * 0.5) +  # Portfolio utilization component  
            (delta_exposure_pct * 10)  # Delta exposure component
        ))
        
        is_compliant = len(violations) == 0
        
        logger.debug(f"Risk assessment for {symbol}: compliant={is_compliant}, "
                    f"risk_score={risk_score:.1f}, violations={len(violations)}")
        
        return RiskAssessment(
            is_compliant=is_compliant,
            risk_score=risk_score,
            violations=violations,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def add_position(self, symbol: str, contracts: int, net_debit: float, max_loss: float,
                    strategy_type: str = "calendar_spread", net_delta: float = 0.0,
                    net_vega: float = 0.0, net_theta: float = 0.0) -> bool:
        """
        Add new position to portfolio tracking.
        
        Returns:
            True if position was added successfully
        """
        try:
            position = Position(
                symbol=symbol,
                contracts=contracts,
                entry_date=date.today().isoformat(),
                strategy_type=strategy_type,
                net_debit=net_debit,
                max_loss=max_loss,
                net_delta=net_delta,
                net_vega=net_vega,
                net_theta=net_theta,
                sector=self._get_symbol_sector(symbol)
            )
            
            self.current_positions.append(position)
            self._save_positions()
            
            logger.info(f"Added position: {symbol} {contracts} contracts, ${net_debit * contracts:.0f} debit")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add position {symbol}: {e}")
            return False
    
    def remove_position(self, symbol: str) -> bool:
        """Remove position from portfolio tracking."""
        try:
            original_count = len(self.current_positions)
            self.current_positions = [pos for pos in self.current_positions if pos.symbol != symbol]
            
            if len(self.current_positions) < original_count:
                self._save_positions()
                logger.info(f"Removed position: {symbol}")
                return True
            else:
                logger.warning(f"Position not found for removal: {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove position {symbol}: {e}")
            return False
    
    def _get_symbol_sector(self, symbol: str) -> str:
        """
        Get sector for symbol (simplified implementation).
        In production, this would use a proper sector mapping service.
        """
        # Simplified sector mapping
        tech_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']
        auto_symbols = ['NIO', 'XPEV', 'LI', 'F', 'GM']
        
        if symbol in tech_symbols:
            return "Technology"
        elif symbol in auto_symbols:
            return "Automotive"
        else:
            return "Other"