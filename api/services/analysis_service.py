"""
Analysis Service - Business logic layer for options analysis
Professional service wrapping existing options_trader functionality
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any, Optional
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.requests import AnalysisRequest
from api.models.responses import (
    AnalysisOverview, ModuleStatus, EarningsAnalysis, 
    TradeConstruction, PositionSizing, TradingDecision
)

logger = logging.getLogger(__name__)

def convert_numpy_types(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

class AnalysisService:
    """
    Service class that wraps the existing options_trader functionality
    Provides async interface and professional error handling
    """
    
    def __init__(self):
        """Initialize the analysis service"""
        self.options_trader_available = False
        self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize the options_trader backend"""
        try:
            # Import the existing analysis function
            from options_trader import analyze_symbol
            self.analyze_symbol_func = analyze_symbol
            self.options_trader_available = True
            logger.info("✅ Options trader backend initialized")
        except ImportError as e:
            logger.error(f"❌ Failed to import options_trader: {e}")
            self.options_trader_available = False
    
    async def analyze_symbol(self, request: AnalysisRequest) -> Dict[str, Any]:
        """
        Perform comprehensive options analysis
        
        Args:
            request: Analysis request parameters
            
        Returns:
            Dict containing structured analysis results
        """
        if not self.options_trader_available:
            raise RuntimeError("Options trader backend not available")
        
        try:
            # Convert API request to backend parameters
            analysis_params = self._convert_request_to_params(request)
            
            # Execute analysis in thread pool (since backend is synchronous)
            loop = asyncio.get_event_loop()
            raw_result = await loop.run_in_executor(
                None, 
                self._execute_analysis,
                analysis_params
            )
            
            # Convert backend result to API response format
            structured_result = self._structure_analysis_result(raw_result, request)
            
            return structured_result
            
        except Exception as e:
            logger.error(f"Analysis failed for {request.symbol}: {str(e)}")
            raise
    
    def _convert_request_to_params(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Convert API request to backend function parameters"""
        params = {
            "symbol": request.symbol,
            "expirations_to_check": request.expirations_to_check,
            "include_earnings": request.include_earnings,
            "include_trade_construction": request.include_trade_construction,
            "include_position_sizing": request.include_position_sizing,
            "include_trading_decision": request.include_trading_decision,
            "trade_structure": request.trade_structure,
            "use_demo": request.use_demo
        }
        
        # Add account parameters if provided
        if request.account_size is not None:
            params["account_size"] = request.account_size
        
        if request.risk_per_trade is not None:
            params["risk_per_trade"] = request.risk_per_trade
        
        return params
    
    def _execute_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the analysis using existing backend (synchronous)"""
        try:
            # Call the existing analyze_symbol function
            result = self.analyze_symbol_func(**params)
            logger.debug(f"Raw analysis result - price: {result.get('price')}, source: {result.get('price_source')}")
            return result
        except Exception as e:
            logger.error(f"Backend analysis failed: {str(e)}")
            raise
    
    def _structure_analysis_result(self, raw_result: Dict[str, Any], request: AnalysisRequest) -> Dict[str, Any]:
        """Structure the backend result into API response format"""
        try:
            # Extract basic information - handle both old and new field names
            symbol = raw_result.get("symbol", request.symbol)
            # Backend returns 'price' but we expect 'current_price'
            current_price = raw_result.get("current_price", raw_result.get("price", 0.0))
            # Backend returns 'price_source' but we expect 'data_source'
            data_source = raw_result.get("data_source", raw_result.get("price_source", "unknown"))
            
            # Create structured response
            structured_result = {
                "overview": AnalysisOverview(
                    symbol=symbol,
                    current_price=current_price,
                    data_source=data_source,
                    analysis_mode="DEMO" if request.use_demo else "LIVE",
                    expirations_checked=request.expirations_to_check,
                    timestamp=datetime.utcnow()
                ).dict(),
                
                "module_status": ModuleStatus(
                    earnings_analysis=request.include_earnings,
                    trade_construction=request.include_trade_construction,
                    position_sizing=request.include_position_sizing,
                    trading_decision=request.include_trading_decision
                ).dict()
            }
            
            # Add earnings analysis if included
            if request.include_earnings and "earnings_analysis" in raw_result:
                structured_result["earnings_analysis"] = self._structure_earnings_analysis(
                    raw_result["earnings_analysis"]
                )
            
            # Add trade construction if included
            if request.include_trade_construction and "trade_construction" in raw_result:
                structured_result["trade_construction"] = self._structure_trade_construction(
                    raw_result["trade_construction"]
                )
            
            # Add position sizing if included
            if request.include_position_sizing and "position_sizing" in raw_result:
                structured_result["position_sizing"] = self._structure_position_sizing(
                    raw_result["position_sizing"]
                )
            
            # Add trading decision if included
            if request.include_trading_decision and "trading_decision" in raw_result:
                structured_result["trading_decision"] = self._structure_trading_decision(
                    raw_result["trading_decision"]
                )
            
            # Add data freshness if available
            if "data_timestamp" in raw_result:
                structured_result["data_freshness"] = raw_result["data_timestamp"]
            
            return structured_result
            
        except Exception as e:
            logger.error(f"Failed to structure analysis result: {str(e)}")
            raise
    
    def _structure_earnings_analysis(self, earnings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure earnings analysis data"""
        return EarningsAnalysis(
            next_earnings_date=earnings_data.get("next_earnings_date"),
            days_to_earnings=earnings_data.get("days_to_earnings"),
            earnings_timing=earnings_data.get("earnings_timing"),
            entry_window=earnings_data.get("entry_window"),
            exit_window=earnings_data.get("exit_window"),
            trading_signals=earnings_data.get("trading_signals")
        ).dict()
    
    def _structure_trade_construction(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure trade construction data"""
        return TradeConstruction(
            calendar_trade=trade_data.get("calendar_trade"),
            straddle_construction=trade_data.get("straddle_construction"),
            quality_assessment=trade_data.get("quality_assessment"),
            greeks_analysis=trade_data.get("greeks_analysis"),
            pnl_analysis=trade_data.get("pnl_analysis")
        ).dict()
    
    def _structure_position_sizing(self, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure position sizing data"""
        # Convert numpy types to native Python types
        clean_position_data = convert_numpy_types(position_data)
        
        return PositionSizing(
            recommended_position=clean_position_data.get("recommended_position"),
            kelly_analysis=clean_position_data.get("kelly_analysis"),
            risk_assessment=clean_position_data.get("risk_assessment"),
            portfolio_impact=clean_position_data.get("portfolio_impact")
        ).dict()
    
    def _structure_trading_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure trading decision data"""
        # Convert numpy types to native Python types
        clean_decision_data = convert_numpy_types(decision_data)
        
        # Ensure signal_strength is converted to string if numeric
        signal_strength = clean_decision_data.get("signal_strength")
        if signal_strength is not None and not isinstance(signal_strength, str):
            signal_strength = str(signal_strength)
        
        return TradingDecision(
            decision=clean_decision_data.get("decision"),
            confidence=clean_decision_data.get("confidence"),
            signal_strength=signal_strength,
            reasoning=clean_decision_data.get("reasoning", []),
            risk_warnings=clean_decision_data.get("risk_warnings", [])
        ).dict()
    
    async def get_basic_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get basic symbol information for validation
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            Dict containing basic symbol information
        """
        if not self.options_trader_available:
            raise RuntimeError("Options trader backend not available")
        
        try:
            # Create minimal analysis request for basic info
            basic_request = AnalysisRequest(
                symbol=symbol,
                include_earnings=False,
                include_trade_construction=False,
                include_position_sizing=False,
                include_trading_decision=False,
                use_demo=False
            )
            
            # Get basic analysis
            loop = asyncio.get_event_loop()
            params = self._convert_request_to_params(basic_request)
            
            # Execute minimal analysis for basic info
            raw_result = await loop.run_in_executor(
                None,
                self._get_basic_info,
                params
            )
            
            return {
                "current_price": raw_result.get("current_price"),
                "data_source": raw_result.get("data_source"),
                "last_updated": raw_result.get("data_timestamp"),
                "market_status": "open" if raw_result.get("market_open", False) else "closed"
            }
            
        except Exception as e:
            logger.error(f"Failed to get basic info for {symbol}: {str(e)}")
            raise
    
    def _get_basic_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get basic symbol information (synchronous)"""
        try:
            # Use existing backend to get minimal info
            # This is a simplified call that just gets price data
            result = self.analyze_symbol_func(**params)
            return {
                "current_price": result.get("current_price"),
                "data_source": result.get("data_source"),
                "data_timestamp": result.get("data_timestamp"),
                "market_open": result.get("market_open", False)
            }
        except Exception as e:
            logger.error(f"Failed to get basic symbol info: {str(e)}")
            raise