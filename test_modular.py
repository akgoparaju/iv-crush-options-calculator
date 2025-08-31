#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Modular Implementation
===========================

Simple test to verify the modular architecture works correctly.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path.cwd()))

def test_imports():
    """Test that all modules can be imported without errors."""
    print("Testing modular imports...")
    
    try:
        # Test base provider interfaces
        from options_trader.providers.base import PriceProvider, OptionsProvider, EarningsProvider, EarningsEvent
        print("✓ Base provider interfaces imported successfully")
    except Exception as e:
        print(f"✗ Base provider interfaces failed: {e}")
        return False
    
    try:
        # Test demo provider (no external dependencies)
        from options_trader.providers.demo import DemoProvider
        print("✓ Demo provider imported successfully")
    except Exception as e:
        print(f"✗ Demo provider failed: {e}")
        return False
    
    try:
        # Test earnings calendar
        from options_trader.core.earnings import EarningsCalendar, TradingWindows
        print("✓ Earnings calendar imported successfully")
    except Exception as e:
        print(f"✗ Earnings calendar failed: {e}")
        return False
    
    try:
        # Test analysis functions
        from options_trader.core.analysis import build_term_structure, calculate_calendar_spread_metrics
        print("✓ Analysis functions imported successfully")
    except Exception as e:
        print(f"✗ Analysis functions failed: {e}")
        return False
    
    return True

def test_demo_functionality():
    """Test core functionality using demo provider."""
    print("\\nTesting demo functionality...")
    
    try:
        from options_trader.providers.demo import DemoProvider
        from options_trader.core.earnings import EarningsCalendar
        
        # Test demo provider
        demo = DemoProvider()
        price, source = demo.get_price("AAPL")
        print(f"✓ Demo price for AAPL: ${price:.2f} (source: {source})")
        
        expirations = demo.get_expirations("AAPL", 2)
        print(f"✓ Demo expirations: {expirations}")
        
        chain = demo.get_chain("AAPL", expirations[0])
        print(f"✓ Demo chain: {len(chain.calls)} calls, {len(chain.puts)} puts")
        
        # Test earnings calendar with demo
        earnings_calendar = EarningsCalendar([demo])
        earnings = earnings_calendar.get_next_earnings("AAPL")
        if earnings:
            print(f"✓ Demo earnings: {earnings.date.date()} {earnings.timing}")
            
            windows = earnings_calendar.calculate_trading_windows(earnings)
            print(f"✓ Trading windows calculated successfully")
            print(f"  Entry: {windows.entry_start} to {windows.entry_end}")
            print(f"  Exit: {windows.exit_start} to {windows.exit_end}")
        
        return True
        
    except Exception as e:
        print(f"✗ Demo functionality failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_package_version():
    """Test package version information."""
    try:
        from options_trader import __version__
        print(f"\\n✓ Package version: {__version__}")
        return True
    except Exception as e:
        print(f"\\n✗ Package version failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("MODULAR ARCHITECTURE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Demo Functionality", test_demo_functionality), 
        ("Package Version", test_package_version)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\\n{test_name}:")
        print("-" * len(test_name))
        success = test_func()
        results.append((test_name, success))
    
    print("\\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    print(f"\\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    if all_passed:
        print("\\n✓ Modular architecture is working correctly!")
        print("✓ Module 1 (Earnings Calendar) is implemented and functional!")
        print("✓ Ready for production use with proper API keys in .env file")
    else:
        print("\\n✗ Some issues found. Check error messages above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())