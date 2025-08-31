#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P&L Simulation Engine - Module 2
================================

Post-earnings P&L simulation with IV crush modeling for calendar spreads.
Provides comprehensive scenario analysis with price movement and volatility changes.

Core Components:
- PnLEngine: Main simulation engine with IV crush modeling
- IVCrushModel: Configurable IV crush parameter management
- ScenarioGenerator: Price and volatility scenario creation
- PnLGrid: Results visualization and analysis

Integrates seamlessly with existing Module 1 architecture.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
import math

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

from .trade_construction import CalendarTrade, OptionQuote

logger = logging.getLogger("options_trader.pnl_engine")


@dataclass
class IVCrushParameters:
    """IV crush parameters for different liquidity tiers."""
    front_iv_drop: float = 0.30  # 30% IV drop in front month
    back_iv_drop: float = 0.10   # 10% IV drop in back month
    liquidity_tier: str = "medium"  # high, medium, low
    confidence: float = 0.8      # Confidence in crush parameters
    
    @classmethod
    def get_by_liquidity(cls, avg_volume: float) -> 'IVCrushParameters':
        """Get IV crush parameters based on average volume."""
        if avg_volume >= 2_000_000:
            return cls(front_iv_drop=0.30, back_iv_drop=0.10, liquidity_tier="high", confidence=0.9)
        elif avg_volume >= 500_000:
            return cls(front_iv_drop=0.35, back_iv_drop=0.15, liquidity_tier="medium", confidence=0.8)
        else:
            return cls(front_iv_drop=0.40, back_iv_drop=0.20, liquidity_tier="low", confidence=0.7)


@dataclass 
class PnLScenario:
    """Single P&L scenario result."""
    price_change_pct: float
    new_underlying_price: float
    iv_crush_scenario: str  # 'conservative', 'expected', 'optimistic'
    front_iv_after: float
    back_iv_after: float
    front_option_value: float
    back_option_value: float
    spread_value: float
    pnl: float
    pnl_pct: float
    
    
class PnLGrid:
    """P&L simulation results grid with analysis methods."""
    
    def __init__(self, scenarios: List[PnLScenario], trade: CalendarTrade):
        self.scenarios = scenarios
        self.trade = trade
        self.logger = logging.getLogger("options_trader.pnl_grid")
    
    def to_dataframe(self) -> Optional[pd.DataFrame]:
        """Convert scenarios to pandas DataFrame."""
        if not HAS_PANDAS or not self.scenarios:
            return None
            
        data = []
        for scenario in self.scenarios:
            data.append({
                'price_change_pct': scenario.price_change_pct,
                'new_price': scenario.new_underlying_price,
                'iv_scenario': scenario.iv_crush_scenario,
                'front_iv_after': scenario.front_iv_after,
                'back_iv_after': scenario.back_iv_after,
                'spread_value': scenario.spread_value,
                'pnl': scenario.pnl,
                'pnl_pct': scenario.pnl_pct
            })
        
        return pd.DataFrame(data)
    
    def get_summary_stats(self) -> Dict[str, float]:
        """Calculate summary statistics from scenarios."""
        if not self.scenarios:
            return {}
        
        pnls = [s.pnl for s in self.scenarios]
        pnl_pcts = [s.pnl_pct for s in self.scenarios]
        
        if not HAS_NUMPY:
            # Basic statistics without numpy
            return {
                'max_profit': max(pnls),
                'max_loss': min(pnls),
                'avg_pnl': sum(pnls) / len(pnls),
                'profit_scenarios': sum(1 for pnl in pnls if pnl > 0),
                'total_scenarios': len(pnls)
            }
        
        pnls_array = np.array(pnls)
        pnl_pcts_array = np.array(pnl_pcts)
        
        return {
            'max_profit': float(np.max(pnls_array)),
            'max_loss': float(np.min(pnls_array)),
            'avg_pnl': float(np.mean(pnls_array)),
            'median_pnl': float(np.median(pnls_array)),
            'std_pnl': float(np.std(pnls_array)),
            'percentile_25': float(np.percentile(pnls_array, 25)),
            'percentile_75': float(np.percentile(pnls_array, 75)),
            'profit_scenarios': int(np.sum(pnls_array > 0)),
            'total_scenarios': len(pnls),
            'win_rate': float(np.sum(pnls_array > 0) / len(pnls))
        }
    
    def get_expected_move_pnl(self, expected_move_pct: float) -> Dict[str, float]:
        """Get P&L at expected move boundaries."""
        results = {}
        
        for scenario in self.scenarios:
            price_change = abs(scenario.price_change_pct)
            
            # Find scenarios near expected move boundaries
            if abs(price_change - expected_move_pct) < 0.5:  # Within 0.5%
                key = f"up_{expected_move_pct:.1f}pct" if scenario.price_change_pct > 0 else f"down_{expected_move_pct:.1f}pct"
                if key not in results:
                    results[key] = scenario.pnl
        
        return results


