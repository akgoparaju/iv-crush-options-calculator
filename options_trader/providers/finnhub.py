#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finnhub Data Provider
=====================

Provides price data, options chains, and earnings calendar from Finnhub API.
Requires FINNHUB_API_KEY in environment variables.

API Documentation: https://finnhub.io/docs/api
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import pandas as pd

from .base import PriceProvider, OptionsProvider, EarningsProvider, EarningsEvent

logger = logging.getLogger("options_trader.providers.finnhub")


class FinnhubProvider(PriceProvider, OptionsProvider, EarningsProvider):
    """Finnhub data provider for prices, options, and earnings."""
    
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Finnhub provider.
        
        Args:
            api_key: Finnhub API key. If None, reads from FINNHUB_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            logger.warning("Finnhub API key not found in environment")
        
        logger.debug("Finnhub provider initialized")
    
    def _is_enabled(self) -> bool:
        """Check if provider is properly configured."""
        return bool(self.api_key)
    
    def _make_request(self, endpoint: str, **params) -> dict:
        """Make API request with error handling."""
        if not self._is_enabled():
            raise RuntimeError("Finnhub API key not configured")
        
        params['token'] = self.api_key
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise RuntimeError(f"Finnhub request failed: {e}")
    
    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        """
        Get current price using quote endpoint.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (price, source_description)
        """
        if not self._is_enabled():
            return None, "finnhub.disabled"
        
        try:
            data = self._make_request("/quote", symbol=symbol)
            price = data.get("c")  # current price
            
            if price is not None:
                logger.debug(f"Finnhub price for {symbol}: ${price:.2f}")
                return float(price), "finnhub.quote"
            
            logger.warning(f"No current price in Finnhub response for {symbol}")
            return None, "finnhub.no_price"
            
        except Exception as e:
            logger.warning(f"Finnhub price lookup failed for {symbol}: {e}")
            return None, "finnhub.error"
    
    def get_expirations(self, symbol: str, max_count: int = 3) -> List[str]:
        """
        Get available option expiration dates.
        
        Args:
            symbol: Stock symbol
            max_count: Maximum number of expirations to return
            
        Returns:
            List of expiration dates in 'YYYY-MM-DD' format
        """
        if not self._is_enabled():
            return []
        
        try:
            data = self._make_request("/stock/options", symbol=symbol)
            expirations = data.get("data", {}).get("expirationDates") or data.get("expirationDates") or []
            
            # Filter and sort valid expiration dates
            valid_exps = [exp for exp in expirations if isinstance(exp, str)]
            valid_exps.sort()
            result = valid_exps[:max_count]
            
            logger.debug(f"Finnhub expirations for {symbol}: {result}")
            return result
            
        except Exception as e:
            logger.warning(f"Finnhub get_expirations failed for {symbol}: {e}")
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
        if not self._is_enabled():
            raise RuntimeError("Finnhub API key not configured")
        
        try:
            data = self._make_request("/stock/options", symbol=symbol, date=expiration)
            contracts = data.get("data", [])
            
            if not contracts:
                raise RuntimeError("Empty option chain from Finnhub")
            
            # Separate calls and puts
            calls = []
            puts = []
            
            for contract in contracts:
                row = {
                    "strike": contract.get("strike"),
                    "bid": contract.get("bid"),
                    "ask": contract.get("ask"),
                    "lastPrice": contract.get("lastPrice"),
                    "impliedVolatility": contract.get("impliedVolatility"),
                }
                
                if contract.get("type") == "call":
                    calls.append(row)
                elif contract.get("type") == "put":
                    puts.append(row)
            
            # Create yfinance-like object
            class OptionChain:
                pass
            
            chain = OptionChain()
            chain.calls = pd.DataFrame(calls)
            chain.puts = pd.DataFrame(puts)
            
            logger.debug(f"Finnhub chain for {symbol} {expiration}: {len(calls)} calls, {len(puts)} puts")
            return chain
            
        except Exception as e:
            logger.warning(f"Finnhub get_chain failed for {symbol} {expiration}: {e}")
            raise
    
    def get_next_earnings(self, symbol: str) -> Optional[EarningsEvent]:
        """
        Get next earnings announcement using earnings calendar endpoint.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            EarningsEvent if found, None otherwise
        """
        if not self._is_enabled():
            return None
        
        try:
            # Get earnings calendar for next 30 days
            today = datetime.now().date()
            end_date = today + timedelta(days=30)
            
            data = self._make_request(
                "/calendar/earnings",
                from_=today.strftime("%Y-%m-%d"),
                to=end_date.strftime("%Y-%m-%d")
            )
            
            earnings_calendar = data.get("earningsCalendar", [])
            
            # Find earnings for this symbol
            for earning in earnings_calendar:
                if earning.get("symbol", "").upper() == symbol.upper():
                    date_str = earning.get("date")
                    if not date_str:
                        continue
                    
                    try:
                        earnings_date = datetime.strptime(date_str, "%Y-%m-%d")
                        
                        # Finnhub provides hour information
                        hour = earning.get("hour", "")
                        timing = "BMO" if "bmo" in hour.lower() or "before" in hour.lower() else "AMC"
                        
                        event = EarningsEvent(
                            symbol=symbol.upper(),
                            date=earnings_date,
                            timing=timing,
                            confirmed=True,  # Finnhub data is generally reliable
                            source="finnhub.earnings_calendar"
                        )
                        
                        logger.info(f"Found next earnings for {symbol}: {earnings_date.date()} {timing}")
                        return event
                        
                    except ValueError as e:
                        logger.warning(f"Invalid date format in Finnhub earnings data: {date_str}")
                        continue
            
            logger.debug(f"No upcoming earnings found for {symbol} in Finnhub calendar")
            return None
            
        except Exception as e:
            logger.warning(f"Finnhub earnings lookup failed for {symbol}: {e}")
            return None
    
    def get_earnings_calendar(self, symbol: str, days_ahead: int = 30) -> List[EarningsEvent]:
        """
        Get earnings calendar for multiple periods.
        
        Args:
            symbol: Stock symbol
            days_ahead: Number of days to look ahead
            
        Returns:
            List of EarningsEvent objects
        """
        # For now, just return the next earnings if available
        next_earnings = self.get_next_earnings(symbol)
        if next_earnings:
            return [next_earnings]
        
        return []