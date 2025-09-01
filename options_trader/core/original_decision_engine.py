#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Original Strategy Decision Engine - Pure Implementation
======================================================

Pure implementation of the original YouTube strategy decision logic:
- ALL 3 conditions = "RECOMMENDED" (EXECUTE)
- 2 conditions INCLUDING slope = "CONSIDER" 
- NO slope condition = "AVOID" (PASS)

This preserves the exact strategy edge without additional complexity.
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("options_trader.original_decision")

class OriginalDecision(Enum):
    """Original strategy decision types"""
    RECOMMENDED = "RECOMMENDED"  # All 3 signals present - high confidence
    CONSIDER = "CONSIDER"        # 2 signals including slope - moderate confidence  
    AVOID = "AVOID"              # Missing slope or insufficient signals - no trade

@dataclass
class OriginalStrategyResult:
    """Pure original strategy decision result"""
    symbol: str
    decision: OriginalDecision
    signal_strength: int  # 0-3 signals present
    
    # Individual signal breakdown
    ts_slope_signal: bool = False
    iv_rv_signal: bool = False  
    volume_signal: bool = False
    
    # Signal values for transparency
    ts_slope_value: float = 0.0
    iv_rv_ratio: float = 0.0
    volume_30d: float = 0.0
    
    # Strategy thresholds (for reference)
    ts_slope_threshold: float = -0.00406
    iv_rv_threshold: float = 1.25
    volume_threshold: float = 1_500_000
    
    # Decision reasoning
    reasoning: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Generate reasoning based on decision"""
        self.reasoning = self._generate_reasoning()
    
    def _generate_reasoning(self) -> List[str]:
        """Generate clear reasoning for the decision"""
        reasons = []
        
        # Safe formatting helpers to handle None values
        def safe_float(val, default=0.0, precision=2):
            return f"{val if val is not None else default:.{precision}f}"
        
        def safe_int(val, default=0):
            return f"{val if val is not None else default:,.0f}"
        
        if self.decision == OriginalDecision.RECOMMENDED:
            reasons.append("ALL 3 ORIGINAL STRATEGY SIGNALS PRESENT - High confidence trade")
            reasons.append(f"✅ Term structure backwardated: {safe_float(self.ts_slope_value, 0.0, 6)} <= {self.ts_slope_threshold}")
            reasons.append(f"✅ IV overpriced vs RV: {safe_float(self.iv_rv_ratio, 0.0, 2)} >= {self.iv_rv_threshold}")  
            reasons.append(f"✅ High liquidity: {safe_int(self.volume_30d, 0)} >= {self.volume_threshold:,.0f}")
            
        elif self.decision == OriginalDecision.CONSIDER:
            reasons.append("2 SIGNALS INCLUDING SLOPE - Moderate confidence, manual review recommended")
            if self.ts_slope_signal:
                reasons.append(f"✅ Term structure backwardated: {safe_float(self.ts_slope_value, 0.0, 6)} <= {self.ts_slope_threshold}")
            if self.iv_rv_signal:
                reasons.append(f"✅ IV overpriced vs RV: {safe_float(self.iv_rv_ratio, 0.0, 2)} >= {self.iv_rv_threshold}")
            if self.volume_signal:
                reasons.append(f"✅ High liquidity: {safe_int(self.volume_30d, 0)} >= {self.volume_threshold:,.0f}")
                
            # Add missing signals
            if not self.iv_rv_signal:
                reasons.append(f"❌ IV/RV ratio insufficient: {safe_float(self.iv_rv_ratio, 0.0, 2)} < {self.iv_rv_threshold}")
            if not self.volume_signal:
                reasons.append(f"❌ Liquidity insufficient: {safe_int(self.volume_30d, 0)} < {self.volume_threshold:,.0f}")
                
        else:  # AVOID
            reasons.append("INSUFFICIENT SIGNALS OR MISSING SLOPE - No trade recommended")
            if not self.ts_slope_signal:
                reasons.append(f"❌ Term structure not backwardated: {safe_float(self.ts_slope_value, 0.0, 6)} > {self.ts_slope_threshold}")
            if not self.iv_rv_signal:
                reasons.append(f"❌ IV/RV ratio insufficient: {safe_float(self.iv_rv_ratio, 0.0, 2)} < {self.iv_rv_threshold}")
            if not self.volume_signal:
                reasons.append(f"❌ Liquidity insufficient: {safe_int(self.volume_30d, 0)} < {self.volume_threshold:,.0f}")
                
        return reasons

class OriginalStrategyDecisionEngine:
    """
    Pure implementation of original YouTube strategy decision logic.
    
    This engine implements exactly the decision framework from the original strategy:
    1. Check 3 core signals: term structure slope, IV/RV ratio, liquidity
    2. Apply exact original thresholds without modification
    3. Return clear RECOMMENDED/CONSIDER/AVOID decisions
    
    No additional complexity, no win rates, no risk/reward ratios - just the pure edge.
    """
    
    # Original strategy thresholds (immutable)
    ORIGINAL_THRESHOLDS = {
        "ts_slope_max": -0.00406,      # Term structure must be backwardated
        "iv_rv_ratio_min": 1.25,       # IV must be overpriced vs RV
        "volume_min": 1_500_000,       # Minimum 30-day average volume
    }
    
    def __init__(self):
        """Initialize original strategy decision engine"""
        self.logger = logging.getLogger(f"{__name__}.OriginalStrategyDecisionEngine")
        self.logger.info("Original strategy decision engine initialized - pure YouTube strategy logic")
        
    def make_original_decision(self, analysis_result: Dict[str, Any]) -> OriginalStrategyResult:
        """
        Make trading decision using pure original strategy logic.
        
        Original Decision Framework:
        - ALL 3 conditions = "RECOMMENDED" (high confidence)
        - 2 conditions INCLUDING slope = "CONSIDER" (moderate confidence)  
        - NO slope condition OR <2 signals = "AVOID" (no trade)
        
        Args:
            analysis_result: Complete analysis from analyzer.py
            
        Returns:
            OriginalStrategyResult with pure strategy decision
        """
        symbol = analysis_result.get("symbol", "UNKNOWN")
        
        try:
            # Extract calendar spread analysis (contains the 3 core signals)
            calendar_analysis = analysis_result.get("calendar_spread_analysis", {})
            
            if "error" in calendar_analysis:
                self.logger.warning(f"Calendar analysis failed for {symbol}, defaulting to AVOID")
                return self._create_avoid_decision(symbol, "Calendar spread analysis failed")
            
            # Extract the 3 original strategy signals
            signals = self._extract_original_signals(calendar_analysis)
            
            # Apply original decision logic
            decision = self._apply_original_logic(signals)
            
            # Create result object
            result = OriginalStrategyResult(
                symbol=symbol,
                decision=decision,
                signal_strength=signals["signal_count"],
                ts_slope_signal=signals["ts_slope_signal"],
                iv_rv_signal=signals["iv_rv_signal"],
                volume_signal=signals["volume_signal"],
                ts_slope_value=signals["ts_slope_value"],
                iv_rv_ratio=signals["iv_rv_ratio"],
                volume_30d=signals["volume_30d"]
            )
            
            self.logger.info(f"Original strategy decision for {symbol}: {decision.value} "
                           f"({signals['signal_count']}/3 signals)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Original strategy decision failed for {symbol}: {e}")
            return self._create_avoid_decision(symbol, f"Decision engine error: {str(e)}")
    
    def _extract_original_signals(self, calendar_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the 3 original strategy signals from calendar analysis"""
        
        # Get individual signals
        ts_slope_signal = calendar_analysis.get("ts_slope_signal", False)
        iv_rv_signal = calendar_analysis.get("iv_rv_signal", False)  
        volume_signal = calendar_analysis.get("volume_signal", False)
        
        # Get signal values for transparency
        ts_slope_value = calendar_analysis.get("term_structure_slope", 0.0)
        iv_rv_ratio = calendar_analysis.get("iv_rv_ratio", 0.0)
        volume_30d = calendar_analysis.get("avg_volume_30d", 0.0)
        
        signal_count = sum([ts_slope_signal, iv_rv_signal, volume_signal])
        
        return {
            "ts_slope_signal": ts_slope_signal,
            "iv_rv_signal": iv_rv_signal,
            "volume_signal": volume_signal,
            "ts_slope_value": ts_slope_value,
            "iv_rv_ratio": iv_rv_ratio,
            "volume_30d": volume_30d,
            "signal_count": signal_count
        }
    
    def _apply_original_logic(self, signals: Dict[str, Any]) -> OriginalDecision:
        """
        Apply exact original strategy decision logic.
        
        Original Logic:
        1. If all 3 signals present → RECOMMENDED
        2. If 2 signals present AND slope signal present → CONSIDER  
        3. Otherwise → AVOID
        """
        signal_count = signals["signal_count"]
        ts_slope_signal = signals["ts_slope_signal"]
        
        if signal_count == 3:
            # All conditions met - high confidence trade
            return OriginalDecision.RECOMMENDED
            
        elif signal_count == 2 and ts_slope_signal:
            # 2 signals including the critical slope signal - moderate confidence
            return OriginalDecision.CONSIDER
            
        else:
            # Missing slope signal or insufficient signals - no trade
            return OriginalDecision.AVOID
    
    def _create_avoid_decision(self, symbol: str, reason: str) -> OriginalStrategyResult:
        """Create AVOID decision with error reason"""
        result = OriginalStrategyResult(
            symbol=symbol,
            decision=OriginalDecision.AVOID,
            signal_strength=0
        )
        result.reasoning = [f"AVOID: {reason}"]
        return result
    
    def validate_original_compliance(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate strict compliance with original strategy thresholds.
        
        Returns validation report showing exact threshold compliance.
        """
        calendar_analysis = analysis_result.get("calendar_spread_analysis", {})
        
        if "error" in calendar_analysis:
            return {
                "compliant": False,
                "error": "Calendar analysis failed",
                "thresholds_check": {}
            }
        
        # Check each threshold exactly
        ts_slope = calendar_analysis.get("term_structure_slope", 0.0)
        iv_rv_ratio = calendar_analysis.get("iv_rv_ratio", 0.0)
        volume_30d = calendar_analysis.get("avg_volume_30d", 0.0)
        
        thresholds_check = {
            "term_structure_slope": {
                "value": ts_slope,
                "threshold": self.ORIGINAL_THRESHOLDS["ts_slope_max"],
                "compliant": ts_slope <= self.ORIGINAL_THRESHOLDS["ts_slope_max"],
                "description": "Must be backwardated (negative slope)"
            },
            "iv_rv_ratio": {
                "value": iv_rv_ratio,
                "threshold": self.ORIGINAL_THRESHOLDS["iv_rv_ratio_min"],
                "compliant": iv_rv_ratio >= self.ORIGINAL_THRESHOLDS["iv_rv_ratio_min"],
                "description": "IV must be overpriced vs realized volatility"
            },
            "volume_30d": {
                "value": volume_30d,
                "threshold": self.ORIGINAL_THRESHOLDS["volume_min"],
                "compliant": volume_30d >= self.ORIGINAL_THRESHOLDS["volume_min"],
                "description": "Sufficient liquidity required"
            }
        }
        
        all_compliant = all(check["compliant"] for check in thresholds_check.values())
        
        return {
            "compliant": all_compliant,
            "thresholds_check": thresholds_check,
            "summary": f"Original strategy compliance: {sum(check['compliant'] for check in thresholds_check.values())}/3 thresholds met"
        }