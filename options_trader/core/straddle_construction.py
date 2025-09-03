#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATM Straddle Construction - Stage 2
===================================

ATM Straddle construction for higher return/risk approach.
Implements the second trade structure from the original strategy:
- Short ATM Call + Short ATM Put
- Higher potential returns with unlimited risk
- Suitable for aggressive risk tolerance

This complements the existing calendar spread structure.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

# Conditional imports for numerical operations
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

# Import the unified OptionQuote from trade_construction
from .trade_construction import OptionQuote

logger = logging.getLogger("options_trader.straddle_construction")


@dataclass
class StraddleTrade:
    """ATM Straddle trade representation"""
    symbol: str
    strike: float
    expiration: str
    
    # Trade components
    call_option: OptionQuote
    put_option: OptionQuote
    
    # Trade metrics
    net_credit: float              # Premium received
    max_profit: float              # Net credit (if stock at strike)
    breakeven_upper: float         # Strike + net credit
    breakeven_lower: float         # Strike - net credit
    max_risk: str = "UNLIMITED"    # Unlimited risk characteristic
    
    # Greeks (net position)
    net_delta: float = 0.0
    net_gamma: float = 0.0
    net_theta: float = 0.0
    net_vega: float = 0.0
    
    # Risk metrics
    probability_of_profit: float = 0.0
    expected_move_coverage: float = 0.0  # How much of expected move is covered
    
    # Quality assessment
    bid_ask_spread_pct: float = 0.0  # Average bid/ask spread as % of mid
    liquidity_score: float = 0.0     # Combined volume and OI score
    breakeven_range_pct: float = 0.0 # Breakeven range as % of current price
    
    def __post_init__(self):
        """Calculate derived metrics"""
        # Note: Greeks calculation requires underlying_price parameter
        # Will be called separately by the construction method
        self._calculate_quality_metrics()
    
    def _calculate_greeks(self, underlying_price: float = None):
        """Calculate net Greeks for the straddle position using GreeksCalculator"""
        try:
            from .greeks import GreeksCalculator
            from datetime import datetime, timedelta
            
            # Skip Greeks calculation if no underlying price provided
            if underlying_price is None:
                logger.warning("Greeks calculation skipped: no underlying price provided")
                return
            
            logger.info(f"Calculating straddle Greeks: price=${underlying_price:.2f}, call_iv={self.call_option.implied_volatility:.4f}, put_iv={self.put_option.implied_volatility:.4f}")
            
            calculator = GreeksCalculator()
            
            # Calculate days to expiration
            try:
                exp_date = datetime.strptime(self.expiration, "%Y-%m-%d")
                days_to_expiry = (exp_date - datetime.now()).days
                days_to_expiry = max(days_to_expiry, 0.1)  # Minimum of 0.1 days
            except:
                days_to_expiry = 1  # Default fallback
            
            logger.info(f"Days to expiry: {days_to_expiry}")
            
            # Calculate Greeks for call option
            call_greeks = calculator.calculate_option_greeks(
                self.call_option, 
                underlying_price, 
                days_to_expiry
            )
            
            # Calculate Greeks for put option  
            put_greeks = calculator.calculate_option_greeks(
                self.put_option,
                underlying_price,
                days_to_expiry
            )
            
            logger.info(f"Call Greeks: δ={call_greeks.delta:.4f}, γ={call_greeks.gamma:.4f}, θ={call_greeks.theta:.4f}, ν={call_greeks.vega:.4f}")
            logger.info(f"Put Greeks: δ={put_greeks.delta:.4f}, γ={put_greeks.gamma:.4f}, θ={put_greeks.theta:.4f}, ν={put_greeks.vega:.4f}")
            
            # Short straddle: negative call delta + negative put delta
            self.net_delta = -(call_greeks.delta + put_greeks.delta)
            self.net_gamma = -(call_greeks.gamma + put_greeks.gamma)
            self.net_theta = -(call_greeks.theta + put_greeks.theta)  # Positive for short position
            self.net_vega = -(call_greeks.vega + put_greeks.vega)
            
            logger.info(f"Straddle Net Greeks: δ={self.net_delta:.4f}, γ={self.net_gamma:.4f}, θ={self.net_theta:.4f}, ν={self.net_vega:.4f}")
            
        except Exception as e:
            logger.warning(f"Greeks calculation failed: {e}. Using zero Greeks.")
            # Fallback to zeros if calculation fails
            self.net_delta = 0.0
            self.net_gamma = 0.0
            self.net_theta = 0.0
            self.net_vega = 0.0
    
    def _calculate_quality_metrics(self):
        """Calculate trade quality assessment metrics"""
        # Bid/ask spread analysis
        call_mid = self.call_option.mid_price
        put_mid = self.put_option.mid_price
        
        if call_mid > 0 and put_mid > 0:
            call_spread_pct = (self.call_option.ask - self.call_option.bid) / call_mid if call_mid > 0 else 0
            put_spread_pct = (self.put_option.ask - self.put_option.bid) / put_mid if put_mid > 0 else 0
            self.bid_ask_spread_pct = (call_spread_pct + put_spread_pct) / 2.0
        
        # Liquidity score (0-100)
        total_volume = self.call_option.volume + self.put_option.volume
        total_oi = self.call_option.open_interest + self.put_option.open_interest
        
        # Simple liquidity scoring
        volume_score = min(total_volume / 100, 50)  # Up to 50 points for volume
        oi_score = min(total_oi / 1000, 50)         # Up to 50 points for OI
        self.liquidity_score = volume_score + oi_score


