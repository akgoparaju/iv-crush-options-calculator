#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Volatility Analysis & Term Structure
====================================

Core volatility analysis functions for earnings IV crush strategy:
- Yang-Zhang realized volatility calculation
- Term structure modeling and slope analysis  
- Calendar spread metrics and recommendations
- IV/RV ratio analysis with trading signals

Preserves all original strategy logic and thresholds.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Conditional imports for optional dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

try:
    from scipy.interpolate import interp1d
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    interp1d = None

logger = logging.getLogger("options_trader.analysis")


def build_term_structure(days: List[float], ivs: List[float]):
    """
    Build interpolated term structure spline from implied volatilities.
    
    Args:
        days: List of days to expiration
        ivs: List of implied volatilities
        
    Returns:
        Interpolation function or None if insufficient data
    """
    if not HAS_NUMPY or not HAS_SCIPY:
        logger.warning("Missing dependencies (numpy, scipy) for term structure analysis")
        return None
        
    if len(days) < 2 or len(ivs) < 2:
        logger.warning("Insufficient data for term structure: need at least 2 points")
        return None
        
    days = np.array(days)
    ivs = np.array(ivs)
    
    # Sort by days to expiry
    sort_idx = days.argsort()
    days = days[sort_idx]
    ivs = ivs[sort_idx]
    
    try:
        # Create interpolation spline
        spline = interp1d(days, ivs, kind='linear', fill_value="extrapolate")
        
        def term_spline(dte: float) -> float:
            """Get implied volatility for given days to expiry."""
            if dte < days[0]:  
                return float(ivs[0])
            elif dte > days[-1]:
                return float(ivs[-1])
            else:  
                return float(spline(dte))
        
        logger.debug(f"Built term structure with {len(days)} points from {days[0]:.1f} to {days[-1]:.1f} days")
        return term_spline
        
    except Exception as e:
        logger.error(f"Failed to build term structure: {e}")
        return None


def yang_zhang_volatility(price_history) -> float:
    """
    Calculate Yang-Zhang realized volatility estimator.
    More accurate than close-to-close volatility.
    
    Args:
        price_history: DataFrame with Open, High, Low, Close columns (or None if pandas unavailable)
        
    Returns:
        Annualized Yang-Zhang volatility
    """
    if not HAS_PANDAS or not HAS_NUMPY:
        logger.warning("Missing dependencies (pandas, numpy) for Yang-Zhang volatility calculation")
        return 0.0
        
    if price_history is None:
        logger.warning("No price history provided for Yang-Zhang calculation")
        return 0.0
        
    try:
        if price_history.empty or len(price_history) < 2:
            logger.warning("Insufficient price history for Yang-Zhang calculation")
            return 0.0
            
        # Required columns: Open, High, Low, Close
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in price_history.columns for col in required_cols):
            logger.warning("Missing OHLC columns for Yang-Zhang calculation")
            return 0.0
            
        df = price_history[required_cols].dropna()
        if len(df) < 2:
            logger.warning("Insufficient clean data for Yang-Zhang calculation")
            return 0.0
            
        # Yang-Zhang volatility calculation
        o = np.log(df['Open'])
        h = np.log(df['High'])
        l = np.log(df['Low'])
        c = np.log(df['Close'])
        
        # Overnight returns (close to next open)
        overnight = o[1:].values - c[:-1].values
        
        # Close-to-open returns
        co = o - c.shift(1)
        co = co.dropna()
        
        # High-low variance
        hl = h - l
        
        # Close-to-open variance
        cc = c - o
        
        # Yang-Zhang estimator components
        overnight_var = np.var(overnight, ddof=1) if len(overnight) > 1 else 0
        co_var = np.var(co, ddof=1) if len(co) > 1 else 0
        hl_var = np.mean(hl ** 2) if len(hl) > 0 else 0
        cc_var = np.var(cc, ddof=1) if len(cc) > 1 else 0
        
        # Yang-Zhang volatility (annualized)
        k = 0.34 / (1.34 + (len(df) + 1) / (len(df) - 1))
        yz_var = overnight_var + k * co_var + (1 - k) * (hl_var + cc_var)
        
        volatility = np.sqrt(yz_var * 252)  # Annualized
        logger.debug(f"Yang-Zhang volatility calculated: {volatility:.4f}")
        
        return volatility
        
    except Exception as e:
        logger.error(f"Yang-Zhang volatility calculation failed: {e}")
        return 0.0


