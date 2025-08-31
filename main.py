#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Options Calculator - Main Entry Point
==============================================

Modular options trading calculator with earnings volatility strategies.

NEW FEATURES (Module 1):
- Earnings calendar integration with precise timing windows
- Multi-provider data sourcing with fallback logic
- Enhanced GUI with earnings analysis panel

USAGE:
    python main.py                    # Launch GUI
    python main.py --help            # Show command-line options
    python main.py --demo            # Launch with demo data
    python main.py --symbol AAPL     # Analyze specific symbol (command-line mode)

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
HAS_GUI = False
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
    from options_trader.gui.interface import run_gui
    HAS_GUI = True
except ImportError as e:
    logger.warning(f"GUI not available: {e}")
    HAS_GUI = False
    run_gui = None


def print_version():
    """Print version information."""
    print(f"Advanced Options Calculator v{__version__}")
    print("Educational options trading analysis tool")
    print(f"Log file: {log_path}")


def analyze_symbol_cli(symbol: str, expirations: int = 2, demo: bool = False, 
                      earnings: bool = False, trade_construction: bool = False,
                      position_sizing: bool = False, trading_decision: bool = False,
                      account_size: float = None, risk_per_trade: float = None) -> None:
    """
    Analyze a symbol in command-line mode.
    
    Args:
        symbol: Stock symbol to analyze
        expirations: Number of expirations to check
        demo: Use demo data
        earnings: Include earnings analysis
        trade_construction: Include trade construction & P&L analysis (Module 2)
        position_sizing: Include position sizing & risk management (Module 3)
        trading_decision: Include trading decision automation (Module 4)
        account_size: Override account size for position sizing
        risk_per_trade: Override risk per trade percentage
    """
    print(f"\\nAnalyzing {symbol.upper()}...")
    print(f"Expirations: {expirations}, Demo: {demo}, Earnings: {earnings}")
    print(f"Modules: Trade Construction: {trade_construction}, Position Sizing: {position_sizing}, Trading Decision: {trading_decision}")
    if position_sizing:
        print(f"Account Settings: Size=${account_size or 'from .env'}, Risk per Trade={risk_per_trade or 'from .env'}")
    print("-" * 60)
    
    try:
        result = analyze_symbol(
            symbol=symbol,
            expirations_to_check=expirations,
            use_demo=demo,
            include_earnings=earnings,
            include_trade_construction=trade_construction,
            include_position_sizing=position_sizing,
            include_trading_decision=trading_decision,
            account_size=account_size,
            risk_per_trade=risk_per_trade
        )
        
        if "error" in result:
            print(f"ERROR: {result['error']}")
            return
        
        # Display basic info
        print(f"Symbol: {result['symbol']}")
        print(f"Price: ${result['price']:.2f} (Source: {result['price_source']})")
        print()
        
        # Display calendar analysis
        calendar = result.get("calendar_spread_analysis", {})
        if "error" not in calendar:
            recommendation = calendar.get("recommendation", "Unknown")
            signal_count = calendar.get("signal_count", 0)
            
            print("CALENDAR SPREAD ANALYSIS:")
            print(f"Recommendation: {recommendation}")
            print(f"Signals: {signal_count}/3")
            
            if calendar.get("term_structure_slope") is not None:
                slope = calendar["term_structure_slope"]
                print(f"Term Structure Slope: {slope:.6f} ({'✓' if calendar.get('ts_slope_signal') else '✗'})")
            
            if calendar.get("iv_rv_ratio") is not None:
                ratio = calendar["iv_rv_ratio"]
                print(f"IV/RV Ratio: {ratio:.2f} ({'✓' if calendar.get('iv_rv_signal') else '✗'})")
            
            if calendar.get("avg_volume_30d") is not None:
                volume = calendar["avg_volume_30d"]
                print(f"Avg Volume (30d): {volume:,.0f} ({'✓' if calendar.get('volume_signal') else '✗'})")
            
            if calendar.get("expected_move_pct") is not None:
                move = calendar["expected_move_pct"]
                print(f"Expected Move: {move:.1f}%")
        
        # Display earnings analysis if requested
        if earnings and "earnings_analysis" in result:
            earnings_data = result["earnings_analysis"]
            print("\\nEARNINGS ANALYSIS:")
            
            if "error" not in earnings_data:
                event = earnings_data.get("earnings_event", {})
                print(f"Next Earnings: {event.get('date', 'Unknown')} {event.get('timing', 'Unknown')}")
                print(f"Confirmed: {'Yes' if event.get('confirmed') else 'No'}")
                
                windows = earnings_data.get("trading_windows", {})
                print(f"Entry Window: {windows.get('entry_start', 'Unknown')} to {windows.get('entry_end', 'Unknown')}")
                print(f"Exit Window: {windows.get('exit_start', 'Unknown')} to {windows.get('exit_end', 'Unknown')}")
                
                time_to_entry = earnings_data.get("time_to_entry")
                if time_to_entry:
                    print(f"Time to Entry: {time_to_entry}")
                
                warnings = earnings_data.get("warnings", [])
                if warnings:
                    print("Warnings:")
                    for warning in warnings:
                        print(f"  ⚠️  {warning}")
            else:
                print(f"Earnings Error: {earnings_data['error']}")
        
        # Display trade construction analysis if requested
        if trade_construction and "trade_construction" in result:
            trade_data = result["trade_construction"]
            print("\\nTRADE CONSTRUCTION & P&L ANALYSIS:")
            
            if "error" not in trade_data:
                trade = trade_data.get("calendar_trade", {})
                quality = trade_data.get("quality_assessment", {})
                greeks = trade_data.get("greeks_analysis", {})
                pnl = trade_data.get("pnl_analysis", {})
                
                # Basic trade info
                print(f"Calendar Trade: {trade.get('trade_type', 'Unknown').replace('_', ' ').title()}")
                print(f"Strike: ${trade.get('strike', 0):.2f}")
                print(f"Front Exp: {trade.get('front_expiration', 'Unknown')}")
                print(f"Back Exp: {trade.get('back_expiration', 'Unknown')}")
                print(f"Net Debit: ${trade.get('net_debit', 0):.2f}")
                print(f"Max Loss: ${trade.get('max_loss', 0):.2f}")
                
                # Breakeven range
                breakeven = trade.get('breakeven_range', (0, 0))
                print(f"Breakeven Range: ${breakeven[0]:.2f} - ${breakeven[1]:.2f}")
                
                # Quality score
                quality_score = quality.get('overall_score', 0)
                print(f"Quality Score: {quality_score:.1f}/100")
                
                # Greeks summary
                if greeks:
                    print(f"Net Delta: {greeks.get('net_delta', 0):.3f}")
                    print(f"Daily Theta: ${greeks.get('theta_dollars', 0):.2f}")
                    print(f"Vega Exposure: ${greeks.get('vega_dollars', 0):.2f}")
                
                # P&L summary
                if pnl:
                    stats = pnl.get('summary_stats', {})
                    print(f"Max Profit: ${stats.get('max_profit', 0):.2f}")
                    print(f"Win Rate: {stats.get('win_rate', 0)*100:.1f}%" if 'win_rate' in stats else "Win Rate: N/A")
                    print(f"Scenarios: {pnl.get('scenario_count', 0)}")
                    
                    crush_params = pnl.get('iv_crush_parameters', {})
                    print(f"IV Crush Model: {crush_params.get('liquidity_tier', 'unknown')} liquidity")
                
                # Validation
                if not trade.get('is_valid', True):
                    print("⚠️  Trade Validation Warnings:")
                    for error in trade.get('validation_errors', []):
                        print(f"  • {error}")
                        
            else:
                print(f"Trade Construction Error: {trade_data['error']}")
        
        # Display position sizing analysis if requested
        if position_sizing and "position_sizing" in result:
            position_data = result["position_sizing"]
            print("\\nPOSITION SIZING & RISK MANAGEMENT:")
            
            if "error" not in position_data:
                # Recommended position
                recommended = position_data.get("recommended_position", {})
                kelly_analysis = position_data.get("kelly_analysis", {})
                risk_assessment = position_data.get("risk_assessment", {})
                account_summary = position_data.get("account_summary", {})
                
                print(f"Recommended Position: {recommended.get('symbol', 'Unknown')} {recommended.get('contracts', 0)} contracts")
                if recommended.get('original_contracts', 0) != recommended.get('contracts', 0):
                    print(f"  (Adjusted from {recommended.get('original_contracts', 0)} contracts: {recommended.get('adjustment_reason', 'Unknown reason')})")
                
                print(f"Capital Required: ${recommended.get('capital_required', 0):,.0f}")
                
                # Kelly analysis
                print(f"Kelly Fraction: {kelly_analysis.get('kelly_fraction', 0):.4f}")
                print(f"Signal Multiplier: {kelly_analysis.get('signal_multiplier', 0):.2f}x ({kelly_analysis.get('signal_strength', 0)} signals)")
                print(f"Risk-Adjusted Kelly: {kelly_analysis.get('risk_adjusted_kelly', 0):.4f}")
                print(f"Account Risk: {kelly_analysis.get('account_risk_pct', 0):.1f}%")
                
                # Account summary
                print(f"Account Size: ${account_summary.get('total_capital', 0):,.0f}")
                print(f"Available Capital: ${account_summary.get('available_capital', 0):,.0f}")
                print(f"Portfolio Utilization: {account_summary.get('utilization_percentage', 0):.1f}%")
                
                # Risk assessment
                compliance_status = "✅ COMPLIANT" if risk_assessment.get("is_compliant", False) else "❌ NON-COMPLIANT"
                print(f"Risk Compliance: {compliance_status} (Score: {risk_assessment.get('risk_score', 0):.1f}/100)")
                
                # Violations and warnings
                violations = risk_assessment.get("violations", [])
                if violations:
                    print("⚠️  Risk Violations:")
                    for violation in violations:
                        print(f"  • {violation}")
                
                warnings = risk_assessment.get("warnings", [])
                if warnings:
                    print("⚠️  Risk Warnings:")
                    for warning in warnings:
                        print(f"  • {warning}")
                
                recommendations = risk_assessment.get("recommendations", [])
                if recommendations:
                    print("💡 Recommendations:")
                    for recommendation in recommendations:
                        print(f"  • {recommendation}")
                
                # Portfolio impact
                portfolio_impact = position_data.get("portfolio_impact", {})
                if portfolio_impact:
                    print(f"Portfolio Impact: Δ{portfolio_impact.get('new_position_delta', 0):.3f}, "
                          f"θ${portfolio_impact.get('estimated_theta_impact', 0):.0f}/day")
                
                # Validation errors
                validation_errors = kelly_analysis.get("validation_errors", [])
                if validation_errors:
                    print("⚠️  Position Sizing Warnings:")
                    for error in validation_errors:
                        print(f"  • {error}")
                        
            else:
                print(f"Position Sizing Error: {position_data['error']}")
        
        # Display trading decision analysis if requested
        if trading_decision and "trading_decision" in result:
            decision_data = result["trading_decision"]
            print("\\nTRADING DECISION AUTOMATION:")
            
            if "error" not in decision_data:
                decision = decision_data.get("decision", "UNKNOWN")
                confidence = decision_data.get("confidence", 0)
                expected_return = decision_data.get("expected_return", 0)
                
                # Main decision with visual indicator
                decision_icon = {"EXECUTE": "🚀", "PASS": "❌", "CONSIDER": "🤔"}.get(decision, "❓")
                print(f"Decision: {decision_icon} {decision}")
                print(f"Confidence: {confidence:.1%}")
                print(f"Expected Return: {expected_return:.1%}")
                
                # Key metrics
                risk_reward = decision_data.get("risk_reward_ratio", 0)
                signal_strength = decision_data.get("signal_strength", 0)
                liquidity_score = decision_data.get("liquidity_score", 0)
                win_probability = decision_data.get("win_probability", 0)
                
                print(f"Risk/Reward Ratio: {risk_reward:.2f}")
                print(f"Signal Strength: {signal_strength:.2f}/3")
                print(f"Liquidity Score: {liquidity_score:.2f}")
                print(f"Win Probability: {win_probability:.1%}")
                
                # Reasoning
                reasoning = decision_data.get("reasoning", [])
                if reasoning:
                    if isinstance(reasoning, list):
                        reasoning_text = "; ".join(reasoning)
                    else:
                        reasoning_text = str(reasoning)
                    print(f"Reasoning: {reasoning_text}")
                
                # Additional metrics
                quality_score = decision_data.get("quality_score", 0)
                position_size = decision_data.get("position_size", 0)
                is_valid = decision_data.get("is_valid", True)
                
                print(f"Quality Score: {quality_score:.1f}/100")
                print(f"Position Size: {position_size} contracts")
                print(f"Valid Decision: {'Yes' if is_valid else 'No'}")
                
                # Validation errors
                validation_errors = decision_data.get("validation_errors", [])
                if validation_errors:
                    print("⚠️  Decision Warnings:")
                    for error in validation_errors:
                        print(f"  • {error}")
                        
            else:
                print(f"Trading Decision Error: {decision_data['error']}")
        
        print()
        
    except Exception as e:
        logger.error(f"Command-line analysis failed: {e}")
        print(f"Analysis failed: {e}")
        print("Check the log file for more details.")


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
                account_size=getattr(args, 'account_size', None),
                risk_per_trade=getattr(args, 'risk_per_trade', None)
            )
        else:
            # GUI mode
            if not HAS_GUI or run_gui is None:
                print("❌ GUI mode is not available due to missing dependencies.")
                print("Install GUI dependencies with: pip install -r requirements.txt")
                print("Or use command-line mode with: python main.py --symbol AAPL")
                sys.exit(1)
            
            logger.info("Running in GUI mode")
            print_version()
            print("Starting GUI... (close terminal window to exit)")
            run_gui()
    
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