#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Trading Logic
==================

Core modules for options trading analysis:
- data_service: Multi-provider data sourcing with fallbacks
- analysis: Volatility analysis and term structure modeling
- earnings: Earnings calendar and timing window management
- analyzer: Main symbol analysis orchestration
"""

# Always available imports
from .data_service import DataService

# Conditional imports based on available dependencies
__all__ = ["DataService"]

try:
    from .analysis import calculate_calendar_spread_metrics, yang_zhang_volatility, build_term_structure
    __all__.extend(["calculate_calendar_spread_metrics", "yang_zhang_volatility", "build_term_structure"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Some analysis functions unavailable due to missing dependencies: {e}")

try:
    from .earnings import EarningsCalendar, EarningsEvent
    __all__.extend(["EarningsCalendar", "EarningsEvent"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Earnings calendar unavailable due to missing dependencies: {e}")

try:
    from .analyzer import analyze_symbol
    __all__.extend(["analyze_symbol"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Symbol analyzer unavailable due to missing dependencies: {e}")

# Module 2: Trade Construction & P&L Engine (conditional imports)
try:
    from .trade_construction import CalendarTrade, CalendarTradeConstructor, OptionQuote, TradeValidator
    __all__.extend(["CalendarTrade", "CalendarTradeConstructor", "OptionQuote", "TradeValidator"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Trade construction module unavailable due to missing dependencies: {e}")

try:
    from .pnl_engine import PnLEngine, PnLGrid, IVCrushParameters, IVCrushModel
    __all__.extend(["PnLEngine", "PnLGrid", "IVCrushParameters", "IVCrushModel"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"P&L engine module unavailable due to missing dependencies: {e}")

try:
    from .greeks import Greeks, CalendarGreeks, GreeksCalculator, SensitivityAnalyzer
    __all__.extend(["Greeks", "CalendarGreeks", "GreeksCalculator", "SensitivityAnalyzer"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Greeks calculator module unavailable due to missing dependencies: {e}")

# Module 3: Position Sizing & Risk Management (conditional imports)
try:
    from .position_sizing import FractionalKellyCalculator, KellyParameters, PositionSize, SIGNAL_SCALING
    __all__.extend(["FractionalKellyCalculator", "KellyParameters", "PositionSize", "SIGNAL_SCALING"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Position sizing module unavailable due to missing dependencies: {e}")

try:
    from .risk_management import RiskManagementEngine, RiskLimits, Position, PortfolioGreeks, RiskAssessment
    __all__.extend(["RiskManagementEngine", "RiskLimits", "Position", "PortfolioGreeks", "RiskAssessment"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Risk management module unavailable due to missing dependencies: {e}")

try:
    from .account import AccountManager, AccountSettings, MarginValidation, CapitalAllocation
    __all__.extend(["AccountManager", "AccountSettings", "MarginValidation", "CapitalAllocation"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Account management module unavailable due to missing dependencies: {e}")

# Module 4: Trading Decision Automation (conditional imports)
try:
    from .decision_engine import ConfigurableDecisionEngine, EnhancedTradingDecision
    __all__.extend(["ConfigurableDecisionEngine", "EnhancedTradingDecision"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Decision engine module unavailable due to missing dependencies: {e}")

try:
    from .backtesting import BacktestingEngine, BacktestResult, ValidationReport, TradeSimulation
    __all__.extend(["BacktestingEngine", "BacktestResult", "ValidationReport", "TradeSimulation"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Backtesting module unavailable due to missing dependencies: {e}")

try:
    from .performance import PerformanceAnalytics, PerformanceMetrics, AccuracyReport, OptimizationResult, PerformanceReport
    __all__.extend(["PerformanceAnalytics", "PerformanceMetrics", "AccuracyReport", "OptimizationResult", "PerformanceReport"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Performance analytics module unavailable due to missing dependencies: {e}")

try:
    from .alerts import TradingAlertSystem, TradingOpportunity, TimingAssessment, AlertPreferences
    __all__.extend(["TradingAlertSystem", "TradingOpportunity", "TimingAssessment", "AlertPreferences"])
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Alert system module unavailable due to missing dependencies: {e}")