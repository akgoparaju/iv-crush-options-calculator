#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Original Strategy Threshold Validator - Stage 3
===============================================

Validates exact adherence to original strategy thresholds with precision
and provides detailed validation results for strategy purity.

Implements strict validation against the original YouTube strategy parameters.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("options_trader.threshold_validator")


@dataclass
class ThresholdValidation:
    """Individual threshold validation result."""
    metric: str
    value: float
    threshold: float
    passes: bool
    margin: float = 0.0  # Default value, will be calculated in __post_init__
    precision_warning: bool = False
    
    def __post_init__(self):
        """Calculate margin and precision warning after initialization."""
        self.margin = abs(self.value - self.threshold)
        # Flag values very close to threshold (within 0.1% relative)
        if self.threshold != 0:
            relative_margin = self.margin / abs(self.threshold)
            self.precision_warning = relative_margin < 0.001  # 0.1% threshold


@dataclass
class ValidationResult:
    """Complete validation result for all thresholds."""
    symbol: str
    timestamp: str
    validations: List[ThresholdValidation]
    overall_pass: bool
    signal_count: int
    strategy_confidence: float
    precision_warnings: List[str]
    
    @property
    def passed_signals(self) -> List[str]:
        """Get list of signals that passed validation."""
        return [v.metric for v in self.validations if v.passes]
    
    @property
    def failed_signals(self) -> List[str]:
        """Get list of signals that failed validation."""
        return [v.metric for v in self.validations if not v.passes]