def calculate_calendar_spread_metrics(atm_ivs: Dict[str, float], 
                                    underlying_price: float,
                                    straddle_price: Optional[float] = None, 
                                    price_history: Optional[Any] = None) -> Dict[str, Any]:
    """
    Calculate calendar spread and term structure metrics.
    Returns trading recommendation based on volatility analysis.
    
    Implements the exact strategy logic:
    - Term structure slope: front vs 45D (threshold: <= -0.00406)
    - IV30/RV30 ratio: IV overpriced vs realized (threshold: >= 1.25)
    - Volume signal: 30-day average volume (threshold: >= 1.5M)
    
    Args:
        atm_ivs: Dictionary of {expiration_date: atm_implied_vol}
        underlying_price: Current stock price
        straddle_price: ATM straddle price for expected move calculation
        price_history: Historical OHLC data for RV calculation
        
    Returns:
        Dictionary with analysis results and trading recommendation
    """
    # For basic functionality, we can work without numpy/pandas
    # but some advanced features will be limited
    try:
        if len(atm_ivs) < 2:
            return {"error": "Need at least 2 expirations for term structure analysis"}
            
        # Convert expiration dates to days to expiry
        today = datetime.now().date()
        dtes = []
        ivs = []
        
        for exp_date_str, iv in atm_ivs.items():
            try:
                exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d").date()
                dte = (exp_date - today).days
                if dte > 0:  # Only future expirations
                    dtes.append(dte)
                    ivs.append(iv)
            except Exception as e:
                logger.warning(f"Invalid expiration date format '{exp_date_str}': {e}")
                continue
                
        if len(dtes) < 2:
            return {"error": "Need at least 2 valid future expirations"}
            
        # Build term structure
        term_spline = build_term_structure(dtes, ivs)
        if term_spline is None:
            return {"error": "Failed to build term structure"}
            
        metrics = {}
        
        # 1. Term structure slope (first expiry to 45 days)
        first_dte = min(dtes)
        if first_dte < 45:
            slope_end = 45
        else:
            # Use second expiration if first is > 45 days
            sorted_dtes = sorted(dtes)
            slope_end = sorted_dtes[1] if len(sorted_dtes) > 1 else first_dte + 15
            
        ts_slope = (term_spline(slope_end) - term_spline(first_dte)) / (slope_end - first_dte)
        metrics['term_structure_slope'] = ts_slope
        metrics['ts_slope_signal'] = ts_slope <= -0.00406  # Bearish term structure (strategy threshold)
        
        logger.debug(f"Term structure slope: {ts_slope:.6f} (signal: {metrics['ts_slope_signal']})")
        
        # 2. IV30 vs RV30 ratio
        iv30 = term_spline(30)
        metrics['iv30'] = iv30
        
        if price_history is not None and not price_history.empty:
            rv30 = yang_zhang_volatility(price_history.tail(30))  # Last 30 days
            metrics['rv30'] = rv30
            if rv30 > 0:
                iv_rv_ratio = iv30 / rv30
                metrics['iv_rv_ratio'] = iv_rv_ratio
                metrics['iv_rv_signal'] = iv_rv_ratio >= 1.25  # IV > RV indicates opportunity (strategy threshold)
                logger.debug(f"IV30/RV30 ratio: {iv_rv_ratio:.2f} (signal: {metrics['iv_rv_signal']})")
            else:
                metrics['iv_rv_ratio'] = None
                metrics['iv_rv_signal'] = False
                logger.warning("RV30 calculation returned zero or invalid value")
        else:
            metrics['rv30'] = None
            metrics['iv_rv_ratio'] = None
            metrics['iv_rv_signal'] = False
            logger.debug("No price history available for RV calculation")
            
        # 3. Expected move calculation
        if straddle_price and underlying_price > 0:
            expected_move_pct = (straddle_price / underlying_price) * 100
            metrics['expected_move_pct'] = expected_move_pct
            logger.debug(f"Expected move: {expected_move_pct:.1f}%")
        else:
            metrics['expected_move_pct'] = None
            
        # 4. Volume analysis (if price history available)
        if price_history is not None and 'Volume' in price_history.columns:
            recent_volume = price_history['Volume'].tail(30).mean()
            metrics['avg_volume_30d'] = recent_volume
            metrics['volume_signal'] = recent_volume >= 1_500_000  # High volume threshold (strategy threshold)
            logger.debug(f"30D avg volume: {recent_volume:,.0f} (signal: {metrics['volume_signal']})")
        else:
            metrics['avg_volume_30d'] = None
            metrics['volume_signal'] = False
            logger.debug("No volume data available for liquidity analysis")
            
        # 5. Overall recommendation (strategy logic)
        signals = [
            metrics.get('ts_slope_signal', False),
            metrics.get('iv_rv_signal', False),
            metrics.get('volume_signal', False)
        ]
        
        signal_count = sum(signals)
        if signal_count >= 2:
            recommendation = "BULLISH - Calendar spread opportunity detected"
        elif signal_count == 1:
            recommendation = "NEUTRAL - Some positive signals"
        else:
            recommendation = "BEARISH - No clear calendar spread opportunity"
            
        metrics['recommendation'] = recommendation
        metrics['signal_count'] = signal_count
        
        logger.info(f"Calendar analysis complete: {signal_count}/3 signals, {recommendation}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Calendar spread calculation failed: {e}")
        return {"error": f"Analysis failed: {str(e)}"}


