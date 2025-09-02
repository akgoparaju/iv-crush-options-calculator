"""
Cache Service - Redis caching layer for analysis results
Professional caching with TTL and intelligent invalidation
"""

import json
import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from redis import asyncio as aioredis
from redis.asyncio import Redis

from api.models.requests import AnalysisRequest
from api.models.responses import AnalysisResponse

logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis-based cache service for analysis results
    Provides intelligent caching with TTL and cache invalidation
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache service"""
        # Use environment variables with fallback
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client: Optional[Redis] = None
        self.default_ttl = int(os.getenv("REDIS_TTL_DEFAULT", "300"))  # 5 minutes for analysis results
        self.price_ttl = int(os.getenv("REDIS_TTL_PRICE", "60"))     # 1 minute for price data
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                retry_on_timeout=True,
                max_connections=10
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Cache service connected to Redis")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("✅ Cache service disconnected from Redis")
    
    def _generate_cache_key(self, request: AnalysisRequest) -> str:
        """
        Generate unique cache key for analysis request
        
        Args:
            request: Analysis request parameters
            
        Returns:
            Unique cache key string
        """
        # Create deterministic hash of request parameters
        request_dict = request.dict()
        
        # Sort dict for consistent hashing
        sorted_params = json.dumps(request_dict, sort_keys=True)
        
        # Generate SHA256 hash
        hash_object = hashlib.sha256(sorted_params.encode())
        hash_hex = hash_object.hexdigest()[:16]  # Use first 16 characters
        
        # Create readable cache key
        cache_key = f"analysis:{request.symbol}:{hash_hex}"
        
        return cache_key
    
    async def get_analysis(self, request: AnalysisRequest) -> Optional[AnalysisResponse]:
        """
        Retrieve analysis result from cache
        
        Args:
            request: Analysis request parameters
            
        Returns:
            Cached analysis response if found, None otherwise
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(request)
            
            # Get cached result
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                # Parse cached JSON
                cached_dict = json.loads(cached_data)
                
                # Convert back to AnalysisResponse
                cached_response = AnalysisResponse(**cached_dict)
                
                logger.debug(f"🎯 Cache hit for {request.symbol}")
                return cached_response
            
            logger.debug(f"🔍 Cache miss for {request.symbol}")
            return None
            
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None
    
    async def cache_analysis(self, request: AnalysisRequest, response: AnalysisResponse):
        """
        Cache analysis result with appropriate TTL
        
        Args:
            request: Analysis request parameters
            response: Analysis response to cache
        """
        if not self.redis_client:
            return
        
        try:
            cache_key = self._generate_cache_key(request)
            
            # Convert response to JSON-serializable dict
            response_dict = response.dict()
            
            # Add cache metadata
            response_dict["cached_at"] = datetime.utcnow().isoformat()
            
            # Serialize to JSON
            cached_data = json.dumps(response_dict, default=str)
            
            # Determine TTL based on analysis type
            ttl = self._get_cache_ttl(request)
            
            # Cache the result
            await self.redis_client.setex(cache_key, ttl, cached_data)
            
            logger.debug(f"🎯 Cached analysis for {request.symbol} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def _get_cache_ttl(self, request: AnalysisRequest) -> int:
        """
        Determine appropriate cache TTL based on request type
        
        Args:
            request: Analysis request parameters
            
        Returns:
            TTL in seconds
        """
        # Use demo data can be cached longer
        if request.use_demo:
            return 3600  # 1 hour for demo data
        
        # Real-time price data needs shorter TTL
        if request.include_trade_construction:
            return self.price_ttl  # 1 minute for trade construction
        
        # Basic analysis can be cached longer
        return self.default_ttl  # 5 minutes default
    
    async def invalidate_symbol(self, symbol: str):
        """
        Invalidate all cached results for a specific symbol
        
        Args:
            symbol: Stock symbol to invalidate
        """
        if not self.redis_client:
            return
        
        try:
            # Find all keys for this symbol
            pattern = f"analysis:{symbol.upper()}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                # Delete all matching keys
                await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Invalidated {len(keys)} cache entries for {symbol}")
            
        except Exception as e:
            logger.warning(f"Cache invalidation failed for {symbol}: {e}")
    
    async def clear_cache(self):
        """Clear all cached analysis results"""
        if not self.redis_client:
            return
        
        try:
            # Find all analysis cache keys
            keys = await self.redis_client.keys("analysis:*")
            
            if keys:
                # Delete all analysis cache keys
                await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Cleared {len(keys)} cache entries")
            
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary containing cache statistics
        """
        if not self.redis_client:
            return {"available": False}
        
        try:
            # Get Redis info
            info = await self.redis_client.info()
            
            # Count analysis cache keys
            analysis_keys = await self.redis_client.keys("analysis:*")
            
            stats = {
                "available": True,
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_keys": len(analysis_keys),
                "analysis_keys": len(analysis_keys),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
            
            # Calculate hit rate
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"]
            total_requests = hits + misses
            
            if total_requests > 0:
                stats["hit_rate"] = round((hits / total_requests) * 100, 2)
            else:
                stats["hit_rate"] = 0.0
            
            return stats
            
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {
                "available": True,
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """
        Check if cache service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            # Simple ping test
            await self.redis_client.ping()
            return True
        except Exception:
            return False