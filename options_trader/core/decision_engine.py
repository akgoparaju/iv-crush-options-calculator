#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurable Decision Engine - Module 4
========================================

Configurable trading decision engine supporting multiple frameworks:
- original: Pure YouTube strategy logic (RECOMMENDED/CONSIDER/AVOID)
- enhanced: Complex multi-criteria approach (EXECUTE/PASS/CONSIDER)
- hybrid: Original primary + enhanced as FYI

Configuration controlled via .env settings for flexible deployment.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

# Import original strategy decision engine
try:
    from .original_decision_engine import OriginalStrategyDecisionEngine, OriginalStrategyResult, OriginalDecision
    HAS_ORIGINAL_ENGINE = True
except ImportError:
    HAS_ORIGINAL_ENGINE = False

logger = logging.getLogger("options_trader.decision_engine")

# Decision criteria weights and thresholds from documentation
EXECUTE_CRITERIA = {
    "signal_strength": {"min": 3, "weight": 0.25},  # All 3 signals present
    "risk_reward_ratio": {"min": 2.0, "weight": 0.20},  # 2:1 minimum
    "win_rate": {"min": 0.65, "weight": 0.20},  # 65%+ historical win rate
    "position_size_valid": {"required": True, "weight": 0.15},  # Risk compliant
    "liquidity_score": {"min": 80, "weight": 0.10},  # High liquidity
    "earnings_timing": {"max_days": 7, "weight": 0.10}  # Within earnings window
}

PASS_CRITERIA = {
    "signal_strength": {"max": 1},  # Only 1 signal or less
    "risk_reward_ratio": {"max": 1.0},  # Poor risk/reward
    "liquidity_score": {"max": 40},  # Low liquidity
    "position_size_violation": True,  # Risk management failure
    "market_conditions": ["high_volatility", "earnings_blackout"]
}

CONSIDER_CRITERIA = {
    "signal_strength": {"range": [2, 2]},  # Exactly 2 signals
    "risk_reward_ratio": {"range": [1.0, 2.0]},  # Moderate risk/reward
    "win_rate": {"range": [0.55, 0.65]},  # Moderate win rate
    "position_size_adjusted": True,  # Size reduced for safety
    "additional_analysis_needed": True  # Requires manual review
}


@dataclass
class TradingDecision:
    """Trading decision with confidence scoring and reasoning."""
    symbol: str
    decision: str  # "EXECUTE", "PASS", "CONSIDER"
    confidence: float  # 0.0-1.0
    reasoning: List[str] = field(default_factory=list)  # Decision factors
    risk_reward_ratio: float = 0.0
    expected_value: float = 0.0
    position_size: int = 0
    signal_strength: int = 0
    quality_score: float = 0.0
    liquidity_score: float = 0.0
    win_rate: float = 0.0
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


@dataclass 
class EnhancedTradingDecision:
    """Extended decision with original + enhanced metrics"""
    symbol: str
    
    # Original strategy fields (always present)
    original_decision: str          # RECOMMENDED/CONSIDER/AVOID
    original_confidence: float      # 0.0-1.0
    signal_strength: int           # 0-3 signals
    signal_breakdown: Dict[str, bool]  # Individual signal status
    original_reasoning: List[str] = field(default_factory=list)
    
    # Enhanced metrics (optional FYI)
    enhanced_metrics: Optional[Dict[str, Any]] = None
    enhanced_decision: Optional[str] = None  # EXECUTE/PASS/CONSIDER  
    enhanced_confidence: Optional[float] = None
    enhanced_reasoning: Optional[List[str]] = None
    risk_reward_ratio: Optional[float] = None
    quality_score: Optional[float] = None
    win_rate_estimate: Optional[float] = None
    expected_value: Optional[float] = None
    position_size: Optional[int] = None
    
    # Framework metadata
    framework: str = "original"  # original|enhanced|hybrid
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