def summarize_chain_for_atm(chain, price: float) -> Dict[str, Any]:
    """
    Summarize option chain for at-the-money analysis.
    
    Args:
        chain: Option chain object with .calls and .puts DataFrames
        price: Current underlying price
        
    Returns:
        Dictionary with ATM option summary
    """
    try:
        from .utils import ensure_numeric_cols, nearest_strike_row
        
        calls = ensure_numeric_cols(chain.calls.copy())
        puts = ensure_numeric_cols(chain.puts.copy())
        
        call_atm = nearest_strike_row(calls, price)
        put_atm = nearest_strike_row(puts, price)
        
        if call_atm is None or put_atm is None:
            return {"error": "Unable to locate ATM rows (calls/puts)."}
        
        def _calculate_mid_price(row):
            """Calculate mid price from bid/ask or use last price."""
            bid = float(row.get("bid", np.nan))
            ask = float(row.get("ask", np.nan))
            
            if np.isfinite(bid) and np.isfinite(ask) and ask >= bid:
                return (bid + ask) / 2.0
            
            last_price = row.get("lastPrice", np.nan)
            return float(last_price) if np.isfinite(last_price) else np.nan
        
        call_mid = _calculate_mid_price(call_atm)
        put_mid = _calculate_mid_price(put_atm)
        
        straddle_mid = call_mid + put_mid if np.isfinite(call_mid) and np.isfinite(put_mid) else np.nan
        
        # Calculate average ATM IV
        ivs = [
            float(call_atm.get("impliedVolatility", np.nan)), 
            float(put_atm.get("impliedVolatility", np.nan))
        ]
        ivs = [v for v in ivs if np.isfinite(v)]
        atm_iv = float(np.mean(ivs)) if ivs else np.nan
        
        result = {
            "atm_strike_call": float(call_atm["strike"]),
            "atm_strike_put": float(put_atm["strike"]),
            "call_mid": float(call_mid) if np.isfinite(call_mid) else None,
            "put_mid": float(put_mid) if np.isfinite(put_mid) else None,
            "straddle_mid": float(straddle_mid) if np.isfinite(straddle_mid) else None,
            "atm_iv": float(atm_iv) if np.isfinite(atm_iv) else None,
        }
        
        iv_display = f"{result['atm_iv']:.4f}" if result['atm_iv'] is not None else 'N/A'
        logger.debug(f"ATM summary: strike={result['atm_strike_call']}, IV={iv_display}")
        
        return result
        
    except Exception as e:
        logger.error(f"ATM chain summarization failed: {e}")
        return {"error": "Exception while summarizing ATM chain."}