class StraddleConstructor:
    """ATM Straddle construction for higher return/risk approach"""
    
    def __init__(self):
        """Initialize straddle constructor"""
        self.logger = logging.getLogger(f"{__name__}.StraddleConstructor")
        self.logger.info("StraddleConstructor initialized")
    
    def build_atm_straddle(self, symbol: str, expiration: str, 
                          current_price: float, options_chain: Dict) -> Optional[StraddleTrade]:
        """
        Build ATM straddle trade:
        - Sell 1x ATM call
        - Sell 1x ATM put  
        - Same strike (closest to current price)
        - Same expiration (front month containing earnings)
        
        Args:
            symbol: Stock symbol
            expiration: Expiration date string (YYYY-MM-DD)
            current_price: Current stock price
            options_chain: Options chain data
            
        Returns:
            StraddleTrade object or None if construction fails
        """
        try:
            self.logger.debug(f"Building ATM straddle for {symbol} at ${current_price:.2f}")
            
            # Find ATM strike (closest to current price)
            atm_strike = self._find_atm_strike(current_price, options_chain, expiration)
            if not atm_strike:
                self.logger.warning(f"Could not find ATM strike for {symbol}")
                return None
            
            # Get call and put options at ATM strike
            call_option = self._get_option_quote(symbol, atm_strike, expiration, "call", options_chain)
            put_option = self._get_option_quote(symbol, atm_strike, expiration, "put", options_chain)
            
            if not call_option or not put_option:
                self.logger.warning(f"Could not find both call and put options at strike {atm_strike}")
                return None
            
            # Calculate straddle metrics
            net_credit = call_option.mid_price + put_option.mid_price
            max_profit = net_credit  # Maximum profit if stock stays at strike
            breakeven_upper = atm_strike + net_credit
            breakeven_lower = atm_strike - net_credit
            
            # Create straddle trade
            straddle = StraddleTrade(
                symbol=symbol,
                strike=atm_strike,
                expiration=expiration,
                call_option=call_option,
                put_option=put_option,
                net_credit=net_credit,
                max_profit=max_profit,
                breakeven_upper=breakeven_upper,
                breakeven_lower=breakeven_lower
            )
            
            # Calculate Greeks using the existing GreeksCalculator
            straddle._calculate_greeks(current_price)
            
            # Calculate probability of profit (basic approximation)
            straddle.probability_of_profit = self._calculate_pop(current_price, straddle)
            
            # Calculate breakeven range percentage
            straddle.breakeven_range_pct = ((breakeven_upper - breakeven_lower) / current_price) * 100
            
            self.logger.info(f"ATM straddle constructed: {symbol} ${atm_strike} straddle for ${net_credit:.2f} credit")
            
            return straddle
            
        except Exception as e:
            self.logger.error(f"Failed to build ATM straddle for {symbol}: {e}")
            return None
    
    def _find_atm_strike(self, current_price: float, options_chain, expiration: str) -> Optional[float]:
        """Find the strike closest to current price"""
        try:
            # Handle yfinance Options object
            if hasattr(options_chain, 'calls'):
                # yfinance Options object - extract strikes from calls DataFrame
                calls_df = options_chain.calls
                if calls_df.empty:
                    self.logger.warning(f"No calls found in options chain")
                    return None
                
                # Extract strikes from the 'strike' column
                if 'strike' in calls_df.columns:
                    strikes = calls_df['strike'].tolist()
                else:
                    self.logger.warning(f"No 'strike' column found in calls DataFrame")
                    return None
                    
            # Handle dictionary structure (legacy format)
            elif isinstance(options_chain, dict):
                # Look for calls in the options chain for this expiration
                if expiration not in options_chain:
                    self.logger.warning(f"Expiration {expiration} not found in options chain")
                    return None
                
                exp_data = options_chain[expiration]
                
                # Get available strikes from calls
                if "calls" not in exp_data:
                    self.logger.warning(f"No calls found for expiration {expiration}")
                    return None
                
                calls = exp_data["calls"]
                strikes = [float(strike) for strike in calls.keys()]
                
            else:
                self.logger.warning(f"Unsupported options chain format: {type(options_chain)}")
                return None
            
            if not strikes:
                return None
            
            # Find closest strike to current price
            closest_strike = min(strikes, key=lambda x: abs(x - current_price))
            
            self.logger.debug(f"ATM strike selected: ${closest_strike} (current: ${current_price:.2f})")
            return closest_strike
            
        except Exception as e:
            self.logger.error(f"Error finding ATM strike: {e}")
            return None
    
    def _get_option_quote(self, symbol: str, strike: float, expiration: str, 
                         option_type: str, options_chain) -> Optional[OptionQuote]:
        """Get option quote for specific strike/expiration/type"""
        try:
            # Handle yfinance Options object
            if hasattr(options_chain, 'calls') and hasattr(options_chain, 'puts'):
                if option_type == "call":
                    df = options_chain.calls
                else:
                    df = options_chain.puts
                
                # Find row with matching strike
                matching_rows = df[df['strike'] == strike]
                if matching_rows.empty:
                    self.logger.warning(f"No {option_type} found for strike ${strike}")
                    return None
                    
                option_row = matching_rows.iloc[0]  # Take first match
                
                # Extract option data from DataFrame row
                quote = OptionQuote(
                    symbol=option_row.get('contractSymbol', f"{symbol}{expiration.replace('-', '')}{option_type[0].upper()}{int(strike)}"),
                    strike=strike,
                    expiration=expiration,
                    option_type=option_type,
                    bid=float(option_row.get("bid", 0)),
                    ask=float(option_row.get("ask", 0)),
                    last_price=float(option_row.get("lastPrice", 0)),
                    volume=int(option_row.get("volume", 0)),
                    open_interest=int(option_row.get("openInterest", 0)),
                    implied_volatility=float(option_row.get("impliedVolatility", 0)),
                    delta=float(option_row.get("delta", 0)),
                    gamma=float(option_row.get("gamma", 0)),
                    theta=float(option_row.get("theta", 0)),
                    vega=float(option_row.get("vega", 0))
                )
                
                return quote
                
            # Handle dictionary structure (legacy format)
            elif isinstance(options_chain, dict):
                exp_data = options_chain[expiration]
                option_data = exp_data[f"{option_type}s"][str(strike)]
                
                # Extract option data
                quote = OptionQuote(
                    symbol=f"{symbol}{expiration.replace('-', '')}{option_type[0].upper()}{strike}",
                    strike=strike,
                    expiration=expiration,
                    option_type=option_type,
                    bid=float(option_data.get("bid", 0)),
                    ask=float(option_data.get("ask", 0)),
                    last_price=float(option_data.get("lastPrice", 0)),
                    volume=int(option_data.get("volume", 0)),
                    open_interest=int(option_data.get("openInterest", 0)),
                    implied_volatility=float(option_data.get("impliedVolatility", 0)),
                    delta=float(option_data.get("delta", 0)),
                    gamma=float(option_data.get("gamma", 0)),
                    theta=float(option_data.get("theta", 0)),
                    vega=float(option_data.get("vega", 0))
                )
                
                return quote
            
            else:
                self.logger.warning(f"Unsupported options chain format for quote extraction: {type(options_chain)}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error getting {option_type} option quote: {e}")
            return None
    
    def _calculate_pop(self, current_price: float, straddle: StraddleTrade) -> float:
        """Calculate probability of profit (simplified)"""
        try:
            # Simple approximation: probability that stock moves outside breakeven range
            # This is a basic calculation - in practice would use more sophisticated models
            
            # Assume normal distribution with IV as standard deviation
            avg_iv = (straddle.call_option.implied_volatility + 
                     straddle.put_option.implied_volatility) / 2.0
            
            if not HAS_NUMPY or avg_iv <= 0:
                return 0.5  # Default estimate
            
            # Calculate days to expiration
            try:
                exp_date = datetime.strptime(straddle.expiration, "%Y-%m-%d")
                days_to_exp = (exp_date - datetime.now()).days
                if days_to_exp <= 0:
                    return 0.0
            except:
                days_to_exp = 30  # Default
            
            # Standard deviation of price movement
            time_factor = (days_to_exp / 365.0) ** 0.5
            std_dev = current_price * avg_iv * time_factor
            
            # Z-scores for breakeven points
            z_upper = (straddle.breakeven_upper - current_price) / std_dev
            z_lower = (straddle.breakeven_lower - current_price) / std_dev
            
            # Probability of being outside breakeven range
            # P(X < lower) + P(X > upper) = P(X < lower) + (1 - P(X < upper))
            from scipy.stats import norm
            prob_profit = norm.cdf(z_lower) + (1 - norm.cdf(z_upper))
            
            return max(0.0, min(1.0, prob_profit))
            
        except Exception as e:
            self.logger.warning(f"Error calculating POP: {e}")
            return 0.5  # Default estimate
    
    def analyze_straddle_risk(self, straddle: StraddleTrade, current_price: float) -> Dict[str, Any]:
        """Analyze risk characteristics of the straddle"""
        risk_analysis = {
            "max_profit": straddle.max_profit,
            "max_risk": "UNLIMITED",
            "breakeven_range": straddle.breakeven_upper - straddle.breakeven_lower,
            "breakeven_range_pct": ((straddle.breakeven_upper - straddle.breakeven_lower) / current_price) * 100,
            "probability_of_profit": straddle.probability_of_profit,
            "profit_at_expiration": {},
            "risk_warnings": []
        }
        
        # Calculate profit/loss at various price levels
        price_levels = [
            current_price * 0.8,   # -20%
            current_price * 0.9,   # -10%
            current_price,         # Current
            current_price * 1.1,   # +10%
            current_price * 1.2    # +20%
        ]
        
        for price in price_levels:
            pnl = self._calculate_straddle_pnl(straddle, price)
            price_label = f"{((price / current_price) - 1) * 100:+.0f}%"
            risk_analysis["profit_at_expiration"][price_label] = pnl
        
        # Risk warnings
        if straddle.breakeven_range_pct > 30:
            risk_analysis["risk_warnings"].append("Wide breakeven range requires large price movement")
        
        if straddle.probability_of_profit < 0.4:
            risk_analysis["risk_warnings"].append("Low probability of profit")
        
        if straddle.liquidity_score < 50:
            risk_analysis["risk_warnings"].append("Low liquidity - wide bid/ask spreads")
        
        return risk_analysis
    
    def _calculate_straddle_pnl(self, straddle: StraddleTrade, stock_price_at_exp: float) -> float:
        """Calculate P&L at expiration for given stock price"""
        # Short call P&L
        call_pnl = straddle.call_option.mid_price  # Credit received
        if stock_price_at_exp > straddle.strike:
            call_pnl -= (stock_price_at_exp - straddle.strike)  # Assignment cost
        
        # Short put P&L
        put_pnl = straddle.put_option.mid_price  # Credit received
        if stock_price_at_exp < straddle.strike:
            put_pnl -= (straddle.strike - stock_price_at_exp)  # Assignment cost
        
        return call_pnl + put_pnl


