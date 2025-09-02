#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Options Calculator - Main Entry Point
==============================================

Modular options trading calculator with earnings volatility strategies.

FEATURES:
- Earnings calendar integration with precise timing windows
- Multi-provider data sourcing with fallback logic
- Trade construction with calendar spreads and straddles
- Position sizing with Kelly criterion
- Trading decision automation

USAGE:
    python main.py --help                               # Show command-line options
    python main.py --symbol AAPL                       # Basic analysis
    python main.py --symbol AAPL --earnings            # With earnings analysis
    python main.py --demo --symbol AAPL --earnings     # Demo mode

DISCLAIMER: 
This software is provided solely for educational and research purposes. 
It is not intended to provide investment advice, and no investment recommendations are made herein. 
The developers are not financial advisors and accept no responsibility for any financial decisions 
or losses resulting from the use of this software. Always consult a professional financial advisor 
before making any investment decisions.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Setup logging with timestamped files in logs folder
logs_dir = Path.cwd() / "logs"
logs_dir.mkdir(exist_ok=True)

# Create timestamped log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"trade_calculator_{timestamp}.log"
log_path = logs_dir / log_filename

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_path, mode="w", encoding="utf-8"),  # 'w' mode for new file each run
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger("options_trader.main")

# Load environment variables from .env if present
env_file = Path(".env")
if env_file.exists():
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
        logger.info("Loaded environment variables from .env")
    except Exception as e:
        logger.warning(f"Failed to parse .env file: {e}")

# Import our modules with fallbacks
try:
    from options_trader import __version__
except ImportError as e:
    print(f"Failed to import options_trader package: {e}")
    print("Make sure you're running from the correct directory and all dependencies are installed.")
    print("Try: pip install -r requirements.txt")
    sys.exit(1)

try:
    from options_trader.core.analyzer import analyze_symbol
except ImportError as e:
    print(f"Core analyzer not available: {e}")
    print("Some features may not work. Install missing dependencies with: pip install -r requirements.txt")
    analyze_symbol = None

try:
    from options_trader.core.cli_formatter import create_enhanced_cli_formatter
    HAS_ENHANCED_CLI = True
except ImportError as e:
    logger.warning(f"Enhanced CLI formatter not available: {e}")
    HAS_ENHANCED_CLI = False


def print_version():
    """Print version information."""
    print(f"Advanced Options Calculator v{__version__}")
    print("Educational options trading analysis tool")
    print(f"Log file: {log_path}")


def analyze_symbol_cli(symbol: str, expirations: int = 2, demo: bool = False, 
                      earnings: bool = False, trade_construction: bool = False,
                      position_sizing: bool = False, trading_decision: bool = False,
                      structure: str = None, account_size: float = None, 
                      risk_per_trade: float = None) -> None:
    """
    Analyze a symbol in command-line mode using enhanced professional formatting.
    
    Args:
        symbol: Stock symbol to analyze
        expirations: Number of expirations to check
        demo: Use demo data
        earnings: Include earnings analysis
        trade_construction: Include trade construction & P&L analysis (Module 2)
        position_sizing: Include position sizing & risk management (Module 3)
        trading_decision: Include trading decision automation (Module 4)
        structure: Trade structure preference ('calendar', 'straddle', 'auto')
        account_size: Override account size for position sizing
        risk_per_trade: Override risk per trade percentage
    """
    try:
        # Run the analysis
        result = analyze_symbol(
            symbol=symbol,
            expirations_to_check=expirations,
            use_demo=demo,
            include_earnings=earnings,
            include_trade_construction=trade_construction,
            include_position_sizing=position_sizing,
            include_trading_decision=trading_decision,
            trade_structure=structure,
            account_size=account_size,
            risk_per_trade=risk_per_trade
        )
        
        if "error" in result:
            print(f"❌ ANALYSIS ERROR: {result['error']}")
            logger.error(f"Analysis error for {symbol}: {result['error']}")
            return
        
        # Use enhanced formatter if available, otherwise fallback to simple output
        if HAS_ENHANCED_CLI:
            try:
                # Create enhanced CLI formatter with logging enabled
                formatter = create_enhanced_cli_formatter(symbol=symbol, log_cli_output=True)
                
                # Format analysis header
                modules_enabled = {
                    "earnings": earnings,
                    "trade_construction": trade_construction,
                    "position_sizing": position_sizing,
                    "trading_decision": trading_decision
                }
                
                formatter.format_analysis_header(
                    symbol=result['symbol'],
                    price=result['price'],
                    price_source=result['price_source'],
                    modules_enabled=modules_enabled,
                    expirations=expirations,
                    demo=demo
                )
                
                # Format calendar analysis (always available)
                calendar_data = result.get("calendar_spread_analysis", {})
                formatter.format_calendar_analysis(calendar_data)
                
                # Format earnings analysis if requested
                if earnings and "earnings_analysis" in result:
                    earnings_data = result["earnings_analysis"]
                    formatter.format_earnings_analysis(earnings_data)
                
                # Format trade construction analysis if requested
                if trade_construction and "trade_construction" in result:
                    trade_data = result["trade_construction"]
                    formatter.format_trade_structures_comparison(trade_data)
                
                # Format position sizing analysis if requested
                if position_sizing and "position_sizing" in result:
                    position_data = result["position_sizing"]
                    formatter.format_position_sizing(position_data)
                
                # Format trading decision analysis if requested
                if trading_decision and "trading_decision" in result:
                    decision_data = result["trading_decision"]
                    formatter.format_trading_decision(decision_data)
                
                # Format footer
                formatter.format_analysis_footer()
                
            except Exception as e:
                logger.error(f"Enhanced CLI formatting failed: {e}")
                print(f"⚠️  Enhanced formatting failed: {e}")
                print("Falling back to basic output format...")
                _format_basic_output(result, symbol, earnings, trade_construction, position_sizing, trading_decision)
                
        else:
            # Fallback to basic output if enhanced formatter not available
            logger.warning("Enhanced CLI formatter not available, using basic output")
            _format_basic_output(result, symbol, earnings, trade_construction, position_sizing, trading_decision)
        
    except Exception as e:
        logger.error(f"Command-line analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")
        print("Check the log file for more details.")


