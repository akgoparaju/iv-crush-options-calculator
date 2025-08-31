#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binary Decision Engine - Module 4
==================================

Automated trading decision engine that provides clear EXECUTE/PASS/CONSIDER
outputs with confidence scoring and reasoning based on analysis from Modules 1-3.

Decision Framework:
- EXECUTE: High confidence trades meeting all criteria
- CONSIDER: Moderate confidence trades requiring review  
- PASS: Low confidence trades not meeting minimum standards
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

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


class BinaryDecisionEngine:
    """
    Binary decision engine for automated trading decisions.
    
    Provides EXECUTE/PASS/CONSIDER decisions based on analysis from Modules 1-3
    with confidence scoring and detailed reasoning.
    """
    
    def __init__(self):
        """Initialize the decision engine."""
        self.logger = logging.getLogger(f"{__name__}.BinaryDecisionEngine")
        
    def make_trading_decision(self, analysis_result: Dict[str, Any]) -> TradingDecision:
        """
        Make a binary trading decision based on complete analysis.
        
        Args:
            analysis_result: Complete analysis from Modules 1-3 including:
                - calendar_spread_analysis: Signal strength and metrics
                - trade_construction: Trade specifications and quality
                - position_sizing: Position size and risk assessment
                - earnings_analysis: Optional earnings timing
        
        Returns:
            TradingDecision with binary decision and reasoning
        """
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
            
            self.logger.info(f"Trading decision for {symbol}: {decision} "
                           f"(confidence: {confidence:.2f}, signals: {metrics.get('signal_strength', 0)})")
            
            return trading_decision
            
        except Exception as e:
            self.logger.error(f"Decision making failed: {e}")
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
        
        # Earnings timing (if available)
        earnings_analysis = analysis_result.get("earnings_analysis", {})
        if earnings_analysis and "error" not in earnings_analysis:
            # Simple timing check - in production this would be more sophisticated
            metrics["earnings_timing_valid"] = True
        
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