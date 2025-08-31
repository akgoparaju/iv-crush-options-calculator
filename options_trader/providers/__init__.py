#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Provider Interfaces
========================

Multi-provider data sourcing with fallbacks for:
- Price data: Yahoo Finance, Alpha Vantage, Finnhub
- Options chains: Yahoo Finance, Finnhub, Tradier
- Earnings calendar: Alpha Vantage, Finnhub, Tradier

All providers implement standard interfaces for seamless fallback handling.
"""

# Import base interfaces (always available)
from .base import PriceProvider, OptionsProvider, EarningsProvider

# Import demo provider (no external dependencies)
from .demo import DemoProvider

# Import other providers conditionally
__all__ = [
    "PriceProvider",
    "OptionsProvider", 
    "EarningsProvider",
    "DemoProvider"
]

# Yahoo provider (requires yfinance)
try:
    from .yahoo import YahooProvider
    __all__.append("YahooProvider")
except ImportError:
    YahooProvider = None

# Alpha Vantage provider (requires requests)
try:
    from .alpha_vantage import AlphaVantageProvider
    __all__.append("AlphaVantageProvider")
except ImportError:
    AlphaVantageProvider = None

# Finnhub provider (requires requests)
try:
    from .finnhub import FinnhubProvider
    __all__.append("FinnhubProvider")
except ImportError:
    FinnhubProvider = None

# Tradier provider (requires requests, pandas)
try:
    from .tradier import TradierProvider
    __all__.append("TradierProvider")
except ImportError:
    TradierProvider = None