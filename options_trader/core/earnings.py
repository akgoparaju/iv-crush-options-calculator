#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Earnings Calendar & Timing Engine - Module 1
============================================

Core module for earnings event detection and trading window calculation.
Implements the precise timing requirements from the IV crush strategy:
- Entry: 15 minutes before close on day before earnings
- Exit: 15 minutes after open on day after earnings

Supports multiple data providers with fallback logic.
"""

import os
import logging
from datetime import datetime, timedelta, time
from typing import Optional, List, Tuple
from dataclasses import dataclass

# Handle timezone imports for different Python versions
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python < 3.9 fallback
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        # Ultimate fallback to pytz
        import pytz
        class ZoneInfo:
            def __init__(self, zone_name):
                self._zone = pytz.timezone(zone_name)
            def __str__(self):
                return str(self._zone)

from ..providers.base import EarningsProvider, EarningsEvent

logger = logging.getLogger("options_trader.earnings")


@dataclass
class TradingWindows:
    """Represents the calculated entry and exit windows for a trade."""
    entry_start: datetime
    entry_end: datetime  
    exit_start: datetime
    exit_end: datetime
    market_timezone: str
    
    def is_in_entry_window(self, current_time: datetime) -> bool:
        """Check if current time is within the entry window."""
        return self.entry_start <= current_time <= self.entry_end
    
    def is_in_exit_window(self, current_time: datetime) -> bool:
        """Check if current time is within the exit window.""" 
        return self.exit_start <= current_time <= self.exit_end
    
    def time_to_entry(self, current_time: datetime) -> Optional[timedelta]:
        """Calculate time remaining until entry window opens."""
        if current_time >= self.entry_start:
            return None  # Entry window already started or passed
        return self.entry_start - current_time
    
    def time_to_exit(self, current_time: datetime) -> Optional[timedelta]:
        """Calculate time remaining until exit window opens."""
        if current_time >= self.exit_start:
            return None  # Exit window already started or passed
        return self.exit_start - current_time


class EarningsCalendar:
    """
    Earnings calendar and timing window calculator.
    
    Provides earnings event detection and precise timing calculations
    for the IV crush strategy entry/exit windows.
    """
    
    def __init__(self, earnings_providers: List[EarningsProvider], user_timezone: str = None):
        """
        Initialize earnings calendar with provider list.
        
        Args:
            earnings_providers: List of earnings data providers in priority order
            user_timezone: User's timezone (e.g., 'America/New_York'). Auto-detect if None.
        """
        self.providers = earnings_providers
        self.user_tz = self._get_user_timezone(user_timezone)
        self.market_tz = ZoneInfo("America/New_York")  # NYSE/NASDAQ timezone
        
        logger.info(f"EarningsCalendar initialized with {len(self.providers)} providers")
        logger.info(f"User timezone: {self.user_tz}")
    
    def _get_user_timezone(self, user_timezone: str = None) -> ZoneInfo:
        """Get user's timezone, auto-detecting if not provided."""
        if user_timezone:
            try:
                return ZoneInfo(user_timezone)
            except Exception as e:
                logger.warning(f"Invalid timezone '{user_timezone}': {e}")
        
        # Try to auto-detect from system
        try:
            import time
            return ZoneInfo(time.tzname[0])
        except Exception:
            pass
            
        # Fallback to Eastern (market timezone)
        logger.warning("Could not detect user timezone, defaulting to Eastern")
        return ZoneInfo("America/New_York")
    
    def get_next_earnings(self, symbol: str) -> Optional[EarningsEvent]:
        """
        Get the next earnings announcement for a symbol.
        
        Tries all providers in order until one succeeds.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            EarningsEvent if found, None otherwise
        """
        symbol = symbol.upper().strip()
        
        for provider in self.providers:
            try:
                earnings = provider.get_next_earnings(symbol)
                if earnings:
                    logger.info(f"Found earnings for {symbol}: {earnings.date} {earnings.timing} from {earnings.source}")
                    return earnings
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed for {symbol}: {e}")
                continue
        
        logger.warning(f"No earnings found for {symbol} from any provider")
        return None
    
    def get_earnings_calendar(self, symbol: str, days_ahead: int = 30) -> List[EarningsEvent]:
        """
        Get earnings calendar for a symbol within specified days.
        
        Args:
            symbol: Stock symbol
            days_ahead: Number of days to look ahead
            
        Returns:
            List of EarningsEvent objects
        """
        symbol = symbol.upper().strip()
        
        for provider in self.providers:
            try:
                events = provider.get_earnings_calendar(symbol, days_ahead)
                if events:
                    logger.info(f"Found {len(events)} earnings events for {symbol} from {provider.__class__.__name__}")
                    return events
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed for {symbol}: {e}")
                continue
        
        logger.warning(f"No earnings calendar found for {symbol}")
        return []
    
    def calculate_trading_windows(self, earnings_event: EarningsEvent, 
                                entry_minutes_before: int = 15,
                                exit_minutes_after: int = 15) -> TradingWindows:
        """
        Calculate precise entry and exit trading windows for an earnings event.
        
        Strategy timing:
        - Entry: 15 minutes before market close on day before earnings
        - Exit: 15 minutes after market open on day after earnings
        
        Args:
            earnings_event: The earnings event to calculate windows for
            entry_minutes_before: Minutes before close to start entry window
            exit_minutes_after: Minutes after open to end exit window
            
        Returns:
            TradingWindows object with precise timing in user's timezone
        """
        
        # Standard market hours (Eastern Time)
        market_open = time(9, 30)  # 9:30 AM ET
        market_close = time(16, 0)  # 4:00 PM ET
        
        # Determine trading dates based on earnings timing
        earnings_date = earnings_event.date.date()
        
        if earnings_event.is_before_market:
            # BMO: Entry day before, exit same day as earnings
            entry_date = earnings_date - timedelta(days=1)
            exit_date = earnings_date
        else:
            # AMC: Entry same day as earnings, exit next day
            entry_date = earnings_date
            exit_date = earnings_date + timedelta(days=1)
        
        # Calculate entry window (around market close)
        entry_close_time = datetime.combine(entry_date, market_close, self.market_tz)
        entry_start = entry_close_time - timedelta(minutes=entry_minutes_before)
        entry_end = entry_close_time
        
        # Calculate exit window (around market open)
        exit_open_time = datetime.combine(exit_date, market_open, self.market_tz)
        exit_start = exit_open_time
        exit_end = exit_open_time + timedelta(minutes=exit_minutes_after)
        
        # Convert to user's timezone
        entry_start_user = entry_start.astimezone(self.user_tz)
        entry_end_user = entry_end.astimezone(self.user_tz)
        exit_start_user = exit_start.astimezone(self.user_tz)
        exit_end_user = exit_end.astimezone(self.user_tz)
        
        windows = TradingWindows(
            entry_start=entry_start_user,
            entry_end=entry_end_user,
            exit_start=exit_start_user, 
            exit_end=exit_end_user,
            market_timezone=str(self.market_tz)
        )
        
        logger.debug(f"Calculated trading windows for {earnings_event.symbol}:")
        logger.debug(f"  Entry: {windows.entry_start} to {windows.entry_end}")
        logger.debug(f"  Exit: {windows.exit_start} to {windows.exit_end}")
        
        return windows
    
    def validate_earnings_event(self, earnings_event: EarningsEvent) -> List[str]:
        """
        Validate an earnings event for trading suitability.
        
        Args:
            earnings_event: The earnings event to validate
            
        Returns:
            List of validation warnings (empty if all good)
        """
        warnings = []
        
        # Check if event is in the future
        now = datetime.now(self.user_tz)
        if earnings_event.date.replace(tzinfo=self.user_tz) <= now:
            warnings.append("Earnings event is in the past")
        
        # Check if event is too far in the future (options might not exist)
        days_ahead = (earnings_event.date.date() - now.date()).days
        if days_ahead > 60:
            warnings.append(f"Earnings event is {days_ahead} days away (options may not be available)")
        
        # Check if timing is confirmed
        if not earnings_event.confirmed:
            warnings.append("Earnings timing (BMO/AMC) not confirmed")
        
        # Check for weekend conflicts (basic check)
        windows = self.calculate_trading_windows(earnings_event)
        if windows.entry_start.weekday() >= 5:  # Saturday = 5, Sunday = 6
            warnings.append("Entry window falls on weekend")
        if windows.exit_start.weekday() >= 5:
            warnings.append("Exit window falls on weekend")
        
        return warnings
    
    def get_trading_opportunity(self, symbol: str) -> Optional[Tuple[EarningsEvent, TradingWindows, List[str]]]:
        """
        Get complete trading opportunity information for a symbol.
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            Tuple of (earnings_event, trading_windows, warnings) if opportunity exists,
            None if no suitable earnings found
        """
        earnings = self.get_next_earnings(symbol)
        if not earnings:
            return None
        
        windows = self.calculate_trading_windows(earnings)
        warnings = self.validate_earnings_event(earnings)
        
        return earnings, windows, warnings