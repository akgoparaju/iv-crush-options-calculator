#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Data Provider
==================

Provides synthetic demo data for testing and development.
No API keys or network access required.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

# Simple DataFrame replacement for demo purposes
class SimpleDataFrame:
    def __init__(self, data):
        self.data = data
    
    def __len__(self):
        return len(self.data)

try:
    import pandas as pd
    DataFrame = pd.DataFrame
except ImportError:
    DataFrame = SimpleDataFrame

from .base import PriceProvider, OptionsProvider, EarningsProvider, EarningsEvent

logger = logging.getLogger("options_trader.providers.demo")


class DemoProvider(PriceProvider, OptionsProvider, EarningsProvider):
    """Demo provider with synthetic data for testing."""
    
    def __init__(self):
        """Initialize demo provider."""
        logger.debug("Demo provider initialized")
    
    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        """
        Generate synthetic price based on symbol hash.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (price, source_description)
        """
        # Use symbol as seed for consistent prices
        random.seed(hash(symbol))
        price = round(100 + random.random() * 50, 2)
        
        logger.debug(f"Demo price for {symbol}: ${price:.2f}")
        return price, "demo.price"
    
    def get_expirations(self, symbol: str, max_count: int = 3) -> List[str]:
        """
        Generate synthetic expiration dates.
        
        Args:
            symbol: Stock symbol
            max_count: Maximum number of expirations to return
            
        Returns:
            List of expiration dates in 'YYYY-MM-DD' format
        """
        today = datetime.now().date()
        expirations = []
        
        # Generate monthly expirations for next few months
        for i in range(max_count):
            exp_date = today + timedelta(days=30 * (i + 1))
            # Adjust to third Friday of the month (typical options expiration)
            while exp_date.weekday() != 4:  # Friday = 4
                exp_date += timedelta(days=1)
            expirations.append(exp_date.strftime("%Y-%m-%d"))
        
        logger.debug(f"Demo expirations for {symbol}: {expirations}")
        return expirations
    
    def get_chain(self, symbol: str, expiration: str):
        """
        Generate synthetic option chain with realistic pricing relationships.
        
        Args:
            symbol: Stock symbol
            expiration: Expiration date in 'YYYY-MM-DD' format
            
        Returns:
            Object with .calls and .puts DataFrame attributes
        """
        # Use consistent seed for this symbol/expiration combo
        random.seed(hash(symbol + expiration))
        
        price, _ = self.get_price(symbol)
        strikes = [round(price + offset, 2) for offset in (-10, -5, -2.5, 0, 2.5, 5, 10)]
        
        # Calculate days to expiration for time decay
        today = datetime.now().date()
        exp_date = datetime.strptime(expiration, "%Y-%m-%d").date()
        days_to_expiration = max(1, (exp_date - today).days)
        time_factor = days_to_expiration / 365.0  # Years to expiration
        
        # Base implied volatility with term structure
        base_iv = 0.25 + (random.random() * 0.15)  # 25-40% base IV
        # Add volatility smile (higher IV for OTM options)
        # Add term structure (longer expirations have different IV)
        term_adjustment = 0.02 * (time_factor - 0.1)  # Slight term structure
        
        def calculate_intrinsic_value(strike: float, is_call: bool) -> float:
            """Calculate intrinsic value for option."""
            if is_call:
                return max(0, price - strike)
            else:
                return max(0, strike - price)
        
        def calculate_time_value(strike: float, days: int, iv: float) -> float:
            """Calculate approximate time value using simplified Black-Scholes factors."""
            # Simplified time value calculation for demo purposes
            # Real implementation would use full Black-Scholes
            moneyness = abs(strike - price) / price
            time_decay = max(0.01, days / 365.0 * 0.5)  # Time component
            volatility_factor = iv * (time_decay ** 0.5)  # Vol component
            smile_factor = 1 + (moneyness * 0.5)  # Volatility smile
            
            return max(0.05, volatility_factor * smile_factor * price * 0.1)
        
        def create_option_side(is_call: bool) -> DataFrame:
            """Create synthetic options with realistic pricing."""
            rows = []
            for strike in strikes:
                # Calculate moneyness for volatility smile
                moneyness = abs(strike - price) / price
                smile_adjustment = moneyness * 0.05  # 5% IV increase per 100% moneyness
                
                # Apply term structure and volatility smile
                iv = base_iv + term_adjustment + smile_adjustment
                iv = max(0.10, min(0.80, iv))  # Cap IV between 10-80%
                
                # Calculate theoretical option value
                intrinsic = calculate_intrinsic_value(strike, is_call)
                time_value = calculate_time_value(strike, days_to_expiration, iv)
                theoretical_price = intrinsic + time_value
                
                # Add bid-ask spread (tighter for ATM options)
                spread_factor = 1 + moneyness * 2  # Wider spreads for OTM
                bid_ask_spread = max(0.05, theoretical_price * 0.03 * spread_factor)
                
                bid = max(0.01, theoretical_price - bid_ask_spread/2)
                ask = theoretical_price + bid_ask_spread/2
                last_price = round((bid + ask) / 2, 2)
                
                rows.append({
                    "strike": strike,
                    "bid": round(bid, 2),
                    "ask": round(ask, 2),
                    "lastPrice": last_price,
                    "impliedVolatility": round(iv, 4)
                })
            
            return DataFrame(rows)
        
        # Create yfinance-like object
        class OptionChain:
            pass
        
        chain = OptionChain()
        chain.calls = create_option_side(True)
        chain.puts = create_option_side(False)
        
        logger.debug(f"Demo chain for {symbol} {expiration}: {len(strikes)} strikes, "
                    f"{days_to_expiration} days to expiration, base IV {base_iv:.2%}")
        return chain
    
    def get_next_earnings(self, symbol: str) -> Optional[EarningsEvent]:
        """
        Generate synthetic earnings event.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            EarningsEvent with synthetic data
        """
        # Use symbol to generate consistent fake earnings
        random.seed(hash(symbol + "earnings"))
        
        # Generate earnings 1-4 weeks ahead
        days_ahead = random.randint(7, 28)
        earnings_date = datetime.now() + timedelta(days=days_ahead)
        
        # Random BMO/AMC timing
        timing = random.choice(["BMO", "AMC"])
        
        event = EarningsEvent(
            symbol=symbol.upper(),
            date=earnings_date,
            timing=timing,
            confirmed=True,  # Demo data is always "confirmed"
            source="demo.synthetic"
        )
        
        logger.debug(f"Demo earnings for {symbol}: {earnings_date.date()} {timing}")
        return event
    
    def get_earnings_calendar(self, symbol: str, days_ahead: int = 30) -> List[EarningsEvent]:
        """
        Generate synthetic earnings calendar.
        
        Args:
            symbol: Stock symbol
            days_ahead: Number of days to look ahead
            
        Returns:
            List of EarningsEvent objects
        """
        # For demo, just return the next earnings
        next_earnings = self.get_next_earnings(symbol)
        if next_earnings:
            return [next_earnings]
        
        return []