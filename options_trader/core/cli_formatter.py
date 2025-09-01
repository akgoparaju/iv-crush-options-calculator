#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced CLI Output Formatter
============================

Professional table-based CLI output formatting for the options trading system with:
- ASCII table generation for structured data display
- Side-by-side comparison tables for Calendar vs Straddle analysis
- Dual output system (console + dedicated log files)
- Professional presentation with consistent formatting
- Comprehensive information organization and visual hierarchy
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import os

logger = logging.getLogger("options_trader.cli_formatter")


class TableFormatter:
    """Professional ASCII table formatter for structured data display"""
    
    @staticmethod
    def create_table(headers: List[str], rows: List[List[str]], title: str = None, width: int = 80) -> str:
        """
        Create a professional ASCII table with borders and proper alignment
        
        Args:
            headers: Column headers
            rows: Table data rows  
            title: Optional table title
            width: Maximum table width
            
        Returns:
            Formatted ASCII table string
        """
        if not headers or not rows:
            return ""
        
        # Helper function to wrap text to fit within width
        def wrap_text(text: str, max_width: int) -> List[str]:
            """Wrap text to fit within max_width, preserving words"""
            if len(text) <= max_width:
                return [text]
            
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                if not current_line:
                    current_line = word
                elif len(current_line + " " + word) <= max_width:
                    current_line += " " + word
                else:
                    lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            return lines
        
        # Calculate column widths based on content
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(min(max_width + 2, width // len(headers)))  # Add padding, respect max width
        
        # Process rows to handle text wrapping
        wrapped_rows = []
        for row in rows:
            # Wrap text in each cell and find max line count
            wrapped_cells = []
            max_lines = 1
            
            for i, width in enumerate(col_widths):
                cell_value = str(row[i]) if i < len(row) else ""
                wrapped_lines = wrap_text(cell_value, width - 1)  # Account for padding
                wrapped_cells.append(wrapped_lines)
                max_lines = max(max_lines, len(wrapped_lines))
            
            # Create multi-line row with proper alignment
            for line_num in range(max_lines):
                row_line_data = []
                for cell_lines in wrapped_cells:
                    if line_num < len(cell_lines):
                        row_line_data.append(cell_lines[line_num])
                    else:
                        row_line_data.append("")  # Empty line for shorter cells
                wrapped_rows.append(row_line_data)
        
        # Build table components
        lines = []
        
        # Title section
        if title:
            total_width = sum(col_widths) + len(headers) + 1
            title_border = "┌" + "─" * (total_width - 2) + "┐"
            title_padding = max(0, (total_width - 2 - len(title)) // 2)
            title_line = f"│{' ' * title_padding}{title}{' ' * (total_width - 2 - title_padding - len(title))}│"
            
            lines.append(title_border)
            lines.append(title_line)
            lines.append("├" + "─" * (total_width - 2) + "┤")
        
        # Header section
        header_line = "│"
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            header_line += f" {header:<{width-1}}│"
        
        if not title:
            top_border = "┌" + "─" * (len(header_line) - 2) + "┐"
            lines.append(top_border)
        
        lines.append(header_line)
        
        # Header separator
        separator = "├"
        for width in col_widths:
            separator += "─" * width + "┼"
        separator = separator[:-1] + "┤"
        lines.append(separator)
        
        # Data rows (now with wrapped text)
        for row in wrapped_rows:
            row_line = "│"
            for i, width in enumerate(col_widths):
                cell_value = str(row[i]) if i < len(row) else ""
                row_line += f" {cell_value:<{width-1}}│"
            lines.append(row_line)
        
        # Bottom border
        bottom_border = "└" + "─" * (len(header_line) - 2) + "┘"
        lines.append(bottom_border)
        
        return "\n".join(lines)
    
    @staticmethod
    def create_comparison_table(left_data: Dict[str, str], right_data: Dict[str, str], 
                              left_title: str, right_title: str, main_title: str = None) -> str:
        """
        Create side-by-side comparison table for Calendar vs Straddle analysis
        
        Args:
            left_data: Left column data {metric: value}
            right_data: Right column data {metric: value}  
            left_title: Left column title (e.g., "Calendar Spread")
            right_title: Right column title (e.g., "ATM Straddle")
            main_title: Optional main table title
            
        Returns:
            Formatted comparison table string
        """
        # Get all unique metrics, preserve order from left_data first, then right_data
        all_metrics = list(left_data.keys())
        for metric in right_data.keys():
            if metric not in all_metrics:
                all_metrics.append(metric)
        
        headers = ["Metric", left_title, right_title]
        rows = []
        
        for metric in all_metrics:
            left_val = left_data.get(metric, "N/A")
            right_val = right_data.get(metric, "N/A")
            rows.append([metric, left_val, right_val])
        
        return TableFormatter.create_table(headers, rows, main_title)
    
    @staticmethod
    def create_summary_box(title: str, content: List[str], width: int = 60) -> str:
        """
        Create a bordered summary box for key information
        
        Args:
            title: Box title
            content: List of content lines
            width: Box width
            
        Returns:
            Formatted summary box
        """
        lines = []
        
        # Top border with title
        title_line = f"┌─ {title} " + "─" * (width - len(title) - 4) + "┐"
        lines.append(title_line)
        
        # Content lines
        for line in content:
            # Wrap long lines
            if len(line) > width - 4:
                line = line[:width-7] + "..."
            padded_line = f"│ {line:<{width-3}} │"
            lines.append(padded_line)
        
        # Bottom border
        bottom_border = "└" + "─" * (width - 2) + "┘"
        lines.append(bottom_border)
        
        return "\n".join(lines)


class CLIOutputLogger:
    """Enhanced dual output system for console and dedicated CLI log files"""
    
    def __init__(self, log_cli_output: bool = True, symbol: str = "ANALYSIS"):
        """
        Initialize CLI output logger with dedicated log file for results
        
        Args:
            log_cli_output: Whether to log CLI output to files
            symbol: Symbol being analyzed (for log file naming)
        """
        self.log_cli_output = log_cli_output
        self.symbol = symbol.upper()
        self.cli_logger = None
        
        # Setup CLI output logging if enabled
        if log_cli_output:
            self._setup_cli_logger()
    
    def _setup_cli_logger(self):
        """Setup dedicated CLI output logger with timestamped file"""
        try:
            # Create logs directory if it doesn't exist
            logs_dir = "logs"
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            
            # Create CLI-specific log file with symbol and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cli_log_file = os.path.join(logs_dir, f"cli_analysis_{self.symbol}_{timestamp}.log")
            
            # Create dedicated logger instance
            self.cli_logger = logging.getLogger(f"options_trader.cli_output.{self.symbol}")
            
            # Prevent duplicate handlers
            if not self.cli_logger.handlers:
                # Create file handler for CLI output
                cli_handler = logging.FileHandler(cli_log_file, mode='w', encoding='utf-8')
                cli_formatter = logging.Formatter('%(message)s')  # Plain format for readability
                cli_handler.setFormatter(cli_formatter)
                cli_handler.setLevel(logging.INFO)
                
                self.cli_logger.addHandler(cli_handler)
                self.cli_logger.setLevel(logging.INFO)
                self.cli_logger.propagate = False  # Prevent duplicate logging
                
                # Log header information
                self.cli_logger.info("=" * 80)
                self.cli_logger.info(f"OPTIONS TRADING ANALYSIS LOG - {self.symbol}")
                self.cli_logger.info(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.cli_logger.info("=" * 80)
                
                logger.info(f"CLI output logging enabled: {cli_log_file}")
            
        except Exception as e:
            logger.warning(f"Failed to setup CLI output logging: {e}")
            self.log_cli_output = False
            self.cli_logger = None
    
    def output(self, message: str):
        """
        Output message to both console and log file
        
        Args:
            message: Message to output to both console and log
        """
        # Always print to console
        print(message)
        
        # Log to file if enabled and logger is available
        if self.log_cli_output and self.cli_logger:
            try:
                self.cli_logger.info(message)
            except Exception as e:
                logger.debug(f"Failed to log CLI output: {e}")
    
    def section_header(self, title: str, level: int = 1, width: int = 80):
        """
        Create formatted section header with different levels
        
        Args:
            title: Section title
            level: Header level (1=main, 2=sub, 3=subsub)
            width: Header width
        """
        if level == 1:
            # Main section header
            separator = "=" * width
            padded_title = f" {title} ".center(width, "=")
            header = f"\n{separator}\n{padded_title}\n{separator}"
        elif level == 2:
            # Sub section header  
            separator = "-" * width
            padded_title = f" {title} ".center(width, "-")
            header = f"\n{padded_title}\n{separator}"
        else:
            # Sub-sub section header
            header = f"\n▸ {title}"
            header += "\n" + "·" * min(len(title) + 2, width)
        
        self.output(header)
        return header


class EnhancedCLIFormatter:
    """
    Comprehensive CLI formatter for complete options analysis output
    Combines professional table formatting with dual output logging
    """
    
    def __init__(self, symbol: str, log_cli_output: bool = True):
        """
        Initialize enhanced CLI formatter
        
        Args:
            symbol: Stock symbol being analyzed
            log_cli_output: Whether to enable CLI output logging
        """
        self.symbol = symbol.upper()
        self.output = CLIOutputLogger(log_cli_output, symbol)
        self.table = TableFormatter()
    
    def format_analysis_header(self, symbol: str, price: float, price_source: str, 
                             modules_enabled: Dict[str, bool], expirations: int, demo: bool):
        """Format comprehensive analysis header with symbol info and configuration"""
        
        self.output.section_header("ADVANCED OPTIONS TRADING ANALYSIS", level=1)
        
        # Analysis overview summary box
        overview_content = [
            f"Symbol: {symbol}",
            f"Current Price: ${price:.2f} ({price_source})",
            f"Analysis Mode: {'DEMO' if demo else 'LIVE DATA'}",
            f"Expirations: {expirations}",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        overview_box = self.table.create_summary_box("Analysis Overview", overview_content)
        self.output.output(overview_box)
        
        # Enabled modules table
        modules_headers = ["Module", "Status", "Description"]
        modules_rows = []
        
        module_info = {
            "earnings": ("Earnings Analysis", "Timing windows and earnings calendar"),
            "trade_construction": ("Trade Construction", "Calendar spreads and straddle analysis"),  
            "position_sizing": ("Position Sizing", "Kelly criterion and risk management"),
            "trading_decision": ("Trading Decision", "Automated decision engine")
        }
        
        for key, (name, desc) in module_info.items():
            status = "✅ ENABLED" if modules_enabled.get(key, False) else "❌ DISABLED"
            modules_rows.append([name, status, desc])
        
        modules_table = self.table.create_table(modules_headers, modules_rows, "Analysis Modules Configuration")
        self.output.output(modules_table)
    
    def format_calendar_analysis(self, calendar_data: Dict[str, Any]):
        """Format calendar spread analysis with comprehensive signal table"""
        
        self.output.section_header("CALENDAR SPREAD STRATEGY ANALYSIS", level=2)
        
        if "error" in calendar_data:
            error_box = self.table.create_summary_box("Analysis Error", [f"❌ {calendar_data['error']}"])
            self.output.output(error_box)
            return
        
        # Strategy signals detailed table
        signals_headers = ["Signal Component", "Actual Value", "Threshold", "Status", "Weight"]
        signals_rows = []
        
        # Term structure slope signal
        slope = calendar_data.get("term_structure_slope")
        if slope is not None:
            status = "✅ PASS" if calendar_data.get('ts_slope_signal') else "❌ FAIL"
            signals_rows.append([
                "Term Structure Slope",
                f"{slope:.6f}",
                "≤ -0.00406",
                status,
                "Critical"
            ])
        
        # IV/RV Ratio signal
        iv_rv = calendar_data.get("iv_rv_ratio")
        if iv_rv is not None:
            status = "✅ PASS" if calendar_data.get('iv_rv_signal') else "❌ FAIL"
            signals_rows.append([
                "IV/RV Ratio", 
                f"{iv_rv:.3f}",
                "≥ 1.25",
                status,
                "High"
            ])
        
        # Volume signal
        volume = calendar_data.get("avg_volume_30d")
        if volume is not None:
            status = "✅ PASS" if calendar_data.get('volume_signal') else "❌ FAIL"
            signals_rows.append([
                "30-Day Avg Volume",
                f"{volume:,.0f}",
                "≥ 1,500,000", 
                status,
                "Medium"
            ])
        
        if signals_rows:
            signals_table = self.table.create_table(signals_headers, signals_rows, "Strategy Signal Analysis")
            self.output.output(signals_table)
        
        # Analysis summary
        recommendation = calendar_data.get("recommendation", "Unknown")
        signal_count = calendar_data.get("signal_count", 0)
        expected_move = calendar_data.get("expected_move_pct", 0)
        
        # Color-coded recommendation based on signal strength
        if signal_count == 3:
            rec_display = f"🟢 {recommendation} (Strong)"
        elif signal_count == 2:
            rec_display = f"🟡 {recommendation} (Moderate)"
        else:
            rec_display = f"🔴 {recommendation} (Weak)"
        
        summary_content = [
            f"Strategy Recommendation: {rec_display}",
            f"Signal Strength: {signal_count}/3 ({signal_count/3*100:.0f}%)",
            f"Expected Move: {expected_move:.1f}%"
        ]
        
        summary_box = self.table.create_summary_box("Calendar Strategy Summary", summary_content)
        self.output.output(summary_box)
    
    def format_trade_structures_comparison(self, trade_data: Dict[str, Any]):
        """Format comprehensive side-by-side calendar vs straddle comparison"""
        
        self.output.section_header("TRADE STRUCTURE ANALYSIS", level=2)
        
        if "error" in trade_data:
            error_box = self.table.create_summary_box("Trade Construction Error", [f"❌ {trade_data['error']}"])
            self.output.output(error_box)
            return
        
        # Extract trade data
        calendar_trade = trade_data.get("calendar_trade", {})
        straddle_data = trade_data.get("straddle_construction", {})
        straddle_trade = straddle_data.get("straddle_trade", {}) if straddle_data else {}
        pnl_data = trade_data.get("pnl_analysis", {})
        greeks_data = trade_data.get("greeks_analysis", {})
        quality_data = trade_data.get("quality_assessment", {})
        
        if not calendar_trade and not straddle_trade:
            self.output.output("❌ No trade structures available for comparison")
            return
        
        # 1. Basic Structure Comparison
        calendar_basics = {}
        straddle_basics = {}
        
        if calendar_trade:
            trade_type = calendar_trade.get('trade_type', 'call_calendar').replace('_', ' ').title()
            breakeven = calendar_trade.get('breakeven_range', (0, 0))
            
            calendar_basics.update({
                "Structure Type": trade_type,
                "Strike Price": f"${calendar_trade.get('strike', 0):.2f}",
                "Front Expiration": calendar_trade.get('front_expiration', 'Unknown'),
                "Back Expiration": calendar_trade.get('back_expiration', 'Unknown'),
                "Entry Cost": f"${calendar_trade.get('net_debit', 0):.2f} (Debit)",
                "Max Loss": f"${calendar_trade.get('max_loss', 0):.2f}",
                "Breakeven Range": f"${breakeven[0]:.2f} - ${breakeven[1]:.2f}",
                "Risk Profile": "Limited Risk/Limited Reward"
            })
            
            if pnl_data and 'summary_stats' in pnl_data:
                max_profit = pnl_data['summary_stats'].get('max_profit', 0)
                calendar_basics["Max Profit"] = f"${max_profit:.2f}"
        
        if straddle_trade:
            lower = straddle_trade.get('breakeven_lower', 0)
            upper = straddle_trade.get('breakeven_upper', 0)
            
            straddle_basics.update({
                "Structure Type": "Short ATM Straddle",
                "Strike Price": f"${straddle_trade.get('strike', 0):.2f}",
                "Front Expiration": straddle_trade.get('expiration', 'Unknown'),
                "Back Expiration": "N/A (Single Expiration)",
                "Entry Cost": f"${straddle_trade.get('net_credit', 0):.2f} (Credit)",
                "Max Loss": straddle_trade.get('max_risk', 'UNLIMITED'),
                "Breakeven Range": f"${lower:.2f} - ${upper:.2f}",
                "Risk Profile": "Unlimited Risk/Limited Reward",
                "Max Profit": f"${straddle_trade.get('max_profit', 0):.2f}"
            })
        
        # Create structure comparison table
        if calendar_basics or straddle_basics:
            structure_table = self.table.create_comparison_table(
                calendar_basics, straddle_basics,
                "Calendar Spread", "ATM Straddle",
                "Trade Structure Comparison"
            )
            self.output.output(structure_table)
        
        # 2. Risk & Greeks Comparison
        calendar_greeks = {}
        straddle_greeks = {}
        
        if calendar_trade and greeks_data:
            calendar_greeks.update({
                "Net Delta": f"{greeks_data.get('net_delta', 0):.4f}",
                "Gamma Exposure": f"{greeks_data.get('net_gamma', 0):.4f}",
                "Daily Theta": f"${greeks_data.get('theta_dollars', 0):.2f}",
                "Vega Risk": f"${greeks_data.get('vega_dollars', 0):.2f}",
                "Quality Score": f"{quality_data.get('overall_score', 0):.1f}/100"
            })
            
            if pnl_data and 'summary_stats' in pnl_data:
                stats = pnl_data['summary_stats']
                win_rate = stats.get('win_rate', 0)
                calendar_greeks["Win Rate"] = f"{win_rate*100:.1f}%" if win_rate else "N/A"
        
        if straddle_trade:
            straddle_greeks.update({
                "Net Delta": f"{straddle_trade.get('net_delta', 0):.4f}",
                "Gamma Exposure": f"{straddle_trade.get('net_gamma', 0):.4f}",
                "Daily Theta": f"${straddle_trade.get('net_theta', 0):.2f}",
                "Vega Risk": f"${straddle_trade.get('net_vega', 0):.2f}",
                "Quality Score": f"{straddle_trade.get('liquidity_score', 0)*10:.1f}/100",
                "Win Rate": f"{straddle_trade.get('probability_of_profit', 0)*100:.1f}%"
            })
        
        if calendar_greeks or straddle_greeks:
            greeks_table = self.table.create_comparison_table(
                calendar_greeks, straddle_greeks,
                "Calendar Spread", "ATM Straddle", 
                "Risk & Greeks Analysis"
            )
            self.output.output(greeks_table)
        
        # 3. P&L Scenario Analysis (if available)
        if pnl_data and 'scenario_count' in pnl_data:
            scenario_headers = ["P&L Metric", "Value"]
            scenario_rows = [
                ["Scenarios Analyzed", f"{pnl_data.get('scenario_count', 0)}"],
                ["IV Crush Model", pnl_data.get('iv_crush_parameters', {}).get('liquidity_tier', 'Unknown')]
            ]
            
            if 'summary_stats' in pnl_data:
                stats = pnl_data['summary_stats']
                scenario_rows.extend([
                    ["Expected Return", f"${stats.get('expected_value', 0):.2f}"],
                    ["Profit Scenarios", f"{stats.get('profitable_scenarios', 0)}"],
                    ["Break-even Scenarios", f"{stats.get('breakeven_scenarios', 0)}"]
                ])
            
            scenario_table = self.table.create_table(scenario_headers, scenario_rows, "P&L Scenario Analysis")
            self.output.output(scenario_table)
        
        # 4. Structure Recommendation
        structure_selection = trade_data.get("structure_selection", {})
        if structure_selection:
            requested = structure_selection.get('requested_structure', 'Unknown').title()
            recommended = structure_selection.get('recommended_structure', 'Unknown').title()
            
            # Color-code recommendation
            if recommended.lower() == 'calendar':
                rec_display = f"🔵 {recommended} (Conservative)"
            else:
                rec_display = f"🟠 {recommended} (Aggressive)"
            
            comparison = structure_selection.get("structure_comparison", {})
            reasoning = comparison.get('reasoning', 'Not provided')
            
            recommendation_content = [
                f"Requested Structure: {requested}",
                f"Recommended Structure: {rec_display}",
                f"Reasoning: {reasoning}"
            ]
            
            rec_box = self.table.create_summary_box("Structure Recommendation", recommendation_content)
            self.output.output(rec_box)
        
        # 5. Risk Warnings for Straddle
        if straddle_data and 'risk_analysis' in straddle_data:
            risk_warnings = straddle_data['risk_analysis'].get('risk_warnings', [])
            if risk_warnings:
                self.output.output("\n⚠️  STRADDLE RISK WARNINGS:")
                for warning in risk_warnings:
                    self.output.output(f"    • {warning}")
    
    def format_position_sizing(self, position_data: Dict[str, Any]):
        """Format comprehensive position sizing and risk management analysis"""
        
        self.output.section_header("POSITION SIZING & RISK MANAGEMENT", level=2)
        
        if "error" in position_data:
            error_box = self.table.create_summary_box("Position Sizing Error", [f"❌ {position_data['error']}"])
            self.output.output(error_box)
            return
        
        # Extract data
        recommended = position_data.get("recommended_position", {})
        kelly_analysis = position_data.get("kelly_analysis", {})
        risk_assessment = position_data.get("risk_assessment", {})
        account_summary = position_data.get("account_summary", {})
        portfolio_impact = position_data.get("portfolio_impact", {})
        
        # 1. Position Recommendation Table
        position_headers = ["Position Component", "Value", "Notes"]
        position_rows = [
            ["Symbol", recommended.get('symbol', 'Unknown'), ""],
            ["Recommended Contracts", f"{recommended.get('contracts', 0)}", "Final position size"],
            ["Capital Required", f"${recommended.get('capital_required', 0):,.0f}", "Total cost"],
            ["Kelly Fraction", f"{kelly_analysis.get('kelly_fraction', 0):.4f}", "Base Kelly calculation"],
            ["Signal Multiplier", f"{kelly_analysis.get('signal_multiplier', 0):.2f}x", f"({kelly_analysis.get('signal_strength', 0)} signals)"],
            ["Risk-Adjusted Kelly", f"{kelly_analysis.get('risk_adjusted_kelly', 0):.4f}", "Final sizing factor"]
        ]
        
        # Add position adjustment info if applicable
        original_contracts = recommended.get('original_contracts', 0)
        final_contracts = recommended.get('contracts', 0)
        if original_contracts != final_contracts and original_contracts > 0:
            adjustment_reason = recommended.get('adjustment_reason', 'Position adjusted')
            position_rows.append([
                "Position Adjustment",
                f"{original_contracts} → {final_contracts}",
                adjustment_reason
            ])
        
        position_table = self.table.create_table(position_headers, position_rows, "Position Recommendation")
        self.output.output(position_table)
        
        # 2. Account & Risk Summary
        account_headers = ["Account Metric", "Current Value", "Post-Trade"]
        account_rows = [
            ["Account Size", f"${account_summary.get('total_capital', 0):,.0f}", "Unchanged"],
            ["Available Capital", f"${account_summary.get('available_capital', 0):,.0f}", f"${account_summary.get('available_capital', 0) - recommended.get('capital_required', 0):,.0f}"],
            ["Portfolio Utilization", f"{account_summary.get('utilization_percentage', 0):.1f}%", f"{(recommended.get('capital_required', 0) / account_summary.get('total_capital', 1)) * 100:.1f}%"],
            ["Risk per Trade", f"{kelly_analysis.get('account_risk_pct', 0):.1f}%", "Target risk level"]
        ]
        
        # Risk compliance status  
        compliance_status = "✅ COMPLIANT" if risk_assessment.get("is_compliant", False) else "❌ NON-COMPLIANT"
        risk_score = risk_assessment.get('risk_score', 0)
        account_rows.append(["Risk Compliance", compliance_status, f"Score: {risk_score:.1f}/100"])
        
        account_table = self.table.create_table(account_headers, account_rows, "Account & Risk Summary")
        self.output.output(account_table)
        
        # 3. Portfolio Impact Analysis
        if portfolio_impact:
            impact_headers = ["Impact Metric", "Current", "After Trade", "Change"]
            impact_rows = []
            
            current_delta = portfolio_impact.get('current_portfolio_delta', 0)
            new_delta = portfolio_impact.get('new_position_delta', 0)
            impact_rows.append([
                "Portfolio Delta",
                f"Δ{current_delta:.3f}",
                f"Δ{new_delta:.3f}",
                f"Δ{new_delta - current_delta:+.3f}"
            ])
            
            current_theta = portfolio_impact.get('current_theta_impact', 0)
            theta_impact = portfolio_impact.get('estimated_theta_impact', 0)
            impact_rows.append([
                "Daily Theta P&L", 
                f"θ${current_theta:.0f}",
                f"θ${theta_impact:.0f}",
                f"θ${theta_impact - current_theta:+.0f}"
            ])
            
            impact_table = self.table.create_table(impact_headers, impact_rows, "Portfolio Impact Analysis")
            self.output.output(impact_table)
        
        # 4. Risk Alerts and Recommendations
        violations = risk_assessment.get("violations", [])
        warnings = risk_assessment.get("warnings", [])
        recommendations = risk_assessment.get("recommendations", [])
        validation_errors = kelly_analysis.get("validation_errors", [])
        
        alerts = []
        if violations:
            alerts.extend([f"❌ VIOLATION: {v}" for v in violations])
        if warnings:
            alerts.extend([f"⚠️  WARNING: {w}" for w in warnings])
        if validation_errors:
            alerts.extend([f"⚠️  SIZING: {e}" for e in validation_errors])
        
        if alerts:
            alert_box = self.table.create_summary_box("Risk Management Alerts", alerts)
            self.output.output(alert_box)
        
        if recommendations:
            rec_box = self.table.create_summary_box("Recommendations", [f"💡 {r}" for r in recommendations])
            self.output.output(rec_box)
    
    def format_trading_decision(self, decision_data: Dict[str, Any]):
        """Format comprehensive trading decision analysis"""
        
        self.output.section_header("TRADING DECISION AUTOMATION", level=2)
        
        if "error" in decision_data:
            error_box = self.table.create_summary_box("Trading Decision Error", [f"❌ {decision_data['error']}"])
            self.output.output(error_box)
            return
        
        # Extract decision data with safe fallbacks
        decision = decision_data.get("decision", "UNKNOWN")
        confidence = decision_data.get("original_confidence", decision_data.get("confidence", 0))
        expected_return = decision_data.get("expected_return", 0)
        
        # 1. Main Trading Decision
        decision_icon = {
            "RECOMMENDED": "🚀", "EXECUTE": "🚀",
            "CONSIDER": "🤔", 
            "AVOID": "❌", "PASS": "❌"
        }.get(decision, "❓")
        
        # Color-code decision based on confidence
        if confidence is not None and confidence > 0.8:
            confidence_display = f"🟢 {confidence:.1%} (High)"
        elif confidence is not None and confidence > 0.5:
            confidence_display = f"🟡 {confidence:.1%} (Medium)"
        elif confidence is not None:
            confidence_display = f"🔴 {confidence:.1%} (Low)"
        else:
            confidence_display = "N/A"
        
        decision_content = [
            f"Decision: {decision_icon} {decision}",
            f"Confidence: {confidence_display}",
            f"Expected Return: {expected_return:.1%}" if expected_return else "Expected Return: N/A"
        ]
        
        decision_box = self.table.create_summary_box("Trading Decision", decision_content)
        self.output.output(decision_box)
        
        # 2. Decision Metrics Table
        metrics_headers = ["Decision Metric", "Value", "Interpretation"]
        metrics_rows = []
        
        # Risk/Reward Ratio
        risk_reward = decision_data.get("risk_reward_ratio", 0)
        if risk_reward:
            if risk_reward > 2.0:
                interpretation = "Excellent"
            elif risk_reward > 1.5:
                interpretation = "Good"
            elif risk_reward > 1.0:
                interpretation = "Acceptable"
            else:
                interpretation = "Poor"
            metrics_rows.append(["Risk/Reward Ratio", f"{risk_reward:.2f}:1", interpretation])
        
        # Signal Strength
        signal_strength = decision_data.get("signal_strength", 0)
        signal_interp = f"{signal_strength}/3 signals" if signal_strength else "N/A"
        metrics_rows.append(["Signal Strength", f"{signal_strength:.1f}", signal_interp])
        
        # Win Probability
        win_probability = decision_data.get("win_probability", 0)
        if win_probability:
            if win_probability > 0.7:
                prob_interp = "High"
            elif win_probability > 0.5:
                prob_interp = "Medium"
            else:
                prob_interp = "Low"
            metrics_rows.append(["Win Probability", f"{win_probability:.1%}", prob_interp])
        
        # Quality Score
        quality_score = decision_data.get("quality_score", 0)
        if quality_score:
            if quality_score > 80:
                quality_interp = "Excellent"
            elif quality_score > 60:
                quality_interp = "Good"
            elif quality_score > 40:
                quality_interp = "Fair"
            else:
                quality_interp = "Poor"
            metrics_rows.append(["Quality Score", f"{quality_score:.0f}/100", quality_interp])
        
        # Position Size
        position_size = decision_data.get("position_size", 0)
        if position_size:
            metrics_rows.append(["Position Size", f"{position_size} contracts", "Recommended"])
        
        # Liquidity Score
        liquidity_score = decision_data.get("liquidity_score", 0)
        if liquidity_score is not None:
            metrics_rows.append(["Liquidity Score", f"{liquidity_score:.1f}", "Market depth"])
        
        # Decision validity
        is_valid = decision_data.get("is_valid", True)
        validity_text = "✅ Valid" if is_valid else "❌ Invalid"
        metrics_rows.append(["Decision Status", validity_text, "System validation"])
        
        if metrics_rows:
            metrics_table = self.table.create_table(metrics_headers, metrics_rows, "Decision Analysis Metrics")
            self.output.output(metrics_table)
        
        # 3. Decision Reasoning
        reasoning = decision_data.get("reasoning", [])
        if reasoning:
            if isinstance(reasoning, list):
                reasoning_content = [f"{i+1}. {reason}" for i, reason in enumerate(reasoning)]
            else:
                reasoning_content = [f"1. {reasoning}"]
            
            reasoning_box = self.table.create_summary_box("Decision Reasoning", reasoning_content)
            self.output.output(reasoning_box)
        
        # 4. Validation Warnings
        validation_errors = decision_data.get("validation_errors", [])
        if validation_errors:
            warning_content = [f"⚠️  {error}" for error in validation_errors]
            warning_box = self.table.create_summary_box("Decision Warnings", warning_content)
            self.output.output(warning_box)
    
    def format_earnings_analysis(self, earnings_data: Dict[str, Any]):
        """Format comprehensive earnings analysis"""
        
        self.output.section_header("EARNINGS CALENDAR ANALYSIS", level=2)
        
        if "error" in earnings_data:
            error_content = [f"❌ {earnings_data['error']}"]
            if "No upcoming earnings found" in earnings_data['error']:
                error_content.append("ℹ️  This may be expected if no earnings are scheduled")
                error_content.append("ℹ️  Strategy can still be applied based on volatility signals")
            
            error_box = self.table.create_summary_box("Earnings Analysis Status", error_content)
            self.output.output(error_box)
            return
        
        # Earnings event information
        event = earnings_data.get("earnings_event", {})
        if event:
            event_headers = ["Earnings Detail", "Value"]
            event_rows = [
                ["Next Earnings Date", event.get('date', 'Unknown')],
                ["Timing", event.get('timing', 'Unknown')],
                ["Confirmed", "✅ Yes" if event.get('confirmed') else "⚠️  Unconfirmed"],
                ["Days Until Earnings", str(event.get('days_until', 'Unknown'))]
            ]
            
            event_table = self.table.create_table(event_headers, event_rows, "Earnings Event Information")
            self.output.output(event_table)
        
        # Trading windows
        windows = earnings_data.get("trading_windows", {})
        if windows:
            windows_headers = ["Trading Window", "Time Range", "Status"]
            windows_rows = []
            
            entry_start = windows.get('entry_start', 'Unknown')
            entry_end = windows.get('entry_end', 'Unknown')
            windows_rows.append(["Entry Window", f"{entry_start} to {entry_end}", "🟢 Active"])
            
            exit_start = windows.get('exit_start', 'Unknown')
            exit_end = windows.get('exit_end', 'Unknown')
            windows_rows.append(["Exit Window", f"{exit_start} to {exit_end}", "⏳ Pending"])
            
            windows_table = self.table.create_table(windows_headers, windows_rows, "Trading Time Windows")
            self.output.output(windows_table)
        
        # Time to entry
        time_to_entry = earnings_data.get("time_to_entry")
        if time_to_entry:
            timing_content = [f"⏰ Time to Entry: {time_to_entry}"]
            timing_box = self.table.create_summary_box("Entry Timing", timing_content)
            self.output.output(timing_box)
        
        # Earnings warnings
        warnings = earnings_data.get("warnings", [])
        if warnings:
            warning_content = [f"⚠️  {warning}" for warning in warnings]
            warning_box = self.table.create_summary_box("Earnings Alerts", warning_content)
            self.output.output(warning_content)
    
    def format_analysis_footer(self):
        """Format analysis completion footer with summary"""
        
        self.output.section_header("ANALYSIS COMPLETE", level=1)
        
        footer_content = [
            f"Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Symbol: {self.symbol}",
            "⚠️  FOR EDUCATIONAL PURPOSES ONLY",
            "ℹ️  This analysis is not financial advice",
            "ℹ️  Consult a financial advisor before trading"
        ]
        
        footer_box = self.table.create_summary_box("Analysis Summary", footer_content)
        self.output.output(footer_box)


class MarkdownFormatter:
    """Professional markdown formatter for analysis results"""
    
    def __init__(self, symbol: str):
        """Initialize markdown formatter
        
        Args:
            symbol: Stock symbol being analyzed
        """
        self.symbol = symbol
        self.content = []
        
    def add_header(self, text: str, level: int = 1):
        """Add markdown header"""
        prefix = "#" * level
        self.content.append(f"{prefix} {text}\n")
        
    def add_text(self, text: str):
        """Add plain text"""
        self.content.append(f"{text}\n")
        
    def add_table(self, headers: List[str], rows: List[List[str]], title: str = None):
        """Add markdown table"""
        if title:
            self.add_header(title, 3)
            
        # Table header
        header_row = "| " + " | ".join(headers) + " |"
        separator_row = "|" + "|".join(["---" for _ in headers]) + "|"
        
        self.content.append(header_row)
        self.content.append(separator_row)
        
        # Table rows
        for row in rows:
            # Ensure we have the right number of columns
            padded_row = row[:len(headers)] + [""] * (len(headers) - len(row))
            row_text = "| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in padded_row) + " |"
            self.content.append(row_text)
            
        self.content.append("")  # Empty line after table
        
    def add_summary_box(self, title: str, items: List[str]):
        """Add summary information as blockquote"""
        self.add_header(title, 3)
        for item in items:
            self.content.append(f"> {item}")
        self.content.append("")
        
    def add_comparison_section(self, left_data: Dict[str, str], right_data: Dict[str, str], 
                             left_title: str, right_title: str, main_title: str = None):
        """Add side-by-side comparison as markdown table"""
        if main_title:
            self.add_header(main_title, 3)
            
        # Get all metrics
        all_metrics = list(left_data.keys())
        for metric in right_data.keys():
            if metric not in all_metrics:
                all_metrics.append(metric)
                
        # Create comparison table
        headers = ["Metric", left_title, right_title]
        rows = []
        
        for metric in all_metrics:
            left_val = left_data.get(metric, "N/A")
            right_val = right_data.get(metric, "N/A")
            rows.append([metric, left_val, right_val])
            
        self.add_table(headers, rows)
        
    def add_alert_section(self, alerts: List[str], alert_type: str = "warning"):
        """Add alerts as markdown admonition"""
        if not alerts:
            return
            
        icon = "⚠️" if alert_type == "warning" else "🚨" if alert_type == "error" else "ℹ️"
        self.add_text(f"{icon} **Alerts:**")
        for alert in alerts:
            self.content.append(f"- {alert}")
        self.content.append("")
        
    def get_content(self) -> str:
        """Get the complete markdown content"""
        return "\n".join(self.content)
        
    def save_to_file(self, filepath: str):
        """Save markdown content to file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.get_content())


class EnhancedCLIFormatterWithMarkdown(EnhancedCLIFormatter):
    """Enhanced CLI formatter that also generates markdown output"""
    
    def __init__(self, symbol: str, log_cli_output: bool = True, generate_markdown: bool = True):
        """Initialize enhanced formatter with markdown support
        
        Args:
            symbol: Stock symbol being analyzed
            log_cli_output: Whether to enable CLI output logging
            generate_markdown: Whether to generate markdown files
        """
        super().__init__(symbol, log_cli_output)
        self.generate_markdown = generate_markdown
        self.markdown = MarkdownFormatter(symbol) if generate_markdown else None
        self.markdown_file_path = None
        
        if generate_markdown:
            # Create markdown output file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            markdown_filename = f"analysis_{symbol}_{timestamp}.md"
            self.markdown_file_path = os.path.join("logs", markdown_filename)
            
    def format_analysis_header(self, symbol: str, price: float, price_source: str, 
                             modules_enabled: Dict[str, bool], expirations: int, demo: bool = False):
        """Format analysis header for both console and markdown"""
        # Console output
        super().format_analysis_header(symbol, price, price_source, modules_enabled, expirations, demo)
        
        # Markdown output
        if self.markdown:
            self.markdown.add_header(f"Advanced Options Trading Analysis - {symbol}", 1)
            self.markdown.add_text(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.markdown.add_text("")
            
            # Analysis overview
            overview_items = [
                f"**Symbol:** {symbol}",
                f"**Current Price:** ${price:.2f} ({price_source})",
                f"**Analysis Mode:** {'DEMO' if demo else 'LIVE DATA'}",
                f"**Expirations:** {expirations}",
            ]
            self.markdown.add_summary_box("Analysis Overview", overview_items)
            
            # Modules configuration
            module_rows = []
            for module_name, enabled in modules_enabled.items():
                status = "✅ ENABLED" if enabled else "❌ DISABLED"
                description = self._get_module_description(module_name)
                module_rows.append([module_name.replace('_', ' ').title(), status, description])
                
            self.markdown.add_table(
                ["Module", "Status", "Description"], 
                module_rows, 
                "Analysis Modules Configuration"
            )
    
    def format_calendar_analysis(self, calendar_data: Dict[str, Any]):
        """Format calendar spread analysis for both console and markdown"""
        # Console output
        super().format_calendar_analysis(calendar_data)
        
        # Markdown output
        if self.markdown:
            self.markdown.add_header("Calendar Spread Strategy Analysis", 2)
            
            if "error" in calendar_data:
                self.markdown.add_alert_section([calendar_data["error"]], "error")
                return
                
            # Strategy signal analysis
            signals_data = []
            if calendar_data.get("ts_slope_signal") is not None:
                slope_val = calendar_data.get("term_structure_slope", 0)
                threshold = "≤ -0.00406"
                status = "✅ PASS" if calendar_data.get("ts_slope_signal") else "❌ FAIL"
                signals_data.append(["Term Structure Slope", f"{slope_val:.6f}", threshold, status, "Critical"])
                
            if calendar_data.get("iv_rv_signal") is not None:
                iv_rv_val = calendar_data.get("iv_rv_ratio", 0)
                threshold = "≥ 1.25"
                status = "✅ PASS" if calendar_data.get("iv_rv_signal") else "❌ FAIL"
                signals_data.append(["IV/RV Ratio", f"{iv_rv_val:.3f}", threshold, status, "High"])
                
            if calendar_data.get("volume_signal") is not None:
                volume_val = calendar_data.get("avg_volume_30d", 0)
                threshold = "≥ 1,500,000"
                status = "✅ PASS" if calendar_data.get("volume_signal") else "❌ FAIL"
                signals_data.append(["30-Day Avg Volume", f"{volume_val:,.0f}", threshold, status, "Medium"])
                
            if signals_data:
                self.markdown.add_table(
                    ["Signal Component", "Actual Value", "Threshold", "Status", "Weight"],
                    signals_data,
                    "Strategy Signal Analysis"
                )
                
            # Strategy summary
            recommendation = calendar_data.get("recommendation", "Unknown")
            signal_count = calendar_data.get("signal_count", 0)
            expected_move = calendar_data.get("expected_move", 0)
            
            summary_items = [
                f"**Strategy Recommendation:** {recommendation}",
                f"**Signal Strength:** {signal_count}/3 ({signal_count/3*100:.0f}%)",
                f"**Expected Move:** {expected_move:.1f}%"
            ]
            self.markdown.add_summary_box("Calendar Strategy Summary", summary_items)
    
    def format_earnings_analysis(self, earnings_data: Dict[str, Any]):
        """Format earnings analysis for both console and markdown"""
        # Console output
        super().format_earnings_analysis(earnings_data)
        
        # Markdown output
        if self.markdown:
            self.markdown.add_header("Earnings Calendar Analysis", 2)
            
            if "error" in earnings_data:
                self.markdown.add_alert_section([earnings_data["error"]], "error")
                return
                
            # Earnings event information
            event = earnings_data.get("earnings_event", {})
            if event:
                event_rows = [
                    ["Next Earnings Date", event.get("date", "Unknown")],
                    ["Timing", event.get("timing", "Unknown")],
                    ["Confirmed", "✅ Yes" if event.get("confirmed", False) else "❌ No"],
                    ["Days Until Earnings", str(event.get("days_until", "Unknown"))]
                ]
                self.markdown.add_table(
                    ["Earnings Detail", "Value"],
                    event_rows,
                    "Earnings Event Information"
                )
                
            # Trading windows
            windows = earnings_data.get("trading_windows", {})
            if windows:
                windows_rows = []
                entry_start = windows.get('entry_start', 'Unknown')
                entry_end = windows.get('entry_end', 'Unknown')
                windows_rows.append(["Entry Window", f"{entry_start} to {entry_end}", "🟢 Active"])
                
                exit_start = windows.get('exit_start', 'Unknown')
                exit_end = windows.get('exit_end', 'Unknown')
                windows_rows.append(["Exit Window", f"{exit_start} to {exit_end}", "⏳ Pending"])
                
                self.markdown.add_table(
                    ["Trading Window", "Time Range", "Status"],
                    windows_rows,
                    "Trading Time Windows"
                )
                
            # Time to entry
            time_to_entry = earnings_data.get("time_to_entry")
            if time_to_entry:
                timing_items = [f"⏰ Time to Entry: {time_to_entry}"]
                self.markdown.add_summary_box("Entry Timing", timing_items)
                
            # Warnings
            warnings = earnings_data.get("warnings", [])
            if warnings:
                self.markdown.add_alert_section(warnings, "warning")
    
    def format_trade_structures_comparison(self, trade_data: Dict[str, Any]):
        """Format trade structures comparison for both console and markdown"""
        # Console output
        super().format_trade_structures_comparison(trade_data)
        
        # Markdown output
        if self.markdown:
            self.markdown.add_header("Trade Structure Analysis", 2)
            
            if "error" in trade_data:
                self.markdown.add_alert_section([trade_data["error"]], "error")
                return
                
            # Extract trade data
            calendar_trade = trade_data.get("calendar_trade", {})
            straddle_data = trade_data.get("straddle_construction", {})
            straddle_trade = straddle_data.get("straddle_trade", {}) if straddle_data else {}
            pnl_data = trade_data.get("pnl_analysis", {})
            greeks_data = trade_data.get("greeks_analysis", {})
            quality_data = trade_data.get("quality_assessment", {})
            
            if not calendar_trade and not straddle_trade:
                self.markdown.add_alert_section(["No trade structures available for comparison"], "error")
                return
            
            # Structure comparison table
            if calendar_trade or straddle_trade:
                calendar_data = {}
                straddle_data_formatted = {}
                
                if calendar_trade:
                    trade_type = calendar_trade.get('trade_type', 'call_calendar').replace('_', ' ').title()
                    breakeven = calendar_trade.get('breakeven_range', (0, 0))
                    max_profit = 0
                    if pnl_data and 'summary_stats' in pnl_data:
                        max_profit = pnl_data['summary_stats'].get('max_profit', 0)
                    
                    calendar_data = {
                        "Structure Type": trade_type,
                        "Strike Price": f"${calendar_trade.get('strike', 0):.2f}",
                        "Front Expiration": calendar_trade.get('front_expiration', 'Unknown'),
                        "Back Expiration": calendar_trade.get('back_expiration', 'Unknown'),
                        "Entry Cost": f"${calendar_trade.get('net_debit', 0):.2f} (Debit)",
                        "Max Loss": f"${calendar_trade.get('max_loss', 0):.2f}",
                        "Breakeven Range": f"${breakeven[0]:.2f} - ${breakeven[1]:.2f}",
                        "Risk Profile": "Limited Risk/Limited Reward",
                        "Max Profit": f"${max_profit:.2f}"
                    }
                
                if straddle_trade:
                    lower = straddle_trade.get('breakeven_lower', 0)
                    upper = straddle_trade.get('breakeven_upper', 0)
                    
                    straddle_data_formatted = {
                        "Structure Type": "Short ATM Straddle",
                        "Strike Price": f"${straddle_trade.get('strike', 0):.2f}",
                        "Front Expiration": straddle_trade.get('expiration', 'Unknown'),
                        "Back Expiration": "N/A (Single Expiration)",
                        "Entry Cost": f"${straddle_trade.get('net_credit', 0):.2f} (Credit)",
                        "Max Loss": "UNLIMITED",
                        "Breakeven Range": f"${lower:.2f} - ${upper:.2f}",
                        "Risk Profile": "Unlimited Risk/Limited Reward",
                        "Max Profit": f"${straddle_trade.get('max_profit', 0):.2f}"
                    }
                
                self.markdown.add_comparison_section(
                    calendar_data, straddle_data_formatted,
                    "Calendar Spread", "ATM Straddle",
                    "Trade Structure Comparison"
                )
            
            # Greeks and risk analysis
            if greeks_data or quality_data:
                greeks_cal = greeks_data.get("calendar_greeks", {}) if greeks_data else {}
                greeks_str = greeks_data.get("straddle_greeks", {}) if greeks_data else {}
                quality_cal = quality_data.get("calendar_quality", {}) if quality_data else {}
                quality_str = quality_data.get("straddle_quality", {}) if quality_data else {}
                
                risk_calendar = {
                    "Net Delta": f"{greeks_cal.get('net_delta', 0):.4f}",
                    "Gamma Exposure": f"{greeks_cal.get('net_gamma', 0):.4f}",
                    "Daily Theta": f"${greeks_cal.get('net_theta', 0):.2f}",
                    "Vega Risk": f"${greeks_cal.get('net_vega', 0):.2f}",
                    "Quality Score": f"{quality_cal.get('overall_score', 0):.1f}/100",
                    "Win Rate": f"{quality_cal.get('win_rate', 0):.1f}%"
                }
                
                risk_straddle = {
                    "Net Delta": f"{greeks_str.get('net_delta', 0):.4f}",
                    "Gamma Exposure": f"{greeks_str.get('net_gamma', 0):.4f}",
                    "Daily Theta": f"${greeks_str.get('net_theta', 0):.2f}",
                    "Vega Risk": f"${greeks_str.get('net_vega', 0):.2f}",
                    "Quality Score": f"{quality_str.get('overall_score', 0):.1f}/100",
                    "Win Rate": f"{quality_str.get('win_rate', 0):.1f}%"
                }
                
                self.markdown.add_comparison_section(
                    risk_calendar, risk_straddle,
                    "Calendar Spread", "ATM Straddle",
                    "Risk & Greeks Analysis"
                )
            
            # P&L Analysis
            if pnl_data:
                pnl_stats = pnl_data.get("summary_stats", {})
                pnl_rows = [
                    ["Scenarios Analyzed", str(pnl_stats.get('scenarios_analyzed', 0))],
                    ["IV Crush Model", pnl_data.get('iv_crush_severity', 'Unknown')],
                    ["Expected Return", f"${pnl_stats.get('expected_return', 0):.2f}"],
                    ["Profit Scenarios", str(pnl_stats.get('profit_scenarios', 0))],
                    ["Break-even Scenarios", str(pnl_stats.get('breakeven_scenarios', 0))]
                ]
                self.markdown.add_table(["P&L Metric", "Value"], pnl_rows, "P&L Scenario Analysis")
            
            # Structure recommendation
            structure_rec = trade_data.get("structure_recommendation", {})
            if structure_rec:
                rec_items = [
                    f"**Requested Structure:** {structure_rec.get('requested', 'Unknown')}",
                    f"**Recommended Structure:** {structure_rec.get('recommended', 'Unknown')}",
                    f"**Reasoning:** {structure_rec.get('reasoning', 'Not provided')}"
                ]
                self.markdown.add_summary_box("Structure Recommendation", rec_items)
            
            # Risk warnings
            if straddle_data and isinstance(straddle_data, dict):
                risk_analysis = straddle_data.get("risk_analysis", {})
                warnings = risk_analysis.get("risk_warnings", [])
                if warnings:
                    self.markdown.add_alert_section(warnings, "warning")
    
    def format_position_sizing(self, position_data: Dict[str, Any]):
        """Format position sizing analysis for both console and markdown"""
        # Console output
        super().format_position_sizing(position_data)
        
        # Markdown output
        if self.markdown:
            self.markdown.add_header("Position Sizing & Risk Management", 2)
            
            if "error" in position_data:
                self.markdown.add_alert_section([position_data["error"]], "error")
                return
            
            # Position recommendation
            recommended = position_data.get("recommended_position", {})
            if recommended:
                position_rows = [
                    ["Symbol", recommended.get('symbol', 'Unknown')],
                    ["Recommended Contracts", str(recommended.get('contracts', 0))],
                    ["Capital Required", f"${recommended.get('capital_required', 0):.0f}"],
                    ["Kelly Fraction", f"{recommended.get('kelly_fraction', 0):.4f}"],
                    ["Signal Multiplier", f"{recommended.get('signal_multiplier', 0):.2f}x"],
                    ["Risk-Adjusted Kelly", f"{recommended.get('risk_adjusted_kelly', 0):.4f}"]
                ]
                self.markdown.add_table(
                    ["Position Component", "Value", "Notes"],
                    [[row[0], row[1], ""] for row in position_rows],
                    "Position Recommendation"
                )
            
            # Account and risk summary
            risk_summary = position_data.get("risk_summary", {})
            if risk_summary:
                account_rows = [
                    ["Account Size", f"${risk_summary.get('account_size', 0):,.0f}"],
                    ["Available Capital", f"${risk_summary.get('available_capital', 0):,.0f}"],
                    ["Portfolio Utilization", f"{risk_summary.get('portfolio_utilization_pct', 0):.1f}%"],
                    ["Risk per Trade", f"{risk_summary.get('risk_per_trade_pct', 0):.1f}%"],
                    ["Risk Compliance", "✅ COMPLIANT" if risk_summary.get('is_compliant', False) else "❌ NON-COMPLIANT"]
                ]
                self.markdown.add_table(
                    ["Account Metric", "Current Value", "Post-Trade"],
                    [[row[0], row[1], ""] for row in account_rows],
                    "Account & Risk Summary"
                )
            
            # Portfolio impact
            portfolio_impact = position_data.get("portfolio_impact", {})
            if portfolio_impact:
                impact_rows = [
                    ["Portfolio Delta", f"Δ{portfolio_impact.get('new_position_delta', 0):.3f}"],
                    ["Daily Theta P&L", f"θ${portfolio_impact.get('estimated_theta_impact', 0):.0f}"]
                ]
                self.markdown.add_table(
                    ["Impact Metric", "Current", "After Trade", "Change"],
                    [[row[0], "", row[1], ""] for row in impact_rows],
                    "Portfolio Impact Analysis"
                )
    
    def format_trading_decision(self, decision_data: Dict[str, Any]):
        """Format trading decision analysis for both console and markdown"""
        # Console output
        super().format_trading_decision(decision_data)
        
        # Markdown output
        if self.markdown:
            self.markdown.add_header("Trading Decision Automation", 2)
            
            if "error" in decision_data:
                self.markdown.add_alert_section([decision_data["error"]], "error")
                return
            
            # Trading decision summary
            decision = decision_data.get("decision", "UNKNOWN")
            confidence = decision_data.get("original_confidence", decision_data.get("confidence", 0))
            expected_return = decision_data.get("expected_return_pct", 0)
            
            decision_items = [
                f"**Decision:** {decision}",
                f"**Confidence:** {confidence:.1%}" if confidence else "**Confidence:** N/A",
                f"**Expected Return:** {expected_return:.1f}%"
            ]
            self.markdown.add_summary_box("Trading Decision", decision_items)
            
            # Decision analysis metrics
            metrics = decision_data.get("decision_metrics", {})
            if metrics:
                metrics_rows = [
                    ["Risk/Reward Ratio", f"{metrics.get('risk_reward_ratio', 0):.2f}:1"],
                    ["Signal Strength", str(metrics.get('signal_strength', 0))],
                    ["Win Probability", f"{metrics.get('win_probability', 0):.1%}"],
                    ["Quality Score", f"{metrics.get('quality_score', 0):.0f}/100"],
                    ["Position Size", f"{metrics.get('recommended_contracts', 0)} contracts"],
                    ["Liquidity Score", str(metrics.get('liquidity_score', 0))],
                    ["Decision Status", "✅ Valid" if metrics.get('is_valid', False) else "❌ Invalid"]
                ]
                self.markdown.add_table(
                    ["Decision Metric", "Value", "Interpretation"],
                    [[row[0], row[1], ""] for row in metrics_rows],
                    "Decision Analysis Metrics"
                )
    
    def format_analysis_footer(self):
        """Format analysis footer for both console and markdown"""
        # Console output
        super().format_analysis_footer()
        
        # Markdown output and file save
        if self.markdown:
            self.markdown.add_header("Analysis Complete", 2)
            
            footer_items = [
                f"**Analysis completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Symbol:** {self.symbol}",
                "⚠️ **FOR EDUCATIONAL PURPOSES ONLY**",
                "ℹ️ This analysis is not financial advice",
                "ℹ️ Consult a financial advisor before trading"
            ]
            self.markdown.add_summary_box("Analysis Summary", footer_items)
            
            # Save markdown file
            if self.markdown_file_path:
                self.markdown.save_to_file(self.markdown_file_path)
                logger.info(f"Markdown analysis saved: {self.markdown_file_path}")
                print(f"\n📄 Markdown report saved: {self.markdown_file_path}")
    
    def _get_module_description(self, module_name: str) -> str:
        """Get description for module"""
        descriptions = {
            "earnings": "Timing windows and earnings calendar",
            "trade_construction": "Calendar spreads and straddle analysis", 
            "position_sizing": "Kelly criterion and risk management",
            "trading_decision": "Automated decision engine"
        }
        return descriptions.get(module_name, "Analysis module")


def create_enhanced_cli_formatter(symbol: str, log_cli_output: bool = True, generate_markdown: bool = True) -> EnhancedCLIFormatterWithMarkdown:
    """
    Factory function to create enhanced CLI formatter with markdown support
    
    Args:
        symbol: Stock symbol being analyzed
        log_cli_output: Whether to enable CLI output logging to files
        generate_markdown: Whether to generate markdown files
        
    Returns:
        Configured EnhancedCLIFormatterWithMarkdown instance
    """
    return EnhancedCLIFormatterWithMarkdown(symbol=symbol, log_cli_output=log_cli_output, generate_markdown=generate_markdown)