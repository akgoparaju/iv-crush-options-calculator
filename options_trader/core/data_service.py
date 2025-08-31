#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Service - Multi-Provider Orchestration
===========================================

Orchestrates data retrieval from multiple providers with intelligent fallback logic.
Handles price caching, rate limiting, and provider health monitoring.

Provider priority order:
1. Demo (if enabled)
2. Yahoo Finance (primary, free but rate-limited)
3. Alpha Vantage (price fallback)
4. Finnhub (options + earnings)
5. Tradier (options + earnings)
6. Cache (last resort for prices)
"""

import os
import json
import time
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from ..providers.base import PriceProvider, OptionsProvider, EarningsProvider
from ..providers.demo import DemoProvider

# Import other providers conditionally
try:
    from ..providers.yahoo import YahooProvider
except ImportError:
    YahooProvider = None

try:
    from ..providers.alpha_vantage import AlphaVantageProvider
except ImportError:
    AlphaVantageProvider = None

try:
    from ..providers.finnhub import FinnhubProvider
except ImportError:
    FinnhubProvider = None

try:
    from ..providers.tradier import TradierProvider
except ImportError:
    TradierProvider = None

logger = logging.getLogger("options_trader.data_service")

# Cache configuration
PRICE_CACHE_TTL_SEC = 300  # 5 minutes
MIN_INTERVAL_BETWEEN_REQUESTS = 0.7
MAX_RETRIES = 3
BASE_DELAY = 0.9


class PriceCache:
    """Thread-safe price caching with TTL."""
    
    def __init__(self, cache_file: str = ".price_cache.json"):
        """Initialize price cache with file persistence."""
        self.cache_file = Path(cache_file)
        self.lock = threading.Lock()
        logger.debug(f"Price cache initialized: {self.cache_file}")
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from disk."""
        try:
            if not self.cache_file.exists():
                return {}
            
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            logger.warning(f"Failed to load price cache: {e}")
            return {}
    
    def _save_cache(self, cache: Dict[str, Any]) -> None:
        """Save cache to disk."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f)
                
        except Exception as e:
            logger.warning(f"Failed to save price cache: {e}")
    
    def get_price(self, symbol: str, ttl_sec: int = PRICE_CACHE_TTL_SEC) -> Optional[float]:
        """Get cached price if still valid."""
        with self.lock:
            try:
                cache = self._load_cache()
                entry = cache.get(symbol.upper())
                
                if not entry:
                    return None
                
                timestamp = entry.get("ts")
                price = entry.get("price")
                
                if isinstance(timestamp, (int, float)) and isinstance(price, (int, float)):
                    age = time.time() - timestamp
                    if age <= ttl_sec:
                        logger.debug(f"Using cached price for {symbol}: ${price:.2f} (age={age:.1f}s)")
                        return float(price)
                
                return None
                
            except Exception as e:
                logger.warning(f"Cache lookup failed for {symbol}: {e}")
                return None
    
    def set_price(self, symbol: str, price: float) -> None:
        """Cache a price with current timestamp."""
        with self.lock:
            try:
                cache = self._load_cache()
                cache[symbol.upper()] = {
                    "price": float(price), 
                    "ts": time.time()
                }
                self._save_cache(cache)
                
                logger.debug(f"Cached price for {symbol}: ${price:.2f}")
                
            except Exception as e:
                logger.warning(f"Cache storage failed for {symbol}: {e}")


class RequestThrottler:
    """Rate limiting for API requests."""
    
    def __init__(self, min_interval: float = MIN_INTERVAL_BETWEEN_REQUESTS):
        """Initialize throttler with minimum interval."""
        self.min_interval = min_interval
        self.last_request_time = 0.0
        self.lock = threading.Lock()
    
    def throttle(self) -> None:
        """Enforce minimum interval between requests."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request_time
            
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                logger.debug(f"Throttling: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()


class DataService:
    """
    Multi-provider data service with intelligent fallback logic.
    
    Provides unified interface for:
    - Price data (with caching)
    - Options chains
    - Earnings calendar (NEW in Module 1)
    
    Handles provider failures gracefully and implements retry logic.
    """
    
    def __init__(self, use_demo: bool = False):
        """
        Initialize data service with all available providers.
        
        Args:
            use_demo: If True, use demo provider for all data (no API calls)
        """
        # Initialize cache and throttling
        self.price_cache = PriceCache()
        self.throttler = RequestThrottler()
        self.use_demo = use_demo
        
        # Initialize providers (with fallbacks for missing dependencies)
        self.yahoo = YahooProvider() if YahooProvider else None
        self.alpha_vantage = AlphaVantageProvider() if AlphaVantageProvider else None
        self.finnhub = FinnhubProvider() if FinnhubProvider else None
        self.tradier = TradierProvider() if TradierProvider else None
        self.demo = DemoProvider() if use_demo else None
        
        logger.info(f"DataService initialized (demo_mode={use_demo})")
        self._log_provider_status()
    
    def _log_provider_status(self) -> None:
        """Log which providers are available."""
        providers = []
        if self.demo:
            providers.append("Demo")
        if self.alpha_vantage and hasattr(self.alpha_vantage, '_is_enabled') and self.alpha_vantage._is_enabled():
            providers.append("AlphaVantage")
        if self.finnhub and hasattr(self.finnhub, '_is_enabled') and self.finnhub._is_enabled():
            providers.append("Finnhub")  
        if self.tradier and hasattr(self.tradier, '_is_enabled') and self.tradier._is_enabled():
            providers.append("Tradier")
        if self.yahoo:
            providers.append("Yahoo")
        
        logger.info(f"Available providers: {', '.join(providers) if providers else 'None (dependencies missing)'}")
    
    def get_price(self, symbol: str) -> Tuple[Optional[float], str, bool]:
        """
        Get current price with provider fallback logic.
        
        Provider priority:
        1. Demo (if enabled)
        2. Cache (if recent)
        3. Yahoo Finance (primary)
        4. Alpha Vantage (your configured provider)
        5. Finnhub (if configured)
        6. Cache (last resort, any age)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (price, source_description, is_cached)
        """
        symbol = symbol.upper().strip()
        
        # 1. Demo mode
        if self.demo:
            price, source = self.demo.get_price(symbol)
            return price, source, False
        
        # 2. Fresh cache
        cached_price = self.price_cache.get_price(symbol)
        if cached_price is not None:
            return cached_price, "cache.recent", True
        
        # 3. Yahoo Finance (primary free provider)
        if self.yahoo:
            self.throttler.throttle()
            price, source = self.yahoo.get_price(symbol)
            if price is not None:
                self.price_cache.set_price(symbol, price)
                return price, source, False
        
        # 4. Alpha Vantage (your configured provider)
        if self.alpha_vantage:
            try:
                price, source = self.alpha_vantage.get_price(symbol)
                if price is not None:
                    self.price_cache.set_price(symbol, price)
                    return price, source, False
            except Exception as e:
                logger.warning(f"Alpha Vantage price failed for {symbol}: {e}")
        
        # 5. Finnhub fallback
        if self.finnhub:
            try:
                price, source = self.finnhub.get_price(symbol)
                if price is not None:
                    self.price_cache.set_price(symbol, price)
                    return price, source, False
            except Exception as e:
                logger.warning(f"Finnhub price failed for {symbol}: {e}")
        
        # 6. Last resort: stale cache
        stale_price = self.price_cache.get_price(symbol, ttl_sec=86400)  # 24 hours
        if stale_price is not None:
            logger.warning(f"Using stale cached price for {symbol}: ${stale_price:.2f}")
            return stale_price, "cache.stale", True
        
        logger.error(f"Failed to get price for {symbol} from any provider")
        return None, "none", False
    
    def get_expirations(self, symbol: str, max_count: int = 3) -> Tuple[List[str], str]:
        """
        Get available option expirations with provider fallback.
        
        Provider priority:
        1. Demo (if enabled)
        2. Yahoo Finance
        3. Finnhub
        4. Tradier
        
        Args:
            symbol: Stock symbol
            max_count: Maximum number of expirations to return
            
        Returns:
            Tuple of (expiration_list, source_description)
        """
        symbol = symbol.upper().strip()
        
        if self.demo:
            expirations = self.demo.get_expirations(symbol, max_count)
            return expirations, "demo"
        
        # Try Yahoo first
        if self.yahoo:
            self.throttler.throttle()
            expirations = self.yahoo.get_expirations(symbol, max_count)
            if expirations:
                logger.debug(f"Yahoo expirations for {symbol}: {len(expirations)} found")
                return expirations, "yahoo"
        
        # Try Finnhub
        if self.finnhub:
            try:
                expirations = self.finnhub.get_expirations(symbol, max_count)
                if expirations:
                    logger.debug(f"Finnhub expirations for {symbol}: {len(expirations)} found")
                    return expirations, "finnhub"
            except Exception as e:
                logger.warning(f"Finnhub expirations failed for {symbol}: {e}")
        
        # Try Tradier
        if self.tradier:
            try:
                expirations = self.tradier.get_expirations(symbol, max_count)
                if expirations:
                    logger.debug(f"Tradier expirations for {symbol}: {len(expirations)} found")
                    return expirations, "tradier"
            except Exception as e:
                logger.warning(f"Tradier expirations failed for {symbol}: {e}")
        
        logger.warning(f"No expirations found for {symbol} from any provider")
        return [], "none"
    
    def get_chain(self, symbol: str, expiration: str) -> Tuple[Any, str]:
        """
        Get option chain with provider fallback.
        
        Provider priority:
        1. Demo (if enabled)
        2. Yahoo Finance
        3. Finnhub
        4. Tradier
        
        Args:
            symbol: Stock symbol
            expiration: Expiration date in 'YYYY-MM-DD' format
            
        Returns:
            Tuple of (chain_object, source_description)
            
        Raises:
            RuntimeError if no provider can return the chain
        """
        symbol = symbol.upper().strip()
        
        if self.demo:
            chain = self.demo.get_chain(symbol, expiration)
            return chain, "demo"
        
        # Try Yahoo first
        if self.yahoo:
            try:
                self.throttler.throttle()
                chain = self.yahoo.get_chain(symbol, expiration)
                logger.debug(f"Yahoo chain for {symbol} {expiration} retrieved successfully")
                return chain, "yahoo"
            except Exception as e:
                logger.warning(f"Yahoo chain failed for {symbol} {expiration}: {e}")
        
        # Try Finnhub
        if self.finnhub:
            try:
                chain = self.finnhub.get_chain(symbol, expiration)
                logger.debug(f"Finnhub chain for {symbol} {expiration} retrieved successfully")
                return chain, "finnhub"
            except Exception as e:
                logger.warning(f"Finnhub chain failed for {symbol} {expiration}: {e}")
        
        # Try Tradier
        if self.tradier:
            try:
                chain = self.tradier.get_chain(symbol, expiration)
                logger.debug(f"Tradier chain for {symbol} {expiration} retrieved successfully")
                return chain, "tradier"
            except Exception as e:
                logger.warning(f"Tradier chain failed for {symbol} {expiration}: {e}")
        
        raise RuntimeError(f"No provider could return option chain for {symbol} {expiration}")
    
    def get_earnings_providers(self) -> List[EarningsProvider]:
        """
        Get list of available earnings providers for the EarningsCalendar.
        
        Returns:
            List of configured earnings providers in priority order
        """
        providers = []
        
        if self.demo:
            providers.append(self.demo)
        
        # Alpha Vantage (your primary provider)
        if self.alpha_vantage and hasattr(self.alpha_vantage, '_is_enabled') and self.alpha_vantage._is_enabled():
            providers.append(self.alpha_vantage)
        
        # Finnhub (better earnings data)
        if self.finnhub and hasattr(self.finnhub, '_is_enabled') and self.finnhub._is_enabled():
            providers.append(self.finnhub)
        
        # Tradier (corporate events)
        if self.tradier and hasattr(self.tradier, '_is_enabled') and self.tradier._is_enabled():
            providers.append(self.tradier)
        
        logger.debug(f"Available earnings providers: {len(providers)}")
        return providers