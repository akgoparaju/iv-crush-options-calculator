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
        Generate synthetic option chain.
        
        Args:
            symbol: Stock symbol
            expiration: Expiration date in 'YYYY-MM-DD' format
            
        Returns:
            Object with .calls and .puts DataFrame attributes
        """
        # Use consistent seed for this symbol/expiration combo
        random.seed(hash(symbol + expiration))
        
        price, _ = self.get_price(symbol)
        strikes = [round(price + offset, 2) for offset in (-5, 0, 5)]
        
        def create_option_side(is_call: bool) -> DataFrame:
            """Create synthetic options for calls or puts."""
            rows = []
            for strike in strikes:
                bid = max(0.1, round(random.random() * 2.0, 2))
                ask = bid + round(random.random(), 2)
                last_price = (bid + ask) / 2
                iv = round(0.2 + random.random() * 0.2, 4)  # 20-40% IV range
                
                rows.append({
                    "strike": strike,
                    "bid": bid,
                    "ask": ask,
                    "lastPrice": last_price,
                    "impliedVolatility": iv
                })
            
            return DataFrame(rows)
        
        # Create yfinance-like object
        class OptionChain:
            pass
        
        chain = OptionChain()
        chain.calls = create_option_side(True)
        chain.puts = create_option_side(False)
        
        logger.debug(f"Demo chain for {symbol} {expiration}: {len(strikes)} strikes each side")
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