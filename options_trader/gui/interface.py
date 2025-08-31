#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Interface
=============

FreeSimpleGUI-based interface for options trading analysis.
Preserves all original functionality while adding Module 1 earnings integration.
"""

import logging
import traceback
from typing import Dict, Any, List

import FreeSimpleGUI as sg

from ..core.analyzer import analyze_symbol

logger = logging.getLogger("options_trader.gui")


def build_layout() -> List[List[Any]]:
    """
    Build the main application layout.
    
    Enhanced with earnings analysis toggle and improved result display.
    
    Returns:
        Layout list for FreeSimpleGUI window
    """
    sg.theme("SystemDefault")
    
    # Header section
    header = [sg.Text("Advanced Options Calculator & Calendar Spread Analyzer", font=("Helvetica", 16, "bold"))]
    
    # Input controls - enhanced with earnings toggle
    row1 = [
        sg.Text("Symbol:"), sg.Input(key="-SYMBOL-", size=(14, 1)),
        sg.Text("Expirations:"), sg.Spin(values=[1,2,3,4,5], initial_value=2, key="-NEXP-", size=(3,1)),
        sg.Checkbox("Earnings Analysis", key="-EARNINGS-", tooltip="Include Module 1 earnings calendar analysis"),
        sg.Checkbox("Debug panel", key="-DEBUG-"), sg.Checkbox("Demo mode", key="-DEMO-"),
        sg.Button("Submit", bind_return_key=True), sg.Button("Exit")
    ]
    
    # Main results - divided into two columns
    left_col = [
        [sg.Text("OPTIONS CHAIN ANALYSIS", font=("Helvetica", 12, "bold"))],
        [sg.Multiline(key="-CHAIN-RESULTS-", size=(50, 20), disabled=True, autoscroll=True, 
                     font=("Courier New", 9), background_color="#f8f9fa")]
    ]
    
    right_col = [
        [sg.Text("CALENDAR SPREAD ANALYSIS", font=("Helvetica", 12, "bold"))],
        [sg.Multiline(key="-CALENDAR-RESULTS-", size=(50, 20), disabled=True, autoscroll=True, 
                     font=("Courier New", 9), background_color="#f0f8ff")]
    ]
    
    # Results section with two columns
    results_section = [
        [sg.Column(left_col, vertical_alignment='top'), 
         sg.VerticalSeparator(), 
         sg.Column(right_col, vertical_alignment='top')]
    ]
    
    # Summary section for key metrics
    summary_frame = [
        [sg.Text("TRADING RECOMMENDATION", font=("Helvetica", 12, "bold"))],
        [sg.Multiline(key="-SUMMARY-", size=(104, 4), disabled=True, autoscroll=True, 
                     font=("Courier New", 10), background_color="#fff9e6")]
    ]
    
    # NEW: Earnings section (Module 1)
    earnings_frame = [
        [sg.Text("EARNINGS CALENDAR & TIMING", font=("Helvetica", 12, "bold"))],
        [sg.Multiline(key="-EARNINGS-RESULTS-", size=(104, 6), disabled=True, autoscroll=True,
                     font=("Courier New", 9), background_color="#f0fff0", visible=False)]
    ]
    
    # Debug section
    debug_frame = [[sg.Multiline(key="-DEBUGOUT-", size=(104, 10), disabled=True, autoscroll=True, 
                                 visible=False, font=("Courier New", 9))]]
    
    # Footer
    footer = [
        sg.Text("TIP: Use 2+ expirations for calendar analysis | Enable 'Earnings Analysis' for Module 1 timing  |  ", text_color="gray"),
        sg.Text("Logs: ./trade_calculator.log", text_color="gray")
    ]
    
    # Complete layout
    layout = [
        header,
        row1,
        [sg.Frame("Analysis Results", results_section, font=("Helvetica", 11))],
        [sg.Frame("Trading Recommendation", summary_frame, font=("Helvetica", 11))],
        [sg.Frame("Earnings Calendar & Timing", earnings_frame, key="-EARNINGSFRAME-", visible=False, font=("Helvetica", 11))],
        [sg.Frame("Debug Output", debug_frame, key="-DEBUGFRAME-", visible=False, font=("Helvetica", 10))],
        footer
    ]
    
    return layout


def format_chain_results(result: Dict[str, Any]) -> str:
    """Format options chain analysis for the left panel."""
    if "error" in result:
        return f"ERROR: {result['error']}"

    lines: List[str] = []
    
    # Header with basic info
    lines.append(f"SYMBOL: {result['symbol']}")
    lines.append(f"Price: ${result['price']:.2f}")
    lines.append(f"Source: {result.get('price_source', 'unknown')}")
    lines.append(f"Cached: {'Yes' if result.get('price_cached') else 'No'}")
    lines.append("=" * 45)
    
    # Options chain data
    for i, item in enumerate(result.get("expirations", []), 1):
        exp = item.get("expiration", "?")
        if "error" in item:
            lines.append(f"Exp #{i}: {exp}")
            lines.append(f"ERROR: {item['error']}")
            lines.append("")
            continue

        # Extract data
        atm_iv = item.get("atm_iv")
        straddle = item.get("straddle_mid")
        call_mid = item.get("call_mid")
        put_mid = item.get("put_mid")
        strike_c = item.get("atm_strike_call")
        strike_p = item.get("atm_strike_put")
        src = item.get("chain_source", "?")

        # Format values
        iv_txt = f"{atm_iv:.4f}" if isinstance(atm_iv, (int, float)) else "n/a"
        cm_txt = f"${call_mid:.2f}" if isinstance(call_mid, (int, float)) else "n/a"
        pm_txt = f"${put_mid:.2f}" if isinstance(put_mid, (int, float)) else "n/a"
        sm_txt = f"${straddle:.2f}" if isinstance(straddle, (int, float)) else "n/a"

        lines.append(f"Exp #{i}: {exp}")
        lines.append(f"Source: {src}")
        lines.append(f"ATM: C@{strike_c} P@{strike_p}")
        lines.append(f"IV: {iv_txt}")
        lines.append(f"Call: {cm_txt} | Put: {pm_txt}")
        lines.append(f"Straddle: {sm_txt}")
        lines.append("")
    
    return "\\n".join(lines)


def format_calendar_results(result: Dict[str, Any]) -> str:
    """Format calendar spread analysis for the right panel."""
    if "error" in result:
        return "Calendar spread analysis requires\\nmultiple expirations.\\n\\nTry increasing 'Expirations' to 2+."
    
    calendar_data = result.get("calendar_spread_analysis", {})
    if "error" in calendar_data:
        return f"Calendar Analysis Error:\\n{calendar_data['error']}"
    
    lines: List[str] = []
    
    lines.append("TERM STRUCTURE METRICS")
    lines.append("=" * 45)
    
    # Term Structure Analysis
    ts_slope = calendar_data.get("term_structure_slope")
    if ts_slope is not None:
        lines.append(f"Term Structure Slope: {ts_slope:.6f}")
        signal = "✓ BEARISH TS" if calendar_data.get("ts_slope_signal", False) else "✗ Not Bearish"
        lines.append(f"TS Signal: {signal}")
    else:
        lines.append("Term Structure Slope: n/a")
    
    lines.append("")
    
    # Volatility Analysis
    lines.append("VOLATILITY ANALYSIS")
    lines.append("-" * 45)
    iv30 = calendar_data.get("iv30")
    rv30 = calendar_data.get("rv30")
    iv_rv_ratio = calendar_data.get("iv_rv_ratio")
    
    if iv30 is not None:
        lines.append(f"30-Day IV: {iv30:.4f}")
    if rv30 is not None:
        lines.append(f"30-Day RV: {rv30:.4f}")
    if iv_rv_ratio is not None:
        lines.append(f"IV/RV Ratio: {iv_rv_ratio:.2f}")
        signal = "✓ HIGH IV/RV" if calendar_data.get("iv_rv_signal", False) else "✗ Low IV/RV"
        lines.append(f"IV/RV Signal: {signal}")
    else:
        lines.append("IV/RV Analysis: Insufficient data")
    
    lines.append("")
    
    # Volume & Expected Move
    lines.append("MARKET METRICS")
    lines.append("-" * 45)
    
    expected_move = calendar_data.get("expected_move_pct")
    if expected_move is not None:
        lines.append(f"Expected Move: {expected_move:.1f}%")
    
    avg_vol = calendar_data.get("avg_volume_30d")
    if avg_vol is not None:
        lines.append(f"Avg Volume (30d): {avg_vol:,.0f}")
        vol_signal = "✓ HIGH VOL" if calendar_data.get("volume_signal", False) else "✗ Low Vol"
        lines.append(f"Volume Signal: {vol_signal}")
    
    lines.append("")
    
    # Signals Summary
    signal_count = calendar_data.get("signal_count", 0)
    lines.append(f"SIGNALS: {signal_count}/3")
    signals = []
    if calendar_data.get("ts_slope_signal"): signals.append("TS")
    if calendar_data.get("iv_rv_signal"): signals.append("IV/RV")  
    if calendar_data.get("volume_signal"): signals.append("VOL")
    
    if signals:
        lines.append(f"Active: {', '.join(signals)}")
    else:
        lines.append("Active: None")
    
    return "\\n".join(lines)


def format_summary_results(result: Dict[str, Any]) -> str:
    """Format trading recommendation summary."""
    if "error" in result:
        return f"Analysis Error: {result['error']}"
    
    calendar_data = result.get("calendar_spread_analysis", {})
    if "error" in calendar_data:
        return "⚠️  Need 2+ expirations for calendar spread analysis. Increase 'Expirations' setting."
    
    lines: List[str] = []
    
    # Get recommendation
    recommendation = calendar_data.get("recommendation", "Analysis incomplete")
    signal_count = calendar_data.get("signal_count", 0)
    
    # Add emoji based on recommendation
    if "BULLISH" in recommendation:
        emoji = "🟢"
    elif "NEUTRAL" in recommendation:
        emoji = "🟡"
    else:
        emoji = "🔴"
    
    lines.append(f"{emoji} {recommendation}")
    lines.append("")
    
    # Add key metrics in summary format
    symbol = result.get("symbol", "")
    price = result.get("price", 0)
    expected_move = calendar_data.get("expected_move_pct")
    
    summary_parts = [f"Symbol: {symbol}", f"Price: ${price:.2f}"]
    
    if expected_move:
        summary_parts.append(f"Expected Move: {expected_move:.1f}%")
        
    if signal_count is not None:
        summary_parts.append(f"Calendar Signals: {signal_count}/3")
    
    lines.append(" | ".join(summary_parts))
    
    return "\\n".join(lines)


def format_earnings_results(result: Dict[str, Any]) -> str:
    """Format earnings analysis results (NEW - Module 1)."""
    earnings_data = result.get("earnings_analysis", {})
    
    if "error" in earnings_data:
        return f"Earnings Analysis: {earnings_data['error']}"
    
    lines: List[str] = []
    
    # Earnings event info
    event = earnings_data.get("earnings_event", {})
    lines.append("NEXT EARNINGS EVENT")
    lines.append("=" * 50)
    lines.append(f"Date: {event.get('date', 'Unknown')}")
    lines.append(f"Timing: {event.get('timing', 'Unknown')} ({'Before Market Open' if event.get('timing') == 'BMO' else 'After Market Close'})")
    lines.append(f"Confirmed: {'Yes' if event.get('confirmed') else 'No'}")
    lines.append(f"Source: {event.get('source', 'Unknown')}")
    lines.append("")
    
    # Trading windows
    windows = earnings_data.get("trading_windows", {})
    lines.append("TRADING WINDOWS (Your Timezone)")
    lines.append("-" * 50)
    lines.append(f"Entry Window:  {windows.get('entry_start', 'N/A')} to {windows.get('entry_end', 'N/A')}")
    lines.append(f"Exit Window:   {windows.get('exit_start', 'N/A')} to {windows.get('exit_end', 'N/A')}")
    lines.append(f"Market TZ: {windows.get('market_timezone', 'N/A')}")
    lines.append("")
    
    # Timing status
    time_to_entry = earnings_data.get("time_to_entry")
    time_to_exit = earnings_data.get("time_to_exit")
    
    lines.append("TIMING STATUS")
    lines.append("-" * 50)
    if time_to_entry:
        lines.append(f"Time to Entry: {time_to_entry}")
    else:
        lines.append("Time to Entry: Window passed or active")
    
    if time_to_exit:
        lines.append(f"Time to Exit: {time_to_exit}")
    else:
        lines.append("Time to Exit: Window passed or active")
    
    # Warnings
    warnings = earnings_data.get("warnings", [])
    if warnings:
        lines.append("")
        lines.append("WARNINGS")
        lines.append("-" * 50)
        for warning in warnings:
            lines.append(f"⚠️  {warning}")
    
    return "\\n".join(lines)


def run_gui():
    """
    Run the main GUI application.
    
    Enhanced with Module 1 earnings analysis integration.
    """
    logger.info("Starting GUI application")
    
    window = sg.Window(
        "Advanced Options Calculator & Calendar Spread Analyzer", 
        build_layout(), 
        finalize=True
    )
    
    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, "Exit"):
            logger.info("GUI application closing")
            break
            
        if event == "Submit":
            try:
                # Get input values
                symbol = values.get("-SYMBOL-", "").strip()
                n_exp = int(values.get("-NEXP-", 1) or 1)
                show_debug = bool(values.get("-DEBUG-", False))
                demo_mode = bool(values.get("-DEMO-", False))
                include_earnings = bool(values.get("-EARNINGS-", False))  # NEW
                
                logger.info(f"Processing request: {symbol}, exps={n_exp}, demo={demo_mode}, earnings={include_earnings}")
                
                # Update panel visibility
                window["-DEBUGFRAME-"].update(visible=show_debug)
                window["-DEBUGOUT-"].update(visible=show_debug)
                window["-EARNINGSFRAME-"].update(visible=include_earnings)  # NEW
                window["-EARNINGS-RESULTS-"].update(visible=include_earnings)  # NEW
                
                # Clear all result panels
                window["-CHAIN-RESULTS-"].update("")
                window["-CALENDAR-RESULTS-"].update("")
                window["-SUMMARY-"].update("")
                if include_earnings:
                    window["-EARNINGS-RESULTS-"].update("")  # NEW
                
                if show_debug:
                    window["-DEBUGOUT-"].update("Starting analysis...")
                
                # Run analysis with earnings if requested
                result = analyze_symbol(
                    symbol, 
                    expirations_to_check=n_exp, 
                    use_demo=demo_mode,
                    include_earnings=include_earnings  # NEW
                )
                
                # Format and display results
                chain_text = format_chain_results(result)
                calendar_text = format_calendar_results(result)
                summary_text = format_summary_results(result)
                
                window["-CHAIN-RESULTS-"].update(chain_text)
                window["-CALENDAR-RESULTS-"].update(calendar_text)
                window["-SUMMARY-"].update(summary_text)
                
                # NEW: Display earnings results if included
                if include_earnings:
                    earnings_text = format_earnings_results(result)
                    window["-EARNINGS-RESULTS-"].update(earnings_text)
                
                if show_debug:
                    window["-DEBUGOUT-"].print("Raw result dict:")
                    window["-DEBUGOUT-"].print(result)
                
                logger.info(f"Analysis completed for {symbol}")
                    
            except Exception as e:
                logger.error(f"GUI submit handler failed: {e}")
                error_msg = f"Error: Unexpected failure in GUI submit handler. Check logs for details.\\n{str(e)}"
                
                window["-CHAIN-RESULTS-"].update(error_msg)
                window["-CALENDAR-RESULTS-"].update("Analysis failed")
                window["-SUMMARY-"].update("🔴 Error occurred")
                
                if include_earnings:
                    window["-EARNINGS-RESULTS-"].update("Earnings analysis failed")
                
                if values.get("-DEBUG-", False):
                    window["-DEBUGOUT-"].print("Exception details:")
                    window["-DEBUGOUT-"].print(traceback.format_exc())
    
    window.close()
    logger.info("GUI application closed")