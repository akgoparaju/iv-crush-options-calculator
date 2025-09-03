#!/usr/bin/env python3
"""
Debug Alpha Vantage raw API response for CRM earnings
"""

import os
import sys
import json
import requests
from pathlib import Path

# Load environment variables
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

def test_alpha_vantage_earnings_raw(symbol="CRM"):
    """Test raw Alpha Vantage earnings API for debugging"""
    
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not found in environment")
        return
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "EARNINGS",
        "symbol": symbol,
        "apikey": api_key
    }
    
    print(f"=== ALPHA VANTAGE RAW API TEST FOR {symbol} ===")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print()
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print("✅ Raw API Response:")
        print(json.dumps(data, indent=2, default=str))
        
        # Check for quarterly earnings specifically
        quarterly = data.get("quarterlyEarnings", [])
        print(f"\n📊 Quarterly Earnings Count: {len(quarterly)}")
        
        if quarterly:
            print("\n📅 Recent Quarterly Earnings:")
            for i, earning in enumerate(quarterly[:5]):  # Show first 5
                reported_date = earning.get("reportedDate")
                eps_estimate = earning.get("estimatedEPS", "N/A")
                eps_actual = earning.get("reportedEPS", "N/A")
                print(f"  {i+1}. Date: {reported_date}, Est EPS: {eps_estimate}, Actual EPS: {eps_actual}")
        
        # Save to file
        output_file = f"logs/alpha_vantage_raw_{symbol}_{os.getpid()}.json"
        os.makedirs("logs", exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"\n📄 Raw data saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Alpha Vantage API Error: {e}")

if __name__ == "__main__":
    test_alpha_vantage_earnings_raw("CRM")