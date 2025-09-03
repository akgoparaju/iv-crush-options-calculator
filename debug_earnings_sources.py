#!/usr/bin/env python3
"""
Debug script to dump JSON output from all earnings data sources
for systematic troubleshooting of Issue 2: CRM earnings not found
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

# Import our providers
from options_trader.providers.alpha_vantage import AlphaVantageProvider
from options_trader.providers.yahoo import YahooProvider
from options_trader.providers.finnhub import FinnhubProvider
from options_trader.providers.tradier import TradierProvider
from options_trader.providers.demo import DemoProvider

def debug_earnings_sources(symbol="CRM"):
    """Debug all earnings data sources for given symbol"""
    
    print(f"=== DEBUGGING EARNINGS SOURCES FOR {symbol} ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test each provider
    providers = [
        ("Demo", DemoProvider()),
        ("Alpha Vantage", AlphaVantageProvider()),
        ("Yahoo Finance", YahooProvider()),
        ("Finnhub", FinnhubProvider()),
        ("Tradier", TradierProvider())
    ]
    
    results = {}
    
    for name, provider in providers:
        print(f"=== {name.upper()} PROVIDER ===")
        try:
            # Test if provider is available
            if not hasattr(provider, 'get_next_earnings'):
                print(f"❌ Provider {name} does not have get_next_earnings method")
                results[name] = {"error": "No get_next_earnings method"}
                continue
                
            # Get earnings data
            earnings_data = provider.get_next_earnings(symbol)
            
            # Convert EarningsEvent to dict for JSON serialization
            if earnings_data:
                earnings_dict = {
                    "symbol": earnings_data.symbol,
                    "date": earnings_data.date.isoformat(),
                    "timing": earnings_data.timing,
                    "confirmed": earnings_data.confirmed,
                    "source": earnings_data.source,
                    "is_before_market": earnings_data.is_before_market,
                    "is_after_market": earnings_data.is_after_market
                }
                earnings_data = earnings_dict
            
            # Pretty print the JSON
            print(f"✅ {name} Response:")
            print(json.dumps(earnings_data, indent=2, default=str))
            
            results[name] = earnings_data
            
        except Exception as e:
            print(f"❌ {name} Error: {e}")
            results[name] = {"error": str(e)}
        
        print("-" * 80)
        print()
    
    # Save results to file
    output_file = f"logs/earnings_debug_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("logs", exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"📄 Results saved to: {output_file}")
    
    # Summary analysis
    print("\n=== SUMMARY ANALYSIS ===")
    for name, result in results.items():
        if "error" in result:
            print(f"❌ {name}: {result['error']}")
        else:
            # Analyze the response structure
            if result and isinstance(result, dict):
                if "earnings_date" in result:
                    print(f"✅ {name}: Found earnings_date = {result['earnings_date']}")
                elif "earnings" in result:
                    print(f"✅ {name}: Found earnings structure")
                else:
                    print(f"⚠️  {name}: Response received but no clear earnings date")
            else:
                print(f"⚠️  {name}: Empty or invalid response")

if __name__ == "__main__":
    # Test with CRM as requested by user
    debug_earnings_sources("CRM")