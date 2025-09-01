#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Output Formatter - Stage 3
====================================

Enhanced formatting for strategy purity with sophisticated display controls.
Centers original strategy prominently with enhanced features as optional FYI.

Stage 3 Implementation:
- Structured output framework with configurable sections
- Original strategy prominently displayed first
- Enhanced metrics clearly marked as FYI
- Threshold validation integration
- Risk warnings and precision alerts
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import decision types and validation
try:
    from .decision_engine import EnhancedTradingDecision
    HAS_DECISION_TYPES = True
except ImportError:
    HAS_DECISION_TYPES = False

try:
    from .threshold_validator import OriginalThresholdValidator, ValidationResult
    HAS_THRESHOLD_VALIDATOR = True
except ImportError:
    HAS_THRESHOLD_VALIDATOR = False

logger = logging.getLogger("options_trader.output_formatter")


def _parse_env_float(env_var: str, default: str) -> float:
    """Parse environment variable as float, handling comments and whitespace."""
    try:
        value = os.getenv(env_var, default)
        # Split on comment character and take first part, then strip whitespace
        clean_value = value.split('#')[0].strip()
        return float(clean_value)
    except (ValueError, TypeError) as e:
        logger.debug(f"Could not parse {env_var}='{value}' as float, using default {default}: {e}")
        return float(default)


