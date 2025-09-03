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

from .base import PriceProvider, OptionsProvider, EarningsProvider, EarningsEvent

try:
    from yfinance.exceptions import YFRateLimitError
except Exception:
    class YFRateLimitError(Exception):
        pass

logger = logging.getLogger("options_trader.providers.yahoo")


class YahooProvider(PriceProvider, OptionsProvider, EarningsProvider):
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
            logger.debug(f"Yahoo fast_info raw data for {symbol}: {info}")
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
            logger.debug(f"Yahoo history raw data for {symbol}: {df.tail() if df is not None and not df.empty else 'Empty/None'}")
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
            logger.debug(f"Yahoo chain raw data for {symbol} {expiration}: calls={len(chain.calls)} rows, puts={len(chain.puts)} rows")
            logger.debug(f"Yahoo chain calls data for {symbol}: {chain.calls.to_dict() if hasattr(chain.calls, 'to_dict') else str(chain.calls)}")
            logger.debug(f"Yahoo chain puts data for {symbol}: {chain.puts.to_dict() if hasattr(chain.puts, 'to_dict') else str(chain.puts)}")
            logger.debug(f"Yahoo chain for {symbol} {expiration}: {len(chain.calls)} calls, {len(chain.puts)} puts")
            return chain
            
        except Exception as e:
            logger.warning(f"Yahoo get_chain failed for {symbol} {expiration}: {e}")
            raise

    def get_next_earnings(self, symbol: str) -> Optional[EarningsEvent]:
        """
        Get next earnings announcement from Yahoo Finance.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            EarningsEvent if found, None otherwise
        """
        ticker = self._get_ticker(symbol)
        try:
            # Try calendar property first (more reliable for upcoming earnings)
            try:
                calendar = ticker.calendar
                logger.debug(f"Raw calendar data for {symbol} from yfinance: {calendar}")
                
                if calendar and 'Earnings Date' in calendar:
                    earnings_dates_list = calendar['Earnings Date']
                    if earnings_dates_list and len(earnings_dates_list) > 0:
                        # Take the first (closest) earnings date
                        earnings_date = earnings_dates_list[0]
                        
                        # Check if it's today or in the future (earnings typically after market close)
                        now = datetime.now().date()
                        if earnings_date >= now:
                            event = EarningsEvent(
                                symbol=symbol.upper(),
                                date=datetime.combine(earnings_date, datetime.min.time()),
                                timing="AMC",  # Default assumption
                                confirmed=True,  # Calendar data is more reliable
                                source="yahoo.calendar"
                            )
                            logger.info(f"Found next earnings for {symbol}: {earnings_date} from yfinance calendar")
                            return event
                        else:
                            logger.debug(f"Calendar earnings date {earnings_date} is not in future for {symbol}")
                    else:
                        logger.debug(f"No earnings dates in calendar for {symbol}")
                else:
                    logger.debug(f"No calendar data or earnings date for {symbol}")
            except Exception as calendar_error:
                logger.debug(f"Calendar lookup failed for {symbol}: {calendar_error}")
            
            # Fallback to earnings_dates property (historical earnings)
            earnings_dates = ticker.earnings_dates
            logger.debug(f"Raw earnings_dates data for {symbol} from yfinance: {earnings_dates}")
            logger.debug(f"Raw earnings_dates full dataframe for {symbol}: {earnings_dates.to_dict() if earnings_dates is not None and hasattr(earnings_dates, 'to_dict') else 'None/Empty'}")
            if earnings_dates is None or earnings_dates.empty:
                logger.debug(f"No earnings dates found for {symbol} from yfinance")
                return None

            # Find the next earnings date (include today since earnings typically after close)
            now = datetime.now().date()
            future_earnings = earnings_dates[earnings_dates.index.date >= now]
            if future_earnings.empty:
                logger.debug(f"No future earnings dates found for {symbol}")
                return None

            next_earnings_row = future_earnings.iloc[0]
            earnings_date = next_earnings_row.name.date()

            # yfinance doesn't reliably provide timing, so we default to AMC
            event = EarningsEvent(
                symbol=symbol.upper(),
                date=datetime.combine(earnings_date, datetime.min.time()),
                timing="AMC",  # Default assumption
                confirmed=False,  # earnings_dates is less reliable
                source="yahoo.earnings_dates"
            )
            logger.info(f"Found next earnings for {symbol}: {earnings_date} (estimated) from yfinance")
            return event

        except Exception as e:
            logger.warning(f"Yahoo earnings lookup failed for {symbol}: {e}")
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
        next_earnings = self.get_next_earnings(symbol)
        if next_earnings:
            return [next_earnings]
        return []
