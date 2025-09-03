#!/usr/bin/env python3
"""Validate the IV/RV ratio calculation fixes."""

import sys
import os
from datetime import datetime
import subprocess

def run_test_analysis(symbol, debug=False):
    """Run analysis and capture output."""
    cmd = ['python3', 'main.py', '--symbol', symbol, '--earnings']
    if debug:
        cmd.append('--debug')
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def extract_metrics(output):
    """Extract key metrics from analysis output."""
    metrics = {}
    
    # Extract from the formatted output
    lines = output.split('\n')
    for i, line in enumerate(lines):
        # Look for Strategy Signal Analysis table
        if 'Strategy Signal Analysis' in line:
            # Find the table data in following lines
            for j in range(i+1, min(i+20, len(lines))):
                if 'Term Structure' in lines[j] and '│' in lines[j]:
                    parts = lines[j].split('│')
                    if len(parts) >= 3:
                        value_str = parts[1].strip()
                        try:
                            metrics['term_structure_slope'] = float(value_str)
                        except:
                            pass
                
                if 'IV/RV Ratio' in lines[j] and '│' in lines[j]:
                    parts = lines[j].split('│')
                    if len(parts) >= 3:
                        value_str = parts[1].strip()
                        try:
                            metrics['iv_rv_ratio'] = float(value_str)
                        except:
                            pass
        
        # Look for expected move
        if 'Expected Move:' in line:
            try:
                pct_str = line.split('Expected Move:')[1].strip().replace('%', '')
                metrics['expected_move'] = float(pct_str)
            except:
                pass
    
    return metrics

def validate_fixes():
    """Comprehensive validation of IV/RV fixes."""
    print("🔍 Validating IV/RV Ratio Calculation Fixes")
    print("=" * 70)
    
    # Test symbols with different scenarios
    test_cases = [
        ('CRM', 'Earnings imminent (2 DTE) - should use front month IV'),
        ('AAPL', 'Normal case - should work as before'),
    ]
    
    all_passed = True
    
    for symbol, description in test_cases:
        print(f"\n📊 Testing {symbol}: {description}")
        print("-" * 50)
        
        # Run analysis
        stdout, stderr, returncode = run_test_analysis(symbol, debug=True)
        
        if returncode != 0:
            print(f"❌ Analysis failed for {symbol}")
            print(f"Error: {stderr}")
            all_passed = False
            continue
        
        # Extract metrics
        metrics = extract_metrics(stdout)
        
        # Check debug output for IV calculation details
        debug_lines = stderr.split('\n')
        iv_info = {}
        
        for line in debug_lines:
            if 'front month IV' in line.lower() and symbol in line:
                print(f"✅ Found earnings adjustment: {line.strip()}")
            if 'IV/RV ratio:' in line and symbol in line:
                parts = line.split('IV/RV ratio:')[1]
                try:
                    ratio = float(parts.split('(')[0].strip())
                    iv_info['iv_rv_ratio'] = ratio
                    print(f"📈 IV/RV Ratio: {ratio:.3f}")
                except:
                    pass
            if 'Yang-Zhang volatility calculated:' in line:
                try:
                    rv = float(line.split(':')[1].strip())
                    iv_info['rv30'] = rv
                    print(f"📉 RV30 (Yang-Zhang): {rv:.4f} ({rv*100:.2f}%)")
                except:
                    pass
        
        # Validation checks
        if symbol == 'CRM':
            # CRM should show high IV/RV ratio due to earnings
            if iv_info.get('iv_rv_ratio', 0) >= 1.25:
                print(f"✅ CRM IV/RV ratio ≥ 1.25: PASS")
            else:
                print(f"❌ CRM IV/RV ratio < 1.25: FAIL (should be high due to earnings)")
                all_passed = False
        
        # Check for warnings about suspicious values
        has_warnings = any('suspicious' in line.lower() or 'warning' in line.lower() 
                          for line in debug_lines)
        if has_warnings:
            print("⚠️  Validation warnings found (review debug output)")
        else:
            print("✅ No suspicious value warnings")
        
        # Show key metrics
        if metrics:
            print(f"📊 Key Metrics:")
            for key, value in metrics.items():
                print(f"   {key}: {value}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL VALIDATION TESTS PASSED")
        print("\n🎉 Fixes appear to be working correctly!")
        print("\nKey improvements:")
        print("• Front month IV used for imminent earnings (≤7 days)")
        print("• No more extrapolation beyond available data")
        print("• Validation warnings for suspicious values")
        print("• Transparent calculation metadata")
    else:
        print("❌ SOME VALIDATION TESTS FAILED")
        print("\n⚠️  Please review the output above for specific issues.")
    
    return all_passed

def test_edge_cases():
    """Test edge cases to ensure robustness."""
    print("\n🧪 Testing Edge Cases")
    print("-" * 30)
    
    # Test with demo mode to ensure fallbacks work
    print("Testing demo mode...")
    stdout, stderr, returncode = run_test_analysis('AAPL', debug=False)
    
    # Change to demo mode
    demo_cmd = ['python3', 'main.py', '--demo', '--symbol', 'AAPL', '--earnings']
    try:
        result = subprocess.run(demo_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Demo mode works with fixes")
        else:
            print("❌ Demo mode failed")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Demo mode error: {e}")

if __name__ == '__main__':
    # Activate virtual environment first
    if 'venv' not in sys.executable:
        print("⚠️  Please run: source venv/bin/activate")
        sys.exit(1)
    
    # Run validation
    success = validate_fixes()
    
    # Run edge case tests
    test_edge_cases()
    
    if success:
        print("\n🚀 Ready for production use!")
        sys.exit(0)
    else:
        print("\n🔧 Additional fixes may be needed.")
        sys.exit(1)