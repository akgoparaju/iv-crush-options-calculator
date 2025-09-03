#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Quality Validator - Options Data Sanity Checking
====================================================

Implements data quality validation and suspicious value detection for options data.
Provides fallback IV estimation when Yahoo Finance returns corrupted implied volatility data.

Key Features:
- IV sanity checks (detect values < 5% as suspicious)
- Black-Scholes IV estimation from option prices
- Data quality warnings and fallback logic
- Provider health monitoring
"""

import logging
import warnings
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import math

# Conditional imports for optional dependencies
try:
    import numpy as np
    from scipy.optimize import brentq
    from scipy.stats import norm
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    np = None

logger = logging.getLogger("options_trader.data_validator")

# Validation thresholds
MIN_REASONABLE_IV = 0.05  # 5% - anything below is suspicious
MAX_REASONABLE_IV = 5.00  # 500% - anything above is suspicious
MIN_OPTION_PRICE = 0.01   # $0.01 minimum for meaningful calculation
MAX_DAYS_FOR_IV_CALC = 365  # Don't calculate IV for options > 1 year out

class DataQualityIssue:
    """Represents a data quality issue with severity and recommendations."""
    
    def __init__(self, severity: str, issue: str, recommendation: str):
        self.severity = severity  # "warning", "error", "critical"
        self.issue = issue
        self.recommendation = recommendation
        
    def __str__(self):
        return f"{self.severity.upper()}: {self.issue} | {self.recommendation}"


class OptionsDataValidator:
    """Validates options data quality and provides fallback IV estimation."""
    
    def __init__(self):
        """Initialize the validator."""
        self.issues = []
        self.fallback_used = False
        
    def clear_issues(self):
        """Clear accumulated issues."""
        self.issues = []
        self.fallback_used = False
        
    def validate_iv_data(self, atm_ivs: Dict[str, float], symbol: str) -> Dict[str, float]:
        """
        Validate implied volatility data and fix issues.
        
        Args:
            atm_ivs: Dictionary of {expiration: atm_iv}
            symbol: Stock symbol for logging
            
        Returns:
            Dictionary of validated/corrected IV values
        """
        self.clear_issues()
        validated_ivs = {}
        
        for exp_date, iv in atm_ivs.items():
            if iv is None or not np.isfinite(iv):
                self.issues.append(DataQualityIssue(
                    "warning", 
                    f"Missing IV data for {exp_date}",
                    "Exclude from term structure analysis"
                ))
                continue
                
            # Check for suspiciously low IV
            if iv < MIN_REASONABLE_IV:
                self.issues.append(DataQualityIssue(
                    "error",
                    f"Suspicious low IV {iv:.4f} ({iv*100:.1f}%) for {exp_date}",
                    "Data may be corrupted, consider alternative source"
                ))
                
                # Try to estimate IV if we have dependencies
                if HAS_SCIPY:
                    # This would need option price data to estimate - placeholder for now
                    logger.warning(f"Low IV detected for {symbol} {exp_date}: {iv:.4f} - marking as suspicious")
                
            # Check for suspiciously high IV  
            elif iv > MAX_REASONABLE_IV:
                self.issues.append(DataQualityIssue(
                    "warning",
                    f"Very high IV {iv:.4f} ({iv*100:.1f}%) for {exp_date}",
                    "Verify if this is realistic for current market conditions"
                ))
                
            validated_ivs[exp_date] = iv
            
        # Log all issues
        for issue in self.issues:
            if issue.severity == "critical":
                logger.error(str(issue))
            elif issue.severity == "error": 
                logger.error(str(issue))
            else:
                logger.warning(str(issue))
                
        return validated_ivs
        
    def black_scholes_call_price(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate Black-Scholes call option price.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility
            
        Returns:
            Call option price
        """
        if not HAS_SCIPY:
            return np.nan
            
        if T <= 0:
            return max(S - K, 0)
            
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return call_price
        
    def black_scholes_put_price(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate Black-Scholes put option price.
        
        Args:
            S: Current stock price
            K: Strike price  
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility
            
        Returns:
            Put option price
        """
        if not HAS_SCIPY:
            return np.nan
            
        if T <= 0:
            return max(K - S, 0)
            
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return put_price
        
    def estimate_iv_from_price(self, option_price: float, S: float, K: float, T: float, 
                              r: float = 0.02, option_type: str = 'call') -> Optional[float]:
        """
        Estimate implied volatility from option price using Black-Scholes.
        
        Args:
            option_price: Market price of option
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate (default 2%)
            option_type: 'call' or 'put'
            
        Returns:
            Estimated implied volatility or None if calculation fails
        """
        if not HAS_SCIPY:
            logger.warning("Cannot estimate IV: scipy not available")
            return None
            
        if option_price < MIN_OPTION_PRICE or T <= 0 or T > MAX_DAYS_FOR_IV_CALC/365:
            return None
            
        try:
            def iv_objective(sigma):
                if option_type.lower() == 'call':
                    bs_price = self.black_scholes_call_price(S, K, T, r, sigma)
                else:
                    bs_price = self.black_scholes_put_price(S, K, T, r, sigma)
                return bs_price - option_price
                
            # Use Brent's method to find IV
            iv = brentq(iv_objective, 0.001, 10.0, xtol=1e-6, maxiter=100)
            
            # Sanity check the result
            if MIN_REASONABLE_IV <= iv <= MAX_REASONABLE_IV:
                return iv
            else:
                logger.warning(f"Estimated IV {iv:.4f} outside reasonable bounds")
                return None
                
        except Exception as e:
            logger.debug(f"IV estimation failed: {e}")
            return None
            
    def validate_and_enhance_atm_summary(self, summary: Dict[str, Any], current_price: float, 
                                        days_to_expiration: float) -> Dict[str, Any]:
        """
        Validate ATM option summary and enhance with estimated IV if needed.
        
        Args:
            summary: ATM summary from chain analysis
            current_price: Current stock price
            days_to_expiration: Days to expiration
            
        Returns:
            Enhanced summary with validation flags and estimated IV if available
        """
        enhanced = summary.copy()
        enhanced['validation_issues'] = []
        enhanced['iv_estimated'] = False
        
        atm_iv = summary.get('atm_iv')
        if atm_iv is None:
            enhanced['validation_issues'].append("Missing IV data")
            return enhanced
            
        # Check for suspicious IV
        if atm_iv < MIN_REASONABLE_IV:
            enhanced['validation_issues'].append(f"Suspicious low IV: {atm_iv:.4f}")
            
            # Try to estimate IV from option prices
            call_mid = summary.get('call_mid')
            put_mid = summary.get('put_mid') 
            strike = summary.get('atm_strike_call')
            
            if call_mid and put_mid and strike and days_to_expiration > 0:
                T = days_to_expiration / 365.0
                
                # Estimate from call
                call_iv = self.estimate_iv_from_price(call_mid, current_price, strike, T, option_type='call')
                # Estimate from put  
                put_iv = self.estimate_iv_from_price(put_mid, current_price, strike, T, option_type='put')
                
                estimated_ivs = [iv for iv in [call_iv, put_iv] if iv is not None]
                
                if estimated_ivs:
                    estimated_iv = np.mean(estimated_ivs)
                    enhanced['atm_iv_estimated'] = estimated_iv
                    enhanced['iv_estimated'] = True
                    enhanced['validation_issues'].append(f"Using estimated IV: {estimated_iv:.4f}")
                    self.fallback_used = True
                    
                    logger.info(f"Estimated IV {estimated_iv:.4f} from option prices (original: {atm_iv:.4f})")
                    
        return enhanced
        
    def generate_data_quality_report(self, symbol: str) -> Dict[str, Any]:
        """
        Generate data quality report for the current validation session.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with data quality metrics and recommendations
        """
        report = {
            'symbol': symbol,
            'validation_timestamp': datetime.now().isoformat(),
            'issues_found': len(self.issues),
            'fallback_used': self.fallback_used,
            'issues': [str(issue) for issue in self.issues],
            'recommendations': []
        }
        
        # Generate recommendations based on issues
        critical_count = sum(1 for issue in self.issues if issue.severity == 'critical')
        error_count = sum(1 for issue in self.issues if issue.severity == 'error')
        
        if critical_count > 0:
            report['recommendations'].append("CRITICAL: Data integrity compromised - avoid trading decisions")
        elif error_count > 0:
            report['recommendations'].append("ERROR: Significant data quality issues - proceed with caution")
        elif self.fallback_used:
            report['recommendations'].append("INFO: Fallback IV estimation used - verify with alternative sources")
            
        return report


# Global validator instance
validator = OptionsDataValidator()