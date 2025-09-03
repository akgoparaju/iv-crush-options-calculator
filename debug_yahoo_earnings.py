#!/usr/bin/env python3
"""
Debug Yahoo Finance earnings data for CRM
"""

import sys
from pathlib import Path
import yfinance as yf
from datetime import datetime
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def debug_yahoo_earnings(symbol="CRM"):
    """Debug Yahoo Finance earnings data directly using yfinance"""
    
    print(f"=== YAHOO FINANCE EARNINGS DEBUG FOR {symbol} ===")
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Test earnings_dates property
        print("🔍 Testing earnings_dates property...")
        earnings_dates = ticker.earnings_dates
        print(f"Raw earnings_dates type: {type(earnings_dates)}")
        print(f"Raw earnings_dates:\n{earnings_dates}")
        
        if earnings_dates is not None and not earnings_dates.empty:
            print(f"\n📊 Earnings dates shape: {earnings_dates.shape}")
            print(f"Index type: {type(earnings_dates.index)}")
            print(f"Columns: {list(earnings_dates.columns) if hasattr(earnings_dates, 'columns') else 'N/A'}")
            
            # Check for future earnings
            now = datetime.now().date()
            print(f"Current date: {now}")
            
            print("\n📅 All earnings dates:")
            for idx, row in earnings_dates.iterrows():
                earnings_date = idx.date()
                is_future = earnings_date > now
                print(f"  {earnings_date} (Future: {is_future}) - {row.to_dict()}")
            
            # Look for future earnings
            future_earnings = earnings_dates[earnings_dates.index.date > now]
            print(f"\n🔮 Future earnings count: {len(future_earnings)}")
            
            if not future_earnings.empty:
                next_earnings_row = future_earnings.iloc[0]
                earnings_date = next_earnings_row.name.date()
                print(f"✅ Next earnings date: {earnings_date}")
                print(f"   Row data: {next_earnings_row.to_dict()}")
            else:
                print("❌ No future earnings found")
        else:
            print("❌ No earnings_dates data available")
        
        # Also try calendar property
        print("\n🔍 Testing calendar property...")
        try:
            calendar = ticker.calendar
            print(f"Calendar data: {calendar}")
        except Exception as e:
            print(f"❌ Calendar error: {e}")
            
        # Try earnings property
        print("\n🔍 Testing earnings property...")
        try:
            earnings = ticker.earnings
            print(f"Earnings data: {earnings}")
        except Exception as e:
            print(f"❌ Earnings error: {e}")
            
    except Exception as e:
        print(f"❌ Yahoo Finance Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_yahoo_earnings("CRM")