"""
Database Service for Phase 5.1+
PostgreSQL connection management with asyncpg
"""

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncpg
from asyncpg import Pool, Connection

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for PostgreSQL connection management"""
    
    def __init__(self):
        # Database configuration
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:password@localhost:5432/options_trading"
        )
        self.min_connections = int(os.getenv("DB_MIN_CONNECTIONS", "5"))
        self.max_connections = int(os.getenv("DB_MAX_CONNECTIONS", "20"))
        self.connection_timeout = int(os.getenv("DB_CONNECTION_TIMEOUT", "10"))
        
        # Connection pool
        self.pool: Optional[Pool] = None
        self._lock = asyncio.Lock()
        
        logger.info("🗄️ Database service initialized")
    
    async def connect(self) -> None:
        """Initialize database connection pool"""
        if self.pool:
            return
        
        async with self._lock:
            if self.pool:  # Double-check pattern
                return
            
            try:
                # Create connection pool
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=self.min_connections,
                    max_size=self.max_connections,
                    command_timeout=self.connection_timeout,
                    server_settings={
                        'application_name': 'options_trading_api',
                        'timezone': 'UTC'
                    }
                )
                
                # Test connection
                async with self.pool.acquire() as conn:
                    result = await conn.fetchval("SELECT 1")
                    if result != 1:
                        raise Exception("Database connection test failed")
                
                logger.info("✅ Database connection pool established")
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to database: {str(e)}")
                self.pool = None
                raise
    
    async def disconnect(self) -> None:
        """Close database connection pool"""
        if self.pool:
            async with self._lock:
                if self.pool:
                    await self.pool.close()
                    self.pool = None
                    logger.info("🔌 Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get database connection from pool"""
        if not self.pool:
            await self.connect()
        
        if not self.pool:
            raise Exception("Database connection pool not available")
        
        async with self.pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                # Log the error but let it propagate
                logger.error(f"❌ Database operation error: {str(e)}")
                raise
    
    @asynccontextmanager
    async def get_transaction(self) -> AsyncGenerator[Connection, None]:
        """Get database transaction"""
        async with self.get_connection() as conn:
            async with conn.transaction():
                yield conn
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"❌ Database health check failed: {str(e)}")
            return False
    
    async def get_pool_stats(self) -> dict:
        """Get connection pool statistics"""
        if not self.pool:
            return {"status": "disconnected"}
        
        return {
            "status": "connected",
            "size": self.pool.get_size(),
            "min_size": self.pool.get_min_size(),
            "max_size": self.pool.get_max_size(),
            "idle_size": self.pool.get_idle_size()
        }

# Global database service instance
database_service = DatabaseService()