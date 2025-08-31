#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Greeks Calculator - Module 2
============================

Options Greeks calculations and sensitivity analysis for calendar spreads.
Provides delta, gamma, theta, vega calculations with risk assessment capabilities.

Core Components:
- Greeks: Individual option Greeks dataclass
- CalendarGreeks: Calendar spread Greeks aggregation
- GreeksCalculator: Main calculation engine
- SensitivityAnalyzer: Risk sensitivity analysis

Integrates with trade construction and P&L engines for comprehensive risk analysis.
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Union

# Conditional imports for optional dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

from .trade_construction import CalendarTrade, OptionQuote

logger = logging.getLogger("options_trader.greeks")


@dataclass
class Greeks:
    """Individual option Greeks."""
    delta: float = 0.0      # Price sensitivity
    gamma: float = 0.0      # Delta sensitivity  
    theta: float = 0.0      # Time decay (per day)
    vega: float = 0.0       # IV sensitivity (per 1% IV change)
    rho: float = 0.0        # Interest rate sensitivity
    
    # Additional risk metrics
    delta_dollars: float = 0.0    # Delta in dollar terms
    theta_dollars: float = 0.0    # Theta in dollar terms per day
    vega_dollars: float = 0.0     # Vega in dollar terms per 1% IV
    
    
@dataclass
class CalendarGreeks:
    """Calendar spread Greeks aggregation."""
    net_delta: float = 0.0
    net_gamma: float = 0.0  
    net_theta: float = 0.0
    net_vega: float = 0.0
    net_rho: float = 0.0
    
    # Component Greeks
    front_greeks: Optional[Greeks] = None
    back_greeks: Optional[Greeks] = None
    
    # Risk metrics
    delta_dollars: float = 0.0
    theta_dollars: float = 0.0
    vega_dollars: float = 0.0
    
    # Calendar-specific metrics
    vega_ratio: float = 0.0       # Front vega / Back vega
    theta_ratio: float = 0.0      # Front theta / Back theta
    gamma_risk: float = 0.0       # Net gamma exposure
    
    @property
    def is_long_vega(self) -> bool:
        """True if calendar is net long vega (benefits from IV increase)."""
        return self.net_vega > 0
    
    @property
    def is_short_gamma(self) -> bool:
        """True if calendar is net short gamma (hurt by large moves)."""
        return self.net_gamma < 0
    
    @property
    def daily_theta_pnl(self) -> float:
        """Expected daily P&L from theta decay."""
        return self.theta_dollars