def _format_basic_output(result: dict, symbol: str, earnings: bool, trade_construction: bool, 
                        position_sizing: bool, trading_decision: bool) -> None:
    """
    Fallback basic output formatting when enhanced formatter is not available.
    
    Args:
        result: Analysis result dictionary
        symbol: Stock symbol
        earnings: Whether earnings analysis was requested
        trade_construction: Whether trade construction was requested
        position_sizing: Whether position sizing was requested
        trading_decision: Whether trading decision was requested
    """
    print(f"\n{'='*60}")
    print(f" BASIC OPTIONS ANALYSIS - {symbol.upper()}")
    print(f"{'='*60}")
    
    # Basic symbol info
    print(f"Symbol: {result['symbol']}")
    print(f"Price: ${result['price']:.2f} (Source: {result['price_source']})")
    
    # Calendar analysis
    calendar = result.get("calendar_spread_analysis", {})
    if "error" not in calendar:
        print(f"\n📊 CALENDAR ANALYSIS:")
        recommendation = calendar.get("recommendation", "Unknown")
        signal_count = calendar.get("signal_count", 0)
        print(f"  Recommendation: {recommendation}")
        print(f"  Signal Strength: {signal_count}/3")
        
        if calendar.get("term_structure_slope") is not None:
            slope = calendar["term_structure_slope"]
            print(f"  Term Structure: {slope:.6f} ({'✓' if calendar.get('ts_slope_signal') else '✗'})")
        
        if calendar.get("iv_rv_ratio") is not None:
            ratio = calendar["iv_rv_ratio"]
            print(f"  IV/RV Ratio: {ratio:.2f} ({'✓' if calendar.get('iv_rv_signal') else '✗'})")
        
        if calendar.get("avg_volume_30d") is not None:
            volume = calendar["avg_volume_30d"]
            print(f"  Volume (30d): {volume:,.0f} ({'✓' if calendar.get('volume_signal') else '✗'})")
    
    # Earnings analysis
    if earnings and "earnings_analysis" in result:
        earnings_data = result["earnings_analysis"]
        print(f"\n📅 EARNINGS ANALYSIS:")
        if "error" in earnings_data:
            print(f"  Error: {earnings_data['error']}")
        else:
            event = earnings_data.get("earnings_event", {})
            if event:
                print(f"  Next Earnings: {event.get('date', 'Unknown')}")
    
    # Trade construction
    if trade_construction and "trade_construction" in result:
        trade_data = result["trade_construction"]
        print(f"\n🔧 TRADE CONSTRUCTION:")
        if "error" in trade_data:
            print(f"  Error: {trade_data['error']}")
        else:
            trade = trade_data.get("calendar_trade", {})
            quality = trade_data.get("quality_assessment", {})
            print(f"  Strike: ${trade.get('strike', 0):.2f}")
            print(f"  Net Debit: ${trade.get('net_debit', 0):.2f}")
            print(f"  Quality Score: {quality.get('overall_score', 0):.1f}/100")
    
    # Position sizing
    if position_sizing and "position_sizing" in result:
        position_data = result["position_sizing"]
        print(f"\n💰 POSITION SIZING:")
        if "error" in position_data:
            print(f"  Error: {position_data['error']}")
        else:
            recommended = position_data.get("recommended_position", {})
            print(f"  Position: {recommended.get('contracts', 0)} contracts")
            print(f"  Capital: ${recommended.get('capital_required', 0):,.0f}")
    
    # Trading decision
    if trading_decision and "trading_decision" in result:
        decision_data = result["trading_decision"]
        print(f"\n🚀 TRADING DECISION:")
        if "error" in decision_data:
            print(f"  Error: {decision_data['error']}")
        else:
            decision = decision_data.get("decision", "UNKNOWN")
            confidence = decision_data.get("original_confidence", decision_data.get("confidence", 0))
            print(f"  Decision: {decision}")
            print(f"  Confidence: {confidence:.1%}" if confidence else "  Confidence: N/A")
    
    print(f"\n{'='*60}")
    print("⚠️  FOR EDUCATIONAL PURPOSES ONLY")
    print(f"{'='*60}\n")


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Advanced Options Calculator with Earnings Analysis",
        epilog="For GUI mode, run without arguments. Use --symbol for command-line analysis."
    )
    
    parser.add_argument("--version", action="store_true", help="Show version information")
    parser.add_argument("--symbol", type=str, help="Symbol to analyze (command-line mode)")
    parser.add_argument("--expirations", type=int, default=2, help="Number of expirations to check (default: 2)")
    parser.add_argument("--demo", action="store_true", help="Use demo data instead of live APIs")
    parser.add_argument("--earnings", action="store_true", help="Include earnings analysis (Module 1)")
    parser.add_argument("--trade-construction", action="store_true", help="Include trade construction & P&L analysis (Module 2)")
    parser.add_argument("--position-sizing", action="store_true", help="Include position sizing & risk management (Module 3)")
    parser.add_argument("--trading-decision", action="store_true", help="Include trading decision automation (Module 4)")
    parser.add_argument("--structure", type=str, choices=["calendar", "straddle", "auto"], 
                       help="Trade structure: calendar (default), straddle, or auto-select")
    parser.add_argument("--account-size", type=float, help="Override account size for position sizing calculations")
    parser.add_argument("--risk-per-trade", type=float, help="Override risk per trade percentage (e.g., 0.02 for 2 percent)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    if args.version:
        print_version()
        return
    
    logger.info("=" * 50)
    logger.info("Advanced Options Calculator starting")
    logger.info(f"Version: {__version__}")
    logger.info(f"Arguments: {sys.argv[1:]}")
    
    try:
        if args.symbol:
            # Command-line mode
            if analyze_symbol is None:
                print("❌ Command-line analysis is not available due to missing dependencies.")
                print("Install required packages with: pip install -r requirements.txt")
                sys.exit(1)
            
            logger.info(f"Running in CLI mode for symbol: {args.symbol}")
            analyze_symbol_cli(
                symbol=args.symbol,
                expirations=args.expirations,
                demo=args.demo,
                earnings=args.earnings,
                trade_construction=getattr(args, 'trade_construction', False),
                position_sizing=getattr(args, 'position_sizing', False),
                trading_decision=getattr(args, 'trading_decision', False),
                structure=getattr(args, 'structure', None),
                account_size=getattr(args, 'account_size', None),
                risk_per_trade=getattr(args, 'risk_per_trade', None)
            )
        else:
            # No GUI mode - show help
            print("❌ GUI mode has been deprecated. Use command-line mode instead.")
            print("\nExamples:")
            print("  python main.py --symbol AAPL --earnings")
            print("  python main.py --symbol AAPL --earnings --trade-construction")
            print("  python main.py --demo --symbol AAPL --earnings --trade-construction")
            print("\nFor full help: python main.py --help")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\\nApplication interrupted by user.")
    
    except Exception as e:
        logger.error(f"Application crashed: {e}", exc_info=True)
        print(f"\\nApplication error: {e}")
        print(f"Check log file for details: {log_path}")
        sys.exit(1)
    
    finally:
        logger.info("Advanced Options Calculator finished")


if __name__ == "__main__":
    main()