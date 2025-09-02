"""
WebSocket endpoints for real-time market data updates
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import yfinance as yf

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections and subscriptions"""
    
    def __init__(self):
        # Active connections
        self.active_connections: Set[WebSocket] = set()
        
        # Symbol subscriptions: symbol -> set of websockets
        self.symbol_subscriptions: Dict[str, Set[WebSocket]] = {}
        
        # Market status subscriptions
        self.market_status_subscriptions: Set[WebSocket] = set()
        
        # Price cache to avoid duplicate API calls
        self.price_cache: Dict[str, Dict] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_duration = 60  # seconds
        
        # Background task for price updates
        self.update_task = None
        self.update_interval = 30  # seconds

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Start price update task if this is the first connection
        if len(self.active_connections) == 1 and not self.update_task:
            self.update_task = asyncio.create_task(self._price_update_loop())

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        
        # Remove from all subscriptions
        for symbol_subs in self.symbol_subscriptions.values():
            symbol_subs.discard(websocket)
        self.market_status_subscriptions.discard(websocket)
        
        # Clean up empty subscriptions
        empty_symbols = [symbol for symbol, subs in self.symbol_subscriptions.items() if not subs]
        for symbol in empty_symbols:
            del self.symbol_subscriptions[symbol]
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
        # Stop price update task if no connections remain
        if not self.active_connections and self.update_task:
            self.update_task.cancel()
            self.update_task = None

    async def subscribe_to_symbol(self, websocket: WebSocket, symbol: str):
        """Subscribe a connection to symbol price updates"""
        symbol = symbol.upper()
        
        if symbol not in self.symbol_subscriptions:
            self.symbol_subscriptions[symbol] = set()
        
        self.symbol_subscriptions[symbol].add(websocket)
        logger.info(f"WebSocket subscribed to {symbol}")
        
        # Send current price if available
        if symbol in self.price_cache:
            await self._send_to_websocket(websocket, {
                'type': 'price_update',
                'data': self.price_cache[symbol],
                'timestamp': datetime.now(timezone.utc).isoformat()
            })

    async def subscribe_to_market_status(self, websocket: WebSocket):
        """Subscribe a connection to market status updates"""
        self.market_status_subscriptions.add(websocket)
        logger.info("WebSocket subscribed to market status")
        
        # Send current market status
        market_status = await self._get_market_status()
        await self._send_to_websocket(websocket, {
            'type': 'market_status',
            'data': market_status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    async def _price_update_loop(self):
        """Background task to fetch and broadcast price updates"""
        while self.active_connections:
            try:
                # Get all subscribed symbols
                symbols = list(self.symbol_subscriptions.keys())
                
                if symbols:
                    # Fetch prices for all symbols
                    await self._fetch_and_broadcast_prices(symbols)
                
                # Send market status updates
                if self.market_status_subscriptions:
                    market_status = await self._get_market_status()
                    await self._broadcast_market_status(market_status)
                
                # Wait before next update
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in price update loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _fetch_and_broadcast_prices(self, symbols: list):
        """Fetch prices for symbols and broadcast updates"""
        for symbol in symbols:
            try:
                # Check cache freshness
                now = datetime.now(timezone.utc)
                if (symbol in self.cache_timestamps and 
                    (now - self.cache_timestamps[symbol]).total_seconds() < self.cache_duration):
                    continue  # Skip if cache is still fresh
                
                # Fetch new price data
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if info:
                    # Calculate change and change percent
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                    previous_close = info.get('previousClose', 0)
                    
                    change = current_price - previous_close if previous_close else 0
                    change_percent = (change / previous_close * 100) if previous_close else 0
                    
                    price_data = {
                        'symbol': symbol,
                        'price': current_price,
                        'change': change,
                        'changePercent': change_percent,
                        'timestamp': now.isoformat(),
                        'source': 'yahoo_finance'
                    }
                    
                    # Update cache
                    self.price_cache[symbol] = price_data
                    self.cache_timestamps[symbol] = now
                    
                    # Broadcast to subscribers
                    await self._broadcast_price_update(symbol, price_data)
                    
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {e}")
                # Send error message to subscribers
                error_data = {
                    'symbol': symbol,
                    'error': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                await self._broadcast_error(symbol, error_data)

    async def _get_market_status(self):
        """Get current market status"""
        # This is a simplified implementation
        # In production, you'd get actual market hours from a reliable source
        now = datetime.now()
        
        # Simplified: assume market is open Monday-Friday, 9:30 AM - 4:00 PM ET
        is_weekend = now.weekday() >= 5
        hour = now.hour
        
        # Very basic market hours check (should be improved with actual market calendar)
        is_market_hours = 9 <= hour < 16
        is_open = not is_weekend and is_market_hours
        
        return {
            'isOpen': is_open,
            'timezone': 'America/New_York',
            'timestamp': now.isoformat()
        }

    async def _broadcast_price_update(self, symbol: str, price_data: dict):
        """Broadcast price update to all subscribers of a symbol"""
        if symbol in self.symbol_subscriptions:
            message = {
                'type': 'price_update',
                'data': price_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            disconnected = set()
            for websocket in self.symbol_subscriptions[symbol]:
                try:
                    await self._send_to_websocket(websocket, message)
                except:
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                await self.disconnect(ws)

    async def _broadcast_market_status(self, market_status: dict):
        """Broadcast market status to all subscribers"""
        message = {
            'type': 'market_status',
            'data': market_status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        disconnected = set()
        for websocket in self.market_status_subscriptions:
            try:
                await self._send_to_websocket(websocket, message)
            except:
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            await self.disconnect(ws)

    async def _broadcast_error(self, symbol: str, error_data: dict):
        """Broadcast error message to subscribers of a symbol"""
        if symbol in self.symbol_subscriptions:
            message = {
                'type': 'error',
                'data': error_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            disconnected = set()
            for websocket in self.symbol_subscriptions[symbol]:
                try:
                    await self._send_to_websocket(websocket, message)
                except:
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                await self.disconnect(ws)

    async def _send_to_websocket(self, websocket: WebSocket, message: dict):
        """Send a message to a specific websocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            raise

# Global connection manager instance
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time data"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get('type')
                message_data = message.get('data', {})
                
                if message_type == 'subscribe':
                    # Subscribe to symbol price updates
                    symbol = message_data.get('symbol')
                    if symbol:
                        await manager.subscribe_to_symbol(websocket, symbol)
                
                elif message_type == 'subscribe_market_status':
                    # Subscribe to market status updates
                    await manager.subscribe_to_market_status(websocket)
                
                elif message_type == 'ping':
                    # Respond to ping with pong
                    await websocket.send_text(json.dumps({
                        'type': 'pong',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }))
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)