#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Utilities
==============

Utility functions for options data processing and analysis.
"""

import logging
import numpy as np
import pandas as pd
from typing import Optional

logger = logging.getLogger("options_trader.utils")


def ensure_numeric_cols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure key option columns are numeric.
    
    Args:
        df: DataFrame with option data
        
    Returns:
        DataFrame with numeric columns
    """
    if df is None or df.empty:
        return df
    
    numeric_cols = ["strike", "impliedVolatility", "bid", "ask", "lastPrice"]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    return df


def nearest_strike_row(df: pd.DataFrame, price: float) -> Optional[pd.Series]:
    """
    Find the option row closest to the given price (ATM).
    
    Args:
        df: DataFrame with option data including 'strike' column
        price: Target price to find nearest strike
        
    Returns:
        Series representing the nearest strike row, or None if not found
    """
    try:
        if df is None or df.empty:
            logger.warning("Empty DataFrame passed to nearest_strike_row")
            return None
        
        df = ensure_numeric_cols(df)
        
        if "strike" not in df.columns:
            logger.error("No 'strike' column found in DataFrame")
            return None
        
        # Find the row with strike closest to price
        strike_diff = (df["strike"] - price).abs()
        nearest_idx = strike_diff.idxmin()
        
        result = df.loc[nearest_idx]
        logger.debug(f"Found nearest strike {result['strike']:.2f} for price ${price:.2f}")
        
        return result
        
    except Exception as e:
        logger.error(f"nearest_strike_row failed: {e}")
        return None