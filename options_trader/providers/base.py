#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Provider Interfaces
========================

Abstract base classes for data provider implementations.
All providers must implement these interfaces for seamless fallback handling.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class EarningsEvent:
    """Represents an earnings announcement event with timing information."""
    symbol: str
    date: datetime
    timing: str  # "BMO" (before market open) or "AMC" (after market close)
    confirmed: bool = False
    source: str = "unknown"
    
    @property
    def is_before_market(self) -> bool:
        """True if earnings are before market open (BMO)."""
        return self.timing.upper() == "BMO"
    
    @property
    def is_after_market(self) -> bool:
        """True if earnings are after market close (AMC)."""
        return self.timing.upper() == "AMC"
    
    @property
    def days_until(self) -> int:
        """Calculate days until earnings date from current date."""
        from datetime import datetime, timezone
        
        # Get current date (ensure timezone aware)
        now = datetime.now(timezone.utc)
        
        # Ensure earnings date has timezone info
        earnings_date = self.date
        if earnings_date.tzinfo is None:
            # Assume UTC if no timezone info
            earnings_date = earnings_date.replace(tzinfo=timezone.utc)
        
        # Calculate the difference in days
        delta = earnings_date.date() - now.date()
        return delta.days


class PriceProvider(ABC):
    """Abstract interface for price data providers."""
    
    @abstractmethod
    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        """
        Get current price for a symbol.
        
        Returns:
            Tuple of (price, source_description)
            price is None if unavailable
        """
        pass


class OptionsProvider(ABC):
    """Abstract interface for options data providers."""
    
    @abstractmethod
    def get_expirations(self, symbol: str, max_count: int = 3) -> List[str]:
        """
        Get available option expiration dates.
        
        Returns:
            List of expiration dates in 'YYYY-MM-DD' format
        """
        pass
    
    @abstractmethod
    def get_chain(self, symbol: str, expiration: str):
        """
        Get option chain for specific expiration.
        
        Returns:
            Object with .calls and .puts DataFrame attributes (yfinance-like)
        """
        pass


class EarningsProvider(ABC):
    """Abstract interface for earnings calendar providers."""
    
    @abstractmethod
    def get_next_earnings(self, symbol: str) -> Optional[EarningsEvent]:
        """
        Get the next earnings announcement for a symbol.
        
        Returns:
            EarningsEvent if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_earnings_calendar(self, symbol: str, days_ahead: int = 30) -> List[EarningsEvent]:
        """
        Get earnings calendar for a symbol within specified days.
        
        Returns:
            List of EarningsEvent objects
        """
        pass