def _parse_env_float(env_var: str, default: str) -> float:
    """Parse environment variable as float, handling comments and whitespace."""
    try:
        value = os.getenv(env_var, default)
        # Split on comment character and take first part, then strip whitespace
        clean_value = value.split('#')[0].strip()
        return float(clean_value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse {env_var}='{value}' as float, using default {default}: {e}")
        return float(default)


class OriginalThresholdValidator:
    """Validate exact adherence to original strategy thresholds."""
    
    # Original strategy thresholds from YouTube video
    ORIGINAL_THRESHOLDS = {
        "ts_slope": _parse_env_float("TS_SLOPE_THRESHOLD", "-0.00406"),      # Term structure slope (≤ -0.00406)
        "iv_rv_ratio": _parse_env_float("IV_RV_RATIO_THRESHOLD", "1.25"),    # IV/RV ratio (≥ 1.25)
        "volume": _parse_env_float("VOLUME_THRESHOLD", "1500000"),           # 30-day avg volume (≥ 1.5M)
    }
    
    def __init__(self, strict_mode: bool = None):
        """
        Initialize threshold validator.
        
        Args:
            strict_mode: If True, use exact original thresholds. If None, read from .env
        """
        if strict_mode is None:
            strict_mode = os.getenv("ORIGINAL_STRATEGY_STRICT", "true").lower() == "true"
        
        self.strict_mode = strict_mode
        self._load_thresholds()
        
        logger.debug(f"OriginalThresholdValidator initialized: strict_mode={self.strict_mode}")
        logger.debug(f"Thresholds: {self.thresholds}")
    
    def _load_thresholds(self):
        """Load thresholds from environment or use defaults."""
        if self.strict_mode:
            # Use exact original strategy thresholds
            self.thresholds = self.ORIGINAL_THRESHOLDS.copy()
        else:
            # Allow slight customization while staying true to strategy
            self.thresholds = {
                "ts_slope": _parse_env_float("TS_SLOPE_THRESHOLD", str(self.ORIGINAL_THRESHOLDS["ts_slope"])),
                "iv_rv_ratio": _parse_env_float("IV_RV_RATIO_THRESHOLD", str(self.ORIGINAL_THRESHOLDS["iv_rv_ratio"])),
                "volume": _parse_env_float("VOLUME_THRESHOLD", str(self.ORIGINAL_THRESHOLDS["volume"])),
            }
        
        logger.info(f"Loaded thresholds: {self.thresholds} (strict_mode={self.strict_mode})")
    
    def validate_strict_compliance(self, metrics: Dict[str, Any], symbol: str = "UNKNOWN") -> ValidationResult:
        """
        Ensure exact match to original strategy parameters.
        
        Args:
            metrics: Dictionary containing calculated metrics
            symbol: Symbol being analyzed
            
        Returns:
            ValidationResult with detailed compliance information
        """
        from datetime import datetime
        
        try:
            validations = []
            precision_warnings = []
            
            # Validate Term Structure Slope (must be ≤ threshold for backwardation)
            ts_slope = metrics.get('ts_slope', 0.0)
            ts_validation = ThresholdValidation(
                metric="ts_slope",
                value=ts_slope,
                threshold=self.thresholds["ts_slope"],
                passes=ts_slope <= self.thresholds["ts_slope"]
            )
            validations.append(ts_validation)
            
            if ts_validation.precision_warning:
                precision_warnings.append(f"TS slope ({ts_slope:.6f}) very close to threshold ({self.thresholds['ts_slope']})")
            
            # Validate IV/RV Ratio (must be ≥ threshold for overpricing)
            iv_rv_ratio = metrics.get('iv_rv_ratio', 0.0)
            iv_validation = ThresholdValidation(
                metric="iv_rv_ratio",
                value=iv_rv_ratio,
                threshold=self.thresholds["iv_rv_ratio"],
                passes=iv_rv_ratio >= self.thresholds["iv_rv_ratio"]
            )
            validations.append(iv_validation)
            
            if iv_validation.precision_warning:
                precision_warnings.append(f"IV/RV ratio ({iv_rv_ratio:.3f}) very close to threshold ({self.thresholds['iv_rv_ratio']})")
            
            # Validate Volume (must be ≥ threshold for liquidity)
            volume = metrics.get('avg_volume_30d', metrics.get('volume', 0))
            volume_validation = ThresholdValidation(
                metric="volume",
                value=volume,
                threshold=self.thresholds["volume"],
                passes=volume >= self.thresholds["volume"]
            )
            validations.append(volume_validation)
            
            if volume_validation.precision_warning:
                precision_warnings.append(f"Volume ({volume:,.0f}) very close to threshold ({self.thresholds['volume']:,.0f})")
            
            # Calculate overall results
            signal_count = sum(1 for v in validations if v.passes)
            overall_pass = signal_count == 3
            
            # Calculate strategy confidence based on original rules
            if signal_count == 3:
                strategy_confidence = 0.95  # High confidence - all signals
            elif signal_count == 2 and ts_validation.passes:
                strategy_confidence = 0.70  # Moderate confidence - slope + 1 other
            elif signal_count == 2:
                strategy_confidence = 0.40  # Lower confidence - 2 signals but no slope
            elif signal_count == 1 and ts_validation.passes:
                strategy_confidence = 0.30  # Low confidence - slope only
            else:
                strategy_confidence = 0.10  # Very low confidence
            
            result = ValidationResult(
                symbol=symbol,
                timestamp=datetime.now().isoformat(),
                validations=validations,
                overall_pass=overall_pass,
                signal_count=signal_count,
                strategy_confidence=strategy_confidence,
                precision_warnings=precision_warnings
            )
            
            logger.info(f"Validation complete for {symbol}: {signal_count}/3 signals, confidence={strategy_confidence:.0%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed for {symbol}: {e}")
            # Return failed validation
            return ValidationResult(
                symbol=symbol,
                timestamp=datetime.now().isoformat(),
                validations=[],
                overall_pass=False,
                signal_count=0,
                strategy_confidence=0.0,
                precision_warnings=[f"Validation error: {str(e)}"]
            )
    
    def get_threshold_info(self) -> Dict[str, Any]:
        """
        Get information about current thresholds.
        
        Returns:
            Dictionary with threshold information
        """
        return {
            "thresholds": self.thresholds.copy(),
            "strict_mode": self.strict_mode,
            "source": "original_strategy" if self.strict_mode else "configurable",
            "description": {
                "ts_slope": "Term structure slope (≤ threshold indicates backwardation)",
                "iv_rv_ratio": "IV/RV ratio (≥ threshold indicates overpricing)",
                "volume": "30-day average volume (≥ threshold for liquidity)"
            }
        }
    
    def validate_individual_threshold(self, metric: str, value: float) -> ThresholdValidation:
        """
        Validate a single threshold.
        
        Args:
            metric: Metric name ('ts_slope', 'iv_rv_ratio', 'volume')
            value: Metric value
            
        Returns:
            ThresholdValidation for this metric
        """
        if metric not in self.thresholds:
            raise ValueError(f"Unknown metric: {metric}")
        
        threshold = self.thresholds[metric]
        
        if metric == "ts_slope":
            passes = value <= threshold
        else:  # iv_rv_ratio, volume
            passes = value >= threshold
        
        return ThresholdValidation(
            metric=metric,
            value=value,
            threshold=threshold,
            passes=passes,
            margin=abs(value - threshold)
        )
    
    def format_validation_summary(self, result: ValidationResult) -> str:
        """
        Format validation result as human-readable summary.
        
        Args:
            result: ValidationResult to format
            
        Returns:
            Formatted summary string
        """
        lines = []
        lines.append(f"=== THRESHOLD VALIDATION ({result.symbol}) ===")
        lines.append(f"Overall: {'PASS' if result.overall_pass else 'FAIL'} ({result.signal_count}/3 signals)")
        lines.append(f"Confidence: {result.strategy_confidence:.0%}")
        lines.append("")
        
        for validation in result.validations:
            status = "✅" if validation.passes else "❌"
            if validation.metric == "ts_slope":
                lines.append(f"{status} TS Slope: {validation.value:.6f} ≤ {validation.threshold:.6f}")
            elif validation.metric == "iv_rv_ratio":
                lines.append(f"{status} IV/RV: {validation.value:.3f} ≥ {validation.threshold:.3f}")
            elif validation.metric == "volume":
                lines.append(f"{status} Volume: {validation.value:,.0f} ≥ {validation.threshold:,.0f}")
            
            if validation.precision_warning:
                lines.append(f"    ⚠️  Close to threshold (margin: {validation.margin:.6f})")
        
        if result.precision_warnings:
            lines.append("")
            lines.append("⚠️  PRECISION WARNINGS:")
            for warning in result.precision_warnings:
                lines.append(f"• {warning}")
        
        return "\n".join(lines)


def validate_original_strategy(metrics: Dict[str, Any], symbol: str = "UNKNOWN", 
                             strict_mode: bool = None) -> ValidationResult:
    """
    Convenience function to validate against original strategy thresholds.
    
    Args:
        metrics: Dictionary containing calculated metrics
        symbol: Symbol being analyzed
        strict_mode: Use strict original thresholds
        
    Returns:
        ValidationResult
    """
    validator = OriginalThresholdValidator(strict_mode=strict_mode)
    return validator.validate_strict_compliance(metrics, symbol)