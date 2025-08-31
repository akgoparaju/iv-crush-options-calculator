#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yahoo Finance Data Provider
===========================

Provides price data and options chains from Yahoo Finance via yfinance library.
Primary provider with good coverage but subject to rate limiting.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import yfinance as yf
import pandas as pd

from .base import PriceProvider, OptionsProvider

try:
    from yfinance.exceptions import YFRateLimitError
except Exception:
    class YFRateLimitError(Exception):
        pass

logger = logging.getLogger("options_trader.providers.yahoo")


class YahooProvider(PriceProvider, OptionsProvider):
    """Yahoo Finance data provider using yfinance library."""
    
    def __init__(self):
        """Initialize Yahoo provider with ticker cache."""
        self._tickers: Dict[str, yf.Ticker] = {}
        logger.debug("Yahoo provider initialized")
    
    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """Get or create ticker object with caching."""
        if symbol not in self._tickers:
            self._tickers[symbol] = yf.Ticker(symbol)
        return self._tickers[symbol]
    
    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        """
        Get current price from Yahoo Finance.
        
        Tries fast_info first, falls back to intraday history.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (price, source_description)
        """
        ticker = self._get_ticker(symbol)
        
        # Try fast_info first (fastest method)
        try:
            info = ticker.fast_info
            price = getattr(info, "last_price", None)
            if price is None and isinstance(info, dict):
                price = info.get("last_price")
            
            if price is not None:
                logger.debug(f"Yahoo fast_info price for {symbol}: ${price:.2f}")
                return float(price), "yahoo.fast_info"
                
        except Exception as e:
            logger.debug(f"Yahoo fast_info failed for {symbol}: {e}")
        
        # Fallback to intraday history
        try:
            df = ticker.history(period="1d", interval="1m")
            if df is not None and not df.empty:
                price = float(df["Close"].iloc[-1])
                logger.debug(f"Yahoo history price for {symbol}: ${price:.2f}")
                return price, "yahoo.history"
                
        except Exception as e:
            logger.warning(f"Yahoo intraday history failed for {symbol}: {e}")
        
        return None, "yahoo.none"
    
    def get_expirations(self, symbol: str, max_count: int = 3) -> List[str]:
        """
        Get available option expiration dates.
        
        Args:
            symbol: Stock symbol
            max_count: Maximum number of expirations to return
            
        Returns:
            List of expiration dates in 'YYYY-MM-DD' format, sorted by date
        """
        ticker = self._get_ticker(symbol)
        
        try:
            expirations = list(ticker.options or [])
            if not expirations:
                logger.debug(f"No options expirations found for {symbol}")
                return []
            
            # Filter for future dates and sort
            today = datetime.utcnow().date()
            future_exps = [
                exp for exp in expirations 
                if datetime.strptime(exp, "%Y-%m-%d").date() > today
            ]
            
            future_exps.sort(key=lambda d: datetime.strptime(d, "%Y-%m-%d").date())
            result = future_exps[:max_count]
            
            logger.debug(f"Yahoo expirations for {symbol}: {result}")
            return result
            
        except Exception as e:
            logger.warning(f"Yahoo get_expirations failed for {symbol}: {e}")
            return []
    
    def get_chain(self, symbol: str, expiration: str):
        """
        Get option chain for specific expiration.
        
        Args:
            symbol: Stock symbol
            expiration: Expiration date in 'YYYY-MM-DD' format
            
        Returns:
            Object with .calls and .puts DataFrame attributes
            
        Raises:
            Exception if chain cannot be retrieved
        """
        ticker = self._get_ticker(symbol)
        
        try:
            chain = ticker.option_chain(expiration)
            logger.debug(f"Yahoo chain for {symbol} {expiration}: {len(chain.calls)} calls, {len(chain.puts)} puts")
            return chain
            
        except Exception as e:
            logger.warning(f"Yahoo get_chain failed for {symbol} {expiration}: {e}")
            raise