class TradeStructureSelector:
    """Choose between calendar and straddle based on user preference and risk tolerance"""
    
    def __init__(self):
        """Initialize structure selector"""
        self.logger = logging.getLogger(f"{__name__}.TradeStructureSelector")
        self.logger.info("TradeStructureSelector initialized")
    
    def recommend_structure(self, risk_tolerance: str, account_size: float) -> str:
        """
        Structure recommendation logic:
        - Conservative: Calendar spread (smoother equity curve)
        - Aggressive: ATM straddle (higher potential returns)  
        - Auto: Based on account size and Kelly fractions
        
        Args:
            risk_tolerance: "conservative", "moderate", "aggressive", or "auto"
            account_size: Account size in dollars
            
        Returns:
            Recommended structure: "calendar" or "straddle"
        """
        try:
            risk_tolerance = risk_tolerance.lower().strip()
            
            if risk_tolerance == "conservative":
                self.logger.debug("Conservative risk tolerance -> calendar spread")
                return "calendar"
            
            elif risk_tolerance == "aggressive":
                self.logger.debug("Aggressive risk tolerance -> ATM straddle")
                return "straddle"
            
            elif risk_tolerance == "moderate":
                # For moderate, default to calendar but could be either
                self.logger.debug("Moderate risk tolerance -> calendar spread (default)")
                return "calendar"
            
            elif risk_tolerance == "auto":
                # Auto-select based on account size
                if account_size >= 100000:  # $100K+ accounts can handle straddle risk
                    self.logger.debug("Large account size -> ATM straddle")
                    return "straddle"
                else:
                    self.logger.debug("Smaller account size -> calendar spread")
                    return "calendar"
            
            else:
                self.logger.warning(f"Unknown risk tolerance '{risk_tolerance}', defaulting to calendar")
                return "calendar"
                
        except Exception as e:
            self.logger.error(f"Error in structure recommendation: {e}")
            return "calendar"  # Safe default
    
    def get_structure_comparison(self, calendar_metrics: Dict, straddle_metrics: Dict) -> Dict[str, Any]:
        """Compare calendar vs straddle structure characteristics"""
        comparison = {
            "calendar_spread": {
                "risk_profile": "Limited risk, limited reward",
                "best_outcome": "Stock stays near strike at expiration",
                "risk_characteristics": "Defined max loss",
                "complexity": "Moderate",
                "maintenance": "Low - time decay works in your favor",
                "suitability": "Conservative to moderate risk tolerance"
            },
            "atm_straddle": {
                "risk_profile": "Unlimited risk, limited reward", 
                "best_outcome": "Stock stays exactly at strike",
                "risk_characteristics": "Unlimited loss potential",
                "complexity": "Simple structure",
                "maintenance": "High - requires active monitoring",
                "suitability": "Aggressive risk tolerance, larger accounts"
            },
            "recommendation": self._generate_recommendation(calendar_metrics, straddle_metrics)
        }
        
        return comparison
    
    def _generate_recommendation(self, calendar_metrics: Dict, straddle_metrics: Dict) -> str:
        """Generate recommendation based on trade metrics"""
        try:
            # Simple recommendation logic based on available metrics
            calendar_quality = calendar_metrics.get("quality_score", 0)
            straddle_pop = straddle_metrics.get("probability_of_profit", 0)
            
            if calendar_quality > 75 and straddle_pop < 0.4:
                return "calendar - Higher quality setup with better risk profile"
            elif straddle_pop > 0.6 and calendar_quality < 60:
                return "straddle - High probability setup for aggressive traders"
            else:
                return "calendar - Default recommendation for balanced approach"
                
        except Exception:
            return "calendar - Conservative default recommendation"