#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha Vantage Data Provider
===========================

Provides price data and earnings calendar from Alpha Vantage API.
Requires ALPHA_VANTAGE_API_KEY in environment variables.

API Documentation: https://www.alphavantage.co/documentation/
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import time

from .base import PriceProvider, EarningsProvider, EarningsEvent

logger = logging.getLogger("options_trader.providers.alpha_vantage")


class AlphaVantageProvider(PriceProvider, EarningsProvider):
    """Alpha Vantage data provider for prices and earnings."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Alpha Vantage provider.
        
        Args:
            api_key: Alpha Vantage API key. If None, reads from ALPHA_VANTAGE_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            logger.warning("Alpha Vantage API key not found in environment")
        
        self._last_request_time = 0
        self._min_interval = 12  # Alpha Vantage free tier: 5 requests per minute
        
        logger.debug("Alpha Vantage provider initialized")
    
    def _is_enabled(self) -> bool:
        """Check if provider is properly configured."""
        return bool(self.api_key)
    
    def _throttle(self):
        """Implement rate limiting for Alpha Vantage free tier."""
        if not self._is_enabled():
            return
            
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            sleep_time = self._min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _make_request(self, **params) -> dict:
        """Make API request with rate limiting and error handling."""
        if not self._is_enabled():
            raise RuntimeError("Alpha Vantage API key not configured")
        
        self._throttle()
        
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                raise RuntimeError(f"Alpha Vantage API error: {data['Error Message']}")
            
            if 'Note' in data:
                # Rate limit warning
                logger.warning(f"Alpha Vantage rate limit warning: {data['Note']}")
                raise RuntimeError("Alpha Vantage rate limit exceeded")
            
            return data
            
        except requests.RequestException as e:
            raise RuntimeError(f"Alpha Vantage request failed: {e}")
    
    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        """
        Get current price using Global Quote endpoint.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (price, source_description)
        """
        if not self._is_enabled():
            return None, "alpha_vantage.disabled"
        
        try:
            data = self._make_request(function="GLOBAL_QUOTE", symbol=symbol)
            
            quote = data.get("Global Quote", {})
            price_str = quote.get("05. price") or quote.get("05. Price")
            
            if not price_str:
                logger.warning(f"No price data in Alpha Vantage response for {symbol}")
                return None, "alpha_vantage.no_price"
            
            price = float(price_str)
            logger.debug(f"Alpha Vantage price for {symbol}: ${price:.2f}")
            
            return price, "alpha_vantage.global_quote"
            
        except Exception as e:
            logger.warning(f"Alpha Vantage price lookup failed for {symbol}: {e}")
            return None, "alpha_vantage.error"
    
    def get_next_earnings(self, symbol: str) -> Optional[EarningsEvent]:
        """
        Get next earnings announcement using Earnings endpoint.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            EarningsEvent if found, None otherwise
        """
        if not self._is_enabled():
            logger.debug("Alpha Vantage earnings disabled - no API key")
            return None
        
        try:
            data = self._make_request(function="EARNINGS", symbol=symbol)
            
            # Look in quarterlyEarnings for upcoming events
            quarterly = data.get("quarterlyEarnings", [])
            if not quarterly:
                logger.debug(f"No quarterly earnings data for {symbol}")
                return None
            
            # Find the next earnings (Alpha Vantage returns in descending order)
            now = datetime.now().date()
            
            for earning in quarterly:
                reported_date_str = earning.get("reportedDate")
                if not reported_date_str:
                    continue
                
                try:
                    reported_date = datetime.strptime(reported_date_str, "%Y-%m-%d").date()
                    
                    # Look for future earnings (Alpha Vantage sometimes has estimated dates)
                    if reported_date > now:
                        # Alpha Vantage doesn't provide BMO/AMC timing, so we default to AMC
                        # This is the most common timing for earnings
                        event = EarningsEvent(
                            symbol=symbol.upper(),
                            date=datetime.combine(reported_date, datetime.min.time()),
                            timing="AMC",  # Default assumption
                            confirmed=False,  # Alpha Vantage doesn't provide confirmation
                            source="alpha_vantage.earnings"
                        )
                        
                        logger.info(f"Found next earnings for {symbol}: {reported_date} (estimated)")
                        return event
                        
                except ValueError as e:
                    logger.warning(f"Invalid date format in earnings data: {reported_date_str}")
                    continue
            
            logger.debug(f"No future earnings found for {symbol}")
            return None
            
        except Exception as e:
            logger.warning(f"Alpha Vantage earnings lookup failed for {symbol}: {e}")
            return None
    
    def get_earnings_calendar(self, symbol: str, days_ahead: int = 30) -> List[EarningsEvent]:
        """
        Get earnings calendar for multiple periods.
        
        Note: Alpha Vantage EARNINGS endpoint only provides historical data.
        For upcoming earnings, we try to extract from the most recent quarters
        and estimate based on typical 90-day cycles.
        
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