class GreeksCalculator:
    """
    Main Greeks calculation engine.
    
    Provides comprehensive Greeks calculations for individual options and 
    calendar spreads using Black-Scholes model with fallback approximations.
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        """Initialize with risk-free rate."""
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger("options_trader.greeks_calculator")
        
        # Configuration
        self.config = {
            "use_black_scholes": True,
            "fallback_approximations": True,
            "iv_shift_for_vega": 0.01,      # 1% IV shift for vega calculation
            "price_shift_for_delta": 0.01,  # 1% price shift for delta calculation
            "time_shift_for_theta": 1/365,  # 1 day for theta calculation
        }
    
    def calculate_option_greeks(self, option_quote: OptionQuote, 
                              underlying_price: float,
                              days_to_expiry: float) -> Greeks:
        """
        Calculate Greeks for individual option.
        
        Args:
            option_quote: Option quote data
            underlying_price: Current underlying price
            days_to_expiry: Days to expiration
            
        Returns:
            Greeks object with all sensitivities
        """
        try:
            if days_to_expiry <= 0:
                # At expiration, most Greeks are zero
                return self._expiration_greeks(option_quote, underlying_price)
            
            if self.config["use_black_scholes"] and option_quote.implied_volatility > 0:
                return self._calculate_bs_greeks(
                    underlying_price,
                    option_quote.strike,
                    option_quote.implied_volatility,
                    days_to_expiry / 365.0,
                    self.risk_free_rate,
                    option_quote.option_type
                )
            elif self.config["fallback_approximations"]:
                return self._calculate_approximate_greeks(option_quote, underlying_price, days_to_expiry)
            else:
                self.logger.warning(f"Cannot calculate Greeks for {option_quote.symbol}")
                return Greeks()
                
        except Exception as e:
            self.logger.error(f"Greeks calculation failed for {option_quote.symbol}: {e}")
            return Greeks()
    
    def calculate_calendar_greeks(self, trade: CalendarTrade) -> CalendarGreeks:
        """
        Calculate Greeks for calendar spread.
        
        Args:
            trade: CalendarTrade object
            
        Returns:
            CalendarGreeks with net exposures and risk metrics
        """
        try:
            # Calculate Greeks for each leg
            front_greeks = self.calculate_option_greeks(
                trade.front_option, trade.underlying_price, trade.days_to_expiration_front
            )
            
            back_greeks = self.calculate_option_greeks(
                trade.back_option, trade.underlying_price, trade.days_to_expiration_back
            )
            
            # Calendar spread: Short front, Long back
            # Net Greeks = Back Greeks - Front Greeks (since we're short front)
            net_delta = back_greeks.delta - front_greeks.delta
            net_gamma = back_greeks.gamma - front_greeks.gamma
            net_theta = back_greeks.theta - front_greeks.theta
            net_vega = back_greeks.vega - front_greeks.vega
            net_rho = back_greeks.rho - front_greeks.rho
            
            # Calculate dollar exposures (per contract)
            delta_dollars = net_delta * trade.underlying_price
            theta_dollars = net_theta
            vega_dollars = net_vega
            
            # Calendar-specific metrics
            vega_ratio = (front_greeks.vega / back_greeks.vega) if back_greeks.vega != 0 else 0
            theta_ratio = (front_greeks.theta / back_greeks.theta) if back_greeks.theta != 0 else 0
            gamma_risk = abs(net_gamma) * trade.underlying_price * trade.underlying_price
            
            calendar_greeks = CalendarGreeks(
                net_delta=net_delta,
                net_gamma=net_gamma,
                net_theta=net_theta,
                net_vega=net_vega,
                net_rho=net_rho,
                front_greeks=front_greeks,
                back_greeks=back_greeks,
                delta_dollars=delta_dollars,
                theta_dollars=theta_dollars,
                vega_dollars=vega_dollars,
                vega_ratio=vega_ratio,
                theta_ratio=theta_ratio,
                gamma_risk=gamma_risk
            )
            
            self.logger.debug(f"Calendar Greeks for {trade.symbol}: delta={net_delta:.3f}, vega={net_vega:.3f}, theta={net_theta:.3f}")
            return calendar_greeks
            
        except Exception as e:
            self.logger.error(f"Calendar Greeks calculation failed for {trade.symbol}: {e}")
            return CalendarGreeks()
    
    def estimate_theta_decay(self, trade: CalendarTrade, days: int = 1) -> float:
        """
        Estimate theta decay for calendar spread.
        
        Args:
            trade: CalendarTrade object
            days: Number of days for decay calculation
            
        Returns:
            Expected dollar P&L from theta decay
        """
        try:
            calendar_greeks = self.calculate_calendar_greeks(trade)
            return calendar_greeks.theta_dollars * days
            
        except Exception as e:
            self.logger.error(f"Theta decay estimation failed for {trade.symbol}: {e}")
            return 0.0
    
    def estimate_vega_sensitivity(self, trade: CalendarTrade, iv_change_pct: float) -> float:
        """
        Estimate P&L from IV change.
        
        Args:
            trade: CalendarTrade object  
            iv_change_pct: IV change in percentage points (e.g., 5.0 for +5%)
            
        Returns:
            Expected dollar P&L from IV change
        """
        try:
            calendar_greeks = self.calculate_calendar_greeks(trade)
            return calendar_greeks.vega_dollars * iv_change_pct
            
        except Exception as e:
            self.logger.error(f"Vega sensitivity estimation failed for {trade.symbol}: {e}")
            return 0.0
    
    def _calculate_bs_greeks(self, s: float, k: float, vol: float, 
                           t: float, r: float, option_type: str) -> Greeks:
        """Calculate Greeks using Black-Scholes formulas."""
        try:
            if t <= 0:
                return self._expiration_greeks_bs(s, k, option_type)
            
            # Black-Scholes d1 and d2
            d1 = (math.log(s / k) + (r + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
            d2 = d1 - vol * math.sqrt(t)
            
            # Normal PDF and CDF
            nd1 = self._normal_cdf(d1)
            nd2 = self._normal_cdf(d2)
            npdf_d1 = self._normal_pdf(d1)
            
            if option_type.lower() == "call":
                # Call Greeks
                delta = nd1
                gamma = npdf_d1 / (s * vol * math.sqrt(t))
                theta = (-s * npdf_d1 * vol / (2 * math.sqrt(t)) - 
                        r * k * math.exp(-r * t) * nd2) / 365  # Per day
                vega = s * npdf_d1 * math.sqrt(t) / 100  # Per 1% IV change
                rho = k * t * math.exp(-r * t) * nd2 / 100
            else:
                # Put Greeks
                delta = nd1 - 1
                gamma = npdf_d1 / (s * vol * math.sqrt(t))
                theta = (-s * npdf_d1 * vol / (2 * math.sqrt(t)) + 
                        r * k * math.exp(-r * t) * self._normal_cdf(-d2)) / 365  # Per day
                vega = s * npdf_d1 * math.sqrt(t) / 100  # Per 1% IV change
                rho = -k * t * math.exp(-r * t) * self._normal_cdf(-d2) / 100
            
            # Dollar exposures
            delta_dollars = delta * s
            theta_dollars = theta
            vega_dollars = vega
            
            return Greeks(
                delta=delta,
                gamma=gamma,
                theta=theta,
                vega=vega,
                rho=rho,
                delta_dollars=delta_dollars,
                theta_dollars=theta_dollars,
                vega_dollars=vega_dollars
            )
            
        except Exception as e:
            self.logger.error(f"Black-Scholes Greeks calculation failed: {e}")
            return Greeks()
    
    def _calculate_approximate_greeks(self, option_quote: OptionQuote, 
                                    underlying_price: float, days_to_expiry: float) -> Greeks:
        """Calculate approximate Greeks using finite differences."""
        try:
            current_value = option_quote.mid_price
            
            # Approximate delta (1% price move)
            price_shift = underlying_price * self.config["price_shift_for_delta"]
            # Would need to recalculate option value at new price - simplified here
            delta = 0.5 if abs(option_quote.strike - underlying_price) < underlying_price * 0.1 else 0.2
            
            # Approximate theta (time decay)
            theta = -current_value * 0.02 if days_to_expiry > 30 else -current_value * 0.05  # Per day
            
            # Approximate vega (IV sensitivity)
            vega = current_value * 0.1  # Rough approximation
            
            # Approximate gamma (delta sensitivity)
            gamma = 0.01
            
            return Greeks(
                delta=delta,
                gamma=gamma,
                theta=theta,
                vega=vega,
                rho=0.0,  # Simplified
                delta_dollars=delta * underlying_price,
                theta_dollars=theta,
                vega_dollars=vega
            )
            
        except Exception as e:
            self.logger.error(f"Approximate Greeks calculation failed: {e}")
            return Greeks()
    
    def _expiration_greeks(self, option_quote: OptionQuote, underlying_price: float) -> Greeks:
        """Calculate Greeks at expiration."""
        try:
            strike = option_quote.strike
            
            if option_quote.option_type.lower() == "call":
                # Call at expiration
                if underlying_price > strike:
                    delta = 1.0  # Deep ITM
                elif abs(underlying_price - strike) < 0.01:
                    delta = 0.5  # ATM
                else:
                    delta = 0.0  # OTM
            else:
                # Put at expiration
                if underlying_price < strike:
                    delta = -1.0  # Deep ITM
                elif abs(underlying_price - strike) < 0.01:
                    delta = -0.5  # ATM
                else:
                    delta = 0.0  # OTM
            
            return Greeks(
                delta=delta,
                gamma=0.0,  # No gamma at expiration
                theta=0.0,  # No time value
                vega=0.0,   # No vega at expiration
                rho=0.0,
                delta_dollars=delta * underlying_price,
                theta_dollars=0.0,
                vega_dollars=0.0
            )
            
        except Exception as e:
            self.logger.error(f"Expiration Greeks calculation failed: {e}")
            return Greeks()
    
    def _expiration_greeks_bs(self, s: float, k: float, option_type: str) -> Greeks:
        """Black-Scholes Greeks at expiration."""
        if option_type.lower() == "call":
            delta = 1.0 if s > k else (0.5 if abs(s - k) < 0.01 else 0.0)
        else:
            delta = -1.0 if s < k else (-0.5 if abs(s - k) < 0.01 else 0.0)
            
        return Greeks(
            delta=delta,
            gamma=0.0,
            theta=0.0,
            vega=0.0,
            rho=0.0,
            delta_dollars=delta * s,
            theta_dollars=0.0,
            vega_dollars=0.0
        )
    
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
            return 0.5
    
    def _normal_pdf(self, x: float) -> float:
        """Normal probability density function."""
        try:
            return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
        except Exception:
            return 0.0


class SensitivityAnalyzer:
    """
    Advanced sensitivity analysis for calendar spreads.
    
    Provides comprehensive risk assessment including:
    - Price sensitivity bands
    - IV sensitivity analysis  
    - Time decay projections
    - Greeks evolution over time
    """
    
    def __init__(self):
        self.logger = logging.getLogger("options_trader.sensitivity_analyzer")
        self.greeks_calc = GreeksCalculator()
    
    def analyze_price_sensitivity(self, trade: CalendarTrade, 
                                price_range_pct: float = 10.0) -> Dict[str, Any]:
        """
        Analyze calendar spread sensitivity to price changes.
        
        Args:
            trade: CalendarTrade object
            price_range_pct: Price range to analyze (±%)
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        try:
            current_greeks = self.greeks_calc.calculate_calendar_greeks(trade)
            
            # Price sensitivity bands
            price_moves = [-price_range_pct, -price_range_pct/2, 0, price_range_pct/2, price_range_pct]
            sensitivity_data = []
            
            for price_move in price_moves:
                new_price = trade.underlying_price * (1 + price_move / 100)
                
                # Estimate P&L from delta (first-order approximation)
                price_pnl = current_greeks.net_delta * (new_price - trade.underlying_price) * 100
                
                sensitivity_data.append({
                    "price_move_pct": price_move,
                    "new_price": new_price,
                    "estimated_pnl": price_pnl,
                    "delta_contribution": price_pnl
                })
            
            return {
                "current_greeks": current_greeks,
                "price_sensitivity": sensitivity_data,
                "max_gamma_risk": current_greeks.gamma_risk,
                "delta_neutral_price": trade.underlying_price - (current_greeks.net_delta * trade.underlying_price / 100)
            }
            
        except Exception as e:
            self.logger.error(f"Price sensitivity analysis failed for {trade.symbol}: {e}")
            return {}
    
    def analyze_iv_sensitivity(self, trade: CalendarTrade,
                             iv_range_pct: float = 20.0) -> Dict[str, Any]:
        """
        Analyze calendar spread sensitivity to IV changes.
        
        Args:
            trade: CalendarTrade object
            iv_range_pct: IV range to analyze (±%)
            
        Returns:
            Dictionary with IV sensitivity analysis
        """
        try:
            current_greeks = self.greeks_calc.calculate_calendar_greeks(trade)
            
            # IV sensitivity analysis
            iv_moves = [-iv_range_pct, -iv_range_pct/2, 0, iv_range_pct/2, iv_range_pct]
            iv_sensitivity_data = []
            
            for iv_move in iv_moves:
                # Estimate P&L from vega
                iv_pnl = current_greeks.net_vega * iv_move
                
                iv_sensitivity_data.append({
                    "iv_move_pct": iv_move,
                    "front_iv_after": trade.front_option.implied_volatility * (1 + iv_move / 100),
                    "back_iv_after": trade.back_option.implied_volatility * (1 + iv_move / 100),
                    "estimated_pnl": iv_pnl,
                    "vega_contribution": iv_pnl
                })
            
            return {
                "current_greeks": current_greeks,
                "iv_sensitivity": iv_sensitivity_data,
                "vega_ratio": current_greeks.vega_ratio,
                "net_vega_exposure": current_greeks.vega_dollars,
                "is_long_vega": current_greeks.is_long_vega
            }
            
        except Exception as e:
            self.logger.error(f"IV sensitivity analysis failed for {trade.symbol}: {e}")
            return {}
    
    def analyze_time_decay(self, trade: CalendarTrade, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Analyze time decay evolution over specified period.
        
        Args:
            trade: CalendarTrade object
            days_ahead: Number of days to project
            
        Returns:
            Dictionary with time decay analysis
        """
        try:
            current_greeks = self.greeks_calc.calculate_calendar_greeks(trade)
            
            decay_projection = []
            cumulative_theta_pnl = 0.0
            
            for day in range(1, days_ahead + 1):
                # Simple linear theta decay approximation
                daily_theta_pnl = current_greeks.theta_dollars
                cumulative_theta_pnl += daily_theta_pnl
                
                # Estimate how theta changes as expiration approaches
                theta_acceleration = 1.0 + (day / days_ahead) * 0.5  # Theta accelerates near expiration
                
                decay_projection.append({
                    "day": day,
                    "daily_theta_pnl": daily_theta_pnl * theta_acceleration,
                    "cumulative_theta_pnl": cumulative_theta_pnl,
                    "front_dte_remaining": trade.days_to_expiration_front - day,
                    "back_dte_remaining": trade.days_to_expiration_back - day
                })
            
            return {
                "current_greeks": current_greeks,
                "decay_projection": decay_projection,
                "total_theta_pnl": cumulative_theta_pnl,
                "theta_ratio": current_greeks.theta_ratio,
                "daily_theta_dollars": current_greeks.theta_dollars
            }
            
        except Exception as e:
            self.logger.error(f"Time decay analysis failed for {trade.symbol}: {e}")
            return {}
    
    def calculate_risk_metrics(self, trade: CalendarTrade) -> Dict[str, float]:
        """Calculate comprehensive risk metrics for calendar spread."""
        try:
            current_greeks = self.greeks_calc.calculate_calendar_greeks(trade)
            
            # Risk metrics calculation
            max_loss = trade.max_loss  # Maximum loss is the debit paid
            
            # Estimate maximum profit (approximate)
            # Calendar spreads typically profit most at the strike at expiration
            est_max_profit = trade.net_debit * 2.0  # Rough approximation
            
            # Risk/reward ratio
            risk_reward = est_max_profit / max_loss if max_loss > 0 else 0
            
            # Gamma risk (dollar risk from 1% underlying move)
            gamma_risk_1pct = current_greeks.gamma_risk * 0.01
            
            # Vega risk (dollar risk from 5% IV drop)
            vega_risk_5pct = abs(current_greeks.vega_dollars) * 5
            
            # Time decay benefit (7-day theta)
            theta_benefit_7d = current_greeks.theta_dollars * 7
            
            return {
                "max_loss": max_loss,
                "estimated_max_profit": est_max_profit,
                "risk_reward_ratio": risk_reward,
                "gamma_risk_1pct": gamma_risk_1pct,
                "vega_risk_5pct": vega_risk_5pct,
                "theta_benefit_7d": theta_benefit_7d,
                "net_delta_risk": abs(current_greeks.delta_dollars),
                "breakeven_width": abs(trade.breakeven_range[1] - trade.breakeven_range[0]),
                "capital_efficiency": est_max_profit / max_loss if max_loss > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Risk metrics calculation failed for {trade.symbol}: {e}")
            return {}