#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symbol Analyzer - Main Orchestration
====================================

Main analysis orchestration that combines:
- Multi-provider data retrieval
- Volatility and term structure analysis  
- Calendar spread metrics and recommendations
- NEW: Earnings calendar integration with timing windows

This is the primary entry point that maintains backward compatibility
with the original analyze_symbol function.
"""

import os
import logging
from typing import Dict, Any

# Conditional import for yfinance
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

from .data_service import DataService
from .analysis import calculate_calendar_spread_metrics, summarize_chain_for_atm
from .earnings import EarningsCalendar

logger = logging.getLogger("options_trader.analyzer")


def analyze_symbol(symbol: str, expirations_to_check: int = 1, use_demo: bool = False, 
                  include_earnings: bool = False, include_trade_construction: bool = False,
                  include_position_sizing: bool = False, include_trading_decision: bool = False,
                  trade_structure: str = None, account_size: float = None, 
                  risk_per_trade: float = None) -> Dict[str, Any]:
    """
    Analyze a symbol for options trading opportunities.
    
    This is the main analysis function that orchestrates:
    1. Price data retrieval with fallback providers
    2. Options chain analysis for multiple expirations  
    3. Calendar spread metrics and trading signals
    4. NEW: Earnings calendar and timing windows (Module 1)
    5. NEW: Trade construction and P&L analysis (Module 2)
    6. NEW: Position sizing and risk management (Module 3)
    7. NEW: Trading decision automation (Module 4)
    
    Args:
        symbol: Stock symbol to analyze
        expirations_to_check: Number of expirations to analyze
        use_demo: Use demo data instead of live APIs
        include_earnings: Include earnings analysis (Module 1 feature)
        include_trade_construction: Include trade construction & P&L (Module 2 feature)
        include_position_sizing: Include position sizing & risk management (Module 3 feature)
        include_trading_decision: Include trading decision automation (Module 4 feature)
        trade_structure: Trade structure preference ('calendar', 'straddle', 'auto', or None for default)
        account_size: Override account size for position sizing calculations
        risk_per_trade: Override risk per trade percentage
        
    Returns:
        Dictionary with comprehensive analysis results including:
        - Original analysis results (backward compatible)
        - Earnings analysis (if requested)
        - Calendar trade construction (if requested)
        - P&L simulation scenarios (if requested)
        - Position sizing and risk assessment (if requested)
        - Trading decision and recommendation (if requested)
    """
    try:
        symbol = symbol.strip().upper()
        if not symbol:
            return {"error": "Please enter a symbol."}
        
        logger.info(f"Starting analysis for {symbol} (expirations={expirations_to_check}, demo={use_demo}, earnings={include_earnings})")
        
        # Initialize data service
        data_service = DataService(use_demo=use_demo)
        
        # Get current price
        price, price_source, is_cached = data_service.get_price(symbol)
        if price is None:
            logger.error(f"Unable to retrieve price for {symbol}")
            return {"error": f"Unable to retrieve current price for {symbol} (all sources failed)."}
        
        # Get available expirations
        expirations, exp_source = data_service.get_expirations(symbol, max_count=max(1, int(expirations_to_check or 1)))
        if not expirations:
            logger.error(f"No expirations found for {symbol}")
            return {"error": f"No upcoming expirations found for {symbol} from any provider."}
        
        # Build result structure
        result: Dict[str, Any] = {
            "symbol": symbol,
            "price": float(price),
            "price_source": price_source,
            "price_cached": bool(is_cached),
            "expirations_source": exp_source,
            "expirations": [],
        }
        
        # Analyze each expiration
        atm_ivs = {}
        first_straddle = None
        
        logger.debug(f"Processing {len(expirations)} expirations: {expirations}")
        
        for expiration in expirations:
            try:
                # Get option chain
                chain, chain_source = data_service.get_chain(symbol, expiration)
                
                # Summarize ATM options
                summary = summarize_chain_for_atm(chain, float(price))
                summary["expiration"] = expiration
                summary["chain_source"] = chain_source
                
                result["expirations"].append(summary)
                
                # Collect data for calendar spread analysis
                if "atm_iv" in summary and summary["atm_iv"] is not None:
                    atm_ivs[expiration] = summary["atm_iv"]
                
                # Get first straddle price for expected move calculation
                if first_straddle is None and "straddle_mid" in summary and summary["straddle_mid"] is not None:
                    first_straddle = summary["straddle_mid"]
                
                iv_value = summary.get('atm_iv')
                iv_display = f"{iv_value:.4f}" if iv_value is not None else 'N/A'
                logger.debug(f"Processed {expiration}: IV={iv_display}")
                
            except Exception as e:
                error_summary = {
                    "expiration": expiration,
                    "error": f"Failed to fetch option chain: {type(e).__name__}: {str(e)}"
                }
                result["expirations"].append(error_summary)
                logger.warning(f"Failed to process {expiration} for {symbol}: {e}")
        
        # Calendar spread analysis (if we have multiple expirations)
        if len(atm_ivs) >= 2:
            try:
                logger.debug(f"Running calendar spread analysis with {len(atm_ivs)} expirations")
                
                # Get price history for volatility analysis
                price_history = None
                if not use_demo and HAS_YFINANCE:
                    try:
                        ticker = yf.Ticker(symbol)
                        price_history = ticker.history(period='3mo')  # 3 months for RV calculation
                        logger.debug(f"Retrieved {len(price_history)} days of price history")
                    except Exception as e:
                        logger.warning(f"Failed to get price history for {symbol}: {e}")
                elif not HAS_YFINANCE:
                    logger.debug("yfinance not available, skipping price history retrieval")
                
                # Calculate calendar spread metrics with data validation
                calendar_metrics = calculate_calendar_spread_metrics(
                    atm_ivs=atm_ivs,
                    underlying_price=float(price),
                    straddle_price=first_straddle,
                    price_history=price_history,
                    symbol=symbol
                )
                
                result["calendar_spread_analysis"] = calendar_metrics
                
                logger.info(f"Calendar analysis complete for {symbol}: {calendar_metrics.get('signal_count', 0)}/3 signals")
                
            except Exception as e:
                logger.error(f"Calendar spread analysis failed for {symbol}: {e}")
                result["calendar_spread_analysis"] = {"error": f"Analysis failed: {str(e)}"}
        else:
            result["calendar_spread_analysis"] = {"error": "Need at least 2 expirations for calendar spread analysis"}
        
        # NEW: Earnings analysis (Module 1)
        if include_earnings:
            try:
                logger.debug(f"Running earnings analysis for {symbol}")
                
                # Initialize earnings calendar with available providers
                earnings_providers = data_service.get_earnings_providers()
                if earnings_providers:
                    earnings_calendar = EarningsCalendar(earnings_providers)
                    
                    # Get earnings opportunity
                    opportunity = earnings_calendar.get_trading_opportunity(symbol)
                    if opportunity:
                        earnings_event, trading_windows, warnings = opportunity
                        
                        result["earnings_analysis"] = {
                            "earnings_event": {
                                "date": earnings_event.date.isoformat(),
                                "timing": earnings_event.timing,
                                "confirmed": earnings_event.confirmed,
                                "source": earnings_event.source,
                                "days_until": earnings_event.days_until
                            },
                            "trading_windows": {
                                "entry_start": trading_windows.entry_start.isoformat(),
                                "entry_end": trading_windows.entry_end.isoformat(),
                                "exit_start": trading_windows.exit_start.isoformat(),
                                "exit_end": trading_windows.exit_end.isoformat(),
                                "market_timezone": trading_windows.market_timezone
                            },
                            "warnings": warnings,
                            "time_to_entry": None,
                            "time_to_exit": None
                        }
                        
                        # Calculate time to windows
                        from datetime import datetime
                        now = datetime.now(trading_windows.entry_start.tzinfo)
                        
                        time_to_entry = trading_windows.time_to_entry(now)
                        if time_to_entry:
                            result["earnings_analysis"]["time_to_entry"] = str(time_to_entry)
                        
                        time_to_exit = trading_windows.time_to_exit(now)  
                        if time_to_exit:
                            result["earnings_analysis"]["time_to_exit"] = str(time_to_exit)
                        
                        logger.info(f"Earnings analysis complete for {symbol}: {earnings_event.date.date()} {earnings_event.timing}")
                        
                    else:
                        result["earnings_analysis"] = {"error": "No upcoming earnings found"}
                        logger.debug(f"No earnings found for {symbol}")
                        
                else:
                    result["earnings_analysis"] = {"error": "No earnings providers available"}
                    logger.warning("No earnings providers configured")
                    
            except Exception as e:
                logger.error(f"Earnings analysis failed for {symbol}: {e}")
                result["earnings_analysis"] = {"error": f"Earnings analysis failed: {str(e)}"}
        
        # NEW: Module 2 - Trade Construction & P&L Engine
        if include_trade_construction:
            try:
                # Import Module 2 components conditionally
                try:
                    from .trade_construction import CalendarTradeConstructor, TradeValidator
                    from .pnl_engine import PnLEngine, IVCrushParameters
                    from .greeks import GreeksCalculator
                    MODULE_2_AVAILABLE = True
                except ImportError as e:
                    logger.warning(f"Module 2 components not available: {e}")
                    MODULE_2_AVAILABLE = False
                
                if MODULE_2_AVAILABLE:
                    logger.debug(f"Running trade construction analysis for {symbol}")
                    
                    # Only build trades if we have positive signals
                    calendar_analysis = result.get("calendar_spread_analysis", {})
                    signal_count = calendar_analysis.get("signal_count", 0)
                    
                    if signal_count >= 2:  # Only build trades with good signals
                        # Initialize trade constructor
                        trade_constructor = CalendarTradeConstructor(data_service)
                        
                        # Get earnings date for expiration selection
                        earnings_date = None
                        if include_earnings and "earnings_analysis" in result:
                            earnings_info = result["earnings_analysis"]
                            if "earnings_event" in earnings_info:
                                from datetime import datetime
                                earnings_date = datetime.fromisoformat(earnings_info["earnings_event"]["date"])
                        
                        # Build optimal calendar trade
                        calendar_trade = trade_constructor.build_optimal_calendar(
                            symbol, result, earnings_date
                        )
                        
                        if calendar_trade:
                            # Validate trade quality
                            trade_validator = TradeValidator()
                            quality_assessment = trade_validator.assess_trade_quality(calendar_trade)
                            
                            # Calculate Greeks and risk metrics
                            greeks_calc = GreeksCalculator()
                            calendar_greeks = greeks_calc.calculate_calendar_greeks(calendar_trade)
                            
                            # Run P&L simulation
                            pnl_engine = PnLEngine()
                            
                            # Get IV crush parameters based on volume
                            avg_volume = calendar_analysis.get("avg_volume_30d", 1000000)
                            crush_params = IVCrushParameters.get_by_liquidity(avg_volume)
                            
                            # Get expected move from analysis
                            expected_move_pct = calendar_analysis.get("expected_move_pct")
                            
                            # Generate P&L scenarios
                            pnl_grid = pnl_engine.simulate_post_earnings_scenarios(
                                calendar_trade, crush_params, expected_move_pct
                            )
                            
                            # Compile trade construction results
                            result["trade_construction"] = {
                                "calendar_trade": {
                                    "symbol": calendar_trade.symbol,
                                    "underlying_price": calendar_trade.underlying_price,
                                    "strike": calendar_trade.strike,
                                    "front_expiration": calendar_trade.front_expiration,
                                    "back_expiration": calendar_trade.back_expiration,
                                    "trade_type": calendar_trade.trade_type,
                                    "net_debit": calendar_trade.net_debit,
                                    "max_loss": calendar_trade.max_loss,
                                    "max_profit": calendar_trade.max_profit,
                                    "breakeven_range": calendar_trade.breakeven_range,
                                    "expected_profit_range": calendar_trade.expected_profit_range,
                                    "capital_requirement": calendar_trade.capital_requirement,
                                    "is_valid": calendar_trade.is_valid,
                                    "validation_errors": calendar_trade.validation_errors,
                                    "days_to_expiration_front": calendar_trade.days_to_expiration_front,
                                    "days_to_expiration_back": calendar_trade.days_to_expiration_back
                                },
                                "quality_assessment": quality_assessment,
                                "greeks_analysis": {
                                    "net_delta": calendar_greeks.net_delta,
                                    "net_gamma": calendar_greeks.net_gamma,
                                    "net_theta": calendar_greeks.net_theta,
                                    "net_vega": calendar_greeks.net_vega,
                                    "delta_dollars": calendar_greeks.delta_dollars,
                                    "theta_dollars": calendar_greeks.theta_dollars,
                                    "vega_dollars": calendar_greeks.vega_dollars,
                                    "is_long_vega": calendar_greeks.is_long_vega,
                                    "is_short_gamma": calendar_greeks.is_short_gamma,
                                    "daily_theta_pnl": calendar_greeks.daily_theta_pnl
                                },
                                "pnl_analysis": {
                                    "summary_stats": pnl_grid.get_summary_stats(),
                                    "iv_crush_parameters": {
                                        "front_iv_drop": crush_params.front_iv_drop,
                                        "back_iv_drop": crush_params.back_iv_drop,
                                        "liquidity_tier": crush_params.liquidity_tier,
                                        "confidence": crush_params.confidence
                                    },
                                    "scenario_count": len(pnl_grid.scenarios),
                                    "expected_move_pnl": pnl_grid.get_expected_move_pnl(expected_move_pct) if expected_move_pct else {}
                                }
                            }
                            
                            # Stage 2: Add ATM Straddle construction if enabled and requested
                            straddle_data = None
                            try:
                                import os as safe_os  # Import locally to avoid conflicts
                                structure_preference = trade_structure or safe_os.getenv("DEFAULT_TRADE_STRUCTURE", "calendar")
                                enable_straddle = safe_os.getenv("ENABLE_STRADDLE_STRUCTURE", "true").lower() == "true"
                            except Exception as env_error:
                                logger.warning(f"Could not access environment variables: {env_error}")
                                structure_preference = trade_structure or "calendar"
                                enable_straddle = True
                            
                            if enable_straddle:  # Build straddle for comparison regardless of preference
                                try:
                                    from .straddle_construction import StraddleConstructor, TradeStructureSelector
                                    
                                    # Initialize straddle constructor
                                    straddle_constructor = StraddleConstructor()
                                    
                                    # Get front expiration (same as calendar front leg)
                                    front_expiration = calendar_trade.front_expiration
                                    
                                    # Try to get options chain data using the correct DataService method
                                    options_chain = {}
                                    try:
                                        # Get options chain for the front expiration (same as calendar spread)
                                        chain_data, source = data_service.get_chain(symbol, front_expiration)
                                        if chain_data:
                                            options_chain = chain_data  # chain_data is already the options chain
                                            logger.debug(f"Retrieved options chain for straddle construction from {source}")
                                    except Exception as e:
                                        logger.debug(f"Could not get options chain for straddle construction: {e}")
                                    
                                    if options_chain:
                                        # Build ATM straddle
                                        straddle_trade = straddle_constructor.build_atm_straddle(
                                            symbol, front_expiration, calendar_trade.underlying_price, options_chain
                                        )
                                        
                                        if straddle_trade:
                                            # Analyze straddle risk
                                            straddle_risk = straddle_constructor.analyze_straddle_risk(
                                                straddle_trade, calendar_trade.underlying_price
                                            )
                                            
                                            straddle_data = {
                                                "straddle_trade": {
                                                    "symbol": straddle_trade.symbol,
                                                    "strike": straddle_trade.strike,
                                                    "expiration": straddle_trade.expiration,
                                                    "net_credit": straddle_trade.net_credit,
                                                    "max_profit": straddle_trade.max_profit,
                                                    "max_risk": straddle_trade.max_risk,
                                                    "breakeven_upper": straddle_trade.breakeven_upper,
                                                    "breakeven_lower": straddle_trade.breakeven_lower,
                                                    "probability_of_profit": straddle_trade.probability_of_profit,
                                                    "liquidity_score": straddle_trade.liquidity_score
                                                },
                                                "straddle_greeks": {
                                                    "net_delta": straddle_trade.net_delta,
                                                    "net_gamma": straddle_trade.net_gamma,
                                                    "net_theta": straddle_trade.net_theta,
                                                    "net_vega": straddle_trade.net_vega
                                                },
                                                "risk_analysis": straddle_risk
                                            }
                                            
                                            logger.info(f"ATM straddle construction complete for {symbol}: ${straddle_trade.net_credit:.2f} credit, POP: {straddle_trade.probability_of_profit:.1%}")
                                        else:
                                            logger.warning(f"Could not construct ATM straddle for {symbol}")
                                    else:
                                        logger.debug(f"No options chain available for straddle construction: {symbol}")
                                        
                                except ImportError as e:
                                    logger.warning(f"Straddle construction components not available: {e}")
                                except Exception as e:
                                    logger.error(f"Straddle construction failed for {symbol}: {e}")
                            
                            # Add straddle data to results if available
                            if straddle_data:
                                result["trade_construction"]["straddle_construction"] = straddle_data
                            
                            # Add structure recommendation
                            try:
                                from .straddle_construction import TradeStructureSelector
                                structure_selector = TradeStructureSelector()
                                
                                # Get account size for structure recommendation - handle os access safely
                                try:
                                    import os as safe_os  # Import locally to avoid variable conflicts
                                    account_size_for_rec = account_size or float(safe_os.getenv("ACCOUNT_SIZE", "10000"))
                                except Exception as env_error:
                                    logger.warning(f"Could not access environment variables: {env_error}")
                                    account_size_for_rec = account_size or 10000.0  # fallback
                                
                                structure_recommendation = structure_selector.recommend_structure(
                                    structure_preference, account_size_for_rec
                                )
                                
                                # Generate reasoning based on recommendation logic
                                reasoning = self._generate_structure_reasoning(structure_preference, account_size_for_rec, structure_recommendation)
                                
                                # Get structure comparison if both structures are available
                                structure_comparison = None
                                if straddle_data:
                                    calendar_metrics = {"quality_score": quality_assessment.get("overall_score", 0)}
                                    straddle_metrics = {"probability_of_profit": straddle_data["straddle_trade"]["probability_of_profit"]}
                                    structure_comparison = structure_selector.get_structure_comparison(calendar_metrics, straddle_metrics)
                                
                                # Store structure recommendation for CLI formatter
                                result["trade_construction"]["structure_recommendation"] = {
                                    "requested": structure_preference,
                                    "recommended": structure_recommendation,
                                    "reasoning": reasoning
                                }
                                
                                # Store detailed structure selection data
                                result["trade_construction"]["structure_selection"] = {
                                    "requested_structure": structure_preference,
                                    "recommended_structure": structure_recommendation,
                                    "reasoning": reasoning,
                                    "structure_comparison": structure_comparison,
                                    "straddle_available": straddle_data is not None
                                }
                                
                            except ImportError:
                                logger.debug("Structure selector not available")
                            except Exception as struct_error:
                                logger.warning(f"Structure recommendation failed: {struct_error}")
                            
                            logger.info(f"Trade construction complete for {symbol}: Calendar ${calendar_trade.net_debit:.2f} debit, quality score: {quality_assessment.get('overall_score', 0):.1f}")
                        else:
                            result["trade_construction"] = {"error": "Could not construct valid calendar trade"}
                            logger.warning(f"Trade construction failed for {symbol}")
                    else:
                        result["trade_construction"] = {"error": f"Insufficient signals for trade construction (need ≥2, got {signal_count})"}
                        logger.debug(f"Skipping trade construction for {symbol}: only {signal_count}/3 signals")
                else:
                    result["trade_construction"] = {"error": "Module 2 components not available"}
                    logger.warning("Trade construction requested but Module 2 not available")
                    
            except Exception as e:
                logger.error(f"Trade construction analysis failed for {symbol}: {e}")
                result["trade_construction"] = {"error": f"Trade construction failed: {str(e)}"}
        
        # NEW: Module 3 - Position Sizing & Risk Management
        if include_position_sizing:
            try:
                # Import Module 3 components conditionally
                try:
                    from .position_sizing import FractionalKellyCalculator
                    from .risk_management import RiskManagementEngine
                    from .account import AccountManager
                    MODULE_3_AVAILABLE = True
                except ImportError as e:
                    logger.warning(f"Module 3 components not available: {e}")
                    MODULE_3_AVAILABLE = False
                
                if MODULE_3_AVAILABLE:
                    logger.debug(f"Running position sizing analysis for {symbol}")
                    
                    # Only calculate position sizing if we have trade construction
                    if include_trade_construction and "trade_construction" in result and "error" not in result["trade_construction"]:
                        trade_data = result["trade_construction"]["calendar_trade"]
                        pnl_analysis = result["trade_construction"]["pnl_analysis"]
                        calendar_analysis = result.get("calendar_spread_analysis", {})
                        signal_count = calendar_analysis.get("signal_count", 0)
                        
                        # Initialize Module 3 components
                        kelly_calculator = FractionalKellyCalculator()
                        risk_manager = RiskManagementEngine()
                        
                        # Setup account manager with optional overrides
                        if account_size or risk_per_trade:
                            # Create account settings with overrides
                            from .account import AccountSettings
                            import os
                            account_settings = AccountSettings(
                                total_capital=account_size or float(os.getenv("ACCOUNT_SIZE", 100000)),
                                risk_per_trade_pct=risk_per_trade or float(os.getenv("RISK_PER_TRADE", 0.02))
                            )
                            account_manager = AccountManager(account_settings)
                        else:
                            account_manager = AccountManager()
                        
                        # Calculate position size
                        position_size = kelly_calculator.calculate_optimal_fraction(
                            trade_data, pnl_analysis, account_manager.settings.total_capital, signal_count
                        )
                        
                        # Get capital allocation details
                        capital_allocation = account_manager.calculate_capital_allocation(
                            symbol, position_size.contracts, trade_data["net_debit"], trade_data["max_loss"]
                        )
                        
                        # Validate margin requirements
                        margin_validation = account_manager.validate_margin_requirements(
                            symbol, position_size.contracts, trade_data["net_debit"]
                        )
                        
                        # Get Greeks for portfolio risk calculation
                        greeks_analysis = result["trade_construction"].get("greeks_analysis", {})
                        net_delta = greeks_analysis.get("net_delta", 0.0) * position_size.contracts
                        
                        # Perform comprehensive risk assessment
                        risk_assessment = risk_manager.validate_risk_compliance(
                            symbol, position_size.contracts, trade_data["max_loss"],
                            account_manager.settings.total_capital, net_delta
                        )
                        
                        # Apply risk management position limits
                        adjusted_position = risk_manager.enforce_position_limits(
                            position_size.contracts, trade_data["max_loss"],
                            account_manager.settings.total_capital, symbol
                        )
                        
                        # Get account summary
                        account_summary = account_manager.get_account_summary()
                        
                        # Compile position sizing results
                        result["position_sizing"] = {
                            "recommended_position": {
                                "symbol": position_size.symbol,
                                "contracts": adjusted_position.adjusted_contracts,
                                "original_contracts": position_size.contracts,
                                "adjustment_reason": adjusted_position.adjustment_reason,
                                "capital_required": adjusted_position.adjusted_contracts * trade_data["max_loss"] * 100,  # Include shares per contract
                                "capital_allocation": capital_allocation.to_dict() if hasattr(capital_allocation, 'to_dict') else {
                                    "symbol": capital_allocation.symbol,
                                    "contracts": capital_allocation.contracts,
                                    "capital_required": capital_allocation.capital_required,
                                    "risk_capital": capital_allocation.risk_capital,
                                    "percentage_of_account": capital_allocation.percentage_of_account,
                                    "is_affordable": capital_allocation.is_affordable
                                }
                            },
                            "kelly_analysis": {
                                "kelly_fraction": position_size.kelly_fraction,
                                "signal_multiplier": position_size.signal_multiplier,
                                "risk_adjusted_kelly": position_size.risk_adjusted_kelly,
                                "account_risk_pct": adjusted_position.adjusted_contracts * trade_data["max_loss"] / account_manager.settings.total_capital * 100,
                                "signal_strength": signal_count,
                                "validation_errors": position_size.validation_errors
                            },
                            "risk_assessment": {
                                "is_compliant": risk_assessment.is_compliant,
                                "risk_score": risk_assessment.risk_score,
                                "violations": risk_assessment.violations,
                                "warnings": risk_assessment.warnings,
                                "recommendations": risk_assessment.recommendations
                            },
                            "margin_validation": {
                                "is_valid": margin_validation.is_valid,
                                "required_margin": margin_validation.required_margin,
                                "available_margin": margin_validation.available_margin,
                                "margin_utilization_pct": margin_validation.margin_utilization_pct,
                                "errors": margin_validation.errors,
                                "warnings": margin_validation.warnings
                            },
                            "account_summary": account_summary,
                            "portfolio_impact": {
                                "new_position_delta": net_delta,
                                "estimated_theta_impact": greeks_analysis.get("theta_dollars", 0.0) * adjusted_position.adjusted_contracts,
                                "estimated_vega_impact": greeks_analysis.get("vega_dollars", 0.0) * adjusted_position.adjusted_contracts
                            }
                        }
                        
                        logger.info(f"Position sizing complete for {symbol}: {adjusted_position.adjusted_contracts} contracts "
                                   f"(${adjusted_position.adjusted_contracts * trade_data['max_loss']:.0f} capital), "
                                   f"risk score: {risk_assessment.risk_score:.1f}")
                    else:
                        result["position_sizing"] = {"error": "Position sizing requires trade construction analysis"}
                        logger.debug(f"Skipping position sizing for {symbol}: trade construction not available")
                else:
                    result["position_sizing"] = {"error": "Module 3 components not available"}
                    logger.warning("Position sizing requested but Module 3 not available")
                    
            except Exception as e:
                logger.error(f"Position sizing analysis failed for {symbol}: {e}")
                result["position_sizing"] = {"error": f"Position sizing failed: {str(e)}"}
        
        # NEW: Module 4 - Configurable Trading Decision Automation
        if include_trading_decision:
            try:
                # Import Module 4 components conditionally
                try:
                    from .decision_engine import ConfigurableDecisionEngine
                    from .output_formatter import StrategyOutputFormatter
                    MODULE_4_AVAILABLE = True
                except ImportError as e:
                    logger.warning(f"Module 4 components not available: {e}")
                    MODULE_4_AVAILABLE = False
                
                if MODULE_4_AVAILABLE:
                    logger.debug(f"Running configurable trading decision analysis for {symbol}")
                    
                    # Initialize configurable decision engine and formatter
                    decision_engine = ConfigurableDecisionEngine()
                    output_formatter = StrategyOutputFormatter()
                    
                    # Make trading decision based on complete analysis
                    enhanced_decision = decision_engine.make_trading_decision(result)
                    
                    # Format decision output for display (Stage 3: pass metrics for threshold validation)
                    analysis_metrics = {
                        'ts_slope': result.get('calendar_spread_analysis', {}).get('ts_slope'),
                        'iv_rv_ratio': result.get('calendar_spread_analysis', {}).get('iv_rv_ratio'),
                        'avg_volume_30d': result.get('calendar_spread_analysis', {}).get('avg_volume_30d'),
                        'volume': result.get('calendar_spread_analysis', {}).get('avg_volume_30d')  # Fallback alias
                    }
                    
                    # Remove None values
                    analysis_metrics = {k: v for k, v in analysis_metrics.items() if v is not None}
                    
                    formatted_output = output_formatter.format_decision_output(enhanced_decision, analysis_metrics)
                    
                    # Add enhanced decision to results
                    result["trading_decision"] = {
                        # Original strategy fields (always present)
                        "decision": enhanced_decision.original_decision,  # "RECOMMENDED", "CONSIDER", or "AVOID"
                        "original_decision": enhanced_decision.original_decision,
                        "original_confidence": enhanced_decision.original_confidence,
                        "signal_strength": enhanced_decision.signal_strength,
                        "signal_breakdown": enhanced_decision.signal_breakdown,
                        "original_reasoning": enhanced_decision.original_reasoning,
                        
                        # Enhanced fields (optional)
                        "enhanced_decision": enhanced_decision.enhanced_decision,
                        "enhanced_confidence": enhanced_decision.enhanced_confidence,
                        "enhanced_reasoning": enhanced_decision.enhanced_reasoning,
                        "risk_reward_ratio": enhanced_decision.risk_reward_ratio,
                        "quality_score": enhanced_decision.quality_score,
                        "win_probability": enhanced_decision.win_rate_estimate,
                        "expected_return": enhanced_decision.expected_value,
                        "position_size": enhanced_decision.position_size,
                        
                        # Framework metadata
                        "framework": enhanced_decision.framework,
                        "is_valid": enhanced_decision.is_valid,
                        "validation_errors": enhanced_decision.validation_errors,
                        
                        # Formatted output for display
                        "formatted_output": formatted_output
                    }
                    
                    logger.info(f"Trading decision for {symbol}: {enhanced_decision.original_decision} "
                               f"(framework: {enhanced_decision.framework}, "
                               f"confidence: {enhanced_decision.original_confidence:.1%})")
                else:
                    result["trading_decision"] = {"error": "Module 4 components not available"}
                    logger.warning("Trading decision requested but Module 4 not available")
                    
            except Exception as e:
                logger.error(f"Trading decision analysis failed for {symbol}: {e}")
                result["trading_decision"] = {"error": f"Trading decision failed: {str(e)}"}
        
        logger.info(f"Analysis complete for {symbol}")
        return result
        
    except Exception as e:
        logger.error(f"analyze_symbol failed for {symbol}: {e}")
        return {"error": f"Unexpected error in analyze_symbol: {str(e)}. Check logs for details."}


def _generate_structure_reasoning(structure_preference: str, account_size: float, recommendation: str) -> str:
    """
    Generate reasoning for structure recommendation based on the logic used.
    
    Args:
        structure_preference: Original user preference ("conservative", "aggressive", "moderate", "auto", etc.)
        account_size: Account size used for recommendation
        recommendation: Final recommendation ("calendar" or "straddle")
        
    Returns:
        Human-readable reasoning string
    """
    preference = structure_preference.lower().strip()
    
    if preference == "conservative":
        return "Calendar spread chosen for conservative approach with smoother equity curve and defined risk"
    
    elif preference == "aggressive":
        return "ATM straddle chosen for aggressive approach with higher potential returns"
    
    elif preference == "moderate":
        return "Calendar spread chosen as moderate default strategy balancing risk and reward"
    
    elif preference == "auto":
        if account_size >= 100000:  # $100K+ accounts
            if recommendation == "straddle":
                return f"ATM straddle chosen for large account (${account_size:,.0f}) capable of handling unlimited risk"
            else:
                return f"Calendar spread chosen despite large account size for conservative risk management"
        else:
            return f"Calendar spread chosen for smaller account (${account_size:,.0f}) to manage risk exposure"
    
    elif preference in ["calendar", "calendar_spread"]:
        return "Calendar spread chosen per user preference for limited risk strategy"
    
    elif preference in ["straddle", "atm_straddle", "short_straddle"]:
        return "ATM straddle chosen per user preference for higher return potential"
    
    else:
        return f"Calendar spread chosen as conservative default for unknown preference '{preference}'"


# Backward compatibility alias
def analyze_symbol_legacy(symbol: str, expirations_to_check: int = 1, use_demo: bool = False) -> Dict[str, Any]:
    """
    Legacy function signature for backward compatibility.
    
    This maintains compatibility with the original optionsCalculator.py interface.
    """
    return analyze_symbol(symbol, expirations_to_check, use_demo, include_earnings=False)