class StrategyOutputFormatter:
    """Enhanced formatter with sophisticated display controls for strategy purity."""
    
    def __init__(self):
        """Initialize output formatter with Stage 3 configuration."""
        # Core display controls
        self.show_enhanced_metrics = os.getenv("SHOW_ENHANCED_METRICS", "true").lower() == "true"
        self.show_warnings = os.getenv("SHOW_RISK_WARNINGS", "true").lower() == "true"
        self.framework = os.getenv("DECISION_FRAMEWORK", "original").lower()
        
        # Stage 3 enhancements
        self.show_threshold_detail = os.getenv("SHOW_THRESHOLD_DETAIL", "true").lower() == "true"
        self.show_precision_warnings = os.getenv("SHOW_PRECISION_WARNINGS", "true").lower() == "true"
        self.show_confidence_breakdown = os.getenv("SHOW_CONFIDENCE_BREAKDOWN", "true").lower() == "true"
        self.show_trade_structure = os.getenv("SHOW_TRADE_STRUCTURE", "true").lower() == "true"
        self.show_timing_windows = os.getenv("SHOW_TIMING_WINDOWS", "true").lower() == "true"
        
        # Initialize threshold validator if available
        self.validator = None
        if HAS_THRESHOLD_VALIDATOR:
            try:
                self.validator = OriginalThresholdValidator()
            except Exception as e:
                logger.warning(f"Could not initialize threshold validator: {e}")
        
        logger.debug(f"StrategyOutputFormatter initialized: enhanced={self.show_enhanced_metrics}, "
                    f"warnings={self.show_warnings}, framework={self.framework}, "
                    f"threshold_detail={self.show_threshold_detail}")
    
    def format_decision_output(self, decision, metrics: Dict[str, Any] = None) -> str:
        """
        Format decision output with Stage 3 enhancements.
        
        Args:
            decision: EnhancedTradingDecision object
            metrics: Optional metrics dictionary for threshold validation
            
        Returns:
            Formatted string output
        """
        if not HAS_DECISION_TYPES:
            return self._format_fallback_output(decision)
        
        try:
            output_parts = []
            
            # 1. Always show original decision prominently (PRIMARY)
            output_parts.append(self._format_original_decision_enhanced(decision, metrics))
            
            # 2. Show trade structure recommendation if enabled
            if self.show_trade_structure:
                structure_section = self._format_trade_structure(decision)
                if structure_section:
                    output_parts.append(structure_section)
            
            # 3. Show enhanced metrics if enabled (FYI SECTION)
            if self.show_enhanced_metrics and self._has_enhanced_data(decision):
                output_parts.append(self._format_enhanced_metrics(decision))
            
            # 4. Show threshold validation details if enabled
            if self.show_threshold_detail and metrics and self.validator:
                validation_section = self._format_threshold_validation(metrics, decision)
                if validation_section:
                    output_parts.append(validation_section)
            
            # 5. Show risk warnings if enabled and applicable (ALWAYS LAST)
            if self.show_warnings and self._has_risk_warnings(decision, metrics):
                output_parts.append(self._format_risk_warnings(decision, metrics))
            
            return "\n\n".join(output_parts)
            
        except Exception as e:
            logger.error(f"Output formatting failed: {e}")
            return f"Error formatting output: {str(e)}"
    
    def _format_original_decision_enhanced(self, decision, metrics: Dict[str, Any] = None) -> str:
        """Format the original strategy decision with Stage 3 enhancements."""
        lines = []
        
        # Header with decision
        decision_emoji = self._get_decision_emoji(decision.original_decision)
        lines.append("=== ORIGINAL STRATEGY DECISION ===")
        lines.append(f"Decision: {decision.original_decision} {decision_emoji}")
        lines.append(f"Signal Strength: {decision.signal_strength}/3 signals present")
        
        # Enhanced signal breakdown with actual values
        signal_lines = []
        if hasattr(decision, 'signal_breakdown') and decision.signal_breakdown:
            breakdown = decision.signal_breakdown
            
            # Term Structure Signal with actual slope value
            if breakdown.get('ts_slope_signal', False):
                if metrics and 'ts_slope' in metrics:
                    slope_val = metrics['ts_slope']
                    signal_lines.append(f"├─ Term Structure: BACKWARDATED ✅ (slope: {slope_val:.6f})")
                else:
                    signal_lines.append("├─ Term Structure: BACKWARDATED ✅")
            else:
                if metrics and 'ts_slope' in metrics:
                    slope_val = metrics['ts_slope']
                    signal_lines.append(f"├─ Term Structure: NOT BACKWARDATED ❌ (slope: {slope_val:.6f})")
                else:
                    signal_lines.append("├─ Term Structure: NOT BACKWARDATED ❌")
            
            # IV/RV Signal with actual ratio
            if breakdown.get('iv_rv_signal', False):
                if metrics and 'iv_rv_ratio' in metrics:
                    iv_rv = metrics['iv_rv_ratio']
                    threshold = _parse_env_float("IV_RV_RATIO_THRESHOLD", "1.25")
                    signal_lines.append(f"├─ IV/RV Ratio: ELEVATED ✅ ({iv_rv:.3f} vs {threshold} threshold)")
                else:
                    signal_lines.append("├─ IV/RV Ratio: ELEVATED ✅")
            else:
                if metrics and 'iv_rv_ratio' in metrics:
                    iv_rv = metrics['iv_rv_ratio']
                    threshold = _parse_env_float("IV_RV_RATIO_THRESHOLD", "1.25")
                    signal_lines.append(f"├─ IV/RV Ratio: INSUFFICIENT ❌ ({iv_rv:.3f} vs {threshold} threshold)")
                else:
                    signal_lines.append("├─ IV/RV Ratio: INSUFFICIENT ❌")
            
            # Volume Signal with actual volume
            if breakdown.get('volume_signal', False):
                volume = metrics.get('avg_volume_30d') or metrics.get('volume') if metrics else None
                if volume:
                    threshold = _parse_env_float("VOLUME_THRESHOLD", "1500000")
                    signal_lines.append(f"└─ Liquidity: HIGH ✅ ({volume:,.0f} vs {threshold:,.0f} threshold)")
                else:
                    signal_lines.append("└─ Liquidity: HIGH ✅")
            else:
                volume = metrics.get('avg_volume_30d') or metrics.get('volume') if metrics else None
                if volume:
                    threshold = _parse_env_float("VOLUME_THRESHOLD", "1500000")
                    signal_lines.append(f"└─ Liquidity: INSUFFICIENT ❌ ({volume:,.0f} vs {threshold:,.0f} threshold)")
                else:
                    signal_lines.append("└─ Liquidity: INSUFFICIENT ❌")
        else:
            # Fallback if no breakdown available
            signal_lines.append(f"└─ {decision.signal_strength} of 3 signals present")
        
        lines.extend(signal_lines)
        
        # Add confidence with breakdown if enabled
        if hasattr(decision, 'original_confidence') and decision.original_confidence is not None:
            confidence_pct = decision.original_confidence * 100
            if self.show_confidence_breakdown:
                lines.append(f"Confidence: {confidence_pct:.0f}% (based on {decision.signal_strength}/3 signals)")
            else:
                lines.append(f"Confidence: {confidence_pct:.0f}%")
        
        # Add timing windows if enabled and available
        if self.show_timing_windows:
            timing_section = self._format_timing_windows(decision)
            if timing_section:
                lines.append("")
                lines.extend(timing_section)
        
        # Add reasoning if available (limited to preserve prominence)
        if hasattr(decision, 'original_reasoning') and decision.original_reasoning:
            lines.append("")
            lines.append("Strategy Reasoning:")
            for reason in decision.original_reasoning[:2]:  # Limit to first 2 reasons for Stage 3
                lines.append(f"• {reason}")
        
        return "\n".join(lines)
    
    def _format_enhanced_metrics(self, decision) -> str:
        """Format enhanced metrics as FYI section."""
        lines = []
        lines.append("=== ENHANCED ANALYSIS (FYI) ===")
        
        # Enhanced decision if different from original
        if (hasattr(decision, 'enhanced_decision') and 
            decision.enhanced_decision and 
            decision.enhanced_decision != decision.original_decision):
            lines.append(f"Enhanced Decision: {decision.enhanced_decision}")
        
        # Quality and risk metrics
        metrics = []
        if hasattr(decision, 'quality_score') and decision.quality_score is not None:
            metrics.append(f"Trade Quality Score: {decision.quality_score:.0f}/100")
        
        if hasattr(decision, 'risk_reward_ratio') and decision.risk_reward_ratio is not None:
            metrics.append(f"Risk/Reward Estimate: {decision.risk_reward_ratio:.1f}:1")
        
        if hasattr(decision, 'win_rate_estimate') and decision.win_rate_estimate is not None:
            win_rate_pct = decision.win_rate_estimate * 100
            metrics.append(f"Win Rate Projection: {win_rate_pct:.0f}%")
        
        if hasattr(decision, 'position_size') and decision.position_size is not None:
            metrics.append(f"Suggested Position Size: {decision.position_size} contracts")
        
        if hasattr(decision, 'expected_value') and decision.expected_value is not None:
            metrics.append(f"Expected Value: ${decision.expected_value:.2f}")
        
        lines.extend(metrics)
        
        # Enhanced reasoning (limited)
        if (hasattr(decision, 'enhanced_reasoning') and 
            decision.enhanced_reasoning and 
            len(decision.enhanced_reasoning) > 0):
            lines.append("")
            lines.append("Enhanced Analysis:")
            # Show only first 2 enhanced reasoning points to keep it as FYI
            for reason in decision.enhanced_reasoning[:2]:
                lines.append(f"• {reason}")
        
        return "\n".join(lines)
    
    def _format_risk_warnings(self, decision, metrics: Dict[str, Any] = None) -> str:
        """Format risk warnings with Stage 3 enhancements."""
        lines = []
        
        # Check for validation errors
        if hasattr(decision, 'validation_errors') and decision.validation_errors:
            lines.append("⚠️  RISK WARNINGS ⚠️")
            for error in decision.validation_errors:
                lines.append(f"• {error}")
        
        # Check for low confidence
        if (hasattr(decision, 'original_confidence') and 
            decision.original_confidence is not None and 
            decision.original_confidence < 0.3):
            if not lines:
                lines.append("⚠️  RISK WARNINGS ⚠️")
            lines.append("• Low confidence decision - consider manual review")
        
        # Check for AVOID decision
        if decision.original_decision == "AVOID":
            if not lines:
                lines.append("⚠️  RISK WARNINGS ⚠️")
            lines.append("• Original strategy recommends avoiding this trade")
        
        # Stage 3: Add precision warnings from threshold validation
        if self.show_precision_warnings and metrics and self.validator:
            try:
                validation = self.validator.validate_strict_compliance(metrics)
                if validation.precision_warnings:
                    if not lines:
                        lines.append("⚠️  PRECISION WARNINGS ⚠️")
                    for warning in validation.precision_warnings:
                        lines.append(f"• {warning}")
            except Exception as e:
                logger.debug(f"Could not generate precision warnings: {e}")
        
        return "\n".join(lines) if lines else ""
    
    def _format_trade_structure(self, decision) -> str:
        """Format trade structure recommendation section (Stage 3)."""
        lines = []
        
        # Check if decision has structure recommendation
        structure = "Calendar Spread"  # Default
        if hasattr(decision, 'recommended_structure'):
            structure = decision.recommended_structure
        elif hasattr(decision, 'trade_structure'):
            structure = decision.trade_structure
        
        lines.append("=== TRADE STRUCTURE ===")
        lines.append(f"Recommended Structure: {structure}")
        
        # Add structure reasoning if available
        if hasattr(decision, 'structure_reasoning') and decision.structure_reasoning:
            for reason in decision.structure_reasoning[:2]:  # Limit for Stage 3 purity
                lines.append(f"• {reason}")
        
        return "\n".join(lines) if len(lines) > 1 else ""
    
    def _format_timing_windows(self, decision) -> List[str]:
        """Format timing windows if available (Stage 3)."""
        lines = []
        
        # Check for earnings timing
        if hasattr(decision, 'entry_window') or hasattr(decision, 'exit_window'):
            entry_window = getattr(decision, 'entry_window', "Today 15:45-16:00 EST")
            exit_window = getattr(decision, 'exit_window', "Tomorrow 09:30-09:45 EST")
            
            lines.append("Trading Windows:")
            lines.append(f"Entry: {entry_window}")
            lines.append(f"Exit: {exit_window}")
        
        return lines
    
    def _format_threshold_validation(self, metrics: Dict[str, Any], decision) -> str:
        """Format detailed threshold validation section (Stage 3)."""
        if not self.validator:
            return ""
        
        try:
            validation = self.validator.validate_strict_compliance(metrics, 
                                                                 getattr(decision, 'symbol', 'UNKNOWN'))
            
            lines = []
            lines.append("=== THRESHOLD VALIDATION ===")
            lines.append(f"Validation: {'PASS' if validation.overall_pass else 'FAIL'} ({validation.signal_count}/3 signals)")
            lines.append(f"Strategy Confidence: {validation.strategy_confidence:.0%}")
            
            # Show individual validations
            for val in validation.validations:
                status = "✅" if val.passes else "❌"
                if val.metric == "ts_slope":
                    lines.append(f"{status} TS Slope: {val.value:.6f} ≤ {val.threshold:.6f}")
                elif val.metric == "iv_rv_ratio":
                    lines.append(f"{status} IV/RV: {val.value:.3f} ≥ {val.threshold:.3f}")
                elif val.metric == "volume":
                    lines.append(f"{status} Volume: {val.value:,.0f} ≥ {val.threshold:,.0f}")
                
                # Show precision warning for close values
                if val.precision_warning:
                    lines.append(f"    ⚠️  Close to threshold (margin: {val.margin:.6f})")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.debug(f"Threshold validation formatting failed: {e}")
            return ""
    
    def _get_decision_emoji(self, decision: str) -> str:
        """Get emoji for decision type."""
        decision_emojis = {
            "RECOMMENDED": "🟢",
            "CONSIDER": "🟡", 
            "AVOID": "🔴",
            "EXECUTE": "✅",
            "PASS": "❌"
        }
        return decision_emojis.get(decision.upper(), "")
    
    def _has_enhanced_data(self, decision) -> bool:
        """Check if decision has enhanced data to display."""
        enhanced_fields = [
            'enhanced_decision', 'enhanced_reasoning', 'quality_score', 
            'risk_reward_ratio', 'win_rate_estimate', 'position_size', 'expected_value'
        ]
        
        return any(
            hasattr(decision, field) and 
            getattr(decision, field) is not None and
            getattr(decision, field) != "" and
            getattr(decision, field) != []
            for field in enhanced_fields
        )
    
    def _has_risk_warnings(self, decision, metrics: Dict[str, Any] = None) -> bool:
        """Check if decision has risk warnings to display (Stage 3 enhanced)."""
        # Check validation errors
        if hasattr(decision, 'validation_errors') and decision.validation_errors:
            return True
        
        # Check low confidence
        if (hasattr(decision, 'original_confidence') and 
            decision.original_confidence is not None and 
            decision.original_confidence < 0.3):
            return True
        
        # Check avoid decision
        if hasattr(decision, 'original_decision') and decision.original_decision == "AVOID":
            return True
        
        # Stage 3: Check for precision warnings
        if self.show_precision_warnings and metrics and self.validator:
            try:
                validation = self.validator.validate_strict_compliance(metrics)
                if validation.precision_warnings:
                    return True
            except Exception:
                pass  # Ignore validation errors for warning check
        
        return False
    
    def _format_fallback_output(self, decision) -> str:
        """Fallback formatting when decision types not available."""
        lines = []
        lines.append("=== TRADING DECISION ===")
        
        # Try to extract basic information
        if hasattr(decision, 'decision'):
            lines.append(f"Decision: {decision.decision}")
        
        if hasattr(decision, 'confidence'):
            confidence_pct = decision.confidence * 100
            lines.append(f"Confidence: {confidence_pct:.0f}%")
        
        if hasattr(decision, 'reasoning') and decision.reasoning:
            lines.append("")
            lines.append("Reasoning:")
            for reason in decision.reasoning[:3]:
                lines.append(f"• {reason}")
        
        return "\n".join(lines)


def format_trading_decision(decision, show_enhanced: bool = None, metrics: Dict[str, Any] = None) -> str:
    """
    Convenience function to format trading decision output (Stage 3 enhanced).
    
    Args:
        decision: Trading decision object
        show_enhanced: Override for showing enhanced metrics
        metrics: Optional metrics dictionary for threshold validation
        
    Returns:
        Formatted decision string
    """
    formatter = StrategyOutputFormatter()
    
    # Override setting if explicitly provided
    if show_enhanced is not None:
        formatter.show_enhanced_metrics = show_enhanced
    
    return formatter.format_decision_output(decision, metrics)