class ConfigurableDecisionEngine:
    """
    Configurable decision engine supporting multiple frameworks:
    - original: Pure YouTube strategy logic
    - enhanced: Current complex multi-criteria approach  
    - hybrid: Original primary + enhanced as FYI
    """
    
    def __init__(self):
        """Initialize the configurable decision engine."""
        self.logger = logging.getLogger(f"{__name__}.ConfigurableDecisionEngine")
        
        # Load configuration from environment
        self.framework = os.getenv("DECISION_FRAMEWORK", "original").lower()
        self.show_enhanced = os.getenv("SHOW_ENHANCED_METRICS", "true").lower() == "true"
        self.strict_original = os.getenv("ORIGINAL_STRATEGY_STRICT", "true").lower() == "true"
        
        # Initialize engines
        self.original_engine = None
        if HAS_ORIGINAL_ENGINE:
            self.original_engine = OriginalStrategyDecisionEngine()
        
        self.logger.info(f"ConfigurableDecisionEngine initialized: framework={self.framework}, "
                        f"enhanced_metrics={self.show_enhanced}, strict_original={self.strict_original}")
    
    def make_trading_decision(self, analysis_result: Dict[str, Any]) -> EnhancedTradingDecision:
        """
        Make a configurable trading decision based on selected framework.
        
        Args:
            analysis_result: Complete analysis from Modules 1-3
        
        Returns:
            EnhancedTradingDecision with framework-specific decision and optional metrics
        """
        symbol = analysis_result.get("symbol", "UNKNOWN")
        
        try:
            if self.framework == "original":
                return self._make_original_decision(analysis_result)
            elif self.framework == "enhanced":
                return self._make_enhanced_decision(analysis_result)  
            elif self.framework == "hybrid":
                return self._make_hybrid_decision(analysis_result)
            else:
                self.logger.warning(f"Unknown framework '{self.framework}', defaulting to original")
                return self._make_original_decision(analysis_result)
                
        except Exception as e:
            self.logger.error(f"Decision making failed for {symbol}: {e}")
            return EnhancedTradingDecision(
                symbol=symbol,
                original_decision="AVOID",
                original_confidence=0.0,
                signal_strength=0,
                signal_breakdown={},
                original_reasoning=[f"Decision engine error: {str(e)}"],
                framework=self.framework,
                is_valid=False,
                validation_errors=[f"Decision engine failed: {str(e)}"]
            )
    
    def _make_original_decision(self, analysis_result: Dict[str, Any]) -> EnhancedTradingDecision:
        """Make decision using pure original strategy logic."""
        symbol = analysis_result.get("symbol", "UNKNOWN")
        
        if not self.original_engine:
            self.logger.error("Original decision engine not available")
            return EnhancedTradingDecision(
                symbol=symbol,
                original_decision="AVOID",
                original_confidence=0.0,
                signal_strength=0,
                signal_breakdown={},
                original_reasoning=["Original decision engine not available"],
                framework="original",
                is_valid=False,
                validation_errors=["Original decision engine not available"]
            )
        
        # Get original strategy decision
        original_result = self.original_engine.make_original_decision(analysis_result)
        
        # Convert to enhanced format
        enhanced_decision = EnhancedTradingDecision(
            symbol=symbol,
            original_decision=original_result.decision.value,
            original_confidence=self._calculate_original_confidence(original_result),
            signal_strength=original_result.signal_strength,
            signal_breakdown={
                "ts_slope_signal": original_result.ts_slope_signal,
                "iv_rv_signal": original_result.iv_rv_signal,
                "volume_signal": original_result.volume_signal
            },
            original_reasoning=original_result.reasoning,
            framework="original"
        )
        
        # Add enhanced metrics as FYI if enabled
        if self.show_enhanced:
            enhanced_metrics = self._calculate_enhanced_metrics(analysis_result)
            if enhanced_metrics and "error" not in enhanced_metrics:
                enhanced_decision.enhanced_decision = enhanced_metrics.get("enhanced_decision")
                enhanced_decision.enhanced_confidence = enhanced_metrics.get("enhanced_confidence")
                enhanced_decision.risk_reward_ratio = enhanced_metrics.get("risk_reward_ratio")
                enhanced_decision.quality_score = enhanced_metrics.get("quality_score")
                enhanced_decision.win_rate_estimate = enhanced_metrics.get("win_rate_estimate")
                enhanced_decision.expected_value = enhanced_metrics.get("expected_value")
                enhanced_decision.position_size = enhanced_metrics.get("position_size")
        
        return enhanced_decision
    
    def _make_enhanced_decision(self, analysis_result: Dict[str, Any]) -> EnhancedTradingDecision:
        """Make decision using enhanced multi-criteria approach."""
        symbol = analysis_result.get("symbol", "UNKNOWN")
        
        # Use existing enhanced logic
        enhanced_result = self._make_legacy_trading_decision(analysis_result)
        
        # Convert to enhanced format
        enhanced_decision = EnhancedTradingDecision(
            symbol=symbol,
            original_decision="CONSIDER",  # Default mapping 
            original_confidence=0.5,
            signal_strength=enhanced_result.signal_strength,
            signal_breakdown=self._extract_signal_breakdown(analysis_result),
            original_reasoning=["Enhanced framework in use - see enhanced decision"],
            enhanced_decision=enhanced_result.decision,
            enhanced_confidence=enhanced_result.confidence,
            enhanced_reasoning=enhanced_result.reasoning,
            risk_reward_ratio=enhanced_result.risk_reward_ratio,
            quality_score=enhanced_result.quality_score,
            win_rate_estimate=enhanced_result.win_rate,
            expected_value=enhanced_result.expected_value,
            position_size=enhanced_result.position_size,
            framework="enhanced"
        )
        
        return enhanced_decision
    
    def _make_hybrid_decision(self, analysis_result: Dict[str, Any]) -> EnhancedTradingDecision:
        """Make decision using hybrid approach (original primary + enhanced FYI)."""
        # Get original decision first
        original_decision = self._make_original_decision(analysis_result)
        
        # Add enhanced metrics as FYI
        enhanced_result = self._make_legacy_trading_decision(analysis_result)
        
        # Combine both
        original_decision.enhanced_decision = enhanced_result.decision
        original_decision.enhanced_confidence = enhanced_result.confidence
        original_decision.enhanced_reasoning = enhanced_result.reasoning
        original_decision.risk_reward_ratio = enhanced_result.risk_reward_ratio
        original_decision.quality_score = enhanced_result.quality_score
        original_decision.win_rate_estimate = enhanced_result.win_rate
        original_decision.expected_value = enhanced_result.expected_value
        original_decision.position_size = enhanced_result.position_size
        original_decision.framework = "hybrid"
        
        return original_decision
    
    def _calculate_original_confidence(self, original_result) -> float:
        """Calculate confidence score for original strategy decision."""
        if original_result.decision.value == "RECOMMENDED":
            return 0.9  # High confidence with all 3 signals
        elif original_result.decision.value == "CONSIDER":  
            return 0.6  # Moderate confidence with 2 signals including slope
        else:
            return 0.1  # Low confidence for avoid
    
    def _calculate_enhanced_metrics(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate enhanced metrics as FYI information."""
        try:
            # Extract metrics using legacy logic
            legacy_result = self._make_legacy_trading_decision(analysis_result)
            
            return {
                "enhanced_decision": legacy_result.decision,
                "enhanced_confidence": legacy_result.confidence,
                "risk_reward_ratio": legacy_result.risk_reward_ratio,
                "quality_score": legacy_result.quality_score,
                "win_rate_estimate": legacy_result.win_rate,
                "expected_value": legacy_result.expected_value,
                "position_size": legacy_result.position_size,
                "liquidity_score": legacy_result.liquidity_score
            }
        except Exception as e:
            self.logger.warning(f"Failed to calculate enhanced metrics: {e}")
            return {"error": str(e)}
    
    def _extract_signal_breakdown(self, analysis_result: Dict[str, Any]) -> Dict[str, bool]:
        """Extract signal breakdown from calendar analysis."""
        calendar_analysis = analysis_result.get("calendar_spread_analysis", {})
        return {
            "ts_slope_signal": calendar_analysis.get("ts_slope_signal", False),
            "iv_rv_signal": calendar_analysis.get("iv_rv_signal", False),
            "volume_signal": calendar_analysis.get("volume_signal", False)
        }
    
    def _make_legacy_trading_decision(self, analysis_result: Dict[str, Any]) -> TradingDecision:
        """Legacy enhanced decision logic - renamed from make_trading_decision."""
        try:
            symbol = analysis_result.get("symbol", "UNKNOWN")
            
            # Extract key metrics from analysis
            metrics = self._extract_decision_metrics(analysis_result)
            
            # Validate minimum requirements
            validation_result = self._validate_analysis_completeness(analysis_result)
            if not validation_result["is_valid"]:
                return TradingDecision(
                    symbol=symbol,
                    decision="PASS",
                    confidence=0.0,
                    reasoning=[f"Analysis incomplete: {', '.join(validation_result['errors'])}"],
                    is_valid=False,
                    validation_errors=validation_result["errors"]
                )
            
            # Apply decision criteria
            decision, confidence = self._apply_decision_criteria(metrics)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(metrics, decision)
            
            # Calculate expected value
            expected_value = self._calculate_expected_value(metrics)
            
            trading_decision = TradingDecision(
                symbol=symbol,
                decision=decision,
                confidence=confidence,
                reasoning=reasoning,
                risk_reward_ratio=metrics.get("risk_reward_ratio", 0.0),
                expected_value=expected_value,
                position_size=metrics.get("position_size", 0),
                signal_strength=metrics.get("signal_strength", 0),
                quality_score=metrics.get("quality_score", 0.0),
                liquidity_score=metrics.get("liquidity_score", 0.0),
                win_rate=metrics.get("win_rate", 0.0),
                is_valid=True
            )
            
            self.logger.info(f"Legacy trading decision for {symbol}: {decision} "
                           f"(confidence: {confidence:.2f}, signals: {metrics.get('signal_strength', 0)})")
            
            return trading_decision
            
        except Exception as e:
            self.logger.error(f"Legacy decision making failed: {e}")
            return TradingDecision(
                symbol=analysis_result.get("symbol", "UNKNOWN"),
                decision="PASS",
                confidence=0.0,
                reasoning=[f"Decision engine error: {str(e)}"],
                is_valid=False,
                validation_errors=[f"Decision engine failed: {str(e)}"]
            )
    
    def _extract_decision_metrics(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from analysis result for decision making."""
        metrics = {}
        
        # Calendar spread analysis metrics
        calendar_analysis = analysis_result.get("calendar_spread_analysis", {})
        metrics["signal_strength"] = calendar_analysis.get("signal_count", 0)
        metrics["liquidity_score"] = 100.0 if calendar_analysis.get("volume_signal", False) else 40.0
        
        # Trade construction metrics
        trade_construction = analysis_result.get("trade_construction", {})
        if trade_construction and "error" not in trade_construction:
            calendar_trade = trade_construction.get("calendar_trade", {})
            quality_assessment = trade_construction.get("quality_assessment", {})
            pnl_analysis = trade_construction.get("pnl_analysis", {})
            
            metrics["quality_score"] = quality_assessment.get("overall_score", 0.0)
            metrics["net_debit"] = calendar_trade.get("net_debit", 0.0)
            metrics["max_loss"] = calendar_trade.get("max_loss", 0.0)
            
            # P&L metrics
            summary_stats = pnl_analysis.get("summary_stats", {})
            metrics["max_profit"] = summary_stats.get("max_profit", 0.0)
            metrics["win_rate"] = summary_stats.get("win_rate", 0.0)
            
            # Calculate risk/reward ratio
            if metrics["max_loss"] > 0:
                metrics["risk_reward_ratio"] = metrics["max_profit"] / metrics["max_loss"]
            else:
                metrics["risk_reward_ratio"] = 0.0
        
        # Position sizing metrics
        position_sizing = analysis_result.get("position_sizing", {})
        if position_sizing and "error" not in position_sizing:
            recommended_position = position_sizing.get("recommended_position", {})
            risk_assessment = position_sizing.get("risk_assessment", {})
            
            metrics["position_size"] = recommended_position.get("contracts", 0)
            metrics["position_size_valid"] = risk_assessment.get("is_compliant", False)
            metrics["position_adjusted"] = (
                recommended_position.get("original_contracts", 0) != 
                recommended_position.get("contracts", 0)
            )
        
        # Earnings timing validation (comprehensive integration)
        earnings_analysis = analysis_result.get("earnings_analysis", {})
        if earnings_analysis and "error" not in earnings_analysis:
            warnings = earnings_analysis.get("warnings", [])
            
            # Check for critical timing issues that should disqualify trades
            critical_timing_issues = [
                "Entry window falls on weekend",
                "Exit window falls on weekend", 
                "Earnings event is in the past"
            ]
            
            has_critical_timing_issues = any(
                any(critical in warning for critical in critical_timing_issues) 
                for warning in warnings
            )
            
            # Check for moderate timing concerns
            moderate_timing_issues = [
                "not confirmed",
                "days away (options may not be available)"
            ]
            
            has_moderate_timing_issues = any(
                any(moderate in warning for moderate in moderate_timing_issues)
                for warning in warnings
            ) 
            
            # Set timing validation flag
            if has_critical_timing_issues:
                metrics["earnings_timing_valid"] = False
                metrics["timing_disqualifies_trade"] = True
            elif has_moderate_timing_issues:
                metrics["earnings_timing_valid"] = True  # Allow but flag concerns
                metrics["timing_reduces_confidence"] = True
            else:
                metrics["earnings_timing_valid"] = True
                
            # Store timing warnings for decision reasoning
            metrics["timing_warnings"] = warnings
            metrics["has_timing_issues"] = len(warnings) > 0
        
        return metrics
    
    def _validate_analysis_completeness(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that required analysis components are present and valid."""
        errors = []
        
        # Check calendar analysis
        calendar_analysis = analysis_result.get("calendar_spread_analysis", {})
        if "error" in calendar_analysis:
            errors.append("Calendar spread analysis failed")
        elif calendar_analysis.get("signal_count", 0) < 1:
            errors.append("No trading signals detected")
        
        # Check trade construction (required for decision making)
        trade_construction = analysis_result.get("trade_construction", {})
        if not trade_construction or "error" in trade_construction:
            errors.append("Trade construction required for trading decisions")
        
        # Check position sizing (required for decision making)
        position_sizing = analysis_result.get("position_sizing", {})
        if not position_sizing or "error" in position_sizing:
            errors.append("Position sizing required for trading decisions")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    def _apply_decision_criteria(self, metrics: Dict[str, Any]) -> tuple:
        """Apply decision criteria and return decision with confidence."""
        
        # Check PASS criteria first (disqualifying factors)
        if self._check_pass_criteria(metrics):
            return "PASS", self._calculate_confidence(metrics, "PASS")
        
        # Check EXECUTE criteria (high confidence)
        if self._check_execute_criteria(metrics):
            return "EXECUTE", self._calculate_confidence(metrics, "EXECUTE")
        
        # Default to CONSIDER (medium confidence)
        return "CONSIDER", self._calculate_confidence(metrics, "CONSIDER")
    
    def _check_execute_criteria(self, metrics: Dict[str, Any]) -> bool:
        """Check if trade meets EXECUTE criteria."""
        criteria = EXECUTE_CRITERIA
        
        # Signal strength
        if metrics.get("signal_strength", 0) < criteria["signal_strength"]["min"]:
            return False
        
        # Risk/reward ratio
        if metrics.get("risk_reward_ratio", 0) < criteria["risk_reward_ratio"]["min"]:
            return False
        
        # Win rate
        if metrics.get("win_rate", 0) < criteria["win_rate"]["min"]:
            return False
        
        # Position size valid
        if not metrics.get("position_size_valid", False):
            return False
        
        # Liquidity score
        if metrics.get("liquidity_score", 0) < criteria["liquidity_score"]["min"]:
            return False
        
        return True
    
    def _check_pass_criteria(self, metrics: Dict[str, Any]) -> bool:
        """Check if trade meets PASS criteria (should be rejected)."""
        criteria = PASS_CRITERIA
        
        # Signal strength too low
        if metrics.get("signal_strength", 0) <= criteria["signal_strength"]["max"]:
            return True
        
        # Risk/reward too poor
        if metrics.get("risk_reward_ratio", 0) <= criteria["risk_reward_ratio"]["max"]:
            return True
        
        # Liquidity too low
        if metrics.get("liquidity_score", 0) <= criteria["liquidity_score"]["max"]:
            return True
        
        # Position size violations
        if not metrics.get("position_size_valid", False):
            return True
        
        # Critical timing issues (weekend conflicts, past events)
        if metrics.get("timing_disqualifies_trade", False):
            return True
        
        return False
    
    def _calculate_confidence(self, metrics: Dict[str, Any], decision: str) -> float:
        """Calculate confidence score based on metrics and decision type."""
        if decision == "PASS":
            return 0.1  # Low confidence for rejected trades
        
        score = 0.0
        
        # Signal strength component (0-0.3)
        signal_strength = metrics.get("signal_strength", 0)
        score += min(signal_strength / 3.0, 1.0) * 0.3
        
        # Risk/reward component (0-0.25)
        risk_reward = metrics.get("risk_reward_ratio", 0)
        score += min(risk_reward / 3.0, 1.0) * 0.25
        
        # Win rate component (0-0.2)
        win_rate = metrics.get("win_rate", 0)
        score += win_rate * 0.2
        
        # Quality score component (0-0.15)
        quality_score = metrics.get("quality_score", 0)
        score += (quality_score / 100.0) * 0.15
        
        # Position sizing component (0-0.1)
        if metrics.get("position_size_valid", False):
            score += 0.1
        
        # Timing adjustment (penalty for moderate timing issues)
        if metrics.get("timing_reduces_confidence", False):
            score *= 0.85  # 15% confidence reduction for timing concerns
        
        # Adjust for decision type
        if decision == "EXECUTE":
            score = max(score, 0.7)  # EXECUTE requires high confidence
        elif decision == "CONSIDER":
            score = min(max(score, 0.4), 0.7)  # CONSIDER is medium confidence
        
        return min(score, 1.0)
    
    def _generate_reasoning(self, metrics: Dict[str, Any], decision: str) -> List[str]:
        """Generate human-readable reasoning for the decision."""
        reasoning = []
        
        # Signal strength reasoning
        signal_count = metrics.get("signal_strength", 0)
        if signal_count == 3:
            reasoning.append("Strong signal: All 3 technical indicators positive")
        elif signal_count == 2:
            reasoning.append("Moderate signal: 2 of 3 technical indicators positive")
        else:
            reasoning.append(f"Weak signal: Only {signal_count} technical indicators positive")
        
        # Risk/reward reasoning
        risk_reward = metrics.get("risk_reward_ratio", 0)
        if risk_reward >= 2.0:
            reasoning.append(f"Excellent risk/reward: {risk_reward:.1f}:1 ratio")
        elif risk_reward >= 1.0:
            reasoning.append(f"Acceptable risk/reward: {risk_reward:.1f}:1 ratio")
        else:
            reasoning.append(f"Poor risk/reward: {risk_reward:.1f}:1 ratio")
        
        # Win rate reasoning
        win_rate = metrics.get("win_rate", 0)
        if win_rate >= 0.7:
            reasoning.append(f"High probability: {win_rate*100:.0f}% historical win rate")
        elif win_rate >= 0.5:
            reasoning.append(f"Moderate probability: {win_rate*100:.0f}% historical win rate")
        else:
            reasoning.append(f"Low probability: {win_rate*100:.0f}% historical win rate")
        
        # Position sizing reasoning
        if metrics.get("position_size_valid", False):
            position_size = metrics.get("position_size", 0)
            reasoning.append(f"Risk compliant: {position_size} contracts within risk limits")
            
            if metrics.get("position_adjusted", False):
                reasoning.append("Position size adjusted for practical constraints")
        else:
            reasoning.append("Risk violation: Position fails risk management criteria")
        
        # Quality reasoning
        quality_score = metrics.get("quality_score", 0)
        if quality_score >= 80:
            reasoning.append(f"High quality trade: {quality_score:.0f}/100 quality score")
        elif quality_score >= 60:
            reasoning.append(f"Moderate quality trade: {quality_score:.0f}/100 quality score")
        else:
            reasoning.append(f"Low quality trade: {quality_score:.0f}/100 quality score")
        
        # Timing-related reasoning
        if metrics.get("timing_disqualifies_trade", False):
            timing_warnings = metrics.get("timing_warnings", [])
            critical_warnings = [w for w in timing_warnings if any(
                critical in w for critical in ["weekend", "past"]
            )]
            if critical_warnings:
                reasoning.append(f"Critical timing issue: {'; '.join(critical_warnings)}")
        elif metrics.get("timing_reduces_confidence", False):
            timing_warnings = metrics.get("timing_warnings", [])
            moderate_warnings = [w for w in timing_warnings if any(
                moderate in w for moderate in ["not confirmed", "days away"]
            )]
            if moderate_warnings:
                reasoning.append(f"Timing concern: {'; '.join(moderate_warnings)} (confidence reduced)")
        elif metrics.get("has_timing_issues", False):
            reasoning.append(f"Minor timing alerts: {len(metrics.get('timing_warnings', []))} warning(s)")
        
        # Decision-specific reasoning
        if decision == "EXECUTE":
            reasoning.append("Recommendation: High-confidence trade meets all execution criteria")
        elif decision == "CONSIDER":
            reasoning.append("Recommendation: Moderate-confidence trade requires manual review")
        else:
            reasoning.append("Recommendation: Low-confidence trade should be avoided")
        
        return reasoning
    
    def _calculate_expected_value(self, metrics: Dict[str, Any]) -> float:
        """Calculate expected value of the trade."""
        win_rate = metrics.get("win_rate", 0.0)
        max_profit = metrics.get("max_profit", 0.0)
        max_loss = metrics.get("max_loss", 0.0)
        position_size = metrics.get("position_size", 0)
        
        if win_rate > 0 and max_profit > 0 and max_loss > 0 and position_size > 0:
            expected_profit = win_rate * max_profit * position_size
            expected_loss = (1 - win_rate) * max_loss * position_size
            return expected_profit - expected_loss
        
        return 0.0