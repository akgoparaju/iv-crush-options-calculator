"""
Portfolio Service for Phase 5.2
Business logic for portfolio tracking and management
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from decimal import Decimal
import asyncpg
from fastapi import HTTPException, status

from api.models.portfolio import (
    PortfolioInDB, PositionInDB, OptionLegInDB,
    PortfolioSummaryResponse, PortfolioDetailResponse, PositionResponse,
    RiskMetricsResponse, PerformanceMetricsResponse, PortfolioAnalyticsResponse,
    PositionStatus, StrategyType, Greeks, PnLCalculation
)
from api.services.database_service import DatabaseService
from api.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

class PortfolioService:
    """Service for portfolio tracking and management"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.market_data_service = MarketDataService()
        
        logger.info("📊 Portfolio service initialized")
    
    # =====================================================================================
    # Portfolio Management
    # =====================================================================================
    
    async def create_portfolio(self, user_id: UUID, name: str, description: Optional[str], 
                             initial_capital: Decimal) -> PortfolioInDB:
        """Create a new portfolio"""
        try:
            query = """
                INSERT INTO portfolios (user_id, name, description, initial_capital, 
                                     current_value, total_invested, available_cash, 
                                     created_at, updated_at)
                VALUES ($1, $2, $3, $4, $4, 0, $4, NOW(), NOW())
                RETURNING id, user_id, name, description, initial_capital, 
                         current_value, total_invested, available_cash, 
                         created_at, updated_at
            """
            
            async with self.db_service.get_connection() as conn:
                row = await conn.fetchrow(query, user_id, name, description, initial_capital)
                
                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create portfolio"
                    )
                
                portfolio = PortfolioInDB(**dict(row))
                logger.info(f"✅ Created portfolio: {name} for user {user_id}")
                return portfolio
                
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Portfolio name already exists"
            )
        except Exception as e:
            logger.error(f"❌ Error creating portfolio: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create portfolio"
            )
    
    async def get_user_portfolios(self, user_id: UUID) -> List[PortfolioSummaryResponse]:
        """Get all portfolios for a user"""
        try:
            query = """
                SELECT p.id, p.name, p.description, p.user_id, p.initial_capital,
                       p.current_value, p.total_invested, p.available_cash,
                       p.created_at, p.updated_at,
                       COUNT(pos.id) as positions_count,
                       COUNT(CASE WHEN pos.status = 'open' THEN 1 END) as open_positions_count
                FROM portfolios p
                LEFT JOIN positions pos ON p.id = pos.portfolio_id
                WHERE p.user_id = $1
                GROUP BY p.id, p.name, p.description, p.user_id, p.initial_capital,
                        p.current_value, p.total_invested, p.available_cash,
                        p.created_at, p.updated_at
                ORDER BY p.created_at DESC
            """
            
            async with self.db_service.get_connection() as conn:
                rows = await conn.fetch(query, user_id)
                
                portfolios = []
                for row in rows:
                    # Calculate P&L metrics
                    unrealized_pnl = row['current_value'] - row['total_invested']
                    realized_pnl = await self._get_portfolio_realized_pnl(row['id'], conn)
                    total_pnl = unrealized_pnl + realized_pnl
                    total_return_pct = (total_pnl / row['initial_capital'] * 100) if row['initial_capital'] > 0 else Decimal('0')
                    
                    portfolio = PortfolioSummaryResponse(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        user_id=row['user_id'],
                        initial_capital=row['initial_capital'],
                        current_value=row['current_value'],
                        total_invested=row['total_invested'],
                        available_cash=row['available_cash'],
                        unrealized_pnl=unrealized_pnl,
                        realized_pnl=realized_pnl,
                        total_pnl=total_pnl,
                        total_return_pct=total_return_pct,
                        positions_count=row['positions_count'],
                        open_positions_count=row['open_positions_count'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    portfolios.append(portfolio)
                
                return portfolios
                
        except Exception as e:
            logger.error(f"❌ Error fetching user portfolios: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch portfolios"
            )
    
    async def get_portfolio_detail(self, portfolio_id: UUID, user_id: UUID) -> PortfolioDetailResponse:
        """Get detailed portfolio information"""
        try:
            async with self.db_service.get_connection() as conn:
                # Get portfolio basic info
                portfolio_query = """
                    SELECT id, user_id, name, description, initial_capital,
                           current_value, total_invested, available_cash,
                           created_at, updated_at
                    FROM portfolios
                    WHERE id = $1 AND user_id = $2
                """
                portfolio_row = await conn.fetchrow(portfolio_query, portfolio_id, user_id)
                
                if not portfolio_row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Portfolio not found"
                    )
                
                # Get positions
                positions = await self._get_portfolio_positions(portfolio_id, conn)
                
                # Calculate P&L metrics
                unrealized_pnl = portfolio_row['current_value'] - portfolio_row['total_invested']
                realized_pnl = await self._get_portfolio_realized_pnl(portfolio_id, conn)
                total_pnl = unrealized_pnl + realized_pnl
                total_return_pct = (total_pnl / portfolio_row['initial_capital'] * 100) if portfolio_row['initial_capital'] > 0 else Decimal('0')
                
                # Calculate risk metrics
                risk_metrics = await self._calculate_risk_metrics(positions)
                
                # Calculate performance metrics
                performance_metrics = await self._calculate_performance_metrics(positions)
                
                return PortfolioDetailResponse(
                    id=portfolio_row['id'],
                    name=portfolio_row['name'],
                    description=portfolio_row['description'],
                    user_id=portfolio_row['user_id'],
                    initial_capital=portfolio_row['initial_capital'],
                    current_value=portfolio_row['current_value'],
                    total_invested=portfolio_row['total_invested'],
                    available_cash=portfolio_row['available_cash'],
                    unrealized_pnl=unrealized_pnl,
                    realized_pnl=realized_pnl,
                    total_pnl=total_pnl,
                    total_return_pct=total_return_pct,
                    positions=positions,
                    risk_metrics=risk_metrics,
                    performance_metrics=performance_metrics,
                    created_at=portfolio_row['created_at'],
                    updated_at=portfolio_row['updated_at']
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error fetching portfolio detail: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch portfolio details"
            )
    
    async def update_portfolio(self, portfolio_id: UUID, user_id: UUID, 
                             updates: Dict[str, Any]) -> PortfolioInDB:
        """Update portfolio information"""
        try:
            # Build dynamic update query
            set_clauses = []
            params = []
            param_idx = 1
            
            allowed_fields = ['name', 'description']
            for field, value in updates.items():
                if field in allowed_fields and value is not None:
                    set_clauses.append(f"{field} = ${param_idx}")
                    params.append(value)
                    param_idx += 1
            
            if not set_clauses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid fields to update"
                )
            
            # Add updated_at and WHERE clause parameters
            set_clauses.append(f"updated_at = ${param_idx}")
            params.append(datetime.utcnow())
            param_idx += 1
            
            params.extend([portfolio_id, user_id])  # For WHERE clause
            
            query = f"""
                UPDATE portfolios 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_idx} AND user_id = ${param_idx + 1}
                RETURNING id, user_id, name, description, initial_capital,
                         current_value, total_invested, available_cash,
                         created_at, updated_at
            """
            
            async with self.db_service.get_connection() as conn:
                row = await conn.fetchrow(query, *params)
                
                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Portfolio not found"
                    )
                
                portfolio = PortfolioInDB(**dict(row))
                logger.info(f"✅ Updated portfolio: {portfolio_id}")
                return portfolio
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error updating portfolio: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update portfolio"
            )
    
    async def delete_portfolio(self, portfolio_id: UUID, user_id: UUID) -> bool:
        """Delete a portfolio (soft delete)"""
        try:
            async with self.db_service.get_transaction() as conn:
                # Check if portfolio has open positions
                position_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM positions WHERE portfolio_id = $1 AND status = 'open'",
                    portfolio_id
                )
                
                if position_count > 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot delete portfolio with open positions"
                    )
                
                # Mark portfolio as deleted (add is_deleted column in future)
                result = await conn.execute(
                    "DELETE FROM portfolios WHERE id = $1 AND user_id = $2",
                    portfolio_id, user_id
                )
                
                if result == "DELETE 0":
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Portfolio not found"
                    )
                
                logger.info(f"✅ Deleted portfolio: {portfolio_id}")
                return True
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error deleting portfolio: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete portfolio"
            )
    
    # =====================================================================================
    # Position Management
    # =====================================================================================
    
    async def add_position(self, portfolio_id: UUID, user_id: UUID, 
                         position_data: Dict[str, Any]) -> PositionResponse:
        """Add a new position to portfolio"""
        try:
            async with self.db_service.get_transaction() as conn:
                # Verify portfolio ownership
                portfolio = await conn.fetchrow(
                    "SELECT id, available_cash FROM portfolios WHERE id = $1 AND user_id = $2",
                    portfolio_id, user_id
                )
                
                if not portfolio:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Portfolio not found"
                    )
                
                # Calculate position entry cost
                entry_cost = self._calculate_position_entry_cost(position_data['legs'])
                
                # Check available cash
                if entry_cost > portfolio['available_cash']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Insufficient funds for position"
                    )
                
                # Create position
                position_query = """
                    INSERT INTO positions (portfolio_id, symbol, strategy_type, status,
                                         entry_date, entry_cost, notes, created_at, updated_at)
                    VALUES ($1, $2, $3, 'open', $4, $5, $6, NOW(), NOW())
                    RETURNING id, portfolio_id, symbol, strategy_type, status,
                             entry_date, exit_date, entry_cost, exit_value, notes,
                             created_at, updated_at
                """
                
                position_row = await conn.fetchrow(
                    position_query,
                    portfolio_id,
                    position_data['symbol'],
                    position_data['strategy_type'],
                    position_data['entry_date'],
                    entry_cost,
                    position_data.get('notes')
                )
                
                position_id = position_row['id']
                
                # Create option legs
                for leg_data in position_data['legs']:
                    await conn.execute("""
                        INSERT INTO option_legs (position_id, option_type, strike_price,
                                               expiration_date, action, contracts, premium,
                                               created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
                    """, 
                    position_id,
                    leg_data['option_type'],
                    leg_data['strike_price'],
                    leg_data['expiration_date'],
                    leg_data['action'],
                    leg_data['contracts'],
                    leg_data['premium']
                    )
                
                # Update portfolio cash
                await conn.execute("""
                    UPDATE portfolios 
                    SET available_cash = available_cash - $1,
                        total_invested = total_invested + $1,
                        updated_at = NOW()
                    WHERE id = $2
                """, entry_cost, portfolio_id)
                
                # Get complete position data
                position = await self._get_position_by_id(position_id, conn)
                
                logger.info(f"✅ Added position {position_data['symbol']} to portfolio {portfolio_id}")
                return position
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error adding position: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add position"
            )
    
    async def close_position(self, position_id: UUID, user_id: UUID, 
                           exit_data: Dict[str, Any]) -> PositionResponse:
        """Close an existing position"""
        try:
            async with self.db_service.get_transaction() as conn:
                # Verify position ownership
                position_check = await conn.fetchrow("""
                    SELECT p.id, p.portfolio_id, p.status, p.entry_cost, port.user_id
                    FROM positions p
                    JOIN portfolios port ON p.portfolio_id = port.id
                    WHERE p.id = $1 AND port.user_id = $2
                """, position_id, user_id)
                
                if not position_check:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Position not found"
                    )
                
                if position_check['status'] != 'open':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Position is already closed"
                    )
                
                # Calculate exit value
                exit_value = exit_data.get('exit_premium', Decimal('0'))
                
                # Update position
                await conn.execute("""
                    UPDATE positions 
                    SET status = 'closed',
                        exit_date = $1,
                        exit_value = $2,
                        notes = COALESCE($3, notes),
                        updated_at = NOW()
                    WHERE id = $4
                """, exit_data['exit_date'], exit_value, exit_data.get('notes'), position_id)
                
                # Update portfolio cash (add exit value)
                await conn.execute("""
                    UPDATE portfolios 
                    SET available_cash = available_cash + $1,
                        updated_at = NOW()
                    WHERE id = $2
                """, exit_value, position_check['portfolio_id'])
                
                # Get updated position
                position = await self._get_position_by_id(position_id, conn)
                
                logger.info(f"✅ Closed position {position_id}")
                return position
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error closing position: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to close position"
            )
    
    # =====================================================================================
    # Analytics and Calculations
    # =====================================================================================
    
    async def get_portfolio_analytics(self, portfolio_id: UUID, user_id: UUID) -> PortfolioAnalyticsResponse:
        """Get comprehensive portfolio analytics"""
        try:
            async with self.db_service.get_connection() as conn:
                # Verify portfolio ownership
                portfolio = await conn.fetchrow(
                    "SELECT id FROM portfolios WHERE id = $1 AND user_id = $2",
                    portfolio_id, user_id
                )
                
                if not portfolio:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Portfolio not found"
                    )
                
                # Get analytics data
                daily_pnl = await self._get_daily_pnl(portfolio_id, conn)
                monthly_returns = await self._get_monthly_returns(portfolio_id, conn)
                strategy_breakdown = await self._get_strategy_breakdown(portfolio_id, conn)
                symbol_allocation = await self._get_symbol_allocation(portfolio_id, conn)
                expiration_calendar = await self._get_expiration_calendar(portfolio_id, conn)
                
                return PortfolioAnalyticsResponse(
                    daily_pnl=daily_pnl,
                    monthly_returns=monthly_returns,
                    strategy_breakdown=strategy_breakdown,
                    symbol_allocation=symbol_allocation,
                    expiration_calendar=expiration_calendar
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error fetching portfolio analytics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch analytics"
            )
    
    # =====================================================================================
    # Private Helper Methods
    # =====================================================================================
    
    async def _get_portfolio_positions(self, portfolio_id: UUID, conn) -> List[PositionResponse]:
        """Get all positions for a portfolio"""
        positions_query = """
            SELECT id, portfolio_id, symbol, strategy_type, status,
                   entry_date, exit_date, entry_cost, exit_value, notes,
                   created_at, updated_at
            FROM positions
            WHERE portfolio_id = $1
            ORDER BY entry_date DESC
        """
        
        position_rows = await conn.fetch(positions_query, portfolio_id)
        positions = []
        
        for row in position_rows:
            position = await self._build_position_response(dict(row), conn)
            positions.append(position)
        
        return positions
    
    async def _get_position_by_id(self, position_id: UUID, conn) -> PositionResponse:
        """Get position by ID"""
        position_query = """
            SELECT id, portfolio_id, symbol, strategy_type, status,
                   entry_date, exit_date, entry_cost, exit_value, notes,
                   created_at, updated_at
            FROM positions
            WHERE id = $1
        """
        
        row = await conn.fetchrow(position_query, position_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found"
            )
        
        return await self._build_position_response(dict(row), conn)
    
    async def _build_position_response(self, position_data: dict, conn) -> PositionResponse:
        """Build complete position response with legs and calculations"""
        position_id = position_data['id']
        
        # Get option legs
        legs_query = """
            SELECT id, position_id, option_type, strike_price, expiration_date,
                   action, contracts, premium, created_at, updated_at
            FROM option_legs
            WHERE position_id = $1
            ORDER BY created_at
        """
        
        leg_rows = await conn.fetch(legs_query, position_id)
        legs = [dict(row) for row in leg_rows]
        
        # Calculate current values and P&L
        current_value = await self._calculate_position_current_value(
            position_data['symbol'], legs
        )
        
        unrealized_pnl = current_value - position_data['entry_cost']
        realized_pnl = position_data['exit_value'] - position_data['entry_cost'] if position_data['exit_value'] else None
        total_pnl = realized_pnl if realized_pnl is not None else unrealized_pnl
        
        # Calculate days to expiration
        days_to_expiration = None
        if legs and position_data['status'] == 'open':
            earliest_expiry = min(leg['expiration_date'] for leg in legs)
            days_to_expiration = (earliest_expiry - date.today()).days
        
        return PositionResponse(
            id=position_data['id'],
            symbol=position_data['symbol'],
            strategy_type=position_data['strategy_type'],
            status=position_data['status'],
            legs=legs,  # Would need to convert to OptionLegResponse
            entry_date=position_data['entry_date'],
            exit_date=position_data['exit_date'],
            entry_cost=position_data['entry_cost'],
            exit_value=position_data['exit_value'],
            current_value=current_value,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            total_pnl=total_pnl,
            days_to_expiration=days_to_expiration,
            notes=position_data['notes'],
            created_at=position_data['created_at'],
            updated_at=position_data['updated_at']
        )
    
    def _calculate_position_entry_cost(self, legs: List[Dict]) -> Decimal:
        """Calculate total entry cost for a position"""
        total_cost = Decimal('0')
        
        for leg in legs:
            leg_cost = leg['contracts'] * leg['premium'] * 100  # Options are per 100 shares
            
            # Adjust for buy/sell actions
            if leg['action'].startswith('buy'):
                total_cost += leg_cost  # Debit
            else:
                total_cost -= leg_cost  # Credit
        
        return abs(total_cost)  # Return absolute value for cash management
    
    async def _calculate_position_current_value(self, symbol: str, legs: List[Dict]) -> Decimal:
        """Calculate current value of position using market data"""
        # This is a simplified calculation - in production, you'd use real options pricing
        # For now, return a placeholder value
        return Decimal('100.00')
    
    async def _get_portfolio_realized_pnl(self, portfolio_id: UUID, conn) -> Decimal:
        """Calculate realized P&L for portfolio"""
        result = await conn.fetchval("""
            SELECT COALESCE(SUM(exit_value - entry_cost), 0)
            FROM positions
            WHERE portfolio_id = $1 AND status = 'closed' AND exit_value IS NOT NULL
        """, portfolio_id)
        
        return result or Decimal('0')
    
    async def _calculate_risk_metrics(self, positions: List[PositionResponse]) -> RiskMetricsResponse:
        """Calculate portfolio risk metrics"""
        # Simplified risk calculation - in production, would use real Greeks
        return RiskMetricsResponse(
            total_delta=Decimal('0'),
            total_gamma=Decimal('0'),
            total_theta=Decimal('0'),
            total_vega=Decimal('0'),
            max_loss=Decimal('1000'),
            concentration_risk={}
        )
    
    async def _calculate_performance_metrics(self, positions: List[PositionResponse]) -> PerformanceMetricsResponse:
        """Calculate portfolio performance metrics"""
        if not positions:
            return PerformanceMetricsResponse(
                win_rate=Decimal('0'),
                avg_win=Decimal('0'),
                avg_loss=Decimal('0'),
                profit_factor=Decimal('0'),
                max_drawdown=Decimal('0'),
                trades_count=0,
                winning_trades=0,
                losing_trades=0
            )
        
        closed_positions = [p for p in positions if p.status == 'closed' and p.realized_pnl is not None]
        
        if not closed_positions:
            return PerformanceMetricsResponse(
                win_rate=Decimal('0'),
                avg_win=Decimal('0'),
                avg_loss=Decimal('0'),
                profit_factor=Decimal('0'),
                max_drawdown=Decimal('0'),
                trades_count=len(positions),
                winning_trades=0,
                losing_trades=0
            )
        
        winning_trades = [p for p in closed_positions if p.realized_pnl > 0]
        losing_trades = [p for p in closed_positions if p.realized_pnl <= 0]
        
        win_rate = Decimal(len(winning_trades)) / Decimal(len(closed_positions)) * 100 if closed_positions else Decimal('0')
        avg_win = sum(p.realized_pnl for p in winning_trades) / len(winning_trades) if winning_trades else Decimal('0')
        avg_loss = abs(sum(p.realized_pnl for p in losing_trades) / len(losing_trades)) if losing_trades else Decimal('0')
        
        profit_factor = avg_win / avg_loss if avg_loss > 0 else Decimal('0')
        
        return PerformanceMetricsResponse(
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=Decimal('0'),  # Would calculate from daily returns
            trades_count=len(closed_positions),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades)
        )
    
    # Analytics helper methods (simplified implementations)
    async def _get_daily_pnl(self, portfolio_id: UUID, conn) -> List[Dict[str, Any]]:
        """Get daily P&L data"""
        return []  # Placeholder
    
    async def _get_monthly_returns(self, portfolio_id: UUID, conn) -> List[Dict[str, Any]]:
        """Get monthly returns data"""
        return []  # Placeholder
    
    async def _get_strategy_breakdown(self, portfolio_id: UUID, conn) -> Dict[StrategyType, Dict[str, Any]]:
        """Get strategy breakdown"""
        return {}  # Placeholder
    
    async def _get_symbol_allocation(self, portfolio_id: UUID, conn) -> Dict[str, Decimal]:
        """Get symbol allocation"""
        return {}  # Placeholder
    
    async def _get_expiration_calendar(self, portfolio_id: UUID, conn) -> List[Dict[str, Any]]:
        """Get expiration calendar"""
        return []  # Placeholder

# Global portfolio service instance
portfolio_service = PortfolioService()