class PnLEngine:
    """
    Main P&L simulation engine for calendar spreads.
    
    Provides comprehensive post-earnings P&L analysis including:
    - IV crush modeling with configurable parameters
    - Price movement scenarios
    - Time decay calculations
    - Greeks-based option revaluation
    """
    
    def __init__(self):
        self.logger = logging.getLogger("options_trader.pnl_engine")
        
        # Default simulation parameters
        self.config = {
            "price_move_range": (-10.0, 10.0),  # -10% to +10%
            "price_move_step": 1.0,             # 1% increments
            "iv_scenarios": ["conservative", "expected", "optimistic"],
            "time_decay_days": 1,               # 1 day time decay
            "risk_free_rate": 0.05,            # 5% risk-free rate
            "use_simplified_pricing": True     # Use simplified Black-Scholes
        }
    
    def simulate_post_earnings_scenarios(self, trade: CalendarTrade, 
                                       crush_params: Optional[IVCrushParameters] = None,
                                       expected_move_pct: Optional[float] = None) -> PnLGrid:
        """
        Simulate post-earnings P&L scenarios for calendar spread.
        
        Args:
            trade: CalendarTrade object
            crush_params: IV crush parameters (auto-generated if None)
            expected_move_pct: Expected move percentage for overlay
            
        Returns:
            PnLGrid with all scenario results
        """
        try:
            self.logger.debug(f"Starting P&L simulation for {trade.symbol}")
            
            # Generate IV crush parameters if not provided
            if crush_params is None:
                # Use default medium liquidity parameters
                crush_params = IVCrushParameters()
            
            # Generate price movement scenarios
            price_scenarios = self._generate_price_scenarios()
            
            # Generate IV crush scenarios
            iv_scenarios = self._generate_iv_scenarios(trade, crush_params)
            
            # Simulate all combinations
            all_scenarios = []
            for price_change_pct in price_scenarios:
                new_price = trade.underlying_price * (1 + price_change_pct / 100)
                
                for iv_scenario_name, (front_iv_after, back_iv_after) in iv_scenarios.items():
                    scenario = self._simulate_single_scenario(
                        trade, price_change_pct, new_price, 
                        iv_scenario_name, front_iv_after, back_iv_after
                    )
                    all_scenarios.append(scenario)
            
            result_grid = PnLGrid(all_scenarios, trade)
            
            self.logger.info(f"Completed P&L simulation for {trade.symbol}: {len(all_scenarios)} scenarios")
            return result_grid
            
        except Exception as e:
            self.logger.error(f"P&L simulation failed for {trade.symbol}: {e}")
            return PnLGrid([], trade)
    
    def _generate_price_scenarios(self) -> List[float]:
        """Generate price movement scenarios."""
        min_move, max_move = self.config["price_move_range"]
        step = self.config["price_move_step"]
        
        scenarios = []
        current = min_move
        while current <= max_move:
            scenarios.append(current)
            current += step
        
        return scenarios
    
    def _generate_iv_scenarios(self, trade: CalendarTrade, 
                             crush_params: IVCrushParameters) -> Dict[str, Tuple[float, float]]:
        """Generate IV crush scenarios."""
        front_iv_before = trade.front_option.implied_volatility
        back_iv_before = trade.back_option.implied_volatility
        
        scenarios = {}
        
        # Conservative scenario (less IV crush)
        conservative_front_drop = crush_params.front_iv_drop * 0.7
        conservative_back_drop = crush_params.back_iv_drop * 0.7
        scenarios["conservative"] = (
            front_iv_before * (1 - conservative_front_drop),
            back_iv_before * (1 - conservative_back_drop)
        )
        
        # Expected scenario (normal IV crush)
        scenarios["expected"] = (
            front_iv_before * (1 - crush_params.front_iv_drop),
            back_iv_before * (1 - crush_params.back_iv_drop)
        )
        
        # Optimistic scenario (more IV crush, better for calendar)
        optimistic_front_drop = crush_params.front_iv_drop * 1.3
        optimistic_back_drop = crush_params.back_iv_drop * 1.3
        scenarios["optimistic"] = (
            front_iv_before * (1 - optimistic_front_drop),
            back_iv_before * (1 - optimistic_back_drop)
        )
        
        return scenarios
    
    def _simulate_single_scenario(self, trade: CalendarTrade, price_change_pct: float,
                                new_price: float, iv_scenario: str, 
                                front_iv_after: float, back_iv_after: float) -> PnLScenario:
        """Simulate single P&L scenario."""
        try:
            # Calculate new option values
            front_value_after = self._calculate_option_value(
                new_price, trade.front_option.strike, front_iv_after,
                trade.days_to_expiration_front - self.config["time_decay_days"],
                trade.front_option.option_type
            )
            
            back_value_after = self._calculate_option_value(
                new_price, trade.back_option.strike, back_iv_after,
                trade.days_to_expiration_back - self.config["time_decay_days"],
                trade.back_option.option_type
            )
            
            # Calculate spread value (buy back, sell front)
            spread_value_after = back_value_after - front_value_after
            
            # Calculate P&L
            pnl = spread_value_after - trade.net_debit
            pnl_pct = (pnl / trade.net_debit) * 100 if trade.net_debit > 0 else 0
            
            return PnLScenario(
                price_change_pct=price_change_pct,
                new_underlying_price=new_price,
                iv_crush_scenario=iv_scenario,
                front_iv_after=front_iv_after,
                back_iv_after=back_iv_after,
                front_option_value=front_value_after,
                back_option_value=back_value_after,
                spread_value=spread_value_after,
                pnl=pnl,
                pnl_pct=pnl_pct
            )
            
        except Exception as e:
            self.logger.error(f"Single scenario simulation failed: {e}")
            return PnLScenario(
                price_change_pct=price_change_pct,
                new_underlying_price=new_price,
                iv_crush_scenario=iv_scenario,
                front_iv_after=front_iv_after,
                back_iv_after=back_iv_after,
                front_option_value=0.0,
                back_option_value=0.0,
                spread_value=0.0,
                pnl=0.0,
                pnl_pct=0.0
            )
    
    def _calculate_option_value(self, spot_price: float, strike: float, 
                              iv: float, days_to_expiry: float, 
                              option_type: str) -> float:
        """Calculate option value using simplified Black-Scholes."""
        try:
            if days_to_expiry <= 0:
                # At expiration, option worth intrinsic value
                if option_type.lower() == "call":
                    return max(0, spot_price - strike)
                else:
                    return max(0, strike - spot_price)
            
            if self.config["use_simplified_pricing"]:
                return self._simplified_black_scholes(
                    spot_price, strike, iv, days_to_expiry / 365.0, 
                    self.config["risk_free_rate"], option_type
                )
            else:
                # Fallback to intrinsic value approximation
                if option_type.lower() == "call":
                    intrinsic = max(0, spot_price - strike)
                else:
                    intrinsic = max(0, strike - spot_price)
                
                # Add time value approximation
                time_value = iv * spot_price * math.sqrt(days_to_expiry / 365.0) * 0.4
                return intrinsic + time_value
                
        except Exception as e:
            self.logger.error(f"Option valuation failed: {e}")
            return 0.0
    
    def _simplified_black_scholes(self, s: float, k: float, vol: float, 
                                t: float, r: float, option_type: str) -> float:
        """Simplified Black-Scholes implementation."""
        try:
            if t <= 0:
                if option_type.lower() == "call":
                    return max(0, s - k)
                else:
                    return max(0, k - s)
            
            # Black-Scholes formula
            d1 = (math.log(s / k) + (r + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
            d2 = d1 - vol * math.sqrt(t)
            
            # Normal CDF approximation
            nd1 = self._normal_cdf(d1)
            nd2 = self._normal_cdf(d2)
            
            if option_type.lower() == "call":
                return s * nd1 - k * math.exp(-r * t) * nd2
            else:
                return k * math.exp(-r * t) * self._normal_cdf(-d2) - s * self._normal_cdf(-d1)
                
        except Exception as e:
            self.logger.error(f"Black-Scholes calculation failed: {e}")
            return 0.0
    
    def _normal_cdf(self, x: float) -> float:
        """Approximation of normal cumulative distribution function."""
        try:
            # Abramowitz and Stegun approximation
            sign = 1 if x >= 0 else -1
            x = abs(x)
            
            # Constants
            a1 =  0.254829592
            a2 = -0.284496736
            a3 =  1.421413741
            a4 = -1.453152027
            a5 =  1.061405429
            p  =  0.3275911
            
            # A&S formula 7.1.26
            t = 1.0 / (1.0 + p * x)
            y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
            
            return 0.5 * (1.0 + sign * y)
            
        except Exception:
            return 0.5  # Fallback to 50%


class IVCrushModel:
    """
    IV crush modeling utilities.
    
    Provides configurable IV crush parameters based on:
    - Liquidity tiers (volume, open interest)
    - Historical crush patterns
    - Market conditions
    """
    
    def __init__(self):
        self.logger = logging.getLogger("options_trader.iv_crush_model")
        
        # Historical IV crush data (could be loaded from file)
        self.historical_patterns = {
            "tech": {"front_drop": 0.32, "back_drop": 0.12},
            "financial": {"front_drop": 0.28, "back_drop": 0.08},
            "healthcare": {"front_drop": 0.35, "back_drop": 0.15},
            "default": {"front_drop": 0.30, "back_drop": 0.10}
        }
    
    def get_crush_parameters(self, symbol: str, avg_volume: float = 0, 
                           sector: str = "default") -> IVCrushParameters:
        """Get IV crush parameters for specific symbol and conditions."""
        try:
            # Start with liquidity-based parameters
            params = IVCrushParameters.get_by_liquidity(avg_volume)
            
            # Adjust for sector if available
            if sector in self.historical_patterns:
                sector_data = self.historical_patterns[sector]
                params.front_iv_drop = sector_data["front_drop"]
                params.back_iv_drop = sector_data["back_drop"]
            
            self.logger.debug(f"IV crush params for {symbol}: front={params.front_iv_drop:.2f}, back={params.back_iv_drop:.2f}")
            return params
            
        except Exception as e:
            self.logger.error(f"Failed to get crush parameters for {symbol}: {e}")
            return IVCrushParameters()  # Return defaults
    
    def validate_crush_parameters(self, params: IVCrushParameters) -> bool:
        """Validate IV crush parameters are reasonable."""
        try:
            # Front month should drop more than back month
            if params.front_iv_drop <= params.back_iv_drop:
                self.logger.warning("Invalid crush parameters: front drop should be greater than back")
                return False
            
            # Reasonable bounds
            if not (0.1 <= params.front_iv_drop <= 0.8):
                self.logger.warning(f"Front IV drop out of range: {params.front_iv_drop}")
                return False
            
            if not (0.05 <= params.back_iv_drop <= 0.5):
                self.logger.warning(f"Back IV drop out of range: {params.back_iv_drop}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Crush parameter validation failed: {e}")
            return False