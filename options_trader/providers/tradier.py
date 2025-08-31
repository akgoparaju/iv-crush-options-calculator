#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tradier Data Provider
====================

Provides options chains and earnings data from Tradier API.
Requires TRADIER_TOKEN in environment variables.

API Documentation: https://documentation.tradier.com/
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import pandas as pd

from .base import OptionsProvider, EarningsProvider, EarningsEvent

logger = logging.getLogger("options_trader.providers.tradier")


class TradierProvider(OptionsProvider, EarningsProvider):
    """Tradier provider for options and earnings data."""
    
    def __init__(self, token: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize Tradier provider.
        
        Args:
            token: Tradier API token. If None, reads from TRADIER_TOKEN env var.
            base_url: Tradier API base URL. If None, reads from TRADIER_BASE env var.
        """
        self.token = token or os.getenv("TRADIER_TOKEN")
        self.base_url = (base_url or os.getenv("TRADIER_BASE", "https://sandbox.tradier.com")).rstrip("/")
        
        if not self.token:
            logger.warning("Tradier token not found in environment")
        
        logger.debug(f"Tradier provider initialized with base URL: {self.base_url}")
    
    def _is_enabled(self) -> bool:
        """Check if provider is properly configured."""
        return bool(self.token)
    
    def _get_headers(self) -> dict:
        """Get headers for Tradier API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
    
    def _make_request(self, endpoint: str, **params) -> dict:
        """Make API request with error handling."""
        if not self._is_enabled():
            raise RuntimeError("Tradier token not configured")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise RuntimeError(f"Tradier request failed: {e}")
    
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
            data = self._make_request(
                "/v1/markets/options/expirations",
                symbol=symbol,
                includeAllRoots="true"
            )
            
            expirations = data.get("expirations", {}).get("date", [])
            
            # Handle single expiration (returned as dict instead of list)
            if isinstance(expirations, dict):
                expirations = [expirations.get("date")]
            
            # Filter valid dates
            valid_exps = [exp for exp in expirations if isinstance(exp, str)]
            valid_exps.sort()
            result = valid_exps[:max_count]
            
            logger.debug(f"Tradier expirations for {symbol}: {result}")
            return result
            
        except Exception as e:
            logger.warning(f"Tradier get_expirations failed for {symbol}: {e}")
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
            raise RuntimeError("Tradier token not configured")
        
        try:
            data = self._make_request(
                "/v1/markets/options/chains",
                symbol=symbol,
                expiration=expiration
            )
            
            options = data.get("options", {}).get("option", [])
            
            calls = []
            puts = []
            
            for option in options:
                row = {
                    "strike": option.get("strike"),
                    "bid": option.get("bid"),
                    "ask": option.get("ask"),
                    "lastPrice": option.get("last"),
                    "impliedVolatility": option.get("greeks", {}).get("mid_iv"),
                }
                
                if option.get("option_type") == "call":
                    calls.append(row)
                else:
                    puts.append(row)
            
            # Create yfinance-like object
            class OptionChain:
                pass
            
            chain = OptionChain()
            chain.calls = pd.DataFrame(calls)
            chain.puts = pd.DataFrame(puts)
            
            logger.debug(f"Tradier chain for {symbol} {expiration}: {len(calls)} calls, {len(puts)} puts")
            return chain
            
        except Exception as e:
            logger.warning(f"Tradier get_chain failed for {symbol} {expiration}: {e}")
            raise
    
    def get_next_earnings(self, symbol: str) -> Optional[EarningsEvent]:
        """
        Get next earnings announcement using corporate calendar endpoint.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            EarningsEvent if found, None otherwise
        """
        if not self._is_enabled():
            return None
        
        try:
            # Get corporate events for next 30 days
            today = datetime.now().date()
            end_date = today + timedelta(days=30)
            
            data = self._make_request(
                "/v1/markets/calendar",
                month=today.month,
                year=today.year
            )
            
            # Tradier calendar structure may vary - this is a basic implementation
            events = data.get("calendar", {}).get("days", {})
            
            # Look for earnings events
            for day, day_events in events.items():
                if not isinstance(day_events, dict):
                    continue
                
                earnings_events = day_events.get("events", [])
                for event in earnings_events:
                    if (event.get("symbol", "").upper() == symbol.upper() and 
                        "earnings" in event.get("description", "").lower()):
                        
                        try:
                            event_date = datetime.strptime(day, "%Y-%m-%d")
                            
                            # Tradier may not provide BMO/AMC timing
                            timing = "AMC"  # Default assumption
                            
                            earnings_event = EarningsEvent(
                                symbol=symbol.upper(),
                                date=event_date,
                                timing=timing,
                                confirmed=False,  # Tradier timing not always confirmed
                                source="tradier.corporate_calendar"
                            )
                            
                            logger.info(f"Found next earnings for {symbol}: {event_date.date()}")
                            return earnings_event
                            
                        except ValueError as e:
                            logger.warning(f"Invalid date format in Tradier calendar: {day}")
                            continue
            
            logger.debug(f"No upcoming earnings found for {symbol} in Tradier calendar")
            return None
            
        except Exception as e:
            logger.warning(f"Tradier earnings lookup failed for {symbol}: {e}")
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