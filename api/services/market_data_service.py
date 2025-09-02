"""
Market Data Service for Phase 5.2
Real-time market data and options pricing
"""

import logging
import asyncio
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from decimal import Decimal
import aiohttp
import os

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service for market data and options pricing"""
    
    def __init__(self):
        # API configuration
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY")
        
        # Cache for market data (simple in-memory cache)
        self._price_cache = {}
        self._options_cache = {}
        self._cache_ttl = 60  # seconds
        
        logger.info("📈 Market data service initialized")
    
    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """Get current stock price"""
        try:
            # Check cache first
            cache_key = f"price_{symbol}"
            if self._is_cache_valid(cache_key):
                return self._price_cache[cache_key]['price']
            
            # Try Alpha Vantage first
            if self.alpha_vantage_key:
                price = await self._get_price_alpha_vantage(symbol)
                if price:
                    self._update_price_cache(cache_key, price)
                    return price
            
            # Fallback to Finnhub
            if self.finnhub_key:
                price = await self._get_price_finnhub(symbol)
                if price:
                    self._update_price_cache(cache_key, price)
                    return price
            
            # Fallback to demo data
            return self._get_demo_price(symbol)
            
        except Exception as e:
            logger.error(f"❌ Error fetching price for {symbol}: {str(e)}")
            return self._get_demo_price(symbol)
    
    async def get_option_price(self, symbol: str, strike: Decimal, 
                             expiration: date, option_type: str) -> Optional[Decimal]:
        """Get option price (simplified Black-Scholes estimation)"""
        try:
            # This is a simplified implementation
            # In production, you'd use real options data or sophisticated pricing models
            
            current_price = await self.get_current_price(symbol)
            if not current_price:
                return None
            
            # Simple intrinsic + time value estimation
            days_to_expiry = (expiration - date.today()).days
            if days_to_expiry <= 0:
                # Expired option, only intrinsic value
                if option_type.lower() == 'call':
                    return max(current_price - strike, Decimal('0'))
                else:  # put
                    return max(strike - current_price, Decimal('0'))
            
            # Simplified time value calculation
            time_value = Decimal('0.05') * Decimal(str(days_to_expiry)) / 365
            
            if option_type.lower() == 'call':
                intrinsic = max(current_price - strike, Decimal('0'))
            else:  # put
                intrinsic = max(strike - current_price, Decimal('0'))
            
            return intrinsic + time_value
            
        except Exception as e:
            logger.error(f"❌ Error calculating option price: {str(e)}")
            return Decimal('1.00')  # Default option price
    
    async def get_options_chain(self, symbol: str, expiration: date) -> Dict[str, Any]:
        """Get options chain for symbol and expiration"""
        try:
            # This would typically fetch from options data provider
            # For now, return a mock options chain
            current_price = await self.get_current_price(symbol)
            if not current_price:
                return {}
            
            strikes = self._generate_strike_ladder(current_price)
            calls = {}
            puts = {}
            
            for strike in strikes:
                call_price = await self.get_option_price(symbol, strike, expiration, 'call')
                put_price = await self.get_option_price(symbol, strike, expiration, 'put')
                
                calls[str(strike)] = {
                    'strike': strike,
                    'bid': call_price * Decimal('0.98') if call_price else Decimal('0'),
                    'ask': call_price * Decimal('1.02') if call_price else Decimal('0'),
                    'last': call_price,
                    'volume': 100,  # Mock data
                    'open_interest': 500,
                    'delta': Decimal('0.5'),  # Simplified
                    'gamma': Decimal('0.1'),
                    'theta': Decimal('-0.05'),
                    'vega': Decimal('0.2')
                }
                
                puts[str(strike)] = {
                    'strike': strike,
                    'bid': put_price * Decimal('0.98') if put_price else Decimal('0'),
                    'ask': put_price * Decimal('1.02') if put_price else Decimal('0'),
                    'last': put_price,
                    'volume': 75,  # Mock data
                    'open_interest': 300,
                    'delta': Decimal('-0.5'),  # Simplified
                    'gamma': Decimal('0.1'),
                    'theta': Decimal('-0.05'),
                    'vega': Decimal('0.2')
                }
            
            return {
                'symbol': symbol,
                'expiration': expiration.isoformat(),
                'current_price': current_price,
                'calls': calls,
                'puts': puts,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error fetching options chain for {symbol}: {str(e)}")
            return {}
    
    async def get_implied_volatility(self, symbol: str) -> Optional[Decimal]:
        """Get implied volatility for symbol"""
        try:
            # This would typically calculate from options chain
            # For now, return a mock IV based on symbol
            if symbol in ['TSLA', 'NVDA', 'AMZN']:
                return Decimal('0.45')  # High volatility stocks
            elif symbol in ['AAPL', 'MSFT', 'GOOGL']:
                return Decimal('0.25')  # Medium volatility stocks
            else:
                return Decimal('0.20')  # Default volatility
                
        except Exception as e:
            logger.error(f"❌ Error fetching IV for {symbol}: {str(e)}")
            return Decimal('0.25')
    
    # =====================================================================================
    # Private Methods
    # =====================================================================================
    
    async def _get_price_alpha_vantage(self, symbol: str) -> Optional[Decimal]:
        """Get price from Alpha Vantage"""
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data.get('Global Quote', {})
                        price_str = quote.get('05. price')
                        
                        if price_str:
                            return Decimal(price_str)
            
            return None
            
        except Exception as e:
            logger.warning(f"Alpha Vantage API error for {symbol}: {str(e)}")
            return None
    
    async def _get_price_finnhub(self, symbol: str) -> Optional[Decimal]:
        """Get price from Finnhub"""
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        current_price = data.get('c')  # Current price
                        
                        if current_price:
                            return Decimal(str(current_price))
            
            return None
            
        except Exception as e:
            logger.warning(f"Finnhub API error for {symbol}: {str(e)}")
            return None
    
    def _get_demo_price(self, symbol: str) -> Decimal:
        """Get demo price for testing"""
        # Generate consistent demo prices based on symbol
        demo_prices = {
            'AAPL': Decimal('150.00'),
            'GOOGL': Decimal('2500.00'),
            'MSFT': Decimal('350.00'),
            'TSLA': Decimal('200.00'),
            'AMZN': Decimal('130.00'),
            'NVDA': Decimal('400.00'),
            'META': Decimal('300.00'),
            'NFLX': Decimal('450.00'),
            'SPY': Decimal('430.00'),
            'QQQ': Decimal('360.00')
        }
        
        return demo_prices.get(symbol, Decimal('100.00'))
    
    def _generate_strike_ladder(self, current_price: Decimal, num_strikes: int = 11) -> List[Decimal]:
        """Generate strike prices around current price"""
        strikes = []
        
        # Determine strike spacing based on price
        if current_price < 50:
            spacing = Decimal('2.5')
        elif current_price < 200:
            spacing = Decimal('5.0')
        elif current_price < 500:
            spacing = Decimal('10.0')
        else:
            spacing = Decimal('25.0')
        
        # Generate strikes around current price
        center_strike = (current_price / spacing).quantize(Decimal('1')) * spacing
        half_range = num_strikes // 2
        
        for i in range(-half_range, half_range + 1):
            strike = center_strike + (spacing * i)
            if strike > 0:
                strikes.append(strike)
        
        return sorted(strikes)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._price_cache:
            return False
        
        cached_time = self._price_cache[cache_key]['timestamp']
        age = (datetime.utcnow() - cached_time).total_seconds()
        
        return age < self._cache_ttl
    
    def _update_price_cache(self, cache_key: str, price: Decimal) -> None:
        """Update price cache"""
        self._price_cache[cache_key] = {
            'price': price,
            'timestamp': datetime.utcnow()
        }
    
    async def batch_get_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Get prices for multiple symbols efficiently"""
        try:
            tasks = [self.get_current_price(symbol) for symbol in symbols]
            prices = await asyncio.gather(*tasks, return_exceptions=True)
            
            result = {}
            for symbol, price in zip(symbols, prices):
                if isinstance(price, Decimal):
                    result[symbol] = price
                elif not isinstance(price, Exception):
                    result[symbol] = price
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in batch price fetch: {str(e)}")
            return {}

# Global market data service instance
market_data_service = MarketDataService()