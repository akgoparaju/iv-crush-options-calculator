#!/usr/bin/env python3
"""
Debug straddle options data and Greeks calculation
"""

import sys
from pathlib import Path
import yfinance as yf
from datetime import datetime
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def debug_straddle_options(symbol="CRM", strike=252.5, expiration="2025-09-05"):
    """Debug options data for straddle Greeks calculation"""
    
    print(f"=== STRADDLE OPTIONS DATA DEBUG FOR {symbol} ===")
    print(f"Strike: ${strike}, Expiration: {expiration}")
    print()
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Get options chain for the expiration
        print(f"📊 Getting options chain for {expiration}...")
        options_chain = ticker.option_chain(expiration)
        
        print(f"Options chain type: {type(options_chain)}")
        print(f"Has calls: {hasattr(options_chain, 'calls')}")
        print(f"Has puts: {hasattr(options_chain, 'puts')}")
        
        if hasattr(options_chain, 'calls'):
            calls_df = options_chain.calls
            puts_df = options_chain.puts
            
            print(f"\n📋 Calls DataFrame shape: {calls_df.shape}")
            print(f"Calls columns: {list(calls_df.columns)}")
            
            print(f"\n📋 Puts DataFrame shape: {puts_df.shape}")
            print(f"Puts columns: {list(puts_df.columns)}")
            
            # Find ATM options (closest to strike)
            target_strike = strike
            
            # Find closest call
            calls_diff = abs(calls_df['strike'] - target_strike)
            closest_call_idx = calls_diff.idxmin()
            atm_call = calls_df.loc[closest_call_idx]
            
            # Find closest put
            puts_diff = abs(puts_df['strike'] - target_strike)
            closest_put_idx = puts_diff.idxmin()
            atm_put = puts_df.loc[closest_put_idx]
            
            print(f"\n🔍 ATM CALL (Strike: {atm_call['strike']}):")
            print(f"  Bid: {atm_call.get('bid', 'N/A')}")
            print(f"  Ask: {atm_call.get('ask', 'N/A')}")
            print(f"  Last Price: {atm_call.get('lastPrice', 'N/A')}")
            print(f"  Volume: {atm_call.get('volume', 'N/A')}")
            print(f"  Open Interest: {atm_call.get('openInterest', 'N/A')}")
            print(f"  Implied Volatility: {atm_call.get('impliedVolatility', 'N/A')}")
            print(f"  Delta: {atm_call.get('delta', 'N/A')}")
            print(f"  Gamma: {atm_call.get('gamma', 'N/A')}")
            print(f"  Theta: {atm_call.get('theta', 'N/A')}")
            print(f"  Vega: {atm_call.get('vega', 'N/A')}")
            
            print(f"\n🔍 ATM PUT (Strike: {atm_put['strike']}):")
            print(f"  Bid: {atm_put.get('bid', 'N/A')}")
            print(f"  Ask: {atm_put.get('ask', 'N/A')}")
            print(f"  Last Price: {atm_put.get('lastPrice', 'N/A')}")
            print(f"  Volume: {atm_put.get('volume', 'N/A')}")
            print(f"  Open Interest: {atm_put.get('openInterest', 'N/A')}")
            print(f"  Implied Volatility: {atm_put.get('impliedVolatility', 'N/A')}")
            print(f"  Delta: {atm_put.get('delta', 'N/A')}")
            print(f"  Gamma: {atm_put.get('gamma', 'N/A')}")
            print(f"  Theta: {atm_put.get('theta', 'N/A')}")
            print(f"  Vega: {atm_put.get('vega', 'N/A')}")
            
            # Check if Greeks columns exist and have data
            greeks_cols = ['delta', 'gamma', 'theta', 'vega']
            print(f"\n📊 GREEKS DATA ANALYSIS:")
            for col in greeks_cols:
                if col in calls_df.columns:
                    non_null_calls = calls_df[col].notna().sum()
                    non_zero_calls = (calls_df[col] != 0).sum()
                    print(f"  {col.upper()} - Calls: {non_null_calls} non-null, {non_zero_calls} non-zero")
                else:
                    print(f"  {col.upper()} - ❌ Column missing in calls")
                
                if col in puts_df.columns:
                    non_null_puts = puts_df[col].notna().sum()
                    non_zero_puts = (puts_df[col] != 0).sum()
                    print(f"  {col.upper()} - Puts: {non_null_puts} non-null, {non_zero_puts} non-zero")
                else:
                    print(f"  {col.upper()} - ❌ Column missing in puts")
            
        else:
            print("❌ Options chain does not have calls/puts attributes")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_straddle_options("CRM")