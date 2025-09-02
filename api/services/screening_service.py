"""
Screening Service for Phase 5.3
Market screening and alert system business logic
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from uuid import UUID, uuid4

from api.models.screening import (
    ScreenInDB, AlertInDB, ScreeningResultInDB, ScreeningResult, ScreenResponse,
    ScreeningResultsResponse, AlertResponse, AlertNotification, ScreeningAnalytics,
    MarketOverviewResponse, CreateScreenRequest, UpdateScreenRequest,
    CreateAlertRequest, UpdateAlertRequest, ScreeningCriteria, OpportunityRank,
    AlertType, ScreeningFrequency
)
from api.services.database_service import database_service
from api.services.market_data_service import market_data_service
from api.core.exceptions import ScreeningServiceError, ValidationError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class ScreeningService:
    """Service for market screening and alerts"""
    
    def __init__(self):
        self.db = database_service
        self.market_data = market_data_service
        self._screening_cache = {}
        self._cache_ttl = 300  # 5 minutes
        logger.info("📊 Screening service initialized")
    
    # =====================================================================================
    # Screen Management
    # =====================================================================================
    
    async def create_screen(self, user_id: UUID, screen_data: CreateScreenRequest) -> ScreenResponse:
        """Create a new market screen"""
        try:
            screen_id = uuid4()
            
            # Validate criteria
            await self._validate_screening_criteria(screen_data.criteria)
            
            # Convert criteria to JSON for storage
            criteria_json = [criterion.dict() for criterion in screen_data.criteria]
            
            query = """
                INSERT INTO screens (id, user_id, name, description, criteria, symbols, 
                                   frequency, is_active, alert_threshold, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                RETURNING *
            """
            
            async with self.db.get_connection() as conn:
                row = await conn.fetchrow(
                    query, screen_id, user_id, screen_data.name, screen_data.description,
                    json.dumps(criteria_json), screen_data.symbols, screen_data.frequency.value,
                    screen_data.is_active, screen_data.alert_threshold
                )
                
                if not row:
                    raise ScreeningServiceError("Failed to create screen")
                
                # Convert to response model
                return self._row_to_screen_response(row)
                
        except Exception as e:
            logger.error(f"❌ Error creating screen: {str(e)}")
            if isinstance(e, (ValidationError, ScreeningServiceError)):
                raise
            raise ScreeningServiceError(f"Failed to create screen: {str(e)}")
    
    async def get_user_screens(self, user_id: UUID, active_only: bool = False) -> List[ScreenResponse]:
        """Get all screens for a user"""
        try:
            query = """
                SELECT s.*, COUNT(sr.id) as results_count
                FROM screens s
                LEFT JOIN screening_results sr ON s.id = sr.screen_id 
                    AND sr.timestamp > NOW() - INTERVAL '24 hours'
                WHERE s.user_id = $1
            """
            
            if active_only:
                query += " AND s.is_active = true"
            
            query += " GROUP BY s.id ORDER BY s.updated_at DESC"
            
            async with self.db.get_connection() as conn:
                rows = await conn.fetch(query, user_id)
                return [self._row_to_screen_response(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Error fetching user screens: {str(e)}")
            raise ScreeningServiceError(f"Failed to fetch screens: {str(e)}")
    
    async def get_screen(self, screen_id: UUID, user_id: UUID) -> ScreenResponse:
        """Get specific screen by ID"""
        try:
            query = """
                SELECT s.*, COUNT(sr.id) as results_count
                FROM screens s
                LEFT JOIN screening_results sr ON s.id = sr.screen_id 
                    AND sr.timestamp > NOW() - INTERVAL '24 hours'
                WHERE s.id = $1 AND s.user_id = $2
                GROUP BY s.id
            """
            
            async with self.db.get_connection() as conn:
                row = await conn.fetchrow(query, screen_id, user_id)
                
                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Screen not found"
                    )
                
                return self._row_to_screen_response(row)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error fetching screen: {str(e)}")
            raise ScreeningServiceError(f"Failed to fetch screen: {str(e)}")
    
    async def update_screen(self, screen_id: UUID, user_id: UUID, 
                          updates: UpdateScreenRequest) -> ScreenResponse:
        """Update existing screen"""
        try:
            # Build dynamic update query
            set_clauses = []
            values = []
            param_count = 1
            
            if updates.name is not None:
                set_clauses.append(f"name = ${param_count}")
                values.append(updates.name)
                param_count += 1
            
            if updates.description is not None:
                set_clauses.append(f"description = ${param_count}")
                values.append(updates.description)
                param_count += 1
            
            if updates.criteria is not None:
                await self._validate_screening_criteria(updates.criteria)
                criteria_json = [criterion.dict() for criterion in updates.criteria]
                set_clauses.append(f"criteria = ${param_count}")
                values.append(json.dumps(criteria_json))
                param_count += 1
            
            if updates.symbols is not None:
                set_clauses.append(f"symbols = ${param_count}")
                values.append(updates.symbols)
                param_count += 1
            
            if updates.frequency is not None:
                set_clauses.append(f"frequency = ${param_count}")
                values.append(updates.frequency.value)
                param_count += 1
            
            if updates.is_active is not None:
                set_clauses.append(f"is_active = ${param_count}")
                values.append(updates.is_active)
                param_count += 1
            
            if updates.alert_threshold is not None:
                set_clauses.append(f"alert_threshold = ${param_count}")
                values.append(updates.alert_threshold)
                param_count += 1
            
            if not set_clauses:
                return await self.get_screen(screen_id, user_id)
            
            set_clauses.append("updated_at = NOW()")
            
            query = f"""
                UPDATE screens 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count} AND user_id = ${param_count + 1}
                RETURNING *
            """
            values.extend([screen_id, user_id])
            
            async with self.db.get_connection() as conn:
                row = await conn.fetchrow(query, *values)
                
                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Screen not found"
                    )
                
                return self._row_to_screen_response(row)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error updating screen: {str(e)}")
            raise ScreeningServiceError(f"Failed to update screen: {str(e)}")
    
    async def delete_screen(self, screen_id: UUID, user_id: UUID) -> bool:
        """Delete a screen"""
        try:
            query = """
                DELETE FROM screens 
                WHERE id = $1 AND user_id = $2
                RETURNING id
            """
            
            async with self.db.get_connection() as conn:
                async with conn.transaction():
                    # Delete related data first
                    await conn.execute(
                        "DELETE FROM screening_results WHERE screen_id = $1", screen_id
                    )
                    await conn.execute(
                        "DELETE FROM alerts WHERE screen_id = $1", screen_id
                    )
                    
                    # Delete screen
                    row = await conn.fetchrow(query, screen_id, user_id)
                    return row is not None
                    
        except Exception as e:
            logger.error(f"❌ Error deleting screen: {str(e)}")
            raise ScreeningServiceError(f"Failed to delete screen: {str(e)}")
    
    # =====================================================================================
    # Screening Execution
    # =====================================================================================
    
    async def run_screen(self, screen_id: UUID, user_id: UUID) -> ScreeningResultsResponse:
        """Execute a market screen"""
        try:
            start_time = datetime.utcnow()
            
            # Get screen configuration
            screen = await self.get_screen(screen_id, user_id)
            
            # Determine symbols to screen
            symbols = await self._get_symbols_to_screen(screen.symbols)
            
            # Execute screening
            results = []
            for symbol in symbols:
                try:
                    result = await self._screen_symbol(symbol, screen.criteria)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to screen {symbol}: {str(e)}")
                    continue
            
            # Sort by score
            results.sort(key=lambda r: r.score, reverse=True)
            
            # Store results
            await self._store_screening_results(screen_id, results)
            
            # Update screen last_run
            await self._update_screen_last_run(screen_id)
            
            # Check for alerts
            if len(results) >= screen.alert_threshold:
                await self._trigger_alerts(screen_id, results)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ScreeningResultsResponse(
                screen_id=screen_id,
                screen_name=screen.name,
                total_symbols=len(symbols),
                opportunities_found=len(results),
                results=results,
                execution_time=execution_time,
                timestamp=start_time,
                next_run=self._calculate_next_run(screen.frequency)
            )
            
        except Exception as e:
            logger.error(f"❌ Error running screen: {str(e)}")
            raise ScreeningServiceError(f"Failed to run screen: {str(e)}")
    
    async def get_screening_results(self, screen_id: UUID, user_id: UUID,
                                  limit: int = 50) -> List[ScreeningResult]:
        """Get latest screening results"""
        try:
            query = """
                SELECT * FROM screening_results 
                WHERE screen_id = $1 
                AND screen_id IN (SELECT id FROM screens WHERE user_id = $2)
                ORDER BY timestamp DESC, score DESC
                LIMIT $3
            """
            
            async with self.db.get_connection() as conn:
                rows = await conn.fetch(query, screen_id, user_id, limit)
                return [self._row_to_screening_result(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Error fetching screening results: {str(e)}")
            raise ScreeningServiceError(f"Failed to fetch results: {str(e)}")
    
    # =====================================================================================
    # Alert Management
    # =====================================================================================
    
    async def create_alert(self, user_id: UUID, alert_data: CreateAlertRequest) -> AlertResponse:
        """Create a new alert configuration"""
        try:
            # Verify screen ownership
            await self.get_screen(alert_data.screen_id, user_id)
            
            alert_id = uuid4()
            
            query = """
                INSERT INTO alerts (id, screen_id, user_id, alert_types, conditions, 
                                  is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                RETURNING *
            """
            
            async with self.db.get_connection() as conn:
                row = await conn.fetchrow(
                    query, alert_id, alert_data.screen_id, user_id,
                    [t.value for t in alert_data.alert_types],
                    json.dumps(alert_data.conditions), alert_data.is_active
                )
                
                return self._row_to_alert_response(row)
                
        except Exception as e:
            logger.error(f"❌ Error creating alert: {str(e)}")
            raise ScreeningServiceError(f"Failed to create alert: {str(e)}")
    
    async def get_user_alerts(self, user_id: UUID) -> List[AlertResponse]:
        """Get all alerts for a user"""
        try:
            query = """
                SELECT a.* FROM alerts a
                JOIN screens s ON a.screen_id = s.id
                WHERE s.user_id = $1
                ORDER BY a.created_at DESC
            """
            
            async with self.db.get_connection() as conn:
                rows = await conn.fetch(query, user_id)
                return [self._row_to_alert_response(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Error fetching alerts: {str(e)}")
            raise ScreeningServiceError(f"Failed to fetch alerts: {str(e)}")
    
    # =====================================================================================
    # Analytics
    # =====================================================================================
    
    async def get_screening_analytics(self, screen_id: UUID, user_id: UUID,
                                    days: int = 30) -> ScreeningAnalytics:
        """Get screening performance analytics"""
        try:
            # Verify screen ownership
            screen = await self.get_screen(screen_id, user_id)
            
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get analytics data
            query = """
                SELECT 
                    COUNT(*) as total_runs,
                    AVG(opportunities_count) as avg_opportunities,
                    AVG(execution_time) as avg_execution_time,
                    COUNT(*) FILTER (WHERE opportunities_count > 0) as successful_runs
                FROM (
                    SELECT 
                        DATE_TRUNC('hour', timestamp) as run_time,
                        COUNT(*) as opportunities_count,
                        AVG(EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp)))) as execution_time
                    FROM screening_results
                    WHERE screen_id = $1 AND timestamp >= $2
                    GROUP BY DATE_TRUNC('hour', timestamp)
                ) runs
            """
            
            async with self.db.get_connection() as conn:
                analytics_row = await conn.fetchrow(query, screen_id, since_date)
                
                # Get symbol frequency
                symbol_query = """
                    SELECT symbol, COUNT(*) as frequency
                    FROM screening_results
                    WHERE screen_id = $1 AND timestamp >= $2
                    GROUP BY symbol
                    ORDER BY frequency DESC
                    LIMIT 10
                """
                symbol_rows = await conn.fetch(symbol_query, screen_id, since_date)
                
                total_runs = analytics_row['total_runs'] or 0
                successful_runs = analytics_row['successful_runs'] or 0
                
                return ScreeningAnalytics(
                    screen_id=screen_id,
                    screen_name=screen.name,
                    total_runs=total_runs,
                    avg_opportunities_per_run=float(analytics_row['avg_opportunities'] or 0),
                    success_rate=float(successful_runs / total_runs) if total_runs > 0 else 0,
                    avg_execution_time=float(analytics_row['avg_execution_time'] or 0),
                    most_frequent_symbols=[row['symbol'] for row in symbol_rows],
                    performance_by_criteria={},  # Would be implemented based on specific needs
                    historical_performance=[],   # Would be implemented based on specific needs
                    recommendations=self._generate_recommendations(screen, analytics_row)
                )
                
        except Exception as e:
            logger.error(f"❌ Error generating analytics: {str(e)}")
            raise ScreeningServiceError(f"Failed to generate analytics: {str(e)}")
    
    # =====================================================================================
    # Private Methods
    # =====================================================================================
    
    async def _validate_screening_criteria(self, criteria: List[Any]) -> None:
        """Validate screening criteria"""
        if not criteria:
            raise ValidationError("At least one screening criterion is required")
        
        for criterion in criteria:
            if hasattr(criterion, 'criteria'):
                if criterion.criteria not in ScreeningCriteria:
                    raise ValidationError(f"Invalid screening criteria: {criterion.criteria}")
    
    async def _get_symbols_to_screen(self, specific_symbols: Optional[List[str]]) -> List[str]:
        """Get list of symbols to screen"""
        if specific_symbols:
            return specific_symbols
        
        # Default symbol universe (top liquid options stocks)
        return [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'SPY', 'QQQ', 'IWM', 'TLT', 'GLD', 'UBER', 'SQ', 'ROKU',
            'SHOP', 'ZM', 'DOCU', 'CRM', 'ADBE', 'NOW', 'WDAY', 'OKTA'
        ]
    
    async def _screen_symbol(self, symbol: str, criteria: List[Any]) -> Optional[ScreeningResult]:
        """Screen a single symbol against criteria"""
        try:
            # Get market data for symbol
            current_price = await self.market_data.get_current_price(symbol)
            if not current_price:
                return None
            
            iv = await self.market_data.get_implied_volatility(symbol)
            
            # Calculate screening scores
            criteria_scores = {}
            total_score = 0
            total_weight = 0
            
            for criterion in criteria:
                score = await self._evaluate_criterion(symbol, criterion, current_price, iv)
                criteria_scores[criterion.criteria.value] = score
                total_score += score * criterion.weight
                total_weight += criterion.weight
            
            # Calculate final score
            final_score = (total_score / total_weight) if total_weight > 0 else 0
            
            # Determine rank
            if final_score >= 80:
                rank = OpportunityRank.EXCELLENT
            elif final_score >= 60:
                rank = OpportunityRank.GOOD
            elif final_score >= 40:
                rank = OpportunityRank.FAIR
            else:
                rank = OpportunityRank.POOR
            
            # Only return if meets minimum threshold
            if final_score < 40:
                return None
            
            return ScreeningResult(
                symbol=symbol,
                current_price=current_price,
                score=final_score,
                rank=rank,
                criteria_scores=criteria_scores,
                market_data={
                    'implied_volatility': float(iv) if iv else 0,
                    'price': float(current_price)
                },
                opportunity_details={
                    'recommendation': rank.value,
                    'confidence': min(final_score / 100, 1.0)
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Error screening {symbol}: {str(e)}")
            return None
    
    async def _evaluate_criterion(self, symbol: str, criterion: Any, 
                                current_price: Decimal, iv: Optional[Decimal]) -> float:
        """Evaluate a single screening criterion"""
        try:
            criteria_type = criterion.criteria
            operator = criterion.operator
            value = criterion.value
            
            if criteria_type == ScreeningCriteria.IV_PERCENTILE:
                # Simplified IV percentile calculation
                if iv:
                    iv_percentile = min(float(iv) * 100, 100)
                    return self._compare_values(iv_percentile, operator, value)
                return 0
            
            elif criteria_type == ScreeningCriteria.PRICE_RANGE:
                price_value = float(current_price)
                return self._compare_values(price_value, operator, value)
            
            elif criteria_type == ScreeningCriteria.VOLUME:
                # Mock volume data - in production would get real volume
                mock_volume = 1500000  # 1.5M average
                return self._compare_values(mock_volume, operator, value)
            
            elif criteria_type == ScreeningCriteria.IV_RV_RATIO:
                if iv:
                    # Mock realized volatility - in production would calculate from price history
                    mock_rv = float(iv) * 0.8  # IV typically higher than RV
                    iv_rv_ratio = float(iv) / mock_rv if mock_rv > 0 else 0
                    return self._compare_values(iv_rv_ratio, operator, value)
                return 0
            
            # Add more criteria evaluations as needed
            return 50  # Default neutral score
            
        except Exception as e:
            logger.warning(f"⚠️ Error evaluating criterion {criteria_type}: {str(e)}")
            return 0
    
    def _compare_values(self, actual: float, operator: str, expected: Any) -> float:
        """Compare actual value against expected using operator"""
        try:
            if operator == '>=':
                return 100 if actual >= expected else 0
            elif operator == '<=':
                return 100 if actual <= expected else 0
            elif operator == '>':
                return 100 if actual > expected else 0
            elif operator == '<':
                return 100 if actual < expected else 0
            elif operator == '==':
                return 100 if abs(actual - expected) < 0.01 else 0
            elif operator == '!=':
                return 100 if abs(actual - expected) >= 0.01 else 0
            elif operator == 'between' and isinstance(expected, list) and len(expected) == 2:
                return 100 if expected[0] <= actual <= expected[1] else 0
            
            return 0
            
        except Exception:
            return 0
    
    async def _store_screening_results(self, screen_id: UUID, results: List[ScreeningResult]) -> None:
        """Store screening results in database"""
        if not results:
            return
        
        try:
            query = """
                INSERT INTO screening_results 
                (id, screen_id, symbol, current_price, score, rank, criteria_scores, 
                 market_data, opportunity_details, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """
            
            async with self.db.get_connection() as conn:
                async with conn.transaction():
                    for result in results:
                        await conn.execute(
                            query, uuid4(), screen_id, result.symbol, result.current_price,
                            result.score, result.rank.value, json.dumps(result.criteria_scores),
                            json.dumps(result.market_data), json.dumps(result.opportunity_details),
                            result.timestamp
                        )
                        
        except Exception as e:
            logger.error(f"❌ Error storing results: {str(e)}")
            # Don't raise - screening can continue without storage
    
    async def _update_screen_last_run(self, screen_id: UUID) -> None:
        """Update screen last run timestamp"""
        try:
            query = "UPDATE screens SET last_run = NOW() WHERE id = $1"
            async with self.db.get_connection() as conn:
                await conn.execute(query, screen_id)
        except Exception as e:
            logger.warning(f"⚠️ Failed to update last run: {str(e)}")
    
    async def _trigger_alerts(self, screen_id: UUID, results: List[ScreeningResult]) -> None:
        """Trigger alerts for screening results"""
        try:
            # Get active alerts for this screen
            query = """
                SELECT a.*, s.name as screen_name, s.user_id
                FROM alerts a
                JOIN screens s ON a.screen_id = s.id
                WHERE a.screen_id = $1 AND a.is_active = true
            """
            
            async with self.db.get_connection() as conn:
                alert_rows = await conn.fetch(query, screen_id)
                
                for alert_row in alert_rows:
                    # Check if alert conditions are met
                    if self._check_alert_conditions(alert_row['conditions'], results):
                        await self._send_alert_notifications(alert_row, results)
                        
                        # Update trigger count
                        await conn.execute(
                            "UPDATE alerts SET last_triggered = NOW(), trigger_count = trigger_count + 1 WHERE id = $1",
                            alert_row['id']
                        )
                        
        except Exception as e:
            logger.error(f"❌ Error triggering alerts: {str(e)}")
    
    def _check_alert_conditions(self, conditions: Dict[str, Any], results: List[ScreeningResult]) -> bool:
        """Check if alert conditions are met"""
        # Simplified condition checking - in production would be more sophisticated
        min_opportunities = conditions.get('min_opportunities', 1)
        min_score = conditions.get('min_score', 60)
        
        qualifying_results = [r for r in results if r.score >= min_score]
        return len(qualifying_results) >= min_opportunities
    
    async def _send_alert_notifications(self, alert_row: Dict[str, Any], 
                                      results: List[ScreeningResult]) -> None:
        """Send alert notifications"""
        try:
            # In production, would integrate with notification services
            alert_types = alert_row['alert_types']
            
            logger.info(f"📢 Alert triggered for screen {alert_row['screen_name']}")
            logger.info(f"   User: {alert_row['user_id']}")
            logger.info(f"   Opportunities: {len(results)}")
            logger.info(f"   Alert types: {alert_types}")
            
            # Mock notification sending
            if 'email' in alert_types:
                logger.info("📧 Email notification sent")
            if 'push' in alert_types:
                logger.info("📱 Push notification sent")
            if 'in_app' in alert_types:
                logger.info("🔔 In-app notification created")
                
        except Exception as e:
            logger.error(f"❌ Error sending notifications: {str(e)}")
    
    def _calculate_next_run(self, frequency: ScreeningFrequency) -> Optional[datetime]:
        """Calculate next run time based on frequency"""
        now = datetime.utcnow()
        
        frequency_map = {
            ScreeningFrequency.REAL_TIME: timedelta(seconds=30),
            ScreeningFrequency.EVERY_5_MIN: timedelta(minutes=5),
            ScreeningFrequency.EVERY_15_MIN: timedelta(minutes=15),
            ScreeningFrequency.EVERY_30_MIN: timedelta(minutes=30),
            ScreeningFrequency.HOURLY: timedelta(hours=1),
            ScreeningFrequency.DAILY: timedelta(days=1),
            ScreeningFrequency.WEEKLY: timedelta(weeks=1)
        }
        
        delta = frequency_map.get(frequency, timedelta(hours=1))
        return now + delta
    
    def _generate_recommendations(self, screen: ScreenResponse, 
                                analytics_data: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        success_rate = analytics_data.get('successful_runs', 0) / max(analytics_data.get('total_runs', 1), 1)
        
        if success_rate < 0.3:
            recommendations.append("Consider relaxing screening criteria - low success rate")
        
        if analytics_data.get('avg_execution_time', 0) > 60:
            recommendations.append("Consider reducing symbol universe - slow execution")
        
        if not screen.is_active:
            recommendations.append("Screen is inactive - enable to continue monitoring")
        
        if len(screen.criteria) > 5:
            recommendations.append("Consider reducing criteria count for better performance")
        
        return recommendations
    
    def _row_to_screen_response(self, row: Dict[str, Any]) -> ScreenResponse:
        """Convert database row to ScreenResponse"""
        from api.models.screening import ScreeningCriteriaFilter
        
        # Parse criteria JSON
        criteria_data = json.loads(row['criteria']) if row['criteria'] else []
        criteria = [ScreeningCriteriaFilter(**c) for c in criteria_data]
        
        return ScreenResponse(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            description=row['description'],
            criteria=criteria,
            symbols=row['symbols'],
            frequency=ScreeningFrequency(row['frequency']),
            is_active=row['is_active'],
            alert_threshold=row['alert_threshold'],
            last_run=row['last_run'],
            results_count=row.get('results_count', 0),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def _row_to_alert_response(self, row: Dict[str, Any]) -> AlertResponse:
        """Convert database row to AlertResponse"""
        return AlertResponse(
            id=row['id'],
            screen_id=row['screen_id'],
            user_id=row['user_id'],
            alert_types=[AlertType(t) for t in row['alert_types']],
            conditions=json.loads(row['conditions']) if row['conditions'] else {},
            is_active=row['is_active'],
            last_triggered=row['last_triggered'],
            trigger_count=row['trigger_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def _row_to_screening_result(self, row: Dict[str, Any]) -> ScreeningResult:
        """Convert database row to ScreeningResult"""
        return ScreeningResult(
            symbol=row['symbol'],
            current_price=row['current_price'],
            score=row['score'],
            rank=OpportunityRank(row['rank']),
            criteria_scores=json.loads(row['criteria_scores']) if row['criteria_scores'] else {},
            market_data=json.loads(row['market_data']) if row['market_data'] else {},
            opportunity_details=json.loads(row['opportunity_details']) if row['opportunity_details'] else {},
            timestamp=row['timestamp']
        )

# Global screening service instance
screening_service = ScreeningService()